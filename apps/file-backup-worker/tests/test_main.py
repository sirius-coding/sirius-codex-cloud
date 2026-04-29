from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from main import backup_folder


class FileBackupWorkerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        base = Path(self.tempdir.name)
        self.source = base / "source"
        self.target = base / "target"
        self.source.mkdir()
        (self.source / "a.txt").write_text("hello", encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_backup_creates_manifest(self) -> None:
        backup_folder(self.source, self.target, keep=10)
        manifest = json.loads((self.target / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest), 1)

    def test_same_file_not_duplicated(self) -> None:
        backup_folder(self.source, self.target, keep=10)
        backup_folder(self.source, self.target, keep=10)
        manifest = json.loads((self.target / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest), 1)

    def test_negative_keep_rejected(self) -> None:
        with self.assertRaises(ValueError):
            backup_folder(self.source, self.target, keep=-1)


if __name__ == "__main__":
    unittest.main()
