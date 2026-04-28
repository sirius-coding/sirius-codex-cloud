# File Backup Worker

增量文件备份工具，适用于：
- 客户交付文件自动归档
- 本地文档快照留存
- 简易灾备与回滚

## 示例

```bash
python main.py --source ./project-files --target ./backup-output --keep 50
```

首次会备份所有文件；后续仅备份有变更的文件（基于 SHA256）。
