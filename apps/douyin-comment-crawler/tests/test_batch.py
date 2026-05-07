from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_core import FakeAdapter

from douyin_comment_crawler.batch import crawl_batch_file
from douyin_comment_crawler.models import RiskProfile
from douyin_comment_crawler.storage import JobStore


class BatchTests(unittest.TestCase):
    def test_batch_file_crawls_video_and_account_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch = root / "targets.txt"
            batch.write_text(
                "\n".join(
                    [
                        "# type,target",
                        "video,video-1",
                        "account,https://example.test/user/demo",
                    ]
                ),
                encoding="utf-8",
            )
            store = JobStore(root / "jobs.db")

            job_ids = crawl_batch_file(
                store=store,
                adapter=FakeAdapter(),
                path=batch,
                include_replies=False,
                risk=RiskProfile(min_delay_seconds=0, max_delay_seconds=0),
            )

            self.assertEqual(len(job_ids), 2)
            self.assertEqual(store.count_comments(job_ids[0]), 2)
            self.assertEqual(store.count_comments(job_ids[1]), 4)


if __name__ == "__main__":
    unittest.main()
