# Expense Tracker

面向自由职业者的命令行支出管理工具，已补齐交付基线：

- 支出新增、最近流水、月度统计
- 参数合法性校验
- SQLite 本地落盘
- 自动化测试覆盖主要命令路径

## 使用示例

```bash
cd apps/expense-tracker
python main.py add --amount 99.9 --category 云服务 --spent-at 2026-04-28 --description "对象存储"
python main.py list --limit 10
python main.py report --month 2026-04
```

## 验证

```bash
cd apps/expense-tracker
python -m unittest discover -s tests
```

## 环境变量

- `EXPENSE_DB_PATH`：默认 `data/expenses.db`
