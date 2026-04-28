from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class BackupRecord:
    source: str
    backup_file: str
    sha256: str
    size: int
    created_at: str


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(path: Path) -> list[BackupRecord]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [BackupRecord(**item) for item in data]


def save_manifest(path: Path, records: list[BackupRecord]) -> None:
    path.write_text(
        json.dumps([asdict(r) for r in records], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def backup_folder(source_dir: Path, target_dir: Path, keep: int) -> None:
    if not source_dir.exists() or not source_dir.is_dir():
        raise ValueError(f"源目录不存在: {source_dir}")

    target_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = target_dir / "manifest.json"
    records = load_manifest(manifest_path)

    indexed = {record.source: record.sha256 for record in records}

    created = 0
    for src in source_dir.rglob("*"):
        if not src.is_file():
            continue
        relative = src.relative_to(source_dir).as_posix()
        digest = sha256_file(src)
        if indexed.get(relative) == digest:
            continue

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        backup_file = f"{relative.replace('/', '__')}__{timestamp}"
        dst = target_dir / backup_file
        shutil.copy2(src, dst)

        records.append(
            BackupRecord(
                source=relative,
                backup_file=backup_file,
                sha256=digest,
                size=src.stat().st_size,
                created_at=datetime.utcnow().isoformat(),
            )
        )
        indexed[relative] = digest
        created += 1

    records.sort(key=lambda x: x.created_at, reverse=True)
    if keep > 0:
        kept = records[:keep]
        keep_names = {record.backup_file for record in kept}
        for stale in target_dir.iterdir():
            if stale.name == "manifest.json":
                continue
            if stale.is_file() and stale.name not in keep_names:
                stale.unlink()
        records = kept

    save_manifest(manifest_path, records)
    print(f"备份完成，新增 {created} 个文件，当前保留 {len(records)} 份记录")


def main() -> None:
    parser = argparse.ArgumentParser(description="Incremental file backup worker")
    parser.add_argument("--source", required=True, help="源目录")
    parser.add_argument("--target", required=True, help="备份目录")
    parser.add_argument("--keep", type=int, default=100, help="最大保留备份记录数")
    args = parser.parse_args()

    backup_folder(Path(args.source), Path(args.target), keep=args.keep)


if __name__ == "__main__":
    main()
