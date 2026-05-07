from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from douyin_comment_crawler.models import CommentRecord, VideoTarget


class PlatformAccessError(RuntimeError):
    def __init__(self, message: str, code: str | None = None, cooldown_seconds: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.cooldown_seconds = cooldown_seconds


class PlatformAdapter(ABC):
    platform: str

    @abstractmethod
    def resolve_target(self, target: str) -> VideoTarget:
        raise NotImplementedError

    @abstractmethod
    def iter_videos(self, account: str, cursor: str | None = None) -> Iterable[VideoTarget]:
        raise NotImplementedError

    @abstractmethod
    def iter_comments(self, video: VideoTarget, cursor: str | None = None) -> Iterable[dict]:
        raise NotImplementedError

    @abstractmethod
    def iter_replies(self, comment: CommentRecord, cursor: str | None = None) -> Iterable[dict]:
        raise NotImplementedError
