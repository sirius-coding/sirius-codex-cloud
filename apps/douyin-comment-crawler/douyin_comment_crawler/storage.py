from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Iterable

from douyin_comment_crawler.models import CommentRecord


class JobStore:
    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init(self) -> None:
        with self.connection() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode = WAL;
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    target_type TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    target TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_error TEXT,
                    cooldown_until TEXT
                );
                CREATE TABLE IF NOT EXISTS comments (
                    job_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    video_id TEXT NOT NULL,
                    comment_id TEXT NOT NULL,
                    parent_comment_id TEXT,
                    user_id TEXT,
                    user_sec_uid TEXT,
                    user_nickname TEXT,
                    raw_text TEXT NOT NULL,
                    clean_text TEXT NOT NULL,
                    created_at TEXT,
                    like_count INTEGER NOT NULL,
                    ip_region TEXT,
                    crawled_at TEXT NOT NULL,
                    flags_json TEXT NOT NULL,
                    PRIMARY KEY (job_id, platform, comment_id)
                );
                CREATE TABLE IF NOT EXISTS cursors (
                    job_id TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    cursor TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (job_id, scope)
                );
                CREATE TABLE IF NOT EXISTS failures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    error TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS account_health (
                    cookie_group TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    last_error TEXT,
                    cooldown_until TEXT,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS job_metrics (
                    job_id TEXT PRIMARY KEY,
                    videos_seen INTEGER NOT NULL DEFAULT 0,
                    comments_seen INTEGER NOT NULL DEFAULT 0,
                    comments_saved INTEGER NOT NULL DEFAULT 0,
                    replies_seen INTEGER NOT NULL DEFAULT 0,
                    api_requests INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL
                );
                """
            )
            _ensure_column(conn, "jobs", "cooldown_until", "TEXT")

    def create_job(self, target_type: str, platform: str, target: str) -> str:
        job_id = uuid.uuid4().hex
        now = _now()
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO jobs (job_id, target_type, platform, target, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'running', ?, ?)
                """,
                (job_id, target_type, platform, target, now, now),
            )
            conn.execute(
                "INSERT INTO job_metrics (job_id, updated_at) VALUES (?, ?)",
                (job_id, now),
            )
        return job_id

    def update_job_status(
        self,
        job_id: str,
        status: str,
        last_error: str | None = None,
        cooldown_until: str | None = None,
    ) -> None:
        with self.connection() as conn:
            conn.execute(
                "UPDATE jobs SET status = ?, updated_at = ?, last_error = ?, cooldown_until = ? WHERE job_id = ?",
                (status, _now(), last_error, cooldown_until, job_id),
            )

    def get_job(self, job_id: str) -> dict[str, Any]:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(f"job not found: {job_id}")
        return dict(row)

    def latest_job(self) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 1").fetchone()
        return dict(row) if row else None

    def save_comment(self, job_id: str, record: CommentRecord) -> bool:
        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO comments (
                    job_id, platform, video_id, comment_id, parent_comment_id, user_id, user_sec_uid,
                    user_nickname, raw_text, clean_text, created_at, like_count, ip_region, crawled_at, flags_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    record.platform,
                    record.video_id,
                    record.comment_id,
                    record.parent_comment_id,
                    record.user_id,
                    record.user_sec_uid,
                    record.user_nickname,
                    record.raw_text,
                    record.clean_text,
                    record.created_at,
                    record.like_count,
                    record.ip_region,
                    record.crawled_at,
                    json.dumps(record.flags, ensure_ascii=False),
                ),
            )
        return cur.rowcount == 1

    def iter_comments(self, job_id: str) -> Iterable[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM comments WHERE job_id = ? ORDER BY rowid ASC",
                (job_id,),
            ).fetchall()
        for row in rows:
            item = dict(row)
            flags_json = item.pop("flags_json")
            item["flags"] = json.loads(flags_json)
            yield item

    def iter_parent_comments(self, job_id: str) -> Iterable[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM comments
                WHERE job_id = ? AND parent_comment_id IS NULL
                ORDER BY rowid ASC
                """,
                (job_id,),
            ).fetchall()
        for row in rows:
            item = dict(row)
            flags_json = item.pop("flags_json")
            item["flags"] = json.loads(flags_json)
            yield item

    def count_comments(self, job_id: str) -> int:
        with self.connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS count FROM comments WHERE job_id = ?", (job_id,)).fetchone()
        return int(row["count"])

    def save_cursor(self, job_id: str, scope: str, cursor: str) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO cursors (job_id, scope, cursor, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(job_id, scope) DO UPDATE SET cursor = excluded.cursor, updated_at = excluded.updated_at
                """,
                (job_id, scope, cursor, _now()),
            )

    def get_cursor(self, job_id: str, scope: str) -> str | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT cursor FROM cursors WHERE job_id = ? AND scope = ?",
                (job_id, scope),
            ).fetchone()
        return str(row["cursor"]) if row else None

    def mark_failed_attempt(self, job_id: str, scope: str, error: str) -> None:
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO failures (job_id, scope, error, created_at) VALUES (?, ?, ?, ?)",
                (job_id, scope, error, _now()),
            )

    def list_failures(self, job_id: str) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT scope, error, created_at FROM failures WHERE job_id = ? ORDER BY id ASC",
                (job_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def update_account_health(
        self,
        cookie_group: str,
        status: str,
        last_error: str | None = None,
        cooldown_until: str | None = None,
    ) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO account_health (cookie_group, status, last_error, cooldown_until, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(cookie_group) DO UPDATE SET
                    status = excluded.status,
                    last_error = excluded.last_error,
                    cooldown_until = excluded.cooldown_until,
                    updated_at = excluded.updated_at
                """,
                (cookie_group, status, last_error, cooldown_until, _now()),
            )

    def get_account_health(self, cookie_group: str) -> dict[str, Any]:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM account_health WHERE cookie_group = ?",
                (cookie_group,),
            ).fetchone()
        if row is None:
            return {
                "cookie_group": cookie_group,
                "status": "unknown",
                "last_error": None,
                "cooldown_until": None,
                "updated_at": None,
            }
        return dict(row)

    def list_account_health(self) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM account_health ORDER BY updated_at DESC").fetchall()
        return [dict(row) for row in rows]

    def increment_metric(self, job_id: str, metric: str, amount: int = 1) -> None:
        allowed = {"videos_seen", "comments_seen", "comments_saved", "replies_seen", "api_requests"}
        if metric not in allowed:
            raise ValueError(f"unsupported metric: {metric}")
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO job_metrics (job_id, updated_at)
                VALUES (?, ?)
                ON CONFLICT(job_id) DO NOTHING
                """,
                (job_id, _now()),
            )
            conn.execute(
                f"UPDATE job_metrics SET {metric} = {metric} + ?, updated_at = ? WHERE job_id = ?",
                (amount, _now(), job_id),
            )

    def set_metric(self, job_id: str, metric: str, value: int) -> None:
        allowed = {"videos_seen", "comments_seen", "comments_saved", "replies_seen", "api_requests"}
        if metric not in allowed:
            raise ValueError(f"unsupported metric: {metric}")
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO job_metrics (job_id, updated_at)
                VALUES (?, ?)
                ON CONFLICT(job_id) DO NOTHING
                """,
                (job_id, _now()),
            )
            conn.execute(
                f"UPDATE job_metrics SET {metric} = ?, updated_at = ? WHERE job_id = ?",
                (value, _now(), job_id),
            )

    def get_job_metrics(self, job_id: str) -> dict[str, Any]:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM job_metrics WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            return {
                "job_id": job_id,
                "videos_seen": 0,
                "comments_seen": 0,
                "comments_saved": 0,
                "replies_seen": 0,
                "api_requests": 0,
                "updated_at": None,
            }
        return dict(row)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def cooldown_deadline(seconds: int | None) -> str:
    delay = seconds if seconds is not None else 3600
    return (datetime.now(timezone.utc) + timedelta(seconds=delay)).isoformat()


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, column_type: str) -> None:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    if column not in {row["name"] for row in rows}:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
