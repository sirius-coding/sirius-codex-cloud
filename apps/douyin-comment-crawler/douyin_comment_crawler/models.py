from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


EMOJI_RE = re.compile(
    "["
    "\U0001f300-\U0001f5ff"
    "\U0001f600-\U0001f64f"
    "\U0001f680-\U0001f6ff"
    "\U0001f700-\U0001f77f"
    "\U0001f780-\U0001f7ff"
    "\U0001f800-\U0001f8ff"
    "\U0001f900-\U0001f9ff"
    "\U0001fa00-\U0001fa6f"
    "\U0001fa70-\U0001faff"
    "]+",
    flags=re.UNICODE,
)
MENTION_RE = re.compile(r"@([\w\-\.\u4e00-\u9fff]+)")
MEDIA_ONLY_TEXT = {"[图片]", "[视频]", "[表情]", "图片", "视频", "表情"}


@dataclass(frozen=True)
class VideoTarget:
    platform: str
    aweme_id: str
    source_url: str | None = None
    author_id: str | None = None


@dataclass(frozen=True)
class RiskProfile:
    min_delay_seconds: float = 1.0
    max_delay_seconds: float = 3.0
    max_failures: int = 3
    workers: int = 1
    retry_backoff_base_seconds: float = 2.0
    cookie_group: str | None = None
    proxy_url: str | None = None


@dataclass
class CommentRecord:
    platform: str
    video_id: str
    comment_id: str
    parent_comment_id: str | None
    user_id: str | None
    user_sec_uid: str | None
    user_nickname: str | None
    raw_text: str
    clean_text: str
    created_at: str | None
    like_count: int
    ip_region: str | None
    crawled_at: str
    flags: list[str] = field(default_factory=list)

    @classmethod
    def from_adapter(cls, platform: str, video_id: str, payload: dict[str, Any]) -> "CommentRecord":
        raw_text = str(payload.get("raw_text") or payload.get("text") or payload.get("content") or "")
        parent_comment_id = _optional_str(payload.get("parent_comment_id"))
        flags = detect_flags(raw_text, parent_comment_id)
        user = payload.get("user") or {}
        return cls(
            platform=platform,
            video_id=str(video_id),
            comment_id=str(payload.get("comment_id") or payload.get("cid") or payload.get("id")),
            parent_comment_id=parent_comment_id,
            user_id=_optional_str(user.get("uid") or user.get("user_id")),
            user_sec_uid=_optional_str(user.get("sec_uid") or user.get("sec_user_id")),
            user_nickname=_optional_str(user.get("nickname") or user.get("name")),
            raw_text=raw_text,
            clean_text=clean_comment_text(raw_text),
            created_at=normalize_timestamp(payload.get("created_at") or payload.get("create_time")),
            like_count=_int_or_zero(payload.get("like_count") or payload.get("digg_count")),
            ip_region=_optional_str(payload.get("ip_region") or payload.get("ip_label") or payload.get("region")),
            crawled_at=datetime.now(timezone.utc).isoformat(),
            flags=flags,
        )

    def to_dict(self, job_id: str | None = None) -> dict[str, Any]:
        row: dict[str, Any] = {
            "platform": self.platform,
            "video_id": self.video_id,
            "comment_id": self.comment_id,
            "parent_comment_id": self.parent_comment_id,
            "user_id": self.user_id,
            "user_sec_uid": self.user_sec_uid,
            "user_nickname": self.user_nickname,
            "raw_text": self.raw_text,
            "clean_text": self.clean_text,
            "created_at": self.created_at,
            "like_count": self.like_count,
            "ip_region": self.ip_region,
            "crawled_at": self.crawled_at,
            "flags": self.flags,
        }
        if job_id is not None:
            row = {"job_id": job_id, **row}
        return row


def clean_comment_text(raw_text: str) -> str:
    without_emoji = EMOJI_RE.sub("", raw_text)
    without_mentions = MENTION_RE.sub(r"\1", without_emoji)
    return re.sub(r"\s+", " ", without_mentions).strip()


def detect_flags(raw_text: str, parent_comment_id: str | None = None) -> list[str]:
    flags: list[str] = []
    stripped = raw_text.strip()
    if EMOJI_RE.search(raw_text):
        flags.append("emoji")
    if MENTION_RE.search(raw_text):
        flags.append("mention")
    if parent_comment_id or stripped.startswith("回复 "):
        flags.append("reply")
    if not stripped:
        flags.append("empty_text")
    if stripped in MEDIA_ONLY_TEXT:
        flags.append("media_only")
    return flags


def normalize_timestamp(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    return str(value)


def _optional_str(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
