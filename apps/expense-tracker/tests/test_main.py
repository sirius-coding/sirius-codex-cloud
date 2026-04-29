from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from main import Expense, add_expense, list_expenses, monthly_report


class ExpenseTrackerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        os.environ["EXPENSE_DB_PATH"] = str(Path(self.tempdir.name) / "expenses.db")

    def tearDown(self) -> None:
        self.tempdir.cleanup()
        os.environ.pop("EXPENSE_DB_PATH", None)

    def test_add_and_list_expense(self) -> None:
        add_expense(Expense(amount=99.9, category="云服务", spent_at="2026-04-28", description="对象存储"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            list_expenses(limit=10)
        output = buf.getvalue()
        self.assertIn("云服务", output)
        self.assertIn("对象存储", output)

    def test_monthly_report(self) -> None:
        add_expense(Expense(amount=99.9, category="云服务", spent_at="2026-04-28", description="对象存储"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            monthly_report("2026-04")
        self.assertIn("月度支出报告", buf.getvalue())

    def test_rejects_invalid_amount(self) -> None:
        with self.assertRaises(ValueError):
            add_expense(Expense(amount=0, category="云服务", spent_at="2026-04-28", description="对象存储"))


if __name__ == "__main__":
    unittest.main()
