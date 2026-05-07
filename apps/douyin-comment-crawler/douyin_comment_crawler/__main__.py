from __future__ import annotations

import argparse
from pathlib import Path

from douyin_comment_crawler.adapters import DouyinAdapter
from douyin_comment_crawler.batch import crawl_batch_file
from douyin_comment_crawler.config import load_runtime_config
from douyin_comment_crawler.crawler import crawl_account, crawl_video
from douyin_comment_crawler.exporter import export_job
from douyin_comment_crawler.models import RiskProfile
from douyin_comment_crawler.storage import JobStore


def main() -> None:
    config = load_runtime_config()
    parser = build_parser()
    args = parser.parse_args()
    store = JobStore(Path(args.db_path))

    if args.command == "crawl":
        adapter = build_douyin_adapter(config)
        risk = RiskProfile(
            min_delay_seconds=args.min_delay,
            max_delay_seconds=args.max_delay,
            max_failures=args.max_failures,
            cookie_group=args.cookie_group,
            proxy_url=args.proxy_url,
        )
        if args.target_type == "video":
            target = args.aweme_id or args.url
            job_id = crawl_video(store, adapter, target, args.include_replies, risk)
        else:
            target = args.sec_user_id or args.url
            job_id = crawl_account(store, adapter, target, args.include_replies, risk)
        print(f"job_id={job_id}")
        print(f"status={store.get_job(job_id)['status']}")
        return

    if args.command == "batch":
        adapter = build_douyin_adapter(config)
        risk = RiskProfile(
            min_delay_seconds=args.min_delay,
            max_delay_seconds=args.max_delay,
            max_failures=args.max_failures,
            cookie_group=args.cookie_group,
            proxy_url=args.proxy_url,
        )
        job_ids = crawl_batch_file(store, adapter, Path(args.file), args.include_replies, risk)
        for job_id in job_ids:
            print(f"job_id={job_id} status={store.get_job(job_id)['status']}")
        return

    if args.command == "export":
        path = export_job(store, args.job_id, Path(args.output_dir), args.format, set(args.exclude_flag))
        print(path)
        return

    if args.command == "status":
        if args.health:
            rows = store.list_account_health()
            if not rows:
                print("暂无账号健康记录")
                return
            for row in rows:
                print(
                    " ".join(
                        [
                            f"cookie_group={row['cookie_group']}",
                            f"status={row['status']}",
                            f"cooldown_until={row['cooldown_until']}",
                            f"last_error={row['last_error']}",
                        ]
                    )
                )
            return
        job = store.get_job(args.job_id) if args.job_id else store.latest_job()
        if job is None:
            print("暂无任务")
            return
        print(f"job_id={job['job_id']}")
        print(f"target_type={job['target_type']}")
        print(f"platform={job['platform']}")
        print(f"status={job['status']}")
        print(f"comments={store.count_comments(job['job_id'])}")
        if job.get("cooldown_until"):
            print(f"cooldown_until={job['cooldown_until']}")
        if job.get("last_error"):
            print(f"last_error={job['last_error']}")
        return

    if args.command == "resume":
        job = store.get_job(args.job_id)
        adapter = build_douyin_adapter(config)
        risk = RiskProfile(min_delay_seconds=args.min_delay, max_delay_seconds=args.max_delay)
        if job["target_type"] == "video":
            job_id = crawl_video(store, adapter, job["target"], args.include_replies, risk, job_id=args.job_id)
        else:
            job_id = crawl_account(store, adapter, job["target"], args.include_replies, risk, job_id=args.job_id)
        print(f"job_id={job_id}")
        print(f"status={store.get_job(job_id)['status']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Douyin comment crawler")
    config = load_runtime_config()
    parser.add_argument("--db-path", default=str(config.db_path), help="SQLite 状态库路径")
    sub = parser.add_subparsers(dest="command", required=True)

    crawl = sub.add_parser("crawl", help="采集评论")
    crawl_sub = crawl.add_subparsers(dest="target_type", required=True)

    video = crawl_sub.add_parser("video", help="采集单个视频评论")
    _add_target_options(video, url=True, aweme_id=True)
    _add_risk_options(video)

    account = crawl_sub.add_parser("account", help="采集账号作品及评论")
    _add_target_options(account, url=True, sec_user_id=True)
    _add_risk_options(account)

    batch = sub.add_parser("batch", help="按文件批量采集")
    batch.add_argument("--file", required=True, help="每行格式：video,<target> 或 account,<target>")
    _add_risk_options(batch)

    export = sub.add_parser("export", help="导出任务数据")
    export.add_argument("--job-id", required=True)
    export.add_argument("--format", choices=["jsonl", "csv"], default="jsonl")
    export.add_argument("--output-dir", default=str(config.export_dir))
    export.add_argument("--exclude-flag", action="append", default=[])

    status = sub.add_parser("status", help="查看任务状态")
    status.add_argument("--job-id")
    status.add_argument("--health", action="store_true", help="查看 Cookie/账号组健康状态")

    resume = sub.add_parser("resume", help="按游标续跑任务")
    resume.add_argument("--job-id", required=True)
    resume.add_argument("--include-replies", action="store_true")
    resume.add_argument("--min-delay", type=float, default=1.0)
    resume.add_argument("--max-delay", type=float, default=3.0)
    return parser


def build_douyin_adapter(config) -> DouyinAdapter:
    return DouyinAdapter(
        cookie=config.douyin_cookie,
        proxy_url=config.douyin_proxy_url,
        api_base_url=config.douyin_api_base_url,
        comments_path=config.douyin_comments_path,
        replies_path=config.douyin_replies_path,
        user_posts_path=config.douyin_user_posts_path,
        page_size=config.douyin_page_size,
        timeout_seconds=config.douyin_timeout_seconds,
    )


def _add_target_options(parser: argparse.ArgumentParser, url: bool = False, aweme_id: bool = False, sec_user_id: bool = False) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    if url:
        group.add_argument("--url")
    if aweme_id:
        group.add_argument("--aweme-id")
    if sec_user_id:
        group.add_argument("--sec-user-id")


def _add_risk_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--include-replies", action="store_true")
    parser.add_argument("--min-delay", type=float, default=1.0)
    parser.add_argument("--max-delay", type=float, default=3.0)
    parser.add_argument("--max-failures", type=int, default=3)
    parser.add_argument("--cookie-group")
    parser.add_argument("--proxy-url")


if __name__ == "__main__":
    main()
