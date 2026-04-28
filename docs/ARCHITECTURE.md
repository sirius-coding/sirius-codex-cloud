# 架构说明

## 1. 设计原则

1. **最小可交付**：先满足私活上线，再逐步扩展。
2. **低运维成本**：单服务即可跑通，默认 SQLite。
3. **可平滑升级**：后续替换 PostgreSQL / Redis 不影响主体结构。
4. **Monorepo-ready**：仓库支持持续增加新项目。

## 2. 当前架构

- `apps/freelance-api`：核心业务 API（FastAPI + SQLAlchemy）。
- `SQLite` 默认存储到 `apps/freelance-api/data/freelance.db`。
- `docker-compose` 负责聚合编排。
- `docs/` 维护统一项目文档。

## 3. 生产级能力（模板默认）

- 健康检查：`/health/live`、`/health/ready`。
- 鉴权：`Authorization: Bearer <API_TOKEN>`。
- 数据库可用性探针：readiness 会执行 DB ping。
- CORS 配置：支持通过环境变量统一配置。
- 容器安全：应用以非 root 用户运行。
- API 版本化：默认前缀 `/api/v1`。

## 4. 领域模型（默认）

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

## 5. 多项目扩展建议

- 在 `apps/` 中新增项目目录：
  - `apps/admin-web`（管理端前端）
  - `apps/report-worker`（异步报表任务）
  - `apps/integration-gateway`（第三方集成层）
- 根 `docker-compose.yml` 统一编排。
- 公共规范放在根目录文档；各项目内部实现独立演进。
