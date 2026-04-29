# 多子项目交付化升级路线

更新时间：2026-04-29

## 目标

将仓库内所有子项目升级到“可直接交付”的统一生产基线：

- 独立 README、启动命令、验证命令、配置说明
- 健康检查、鉴权、错误路径与最小测试覆盖
- Docker 或本地运行方式清晰
- OpenAPI 或接口示例可直接给客户/Apifox 使用

## 升级优先级

1. `freelance-api`
2. `crm-api`
3. `invoice-service`
4. `contract-lifecycle-api`
5. `timesheet-api`
6. `booking-api`
7. `helpdesk-api`
8. `inventory-api`
9. `subscription-billing-api`
10. `lead-scoring-api`
11. `knowledge-base-api`
12. `notification-hub`
13. `expense-tracker`
14. `file-backup-worker`
15. `web-crawler`
16. `china-commerce-starter`

## 统一交付基线

### Python API

- `GET /health/live` 和 `GET /health/ready`
- 默认 `X-API-Token` 鉴权，支持 `.env` 或外部环境变量
- 默认 SQLite 直接交付，保留 `DATABASE_URL` 升级入口
- 在线 `openapi.json`，README 提供导出命令
- `tests/` 下最小冒烟测试

### CLI / Worker

- 参数合法性校验
- README 提供典型示例、失败场景和输出说明
- `tests/` 下最小回归测试

### Spring Boot

- README 明确运行、测试、配置和生产替换项
- 健康检查与容器化说明
- Maven 测试和环境变量占位配置

## 本次实施状态

- [x] 仓库级统一脚本
- [x] 升级路线写入项目文件
- [x] Python API README / 健康检查 / 测试基线
- [x] CLI / Worker 验证基线
- [x] Spring Boot README / Docker / 健康检查

## 后续可选深化

- 将部分高价值 API 切换到 PostgreSQL + Alembic
- 补充统一 CI
- 为高价值项目增加审计日志、限流、幂等和监控指标
