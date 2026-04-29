# API 文档

## 统一约定

### FastAPI 子项目

- 默认前缀：`/api/v1`
- 默认鉴权：`X-API-Token: <API_TOKEN>`，`freelance-api` 使用 `Authorization: Bearer <API_TOKEN>`
- 在线文档：`/docs`
- OpenAPI：`/openapi.json`
- 健康检查：`/health/live`、`/health/ready`

### Apifox 导入

FastAPI 子项目启动后，可直接导入对应服务的 `http://localhost:<port>/openapi.json`。

也可在项目目录中导出：

```bash
python -c 'import json; from app.main import app; print(json.dumps(app.openapi(), ensure_ascii=False, indent=2))' > openapi.json
```

## 参考接口

### `freelance-api`

- `POST /api/v1/clients`
- `GET /api/v1/clients`
- `POST /api/v1/projects`
- `GET /api/v1/projects`

### 通用 CRUD API

以下项目统一提供：创建、列表、详情、更新四类接口。

- `crm-api`：`/customers`
- `invoice-service`：`/invoices`
- `helpdesk-api`：`/tickets`
- `inventory-api`：`/items`
- `subscription-billing-api`：`/subscriptions`
- `notification-hub`：`/messages`
- `contract-lifecycle-api`：`/contracts`
- `timesheet-api`：`/timesheets`
- `lead-scoring-api`：`/leads`
- `knowledge-base-api`：`/articles`

### 特殊项目

- `booking-api`：预约创建、按日期/状态过滤、状态流转
- `china-commerce-starter`：注册、商品、购物车、订单、支付
