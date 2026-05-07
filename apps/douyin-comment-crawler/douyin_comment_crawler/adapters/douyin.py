from __future__ import annotations

import os
import json
import random
import time
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from douyin_comment_crawler.adapters.base import PlatformAccessError, PlatformAdapter
from douyin_comment_crawler.models import CommentRecord, VideoTarget


class DouyinAdapter(PlatformAdapter):
    """HTTP adapter for a private Douyin API service.

    The expected deployment is a user-controlled API wrapper such as a private
    Evil0ctal/Douyin_TikTok_Download_API instance. This class does not bypass
    platform restrictions; it stops on auth, permission, rate-limit, or captcha
    style responses.
    """

    platform = "douyin"

    def __init__(
        self,
        cookie: str | None = None,
        proxy_url: str | None = None,
        api_base_url: str | None = None,
        comments_path: str | None = None,
        replies_path: str | None = None,
        user_posts_path: str | None = None,
        page_size: int = 20,
        timeout_seconds: float = 20,
        request_delay_seconds: tuple[float, float] = (0.0, 0.0),
    ) -> None:
        self.cookie = cookie or os.getenv("DOUYIN_COOKIE")
        self.proxy_url = proxy_url or os.getenv("DOUYIN_PROXY_URL")
        self.api_base_url = (api_base_url or os.getenv("DOUYIN_API_BASE_URL") or "").rstrip("/")
        self.comments_path = comments_path or os.getenv(
            "DOUYIN_COMMENTS_PATH",
            "/api/douyin/web/fetch_video_comments?aweme_id={aweme_id}&cursor={cursor}&count={count}",
        )
        self.replies_path = replies_path or os.getenv(
            "DOUYIN_REPLIES_PATH",
            "/api/douyin/web/fetch_video_comment_replies?item_id={aweme_id}&comment_id={comment_id}&cursor={cursor}&count={count}",
        )
        self.user_posts_path = user_posts_path or os.getenv(
            "DOUYIN_USER_POSTS_PATH",
            "/api/douyin/web/fetch_user_post_videos?sec_user_id={sec_user_id}&max_cursor={cursor}&count={count}",
        )
        self.page_size = page_size
        self.timeout_seconds = timeout_seconds
        self.request_delay_seconds = request_delay_seconds
        self.request_count = 0

    def resolve_target(self, target: str) -> VideoTarget:
        return VideoTarget(platform=self.platform, aweme_id=_last_path_token(target), source_url=target)

    def iter_videos(self, account: str, cursor: str | None = None) -> Iterable[VideoTarget]:
        self._ensure_configured()
        next_cursor = cursor or "0"
        while True:
            payload = self._get_json(
                self.user_posts_path,
                sec_user_id=account,
                cursor=next_cursor,
                count=str(self.page_size),
            )
            data = _data(payload)
            for item in _list_from(data, "aweme_list", "videos", "items", "data"):
                aweme_id = str(item.get("aweme_id") or item.get("id") or item.get("awemeId") or "")
                if not aweme_id:
                    continue
                author = item.get("author") or {}
                yield VideoTarget(
                    platform=self.platform,
                    aweme_id=aweme_id,
                    source_url=item.get("share_url") or item.get("url"),
                    author_id=author.get("sec_uid") or author.get("sec_user_id") or account,
                )
            if not _has_more(data):
                break
            next_cursor = str(data.get("cursor") or data.get("next_cursor") or data.get("max_cursor") or "")
            if not next_cursor:
                break

    def iter_comments(self, video: VideoTarget, cursor: str | None = None) -> Iterable[dict]:
        self._ensure_configured()
        next_cursor = cursor or "0"
        while True:
            payload = self._get_json(
                self.comments_path,
                aweme_id=video.aweme_id,
                cursor=next_cursor,
                count=str(self.page_size),
            )
            data = _data(payload)
            for item in _list_from(data, "comments", "comment_list", "items", "data"):
                yield _normalize_comment(item)
            if not _has_more(data):
                break
            next_cursor = str(data.get("cursor") or data.get("next_cursor") or "")
            if not next_cursor:
                break

    def iter_replies(self, comment: CommentRecord, cursor: str | None = None) -> Iterable[dict]:
        self._ensure_configured()
        next_cursor = cursor or "0"
        while True:
            payload = self._get_json(
                self.replies_path,
                aweme_id=comment.video_id,
                comment_id=comment.comment_id,
                cursor=next_cursor,
                count=str(self.page_size),
            )
            data = _data(payload)
            for item in _list_from(data, "comments", "replies", "comment_list", "items", "data"):
                normalized = _normalize_comment(item)
                normalized["parent_comment_id"] = normalized.get("parent_comment_id") or comment.comment_id
                yield normalized
            if not _has_more(data):
                break
            next_cursor = str(data.get("cursor") or data.get("next_cursor") or "")
            if not next_cursor:
                break

    def _ensure_configured(self) -> None:
        if not self.api_base_url:
            raise NotImplementedError("缺少 DOUYIN_API_BASE_URL，尚未接入私有 Douyin API 服务")

    def _get_json(self, path_template: str, **params: str) -> dict:
        path = _format_path(path_template, params)
        url = urljoin(f"{self.api_base_url}/", path.lstrip("/"))
        request = Request(url, headers=self._headers(), method="GET")
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                status = getattr(response, "status", 200)
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            _raise_access_error(exc.code, exc.read().decode("utf-8", errors="replace"))
        except URLError as exc:
            raise PlatformAccessError(f"network error: {exc.reason}", code="network") from exc
        if status in {401, 403, 409, 418, 429}:
            _raise_access_error(status, body)
        if status >= 400:
            raise PlatformAccessError(f"http error: {status}", code=str(status))
        payload = json.loads(body or "{}")
        _raise_if_platform_blocked(payload)
        self.request_count += 1
        self._throttle()
        return payload

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "User-Agent": "douyin-comment-crawler/0.1"}
        if self.cookie:
            headers["Cookie"] = self.cookie
        return headers

    def _throttle(self) -> None:
        min_delay, max_delay = self.request_delay_seconds
        if max_delay <= 0:
            return
        delay = random.uniform(min_delay, max_delay)
        if delay > 0:
            time.sleep(delay)


def _last_path_token(value: str) -> str:
    stripped = value.rstrip("/")
    if "/" not in stripped:
        return stripped
    return stripped.rsplit("/", 1)[-1].split("?", 1)[0] or stripped


def _format_path(template: str, params: dict[str, str]) -> str:
    escaped = {key: urlencode({key: value}).split("=", 1)[1] for key, value in params.items()}
    return template.format(**escaped)


def _data(payload: dict) -> dict:
    data = payload.get("data", payload)
    return data if isinstance(data, dict) else {"data": data}


def _list_from(data: dict, *keys: str) -> list[dict]:
    for key in keys:
        value = data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _has_more(data: dict) -> bool:
    value = data.get("has_more", data.get("hasMore", False))
    return value in {True, 1, "1", "true", "True"}


def _normalize_comment(item: dict) -> dict:
    return {
        "comment_id": item.get("comment_id") or item.get("cid") or item.get("id"),
        "parent_comment_id": item.get("parent_comment_id") or item.get("reply_id"),
        "raw_text": item.get("raw_text") or item.get("text") or item.get("content") or "",
        "user": item.get("user") or item.get("author") or {},
        "created_at": item.get("created_at") or item.get("create_time"),
        "like_count": item.get("like_count") or item.get("digg_count"),
        "ip_region": item.get("ip_region") or item.get("ip_label") or item.get("region"),
    }


def _raise_if_platform_blocked(payload: dict) -> None:
    status = str(payload.get("status_code", payload.get("code", "0")))
    message = str(payload.get("message", payload.get("msg", "")))
    lower = message.lower()
    if status in {"401", "403", "429"} or any(word in lower for word in ["captcha", "验证码", "登录", "权限", "频控"]):
        code = "429" if "频控" in message else status
        raise PlatformAccessError(message or "platform access blocked", code=code)


def _raise_access_error(status: int, body: str) -> None:
    message = body
    try:
        payload = json.loads(body or "{}")
        message = str(payload.get("message") or payload.get("msg") or body)
    except json.JSONDecodeError:
        pass
    cooldown = 3600 if status == 429 else None
    raise PlatformAccessError(message or f"http error: {status}", code=str(status), cooldown_seconds=cooldown)
