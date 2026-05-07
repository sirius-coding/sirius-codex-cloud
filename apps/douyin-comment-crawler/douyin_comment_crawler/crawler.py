from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
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
        store.increment_metric(current_job_id, "videos_seen")
        _crawl_video_target(store, current_job_id, adapter, video, include_replies, risk)
    except PlatformAccessError as exc:
        store.mark_failed_attempt(current_job_id, f"video:{target}", str(exc))
        _handle_access_error(store, current_job_id, adapter, risk, exc)
    except NotImplementedError as exc:
        store.update_job_status(current_job_id, "failed", str(exc))
    except Exception as exc:  # noqa: BLE001 - job state must capture unexpected adapter failures.
        store.mark_failed_attempt(current_job_id, f"video:{target}", str(exc))
        _capture_adapter_metrics(store, current_job_id, adapter)
        store.update_job_status(current_job_id, "failed", str(exc))
    else:
        _capture_adapter_metrics(store, current_job_id, adapter)
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
        videos = []
        for video in adapter.iter_videos(account, cursor=cursor):
            videos.append(video)
            store.increment_metric(current_job_id, "videos_seen")
            store.save_cursor(current_job_id, f"account:{account}", video.aweme_id)
        if risk.workers > 1 and len(videos) > 1:
            with ThreadPoolExecutor(max_workers=risk.workers) as executor:
                futures = [
                    executor.submit(_crawl_video_target, store, current_job_id, adapter, video, include_replies, risk)
                    for video in videos
                ]
                for future in as_completed(futures):
                    future.result()
        else:
            for video in videos:
                _crawl_video_target(store, current_job_id, adapter, video, include_replies, risk)
    except PlatformAccessError as exc:
        store.mark_failed_attempt(current_job_id, f"account:{account}", str(exc))
        _handle_access_error(store, current_job_id, adapter, risk, exc)
    except NotImplementedError as exc:
        store.update_job_status(current_job_id, "failed", str(exc))
    except Exception as exc:  # noqa: BLE001
        store.mark_failed_attempt(current_job_id, f"account:{account}", str(exc))
        _capture_adapter_metrics(store, current_job_id, adapter)
        store.update_job_status(current_job_id, "failed", str(exc))
    else:
        _capture_adapter_metrics(store, current_job_id, adapter)
        store.update_job_status(current_job_id, "completed")
        _mark_healthy(store, risk)
    return current_job_id


def crawl_replies_for_job(
    store: JobStore,
    adapter: PlatformAdapter,
    job_id: str,
    risk: RiskProfile,
) -> str:
    try:
        comments = [_comment_from_row(row) for row in store.iter_parent_comments(job_id)]
        if risk.workers > 1 and len(comments) > 1:
            with ThreadPoolExecutor(max_workers=risk.workers) as executor:
                futures = [executor.submit(_crawl_replies, store, job_id, adapter, comment) for comment in comments]
                for future in as_completed(futures):
                    future.result()
        else:
            for comment in comments:
                _crawl_replies(store, job_id, adapter, comment)
    except PlatformAccessError as exc:
        store.mark_failed_attempt(job_id, f"replies:{job_id}", str(exc))
        _handle_access_error(store, job_id, adapter, risk, exc)
    except NotImplementedError as exc:
        store.update_job_status(job_id, "failed", str(exc))
    except Exception as exc:  # noqa: BLE001
        store.mark_failed_attempt(job_id, f"replies:{job_id}", str(exc))
        _capture_adapter_metrics(store, job_id, adapter)
        store.update_job_status(job_id, "failed", str(exc))
    else:
        _capture_adapter_metrics(store, job_id, adapter)
        store.update_job_status(job_id, "completed")
        _mark_healthy(store, risk)
    return job_id


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
        store.increment_metric(job_id, "comments_seen")
        record = CommentRecord.from_adapter(adapter.platform, video.aweme_id, payload)
        if store.save_comment(job_id, record):
            store.increment_metric(job_id, "comments_saved")
        store.save_cursor(job_id, scope, record.comment_id)
        if include_replies:
            _crawl_replies(store, job_id, adapter, record)


def _crawl_replies(store: JobStore, job_id: str, adapter: PlatformAdapter, comment: CommentRecord) -> None:
    scope = f"replies:{comment.comment_id}"
    cursor = store.get_cursor(job_id, scope)
    for payload in adapter.iter_replies(comment, cursor=cursor):
        store.increment_metric(job_id, "replies_seen")
        store.increment_metric(job_id, "comments_seen")
        reply = CommentRecord.from_adapter(adapter.platform, comment.video_id, payload)
        if store.save_comment(job_id, reply):
            store.increment_metric(job_id, "comments_saved")
        store.save_cursor(job_id, scope, reply.comment_id)


def _cool_down(store: JobStore, job_id: str, risk: RiskProfile, exc: PlatformAccessError) -> None:
    deadline = cooldown_deadline(exc.cooldown_seconds)
    cookie_group = risk.cookie_group or "default"
    store.update_job_status(job_id, "cooldown", str(exc), cooldown_until=deadline)
    store.update_account_health(cookie_group, "cooldown", str(exc), cooldown_until=deadline)


def _handle_access_error(
    store: JobStore,
    job_id: str,
    adapter: PlatformAdapter,
    risk: RiskProfile,
    exc: PlatformAccessError,
) -> None:
    _capture_adapter_metrics(store, job_id, adapter)
    if exc.code in {"401", "403", "409", "418", "429"}:
        _cool_down(store, job_id, risk, exc)
        return
    store.update_job_status(job_id, "failed", str(exc))


def _mark_healthy(store: JobStore, risk: RiskProfile) -> None:
    cookie_group = risk.cookie_group or "default"
    store.update_account_health(cookie_group, "healthy")


def _capture_adapter_metrics(store: JobStore, job_id: str, adapter: PlatformAdapter) -> None:
    request_count = getattr(adapter, "request_count", None)
    if isinstance(request_count, int):
        store.set_metric(job_id, "api_requests", request_count)


def _comment_from_row(row: dict) -> CommentRecord:
    flags = row.get("flags") or []
    return CommentRecord(
        platform=row["platform"],
        video_id=row["video_id"],
        comment_id=row["comment_id"],
        parent_comment_id=row.get("parent_comment_id"),
        user_id=row.get("user_id"),
        user_sec_uid=row.get("user_sec_uid"),
        user_nickname=row.get("user_nickname"),
        raw_text=row.get("raw_text") or "",
        clean_text=row.get("clean_text") or "",
        created_at=row.get("created_at"),
        like_count=int(row.get("like_count") or 0),
        ip_region=row.get("ip_region"),
        crawled_at=row.get("crawled_at") or "",
        flags=list(flags),
    )
