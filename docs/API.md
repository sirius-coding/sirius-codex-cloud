# API 文档（默认模板）

## 基础信息

- Base URL: `http://localhost:8000`
- 鉴权方式：`Authorization: Bearer <API_TOKEN>`
- 业务 API 前缀：`/api/v1`

## 健康检查

### `GET /health/live`
用于容器存活探针（liveness）。

### `GET /health/ready`
用于依赖可用性探针（readiness，含数据库检查）。

## 客户接口

### 创建客户
`POST /api/v1/clients`

请求体：

```json
{
  "name": "某某科技",
  "contact": "王总 138xxxx",
  "notes": "老客户"
}
```

### 客户列表
`GET /api/v1/clients?limit=50&offset=0`

## 项目接口

### 创建项目
`POST /api/v1/projects`

请求体：

```json
{
  "client_id": 1,
  "title": "官网改版",
  "status": "doing",
  "budget": 20000,
  "deadline": "2026-12-31"
}
```

### 项目列表
`GET /api/v1/projects?limit=50&offset=0`

## 在线文档

启动后访问：
- Swagger UI: `/docs`
- ReDoc: `/redoc`
