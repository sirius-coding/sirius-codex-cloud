# Booking API

用于中小团队的预约管理 API，已补齐交付基线：

- 预约创建与时间冲突检测
- `GET /health/live` 与 `GET /health/ready`
- `X-API-Token` 鉴权
- SQLite 默认落盘，支持 `DATABASE_URL` 覆盖
- 自动化测试覆盖基础流程和冲突场景

## 本地运行

```bash
cd apps/booking-api
export API_TOKEN=dev-token
uvicorn app.main:app --reload --port 8010
```

## Docker 运行

```bash
cd <repo-root>
docker compose --profile booking up --build booking-api
```

## 验证

```bash
cd apps/booking-api
python -m unittest discover -s tests
```

## OpenAPI / Apifox

启动后可直接导入：`http://localhost:8010/openapi.json`

导出命令：

```bash
cd apps/booking-api
python -c 'import json; from app.main import app; print(json.dumps(app.openapi(), ensure_ascii=False, indent=2))' > openapi.json
```

## 示例请求

```bash
curl -X POST 'http://localhost:8010/api/v1/bookings'       -H 'Content-Type: application/json'       -H 'X-API-Token: dev-token'       -d '{
    "client_name":"张三",
    "service_name":"网站维护",
    "start_at":"2026-04-28T10:00:00",
    "end_at":"2026-04-28T11:00:00",
    "notes":"远程会议"
  }'
```
