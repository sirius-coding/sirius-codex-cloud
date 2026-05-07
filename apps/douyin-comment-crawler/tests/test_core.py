from __future__ import annotations

import csv
import json
import threading
import time
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from douyin_comment_crawler.adapters.base import PlatformAdapter
from douyin_comment_crawler.crawler import crawl_account, crawl_replies_for_job, crawl_video
from douyin_comment_crawler.exporter import export_job
from douyin_comment_crawler.models import CommentRecord, RiskProfile, VideoTarget
from douyin_comment_crawler.storage import JobStore


class FakeAdapter(PlatformAdapter):
    platform = "fake"

    def resolve_target(self, target: str) -> VideoTarget:
        return VideoTarget(platform=self.platform, aweme_id=target, source_url=f"https://example.test/{target}")

    def iter_videos(self, account: str, cursor: str | None = None):
        yield VideoTarget(platform=self.platform, aweme_id="video-1", source_url=f"{account}/video-1")
        yield VideoTarget(platform=self.platform, aweme_id="video-2", source_url=f"{account}/video-2")

    def iter_comments(self, video: VideoTarget, cursor: str | None = None):
        yield {
            "comment_id": f"{video.aweme_id}-c1",
            "raw_text": "回复 @alice: 你好😀",
            "user": {"uid": "u1", "nickname": "张三"},
            "created_at": "2026-05-07T10:00:00+08:00",
            "like_count": 3,
            "ip_region": "北京",
        }
        yield {
            "comment_id": f"{video.aweme_id}-c2",
            "raw_text": "",
            "user": {"uid": "u2", "nickname": "李四"},
            "created_at": None,
            "like_count": 0,
        }

    def iter_replies(self, comment: CommentRecord, cursor: str | None = None):
        if comment.comment_id.endswith("-c2"):
            return
        yield {
            "comment_id": f"{comment.comment_id}-r1",
            "parent_comment_id": comment.comment_id,
            "raw_text": "[图片]",
            "user": {"uid": "u3", "nickname": "王五"},
            "created_at": "2026-05-07T10:01:00+08:00",
            "like_count": 1,
        }


class ConcurrentFakeAdapter(FakeAdapter):
    def __init__(self) -> None:
        self.active = 0
        self.max_active = 0
        self.lock = threading.Lock()

    def iter_videos(self, account: str, cursor: str | None = None):
        for index in range(4):
            yield VideoTarget(platform=self.platform, aweme_id=f"video-{index}", source_url=f"{account}/video-{index}")

    def iter_comments(self, video: VideoTarget, cursor: str | None = None):
        with self.lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            time.sleep(0.02)
            yield {"comment_id": f"{video.aweme_id}-c1", "raw_text": "hello"}
        finally:
            with self.lock:
                self.active -= 1


class CoreTests(unittest.TestCase):
    def test_comment_record_normalizes_fields_and_flags(self) -> None:
        record = CommentRecord.from_adapter(
            platform="douyin",
            video_id="7123",
            payload={
                "comment_id": "c1",
                "parent_comment_id": "p1",
                "raw_text": "回复 @alice: 你好😀",
                "user": {"uid": "u1", "nickname": "张三", "sec_uid": "sec"},
                "created_at": 1778128800,
                "like_count": "5",
                "ip_region": "上海",
            },
        )

        self.assertEqual(record.platform, "douyin")
        self.assertEqual(record.video_id, "7123")
        self.assertEqual(record.comment_id, "c1")
        self.assertEqual(record.parent_comment_id, "p1")
        self.assertEqual(record.user_id, "u1")
        self.assertEqual(record.user_nickname, "张三")
        self.assertEqual(record.user_sec_uid, "sec")
        self.assertEqual(record.clean_text, "回复 alice: 你好")
        self.assertEqual(record.like_count, 5)
        self.assertEqual(record.ip_region, "上海")
        self.assertIn("emoji", record.flags)
        self.assertIn("mention", record.flags)
        self.assertIn("reply", record.flags)

    def test_storage_deduplicates_comments_and_tracks_resume_cursor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = JobStore(Path(tmp) / "jobs.db")
            job_id = store.create_job("video", "douyin", "https://example.test/video")
            record = CommentRecord.from_adapter(
                platform="douyin",
                video_id="v1",
                payload={"comment_id": "c1", "raw_text": "hello"},
            )

            self.assertTrue(store.save_comment(job_id, record))
            self.assertFalse(store.save_comment(job_id, record))
            store.save_cursor(job_id, "comments:v1", "cursor-2")
            store.mark_failed_attempt(job_id, "comments:v1", "timeout")

            self.assertEqual(store.get_cursor(job_id, "comments:v1"), "cursor-2")
            self.assertEqual(store.count_comments(job_id), 1)
            failures = store.list_failures(job_id)
            self.assertEqual(failures[0]["error"], "timeout")

    def test_fake_adapter_crawls_video_replies_and_exports_stable_jsonl_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = JobStore(root / "jobs.db")
            adapter = FakeAdapter()
            risk = RiskProfile(min_delay_seconds=0, max_delay_seconds=0)

            job_id = crawl_video(
                store=store,
                adapter=adapter,
                target="video-1",
                include_replies=True,
                risk=risk,
            )

            self.assertEqual(store.count_comments(job_id), 3)

            jsonl_path = export_job(store, job_id, root / "out", "jsonl")
            rows = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[0]["job_id"], job_id)
            self.assertIn("clean_text", rows[0])
            self.assertIn("flags", rows[0])

            csv_path = export_job(store, job_id, root / "out", "csv", exclude_flags={"empty_text"})
            with csv_path.open("r", encoding="utf-8", newline="") as fh:
                csv_rows = list(csv.DictReader(fh))
            self.assertEqual(len(csv_rows), 2)
            self.assertEqual(csv_rows[0]["platform"], "fake")

    def test_account_crawl_uses_adapter_video_iteration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = JobStore(Path(tmp) / "jobs.db")
            job_id = crawl_account(
                store=store,
                adapter=FakeAdapter(),
                account="https://example.test/user/demo",
                include_replies=False,
                risk=RiskProfile(min_delay_seconds=0, max_delay_seconds=0),
            )

            self.assertEqual(store.get_job(job_id)["status"], "completed")
            self.assertEqual(store.count_comments(job_id), 4)

    def test_core_crawler_does_not_sleep_per_comment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = JobStore(Path(tmp) / "jobs.db")
            with patch("time.sleep") as sleep:
                crawl_video(
                    store=store,
                    adapter=FakeAdapter(),
                    target="video-1",
                    include_replies=False,
                    risk=RiskProfile(min_delay_seconds=1, max_delay_seconds=1),
                )

            sleep.assert_not_called()

    def test_account_crawl_uses_bounded_video_workers_and_records_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = JobStore(Path(tmp) / "jobs.db")
            adapter = ConcurrentFakeAdapter()
            job_id = crawl_account(
                store=store,
                adapter=adapter,
                account="https://example.test/user/demo",
                include_replies=False,
                risk=RiskProfile(min_delay_seconds=0, max_delay_seconds=0, workers=4),
            )

            self.assertGreater(adapter.max_active, 1)
            metrics = store.get_job_metrics(job_id)
            self.assertEqual(metrics["videos_seen"], 4)
            self.assertEqual(metrics["comments_seen"], 4)
            self.assertEqual(metrics["comments_saved"], 4)

    def test_replies_can_be_crawled_as_second_stage_for_existing_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = JobStore(Path(tmp) / "jobs.db")
            adapter = FakeAdapter()
            risk = RiskProfile(min_delay_seconds=0, max_delay_seconds=0, workers=2)
            job_id = crawl_video(
                store=store,
                adapter=adapter,
                target="video-1",
                include_replies=False,
                risk=risk,
            )
            self.assertEqual(store.count_comments(job_id), 2)

            crawl_replies_for_job(store=store, adapter=adapter, job_id=job_id, risk=risk)
            crawl_replies_for_job(store=store, adapter=adapter, job_id=job_id, risk=risk)

            self.assertEqual(store.get_job(job_id)["status"], "completed")
            self.assertEqual(store.count_comments(job_id), 3)
            metrics = store.get_job_metrics(job_id)
            self.assertEqual(metrics["replies_seen"], 2)
            self.assertEqual(metrics["comments_saved"], 3)


if __name__ == "__main__":
    unittest.main()
