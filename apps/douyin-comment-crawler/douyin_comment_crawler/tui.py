from __future__ import annotations

import curses
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


APP_TITLE = "抖音评论采集操作台"
PYTHON_BIN = os.getenv("PYTHON_BIN", "python3")
PASTE_START = "\x1b[200~"
PASTE_END = "\x1b[201~"


@dataclass(frozen=True)
class Tuning:
    page_size: int = int(os.getenv("CRAWLER_PAGE_SIZE", "50"))
    workers: int = int(os.getenv("CRAWLER_WORKERS", "4"))
    min_delay: float = float(os.getenv("CRAWLER_MIN_DELAY", "0.5"))
    max_delay: float = float(os.getenv("CRAWLER_MAX_DELAY", "1.5"))


class Back(Exception):
    pass


def tuning_args(tuning: Tuning) -> list[str]:
    return [
        "--page-size",
        str(tuning.page_size),
        "--workers",
        str(tuning.workers),
        "--min-delay",
        str(tuning.min_delay),
        "--max-delay",
        str(tuning.max_delay),
    ]


def build_video_command(target: str, target_type: str, include_replies: bool, tuning: Tuning) -> list[str]:
    target_arg = "--url" if target_type == "url" else "--aweme-id"
    command = [PYTHON_BIN, "-m", "douyin_comment_crawler", "crawl", "video", target_arg, target]
    if include_replies:
        command.append("--include-replies")
    return command + tuning_args(tuning)


def build_account_command(target: str, target_type: str, include_replies: bool, tuning: Tuning) -> list[str]:
    target_arg = "--url" if target_type == "url" else "--sec-user-id"
    command = [PYTHON_BIN, "-m", "douyin_comment_crawler", "crawl", "account", target_arg, target]
    if include_replies:
        command.append("--include-replies")
    return command + tuning_args(tuning)


def build_replies_command(job_id: str, tuning: Tuning) -> list[str]:
    return [PYTHON_BIN, "-m", "douyin_comment_crawler", "crawl", "replies", "--job-id", job_id] + tuning_args(tuning)


def build_resume_command(job_id: str, tuning: Tuning) -> list[str]:
    return [PYTHON_BIN, "-m", "douyin_comment_crawler", "resume", "--job-id", job_id] + tuning_args(tuning)


def build_batch_command(path: str, include_replies: bool, tuning: Tuning) -> list[str]:
    command = [PYTHON_BIN, "-m", "douyin_comment_crawler", "batch", "--file", path]
    if include_replies:
        command.append("--include-replies")
    return command + tuning_args(tuning)


def build_export_command(job_id: str, fmt: str, exclude_flags: list[str]) -> list[str]:
    command = [PYTHON_BIN, "-m", "douyin_comment_crawler", "export", "--job-id", job_id, "--format", fmt]
    for flag in exclude_flags:
        command.extend(["--exclude-flag", flag])
    return command


def build_doctor_command(aweme_id: str = "0", timeout: float = 5) -> list[str]:
    return [PYTHON_BIN, "-m", "douyin_comment_crawler", "doctor", "--aweme-id", aweme_id, "--timeout", str(timeout)]


def parse_status_output(output: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in output.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def status_summary(status: dict[str, str]) -> str:
    if not status:
        return "暂无任务状态"
    job_id = status.get("job_id", "-")
    short_job = job_id[:8] if len(job_id) > 8 else job_id
    state = status.get("status", "-")
    saved = status.get("comments_saved", status.get("comments", "0"))
    requests = status.get("api_requests", "0")
    return f"{short_job} | {state} | saved={saved} | requests={requests}"


def format_status_rows(status: dict[str, str]) -> list[tuple[str, str, str]]:
    groups = [
        ("任务", ["job_id", "target_type", "platform", "status"]),
        ("指标", ["comments", "videos_seen", "comments_seen", "comments_saved", "replies_seen", "api_requests"]),
        ("风控", ["cooldown_until", "last_error"]),
    ]
    rows: list[tuple[str, str, str]] = []
    for group, keys in groups:
        for key in keys:
            if key in status:
                rows.append((group, key, status[key]))
    for key, value in status.items():
        if not any(key == existing_key for _, existing_key, _ in rows):
            rows.append(("其他", key, value))
    return rows


def run_command(command: list[str]) -> tuple[int, str]:
    try:
        completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    except KeyboardInterrupt:
        return 130, "已取消当前命令。可返回任务快捷操作后选择 Resume、补采回复或导出。\n"
    return completed.returncode, completed.stdout


def status_command(job_id: str = "") -> list[str]:
    command = [PYTHON_BIN, "-m", "douyin_comment_crawler", "status"]
    if job_id:
        command.extend(["--job-id", job_id])
    return command


def normalize_paste_text(text: str) -> str:
    return text.replace(PASTE_START, "").replace(PASTE_END, "")


class Tui:
    def __init__(self, screen) -> None:
        self.screen = screen
        self.tuning = Tuning()
        self.last_job_id = ""
        self.global_status: dict[str, str] = {}
        curses.curs_set(0)
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)
        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_CYAN)
        self.colors = {
            "title": curses.color_pair(1) | curses.A_BOLD,
            "ok": curses.color_pair(2) | curses.A_BOLD,
            "warn": curses.color_pair(3) | curses.A_BOLD,
            "err": curses.color_pair(4) | curses.A_BOLD,
            "metric": curses.color_pair(5) | curses.A_BOLD,
            "selected": curses.color_pair(6) | curses.A_BOLD,
            "dim": curses.A_DIM,
            "bold": curses.A_BOLD,
        }

    def run(self) -> None:
        self.check_ready()
        while True:
            try:
                choice = self.menu(
                    "主菜单",
                    [
                        ("采集单个视频", self.page_video),
                        ("采集账号作品主评论", self.page_account),
                        ("为已有任务补采回复", self.page_replies),
                        ("批量文件采集", self.page_batch),
                        ("查看任务状态", self.page_status),
                        ("实时监控任务", self.page_watch),
                        ("导出任务数据", self.page_export),
                        ("Resume 失败/冷却任务", self.page_resume),
                        ("诊断 Download API", self.page_doctor),
                        ("查看账号组健康状态", self.page_health),
                        ("退出", None),
                    ],
                )
            except Back:
                continue
            if choice is None:
                return
            try:
                choice()
            except Back:
                continue

    def check_ready(self) -> None:
        Path("data").mkdir(exist_ok=True)
        Path("exports").mkdir(exist_ok=True)
        code, output = run_command([PYTHON_BIN, "-m", "douyin_comment_crawler", "--help"])
        if code != 0:
            self.message("CLI smoke check 失败", output, "err")

    def draw_header(self, crumb: str) -> None:
        self.screen.erase()
        self.add(0, 2, APP_TITLE, "title")
        self.add(1, 2, f"当前位置: {crumb}", "dim")
        self.add(2, 2, f"默认: page_size={self.tuning.page_size} workers={self.tuning.workers} delay={self.tuning.min_delay}-{self.tuning.max_delay}s/request", "metric")
        self.refresh_global_status()
        self.add(3, 2, f"全局任务: {status_summary(self.global_status)}", self.status_style(self.global_status.get("status", "")))
        self.hline(4)

    def menu(self, crumb: str, items: list[tuple[str, object]]) -> object:
        index = 0
        while True:
            self.draw_header(crumb)
            self.draw_footer("↑/↓ 选择  Enter 确认  b/Esc 返回  q 退出")
            for offset, (label, _) in enumerate(items):
                style = "selected" if offset == index else "bold"
                prefix = "▶ " if offset == index else "  "
                self.add(6 + offset, 4, f"{prefix}{label}", style)
            self.screen.refresh()
            key = self.screen.getch()
            if key in (curses.KEY_UP, ord("k")):
                index = (index - 1) % len(items)
            elif key in (curses.KEY_DOWN, ord("j")):
                index = (index + 1) % len(items)
            elif key in (10, 13, curses.KEY_ENTER):
                return items[index][1]
            elif key in (27, ord("b")):
                raise Back()
            elif key == ord("q"):
                raise SystemExit(0)

    def page_video(self) -> None:
        target_type = self.pick("单视频采集 / 目标类型", [("aweme-id", "aweme-id"), ("url", "url")])
        target = self.prompt("请输入视频 URL" if target_type == "url" else "请输入 aweme-id")
        include = self.pick("是否同时采集回复？大任务建议否", [("否，后续二阶段补采", False), ("是，同时采回复", True)])
        tuning = self.prompt_tuning()
        self.run_job(build_video_command(target, target_type, include, tuning))

    def page_account(self) -> None:
        target_type = self.pick("账号采集 / 目标类型", [("sec-user-id", "sec-user-id"), ("url", "url")])
        target = self.prompt("请输入账号 URL" if target_type == "url" else "请输入 sec-user-id")
        include = self.pick("是否同时采集回复？推荐否", [("否，只采主评论", False), ("是，同时采回复", True)])
        tuning = self.prompt_tuning()
        self.run_job(build_account_command(target, target_type, include, tuning))

    def page_replies(self) -> None:
        job_id = self.prompt("请输入 job_id", self.last_job_id)
        tuning = self.prompt_tuning()
        self.run_job(build_replies_command(job_id, tuning))

    def page_batch(self) -> None:
        path = self.prompt("请输入批量文件路径")
        include = self.pick("是否同时采集回复？推荐否", [("否，只采主评论", False), ("是，同时采回复", True)])
        tuning = self.prompt_tuning()
        self.run_job(build_batch_command(path, include, tuning))

    def page_status(self) -> None:
        job_id = self.prompt("请输入 job_id，留空查看最近任务", self.last_job_id, required=False)
        self.show_command_output("查看状态", status_command(job_id))

    def page_watch(self) -> None:
        job_id = self.prompt("请输入 job_id", self.last_job_id)
        self.watch(job_id)

    def page_export(self) -> None:
        job_id = self.prompt("请输入 job_id", self.last_job_id)
        fmt = self.pick("导出格式", [("csv", "csv"), ("jsonl", "jsonl")])
        flags: list[str] = []
        if self.pick("过滤 empty_text？", [("是", True), ("否", False)]):
            flags.append("empty_text")
        if self.pick("过滤 media_only？", [("是", True), ("否", False)]):
            flags.append("media_only")
        self.show_command_output("导出", build_export_command(job_id, fmt, flags))

    def page_resume(self) -> None:
        job_id = self.prompt("请输入 job_id", self.last_job_id)
        tuning = self.prompt_tuning()
        self.run_job(build_resume_command(job_id, tuning))

    def page_health(self) -> None:
        self.show_command_output("账号组健康状态", [PYTHON_BIN, "-m", "douyin_comment_crawler", "status", "--health"])

    def page_doctor(self) -> None:
        aweme_id = self.prompt("用于探测评论接口的 aweme-id，留空用 0", "0", required=False)
        self.show_command_output("诊断 Download API", build_doctor_command(aweme_id or "0"))

    def pick(self, crumb: str, items: list[tuple[str, object]]) -> object:
        return self.menu(crumb, items)

    def prompt_tuning(self) -> Tuning:
        page_size = int(self.prompt("page_size", str(self.tuning.page_size)))
        workers = int(self.prompt("workers", str(self.tuning.workers)))
        min_delay = float(self.prompt("min_delay", str(self.tuning.min_delay)))
        max_delay = float(self.prompt("max_delay", str(self.tuning.max_delay)))
        self.tuning = Tuning(page_size=page_size, workers=workers, min_delay=min_delay, max_delay=max_delay)
        return self.tuning

    def prompt(self, label: str, default: str = "", required: bool = True) -> str:
        curses.curs_set(1)
        value = default
        error = ""
        while True:
            self.draw_header("输入")
            self.add(5, 2, label, "bold")
            if default:
                self.add(6, 2, f"默认: {default}", "dim")
            self.add(8, 2, f"> {value}")
            if error:
                self.add(10, 2, error, "warn")
            self.draw_footer("Enter 确认  b/Esc 返回  Backspace 删除  支持整段粘贴")
            self.screen.refresh()
            key = self.screen.get_wch()
            if key in (curses.KEY_BACKSPACE, 127, 8):
                value = value[:-1]
                continue
            if key in (10, 13, "\n", "\r", curses.KEY_ENTER):
                if value or not required:
                    curses.curs_set(0)
                    return value
                error = "该项必填。"
                continue
            chunk = self.read_text_chunk(key)
            if chunk == "__BACK__":
                curses.curs_set(0)
                raise Back()
            value += chunk

    def read_text_chunk(self, first_key) -> str:
        if isinstance(first_key, int):
            if first_key == 27:
                return "__BACK__"
            if 32 <= first_key <= 126:
                first = chr(first_key)
            else:
                return ""
        else:
            if first_key == "\x1b":
                first = self.drain_queued_text(prefix="\x1b")
                if first == "\x1b":
                    return "__BACK__"
                return normalize_paste_text(first)
            first = first_key
        return normalize_paste_text(first + self.drain_queued_text())

    def drain_queued_text(self, prefix: str = "") -> str:
        text = prefix
        self.screen.nodelay(True)
        try:
            while True:
                try:
                    key = self.screen.get_wch()
                except curses.error:
                    break
                if isinstance(key, str):
                    text += key
                elif 32 <= key <= 126:
                    text += chr(key)
                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    text = text[:-1]
                else:
                    break
        finally:
            self.screen.nodelay(False)
        return text

    def run_job(self, command: list[str]) -> None:
        self.show_command_output("执行任务", command, capture_job=True)
        if self.last_job_id:
            self.job_actions(self.last_job_id)

    def show_command_output(self, crumb: str, command: list[str], capture_job: bool = False) -> None:
        self.draw_header(crumb)
        self.add(5, 2, "执行命令:", "dim")
        self.add(6, 2, " ".join(command), "bold")
        self.screen.refresh()
        code, output = run_command(command)
        if capture_job:
            status = parse_status_output(output)
            self.last_job_id = status.get("job_id", self.last_job_id)
            if self.last_job_id:
                status_code, status_output = run_command(status_command(self.last_job_id))
                if status_code == 0:
                    output = status_output
                    code = status_code
                    status = parse_status_output(status_output)
            if status:
                self.global_status = status
        self.render_output(crumb, output, code)

    def render_output(self, crumb: str, output: str, code: int) -> None:
        self.draw_header(crumb)
        self.add(5, 2, "结果", "ok" if code == 0 else "err")
        status = parse_status_output(output)
        if status:
            self.render_status_table(status, start_row=7)
        else:
            row = 7
            for line in output.splitlines() or ["<empty>"]:
                self.add(row, 2, line[: max(10, self.screen.getmaxyx()[1] - 4)], self.style_for_line(line))
                row += 1
                if row >= self.screen.getmaxyx()[0] - 3:
                    break
        self.draw_footer("Enter/b/Esc 返回")
        self.wait_enter()

    def watch(self, job_id: str) -> None:
        interval = int(os.getenv("CRAWLER_WATCH_SECONDS", "5"))
        while True:
            code, output = run_command([PYTHON_BIN, "-m", "douyin_comment_crawler", "status", "--job-id", job_id])
            status = parse_status_output(output)
            if status:
                self.global_status = status
            self.draw_header(f"实时监控 / {job_id}")
            row = self.render_status_table(status, start_row=6)
            self.add(row + 1, 2, f"每 {interval}s 刷新。最近 exit={code}", "dim")
            self.draw_footer("r Resume  p 补回复  e 导出  b/Esc 返回  q 退出")
            self.screen.timeout(interval * 1000)
            key = self.screen.getch()
            self.screen.timeout(-1)
            if key in (ord("b"), 27):
                return
            if key == ord("q"):
                raise SystemExit(0)
            if key == ord("r"):
                self.run_job(build_resume_command(job_id, self.tuning))
                return
            if key == ord("p"):
                self.run_job(build_replies_command(job_id, self.tuning))
                return
            if key == ord("e"):
                self.show_command_output("导出", build_export_command(job_id, "csv", ["empty_text", "media_only"]))
                return

    def job_actions(self, job_id: str) -> None:
        while True:
            action = self.menu(
                f"任务快捷操作 / {job_id}",
                [
                    ("实时监控", "watch"),
                    ("查看状态", "status"),
                    ("Resume", "resume"),
                    ("补采回复", "replies"),
                    ("导出 CSV", "export"),
                    ("返回主菜单", "back"),
                ],
            )
            if action == "watch":
                self.watch(job_id)
            elif action == "status":
                self.show_command_output("查看状态", status_command(job_id))
            elif action == "resume":
                self.run_job(build_resume_command(job_id, self.tuning))
            elif action == "replies":
                self.run_job(build_replies_command(job_id, self.tuning))
            elif action == "export":
                self.show_command_output("导出", build_export_command(job_id, "csv", ["empty_text", "media_only"]))
            else:
                return

    def style_for_line(self, line: str) -> str:
        if line.startswith("status=completed"):
            return "ok"
        if line.startswith("status=cooldown") or line.startswith("cooldown_until=") or line.startswith("last_error="):
            return "warn"
        if line.startswith("status=failed"):
            return "err"
        if line.startswith(("comments=", "videos_seen=", "comments_seen=", "comments_saved=", "replies_seen=", "api_requests=")):
            return "metric"
        if line.startswith("job_id="):
            return "bold"
        return ""

    def status_style(self, status: str) -> str:
        if status == "completed":
            return "ok"
        if status == "cooldown":
            return "warn"
        if status == "failed":
            return "err"
        return "metric"

    def render_status_table(self, status: dict[str, str], start_row: int) -> int:
        rows = format_status_rows(status)
        widths = (8, 20)
        row = start_row
        self.add(row, 2, "┌──────────┬──────────────────────┬────────────────────────────────────────┐", "dim")
        row += 1
        self.add(row, 2, "│ 分组     │ 字段                 │ 值                                     │", "bold")
        row += 1
        self.add(row, 2, "├──────────┼──────────────────────┼────────────────────────────────────────┤", "dim")
        row += 1
        for group, key, value in rows:
            style = self.style_for_line(f"{key}={value}")
            value_text = value[:38]
            self.add(row, 2, f"│ {group:<8} │ {key:<20} │ {value_text:<38} │", style)
            row += 1
            if row >= self.screen.getmaxyx()[0] - 4:
                break
        self.add(row, 2, "└──────────┴──────────────────────┴────────────────────────────────────────┘", "dim")
        return row + 1

    def refresh_global_status(self) -> None:
        command = [PYTHON_BIN, "-m", "douyin_comment_crawler", "status"]
        if self.last_job_id:
            command.extend(["--job-id", self.last_job_id])
        code, output = run_command(command)
        if code == 0:
            status = parse_status_output(output)
            if status:
                self.global_status = status

    def add(self, y: int, x: int, text: str, style: str = "") -> None:
        height, width = self.screen.getmaxyx()
        if y >= height:
            return
        attr = self.colors.get(style, 0)
        self.screen.addnstr(y, x, text, max(0, width - x - 1), attr)

    def hline(self, y: int) -> None:
        height, width = self.screen.getmaxyx()
        if y < height:
            self.screen.hline(y, 2, curses.ACS_HLINE, max(0, width - 4), self.colors["dim"])

    def footer(self, text: str) -> None:
        height, _ = self.screen.getmaxyx()
        self.add(height - 2, 2, text, "dim")

    def draw_footer(self, text: str) -> None:
        height, width = self.screen.getmaxyx()
        self.hline(height - 3)
        self.add(height - 2, 2, text, "dim")

    def wait_enter(self) -> None:
        while self.screen.getch() not in (10, 13, curses.KEY_ENTER, 27, ord("b")):
            pass

    def message(self, crumb: str, body: str, style: str = "") -> None:
        self.draw_header(crumb)
        for index, line in enumerate(body.splitlines() or [body]):
            self.add(5 + index, 2, line, style)
        self.footer("Enter 返回")
        self.wait_enter()


def main() -> None:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("TUI 需要交互式终端。请直接在终端运行：python3 scripts/crawler.py", file=sys.stderr)
        raise SystemExit(2)
    curses.wrapper(lambda screen: Tui(screen).run())


if __name__ == "__main__":
    main()
