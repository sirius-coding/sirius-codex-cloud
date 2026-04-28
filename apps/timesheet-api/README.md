# Timesheet API

这是一个面向接单交付的 **工时管理** 服务模板，具备可直接上线的小型生产能力。

## 功能清单

- 统一健康检查：`/health/live`
- 鉴权入口：`X-API-Token`（默认兼容开发态 `dev-token`）
- SQLite 持久化存储（容器挂载 `data/`）
- 完整 CRUD：创建、列表、详情、更新
- 列表过滤：支持按状态与负责人过滤，支持分页参数 `limit/offset`

## 接口概览

- `POST /api/v1/timesheets`：创建记录
- `GET /api/v1/timesheets`：分页查询记录
- `GET /api/v1/timesheets/{id}`：查看单条记录
- `PATCH /api/v1/timesheets/{id}`：更新记录

## 本地运行

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8028 --reload
```

## Docker 运行

```bash
docker build -t timesheet-api:local .
docker run --rm -p 8028:8028 -v $(pwd)/data:/app/data timesheet-api:local
```

## 生产部署建议

1. 将 `X-API-Token` 改为网关统一鉴权（JWT/OAuth2）。
2. 将 SQLite 升级为 PostgreSQL，并接入迁移工具（Alembic）。
3. 追加审计日志、监控告警与备份策略。
4. 通过反向代理接入 TLS 与访问限流。

## 示例请求

```bash
curl -X POST 'http://localhost:8028/api/v1/timesheets'   -H 'Content-Type: application/json'   -H 'X-API-Token: dev-token'   -d '{
    "name": "示例记录",
    "description": "用于验收联调",
    "owner": "ops-team",
    "status": "active"
  }'
```
