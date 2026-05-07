from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from douyin_comment_crawler.config import load_runtime_config
from douyin_comment_crawler.__main__ import build_douyin_adapter, build_parser


class ConfigTests(unittest.TestCase):
    def test_load_runtime_config_reads_local_env_without_overriding_process_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "COMMENT_CRAWLER_DB_PATH=data/custom.db",
                        "DOUYIN_API_BASE_URL=https://api.example.test",
                        "DOUYIN_COOKIE=local-cookie",
                    ]
                ),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"DOUYIN_COOKIE": "process-cookie"}, clear=False):
                config = load_runtime_config(env_path)

        self.assertEqual(config.db_path, Path("data/custom.db"))
        self.assertEqual(config.douyin_api_base_url, "https://api.example.test")
        self.assertEqual(config.douyin_cookie, "process-cookie")

    def test_cli_accepts_page_size_and_workers_overrides(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "crawl",
                "account",
                "--sec-user-id",
                "sec",
                "--page-size",
                "50",
                "--workers",
                "4",
                "--min-delay",
                "0",
                "--max-delay",
                "0",
            ]
        )

        self.assertEqual(args.page_size, 50)
        self.assertEqual(args.workers, 4)

    def test_cli_accepts_replies_second_stage_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "crawl",
                "replies",
                "--job-id",
                "job-1",
                "--workers",
                "4",
                "--min-delay",
                "0",
                "--max-delay",
                "0",
            ]
        )

        self.assertEqual(args.target_type, "replies")
        self.assertEqual(args.job_id, "job-1")
        self.assertEqual(args.workers, 4)

    def test_build_adapter_applies_page_size_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("DOUYIN_API_BASE_URL=https://api.example.test\nDOUYIN_PAGE_SIZE=20", encoding="utf-8")
            config = load_runtime_config(env_path)

        adapter = build_douyin_adapter(config, page_size_override=80, min_delay=2, max_delay=2)

        self.assertEqual(adapter.page_size, 80)
        self.assertEqual(adapter.request_delay_seconds, (2, 2))


if __name__ == "__main__":
    unittest.main()
