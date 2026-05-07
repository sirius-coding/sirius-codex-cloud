from __future__ import annotations

import json
import unittest
from io import BytesIO
from unittest.mock import patch

from douyin_comment_crawler.adapters.base import PlatformAccessError
from douyin_comment_crawler.adapters.douyin import DouyinAdapter
from douyin_comment_crawler.models import CommentRecord, VideoTarget


class FakeResponse:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self.payload = payload
        self.status = status
        self.headers = {"Content-Type": "application/json"}

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class DouyinAdapterTests(unittest.TestCase):
    def test_http_adapter_reads_comments_replies_and_account_videos(self) -> None:
        adapter = DouyinAdapter(
            api_base_url="https://api.example.test",
            comments_path="/comments?aweme_id={aweme_id}&cursor={cursor}&count={count}",
            replies_path="/replies?comment_id={comment_id}&cursor={cursor}&count={count}",
            user_posts_path="/posts?sec_user_id={sec_user_id}&cursor={cursor}&count={count}",
        )

        responses = [
            FakeResponse(
                {
                    "data": {
                        "comments": [
                            {
                                "cid": "c1",
                                "text": "你好 @demo😀",
                                "user": {"uid": "u1", "nickname": "测试用户"},
                                "create_time": 1778128800,
                                "digg_count": 7,
                                "ip_label": "广东",
                            }
                        ],
                        "cursor": "20",
                        "has_more": False,
                    }
                }
            ),
            FakeResponse({"data": {"comments": [{"cid": "r1", "text": "收到", "user": {"uid": "u2"}}], "has_more": False}}),
            FakeResponse(
                {
                    "data": {
                        "aweme_list": [
                            {"aweme_id": "v1", "share_url": "https://example.test/v1", "author": {"sec_uid": "sec"}}
                        ],
                        "has_more": False,
                    }
                }
            ),
        ]
        with patch("douyin_comment_crawler.adapters.douyin.urlopen", side_effect=responses):
            comments = list(adapter.iter_comments(VideoTarget(platform="douyin", aweme_id="v1")))
            self.assertEqual(comments[0]["comment_id"], "c1")
            self.assertEqual(comments[0]["raw_text"], "你好 @demo😀")
            self.assertEqual(comments[0]["ip_region"], "广东")

            record = CommentRecord.from_adapter("douyin", "v1", comments[0])
            replies = list(adapter.iter_replies(record))
            self.assertEqual(replies[0]["parent_comment_id"], "c1")
            self.assertEqual(replies[0]["comment_id"], "r1")

            videos = list(adapter.iter_videos("sec"))
            self.assertEqual(videos[0].aweme_id, "v1")
            self.assertEqual(videos[0].author_id, "sec")

    def test_http_429_becomes_cooldown_access_error(self) -> None:
        adapter = DouyinAdapter(
            api_base_url="https://api.example.test",
            comments_path="/rate-limit",
        )

        with patch("douyin_comment_crawler.adapters.douyin.urlopen", return_value=FakeResponse({"message": "too many requests"}, status=429)):
            with self.assertRaises(PlatformAccessError) as caught:
                list(adapter.iter_comments(VideoTarget(platform="douyin", aweme_id="v1")))
        self.assertEqual(caught.exception.code, "429")

    def test_timeout_becomes_network_access_error_with_clear_message(self) -> None:
        adapter = DouyinAdapter(
            api_base_url="https://api.example.test",
            comments_path="/comments?aweme_id={aweme_id}",
            timeout_seconds=7,
        )

        with patch("douyin_comment_crawler.adapters.douyin.urlopen", side_effect=TimeoutError("timed out")):
            with self.assertRaises(PlatformAccessError) as caught:
                list(adapter.iter_comments(VideoTarget(platform="douyin", aweme_id="v1")))

        self.assertEqual(caught.exception.code, "network")
        self.assertIn("timeout after 7s", str(caught.exception))

    def test_api_wrapper_error_message_becomes_failed_access_error(self) -> None:
        adapter = DouyinAdapter(
            api_base_url="https://api.example.test",
            comments_path="/comments?aweme_id={aweme_id}",
        )
        response = FakeResponse(
            {
                "code": 500,
                "router": "/api/douyin/web/fetch_video_comments",
                "data": None,
                "message": "无效响应类型。响应类型: <class 'NoneType'>",
            }
        )

        with patch("douyin_comment_crawler.adapters.douyin.urlopen", return_value=response):
            with self.assertRaises(PlatformAccessError) as caught:
                list(adapter.iter_comments(VideoTarget(platform="douyin", aweme_id="v1")))

        self.assertEqual(caught.exception.code, "api_wrapper")
        self.assertIn("Download API upstream returned empty/invalid response", str(caught.exception))

    def test_http_adapter_throttles_once_per_request_page_and_counts_requests(self) -> None:
        adapter = DouyinAdapter(
            api_base_url="https://api.example.test",
            comments_path="/comments?aweme_id={aweme_id}&cursor={cursor}&count={count}",
            page_size=50,
            request_delay_seconds=(1, 1),
        )
        responses = [
            FakeResponse({"data": {"comments": [{"cid": "c1", "text": "a"}], "cursor": "1", "has_more": True}}),
            FakeResponse({"data": {"comments": [{"cid": "c2", "text": "b"}], "has_more": False}}),
        ]

        with patch("douyin_comment_crawler.adapters.douyin.urlopen", side_effect=responses) as open_url:
            with patch("douyin_comment_crawler.adapters.douyin.time.sleep") as sleep:
                comments = list(adapter.iter_comments(VideoTarget(platform="douyin", aweme_id="v1")))

        self.assertEqual([comment["comment_id"] for comment in comments], ["c1", "c2"])
        self.assertEqual(adapter.request_count, 2)
        self.assertEqual(sleep.call_count, 2)
        first_url = open_url.call_args_list[0].args[0].full_url
        self.assertIn("count=50", first_url)


if __name__ == "__main__":
    unittest.main()
