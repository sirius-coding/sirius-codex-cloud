from __future__ import annotations

import random
import time
from collections.abc import Iterable

from douyin_comment_crawler.adapters.base import PlatformAccessError, PlatformAdapter
from douyin_comment_crawler.models import CommentRecord, RiskProfile, VideoTarget
from douyin_comment_crawler.storage import JobStore, cooldown_deadline


def crawl_video(
    store: JobStore,
    adapter: PlatformAdapter,
    target: str,
    include_replies: bool,
    risk: RiskProfile,
    job_id: str | None = None,
) -> str:
    current_job_id = job_id or store.create_job("video", adapter.platform, target)
    try:
        video = adapter.resolve_target(target)
        _crawl_video_target(store, current_job_id, adapter, video, include_replies, risk)
    except PlatformAccessError as exc:
        store.mark_failed_attempt(current_job_id, f"video:{target}", str(exc))
        _cool_down(store, current_job_id, risk, exc)
    except NotImplementedError as exc:
        store.update_job_status(current_job_id, "failed", str(exc))
    except Exception as exc:  # noqa: BLE001 - job state must capture unexpected adapter failures.
        store.mark_failed_attempt(current_job_id, f"video:{target}", str(exc))
        store.update_job_status(current_job_id, "failed", str(exc))
    else:
        store.update_job_status(current_job_id, "completed")
        _mark_healthy(store, risk)
    return current_job_id


def crawl_account(
    store: JobStore,
    adapter: PlatformAdapter,
    account: str,
    include_replies: bool,
    risk: RiskProfile,
    job_id: str | None = None,
) -> str:
    current_job_id = job_id or store.create_job("account", adapter.platform, account)
    try:
        cursor = store.get_cursor(current_job_id, f"account:{account}")
        for video in adapter.iter_videos(account, cursor=cursor):
            _crawl_video_target(store, current_job_id, adapter, video, include_replies, risk)
            store.save_cursor(current_job_id, f"account:{account}", video.aweme_id)
            _sleep(risk)
    except PlatformAccessError as exc:
        store.mark_failed_attempt(current_job_id, f"account:{account}", str(exc))
        _cool_down(store, current_job_id, risk, exc)
    except NotImplementedError as exc:
        store.update_job_status(current_job_id, "failed", str(exc))
    except Exception as exc:  # noqa: BLE001
        store.mark_failed_attempt(current_job_id, f"account:{account}", str(exc))
        store.update_job_status(current_job_id, "failed", str(exc))
    else:
        store.update_job_status(current_job_id, "completed")
        _mark_healthy(store, risk)
    return current_job_id


def _crawl_video_target(
    store: JobStore,
    job_id: str,
    adapter: PlatformAdapter,
    video: VideoTarget,
    include_replies: bool,
    risk: RiskProfile,
) -> None:
    scope = f"comments:{video.aweme_id}"
    cursor = store.get_cursor(job_id, scope)
    for payload in adapter.iter_comments(video, cursor=cursor):
        record = CommentRecord.from_adapter(adapter.platform, video.aweme_id, payload)
        store.save_comment(job_id, record)
        store.save_cursor(job_id, scope, record.comment_id)
        if include_replies:
            _crawl_replies(store, job_id, adapter, record)
        _sleep(risk)


def _crawl_replies(store: JobStore, job_id: str, adapter: PlatformAdapter, comment: CommentRecord) -> None:
    scope = f"replies:{comment.comment_id}"
    cursor = store.get_cursor(job_id, scope)
    for payload in adapter.iter_replies(comment, cursor=cursor):
        reply = CommentRecord.from_adapter(adapter.platform, comment.video_id, payload)
        store.save_comment(job_id, reply)
        store.save_cursor(job_id, scope, reply.comment_id)


def _sleep(risk: RiskProfile) -> None:
    if risk.max_delay_seconds <= 0:
        return
    delay = random.uniform(risk.min_delay_seconds, risk.max_delay_seconds)
    if delay > 0:
        time.sleep(delay)


def _cool_down(store: JobStore, job_id: str, risk: RiskProfile, exc: PlatformAccessError) -> None:
    deadline = cooldown_deadline(exc.cooldown_seconds)
    cookie_group = risk.cookie_group or "default"
    store.update_job_status(job_id, "cooldown", str(exc), cooldown_until=deadline)
    store.update_account_health(cookie_group, "cooldown", str(exc), cooldown_until=deadline)


def _mark_healthy(store: JobStore, risk: RiskProfile) -> None:
    cookie_group = risk.cookie_group or "default"
    store.update_account_health(cookie_group, "healthy")
