# 架构说明

## 1. 设计原则

1. **最小可交付**：先满足私活上线，再逐步扩展。
2. **低运维成本**：单容器 + SQLite 默认可跑通。
3. **可平滑升级**：后续替换 PostgreSQL / Redis 不影响主体结构。

## 2. 当前架构

- `FastAPI` 提供 REST API。
- `SQLAlchemy` 负责 ORM 与持久化。
- `SQLite` 默认存储到 `backend/data/freelance.db`。
- `docker-compose` 负责构建与启动。

## 3. 领域模型（默认）

### Client（客户）
- name
- contact
- notes

### Project（项目）
- client_id
- title
- status
- budget
- deadline

> 一个 Client 下可以有多个 Project。

## 4. 鉴权策略

为了便于私活快速落地，模板采用 **静态 Token**：
- Header: `Authorization: Bearer <API_TOKEN>`
- 适用于 MVP 或内网系统。

生产建议升级为：
- JWT + 用户系统
- RBAC（角色权限）
- API 网关限流

## 5. 扩展建议

- 增加 `Invoice`（开票）模型。
- 增加 `Task`（任务）模型。
- 增加 `Worklog`（工时）模型。
- 增加 Webhook 与消息通知（邮件/企业微信/飞书）。

