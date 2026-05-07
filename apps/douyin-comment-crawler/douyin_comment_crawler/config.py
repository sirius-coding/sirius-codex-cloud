from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeConfig:
    db_path: Path
    export_dir: Path
    douyin_cookie: str | None
    douyin_proxy_url: str | None
    douyin_api_base_url: str | None
    douyin_comments_path: str
    douyin_replies_path: str
    douyin_user_posts_path: str
    douyin_page_size: int
    douyin_timeout_seconds: float


def load_runtime_config(env_path: Path | str = ".env") -> RuntimeConfig:
    values = _read_env_file(Path(env_path))

    def get(name: str, default: str | None = None) -> str | None:
        return os.getenv(name, values.get(name, default))

    return RuntimeConfig(
        db_path=Path(get("COMMENT_CRAWLER_DB_PATH", "data/jobs.db") or "data/jobs.db"),
        export_dir=Path(get("COMMENT_CRAWLER_EXPORT_DIR", "exports") or "exports"),
        douyin_cookie=get("DOUYIN_COOKIE"),
        douyin_proxy_url=get("DOUYIN_PROXY_URL"),
        douyin_api_base_url=get("DOUYIN_API_BASE_URL"),
        douyin_comments_path=get(
            "DOUYIN_COMMENTS_PATH",
            "/api/douyin/web/fetch_video_comments?aweme_id={aweme_id}&cursor={cursor}&count={count}",
        )
        or "",
        douyin_replies_path=get(
            "DOUYIN_REPLIES_PATH",
            "/api/douyin/web/fetch_video_comment_replies?item_id={aweme_id}&comment_id={comment_id}&cursor={cursor}&count={count}",
        )
        or "",
        douyin_user_posts_path=get(
            "DOUYIN_USER_POSTS_PATH",
            "/api/douyin/web/fetch_user_post_videos?sec_user_id={sec_user_id}&max_cursor={cursor}&count={count}",
        )
        or "",
        douyin_page_size=int(get("DOUYIN_PAGE_SIZE", "20") or "20"),
        douyin_timeout_seconds=float(get("DOUYIN_TIMEOUT_SECONDS", "20") or "20"),
    )


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values
