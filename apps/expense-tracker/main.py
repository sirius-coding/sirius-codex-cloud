from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/expenses.db")


@dataclass
class Expense:
    amount: float
    category: str
    spent_at: str
    description: str


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            spent_at TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def add_expense(expense: Expense) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO expenses (amount, category, spent_at, description, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (expense.amount, expense.category, expense.spent_at, expense.description, datetime.utcnow().isoformat()),
        )
        conn.commit()


def list_expenses(limit: int) -> None:
    with get_conn() as conn:
        cursor = conn.execute(
            """
            SELECT id, amount, category, spent_at, description
            FROM expenses
            ORDER BY spent_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()

    if not rows:
        print("暂无支出记录")
        return

    for row in rows:
        print(f"#{row[0]} | ¥{row[1]:.2f} | {row[2]} | {row[3]} | {row[4]}")


def monthly_report(month: str) -> None:
    with get_conn() as conn:
        cursor = conn.execute(
            """
            SELECT category, COUNT(*), SUM(amount)
            FROM expenses
            WHERE substr(spent_at, 1, 7) = ?
            GROUP BY category
            ORDER BY SUM(amount) DESC
            """,
            (month,),
        )
        rows = cursor.fetchall()

    if not rows:
        print(f"{month} 没有支出记录")
        return

    total = 0.0
    print(f"{month} 月度支出报告")
    for category, count, amount in rows:
        total += amount
        print(f"- {category}: {count} 笔, 合计 ¥{amount:.2f}")
    print(f"总计: ¥{total:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Freelancer Expense Tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    add_parser = sub.add_parser("add", help="新增支出")
    add_parser.add_argument("--amount", type=float, required=True)
    add_parser.add_argument("--category", required=True)
    add_parser.add_argument("--spent-at", required=True, help="YYYY-MM-DD")
    add_parser.add_argument("--description", required=True)

    list_parser = sub.add_parser("list", help="查看最近支出")
    list_parser.add_argument("--limit", type=int, default=20)

    report_parser = sub.add_parser("report", help="生成月度报告")
    report_parser.add_argument("--month", required=True, help="YYYY-MM")

    args = parser.parse_args()

    if args.command == "add":
        add_expense(
            Expense(
                amount=args.amount,
                category=args.category,
                spent_at=args.spent_at,
                description=args.description,
            )
        )
        print("已新增支出")
    elif args.command == "list":
        list_expenses(limit=args.limit)
    elif args.command == "report":
        monthly_report(month=args.month)


if __name__ == "__main__":
    main()
