from __future__ import annotations

import unittest
from unittest.mock import patch

from douyin_comment_crawler.tui import (
    Tuning,
    build_account_command,
    build_export_command,
    build_doctor_command,
    build_replies_command,
    build_resume_command,
    build_video_command,
    format_status_rows,
    status_summary,
    normalize_paste_text,
    parse_status_output,
    run_command,
    status_command,
)


class TuiTests(unittest.TestCase):
    def test_build_video_command_keeps_only_required_target_and_tuning(self) -> None:
        command = build_video_command("abc", "aweme-id", True, Tuning(page_size=80, workers=3, min_delay=0.2, max_delay=0.8))

        self.assertEqual(command[:4], ["python3", "-m", "douyin_comment_crawler", "crawl"])
        self.assertIn("--aweme-id", command)
        self.assertIn("abc", command)
        self.assertIn("--include-replies", command)
        self.assertIn("--page-size", command)
        self.assertIn("80", command)

    def test_build_account_command_uses_url_or_sec_user_id(self) -> None:
        by_url = build_account_command("https://example.test/user/sec", "url", False, Tuning())
        by_sec = build_account_command("sec", "sec-user-id", False, Tuning())

        self.assertIn("--url", by_url)
        self.assertNotIn("--include-replies", by_url)
        self.assertIn("--sec-user-id", by_sec)

    def test_build_replies_resume_and_export_commands(self) -> None:
        self.assertEqual(build_replies_command("job-1", Tuning())[2:5], ["douyin_comment_crawler", "crawl", "replies"])
        self.assertEqual(build_resume_command("job-1", Tuning())[2:4], ["douyin_comment_crawler", "resume"])
        export = build_export_command("job-1", "csv", ["empty_text", "media_only"])
        self.assertIn("--exclude-flag", export)
        self.assertEqual(export.count("--exclude-flag"), 2)

    def test_parse_status_output(self) -> None:
        status = parse_status_output(
            "\n".join(
                [
                    "job_id=abc",
                    "status=cooldown",
                    "comments_saved=120",
                    "last_error=rate limited",
                ]
            )
        )

        self.assertEqual(status["job_id"], "abc")
        self.assertEqual(status["status"], "cooldown")
        self.assertEqual(status["comments_saved"], "120")
        self.assertEqual(status["last_error"], "rate limited")

    def test_status_summary_and_rows_are_table_friendly(self) -> None:
        status = {
            "job_id": "abc",
            "status": "completed",
            "comments": "130",
            "videos_seen": "5",
            "comments_saved": "120",
            "api_requests": "8",
        }

        self.assertEqual(status_summary(status), "abc | completed | saved=120 | requests=8")
        rows = format_status_rows(status)

        self.assertIn(("任务", "job_id", "abc"), rows)
        self.assertIn(("指标", "comments_saved", "120"), rows)
        self.assertIn(("指标", "api_requests", "8"), rows)

    def test_run_command_returns_cancelled_result_on_keyboard_interrupt(self) -> None:
        with patch("subprocess.run", side_effect=KeyboardInterrupt):
            code, output = run_command(["python3", "-m", "douyin_comment_crawler", "status"])

        self.assertEqual(code, 130)
        self.assertIn("已取消", output)

    def test_status_command_targets_job_when_available(self) -> None:
        self.assertEqual(status_command("job-1"), ["python3", "-m", "douyin_comment_crawler", "status", "--job-id", "job-1"])
        self.assertEqual(status_command(""), ["python3", "-m", "douyin_comment_crawler", "status"])

    def test_build_doctor_command(self) -> None:
        command = build_doctor_command("123", timeout=9)

        self.assertEqual(command[:4], ["python3", "-m", "douyin_comment_crawler", "doctor"])
        self.assertIn("--aweme-id", command)
        self.assertIn("123", command)
        self.assertIn("9", command)

    def test_normalize_paste_text_strips_bracketed_paste_markers(self) -> None:
        self.assertEqual(normalize_paste_text("\x1b[200~abc123\x1b[201~"), "abc123")
        self.assertEqual(normalize_paste_text("plain text"), "plain text")


if __name__ == "__main__":
    unittest.main()
