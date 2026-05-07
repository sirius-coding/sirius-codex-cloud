from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from douyin_comment_crawler.adapters.base import PlatformAdapter, PlatformAccessError
from douyin_comment_crawler.crawler import crawl_video
from douyin_comment_crawler.models import RiskProfile, VideoTarget
from douyin_comment_crawler.storage import JobStore


class RateLimitedAdapter(PlatformAdapter):
    platform = "fake"

    def resolve_target(self, target: str) -> VideoTarget:
        return VideoTarget(platform=self.platform, aweme_id=target, source_url=target)

    def iter_videos(self, account: str, cursor: str | None = None):
        return iter(())

    def iter_comments(self, video: VideoTarget, cursor: str | None = None):
        raise PlatformAccessError("rate limited", code="429", cooldown_seconds=3600)

    def iter_replies(self, comment, cursor: str | None = None):
        return iter(())


class RiskTests(unittest.TestCase):
    def test_access_errors_cool_down_job_without_retry_storm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = JobStore(Path(tmp) / "jobs.db")
            job_id = crawl_video(
                store=store,
                adapter=RateLimitedAdapter(),
                target="video-1",
                include_replies=True,
                risk=RiskProfile(min_delay_seconds=0, max_delay_seconds=0, max_failures=1),
            )

            job = store.get_job(job_id)
            self.assertEqual(job["status"], "cooldown")
            self.assertEqual(job["last_error"], "rate limited")
            self.assertIsNotNone(job["cooldown_until"])
            health = store.get_account_health("default")
            self.assertEqual(health["status"], "cooldown")
            self.assertEqual(health["last_error"], "rate limited")
            self.assertEqual(store.count_comments(job_id), 0)

    def test_successful_job_marks_cookie_group_healthy(self) -> None:
        try:
            from test_core import FakeAdapter
        except ModuleNotFoundError:
            from tests.test_core import FakeAdapter

        with tempfile.TemporaryDirectory() as tmp:
            store = JobStore(Path(tmp) / "jobs.db")
            store.update_account_health("primary", "cooldown", "previous error", "2099-01-01T00:00:00+00:00")

            crawl_video(
                store=store,
                adapter=FakeAdapter(),
                target="video-1",
                include_replies=False,
                risk=RiskProfile(min_delay_seconds=0, max_delay_seconds=0, cookie_group="primary"),
            )

            health = store.get_account_health("primary")
            self.assertEqual(health["status"], "healthy")
            self.assertIsNone(health["last_error"])
            self.assertIsNone(health["cooldown_until"])


if __name__ == "__main__":
    unittest.main()
