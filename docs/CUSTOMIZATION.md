# 定制指南

## 推荐扩展顺序

1. 先改领域模型和校验规则
2. 再补接口或 CLI 参数
3. 最后补权限、报表、通知和外部集成

## Python API 常见改造

- 调整资源字段：直接修改各项目的 `app/main.py` 数据模型和请求模型
- 切换数据库：通过 `DATABASE_URL` 从 SQLite 升级到 PostgreSQL
- 增加权限：在现有 `X-API-Token` 或 `Authorization` 基础上切换到网关/JWT
- 增加测试：在对应项目 `tests/` 目录追加 unittest 用例

## CLI / Worker 常见改造

- `expense-tracker`：增加分类、标签、导出 CSV
- `file-backup-worker`：增加排除规则、远程对象存储
- `web-crawler`：增加 robots 策略、抓取深度和输出格式

## Spring Boot 项目常见改造

- 将 `application.yml` 中的数据库、Redis、端口切换为环境变量
- 将支付 mock 替换为真实 SDK
- 补充控制器测试、限流和幂等逻辑

## 新增子项目建议

- 继续放在 `apps/` 下独立维护
- README 至少包含启动、测试、配置、交付说明
- 优先复用本仓库的健康检查、配置和验证约定
