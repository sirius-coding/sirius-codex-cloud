from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from douyin_comment_crawler.storage import JobStore


FIELDNAMES = [
    "job_id",
    "platform",
    "video_id",
    "comment_id",
    "parent_comment_id",
    "user_id",
    "user_sec_uid",
    "user_nickname",
    "raw_text",
    "clean_text",
    "created_at",
    "like_count",
    "ip_region",
    "crawled_at",
    "flags",
]


def export_job(
    store: JobStore,
    job_id: str,
    output_dir: Path | str,
    fmt: str,
    exclude_flags: set[str] | None = None,
) -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = list(_filtered_rows(store, job_id, exclude_flags or set()))
    if fmt == "jsonl":
        path = output / f"{job_id}.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return path
    if fmt == "csv":
        path = output / f"{job_id}.csv"
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
            writer.writeheader()
            for row in rows:
                row = dict(row)
                row["flags"] = ",".join(row["flags"])
                writer.writerow(row)
        return path
    raise ValueError("format must be jsonl or csv")


def _filtered_rows(store: JobStore, job_id: str, exclude_flags: set[str]) -> Iterable[dict]:
    for row in store.iter_comments(job_id):
        flags = set(row["flags"])
        if flags.intersection(exclude_flags):
            continue
        yield {"job_id": job_id, **row}
