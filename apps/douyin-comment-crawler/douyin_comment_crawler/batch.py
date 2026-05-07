from __future__ import annotations

from pathlib import Path

from douyin_comment_crawler.adapters.base import PlatformAdapter
from douyin_comment_crawler.crawler import crawl_account, crawl_video
from douyin_comment_crawler.models import RiskProfile
from douyin_comment_crawler.storage import JobStore


def crawl_batch_file(
    store: JobStore,
    adapter: PlatformAdapter,
    path: Path | str,
    include_replies: bool,
    risk: RiskProfile,
) -> list[str]:
    job_ids: list[str] = []
    for line_no, target_type, target in _iter_targets(Path(path)):
        if target_type == "video":
            job_ids.append(crawl_video(store, adapter, target, include_replies, risk))
        elif target_type == "account":
            job_ids.append(crawl_account(store, adapter, target, include_replies, risk))
        else:
            raise ValueError(f"unsupported target type on line {line_no}: {target_type}")
    return job_ids


def _iter_targets(path: Path):
    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "," not in line:
            raise ValueError(f"batch line {line_no} must be '<video|account>,<target>'")
        target_type, target = line.split(",", 1)
        target_type = target_type.strip().lower()
        target = target.strip()
        if not target:
            raise ValueError(f"batch line {line_no} target is empty")
        yield line_no, target_type, target
