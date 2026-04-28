# API 文档（简版）

## 通用说明

- Base URL: `http://localhost:8000`
- 受保护接口需要 Header：

```http
Authorization: Bearer <API_TOKEN>
```

## 1. 健康检查

### GET /health

无需鉴权。

响应：

```json
{"status": "ok"}
```

## 2. 创建客户

### POST /api/clients

请求体：

```json
{
  "name": "某某餐饮",
  "contact": "王总 138xxxx",
  "notes": "重点客户"
}
```

## 3. 查询客户列表

### GET /api/clients

返回客户数组。

## 4. 创建项目

### POST /api/projects

请求体：

```json
{
  "client_id": 1,
  "title": "门店预约小程序后端",
  "status": "in_progress",
  "budget": 18000,
  "deadline": "2026-06-30"
}
```

## 5. 查询项目列表

### GET /api/projects

返回项目数组。

