# File Backup Worker

增量文件备份工具，适用于客户交付文件归档、快照留存和简易灾备。

- 基于 SHA256 的增量备份
- `manifest.json` 记录备份元数据
- `--keep` 控制保留策略
- 自动化测试覆盖新增、去重和参数错误

## 示例

```bash
cd apps/file-backup-worker
python main.py --source ./project-files --target ./backup-output --keep 50
```

## 验证

```bash
cd apps/file-backup-worker
python -m unittest discover -s tests
```
