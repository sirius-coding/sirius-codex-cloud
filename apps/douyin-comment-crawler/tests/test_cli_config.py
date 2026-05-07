from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from douyin_comment_crawler.config import load_runtime_config


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


if __name__ == "__main__":
    unittest.main()
