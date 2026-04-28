# Booking API

用于中小团队的预约管理 API，支持：
- 创建预约并检测时间冲突
- 按日期/状态筛选预约
- 更新预约状态（待确认/已确认/已取消）

## 本地运行

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8010
```

## 示例

```bash
curl -X POST 'http://localhost:8010/api/v1/bookings' \
  -H 'Content-Type: application/json' \
  -d '{
    "client_name":"张三",
    "service_name":"网站维护",
    "start_at":"2026-04-28T10:00:00",
    "end_at":"2026-04-28T11:00:00",
    "notes":"远程会议"
  }'
```
