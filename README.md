# 程序员私活项目模板（Freelance Starter）

这是一个面向接单交付场景的多项目模板仓库。`apps/` 下的每个子项目都保持独立可交付，根目录负责统一编排、文档和交付规范。

## 当前内置项目

### API 服务

- `freelance-api`：客户与项目管理 API（FastAPI）
- `booking-api`：预约/排期管理 API
- `crm-api`：客户档案 API
- `invoice-service`：发票管理 API
- `helpdesk-api`：工单管理 API
- `inventory-api`：库存管理 API
- `subscription-billing-api`：订阅计费 API
- `notification-hub`：通知中心 API
- `contract-lifecycle-api`：合同管理 API
- `timesheet-api`：工时管理 API
- `lead-scoring-api`：销售线索 API
- `knowledge-base-api`：知识库 API
- `china-commerce-starter`：Spring Boot 电商骨架

### CLI / Worker

- `expense-tracker`：自由职业者支出管理 CLI
- `file-backup-worker`：增量备份 Worker
- `web-crawler`：单域名 BFS 爬虫

## 交付基线

本轮仓库统一升级后的交付要求：

- 每个子项目都具备独立 README、启动命令、验证命令、配置说明。
- Python API 统一具备 `health/live`、`health/ready`、鉴权、SQLite 默认交付和 PostgreSQL 升级入口。
- CLI / Worker 统一具备参数校验、示例命令和自动化测试。
- 根目录提供统一启动、停止、状态查看脚本和升级路线文档。

升级顺序与状态见 [docs/roadmaps/2026-04-29-subproject-delivery-upgrade-plan.md](docs/roadmaps/2026-04-29-subproject-delivery-upgrade-plan.md)。

## 快速开始

### 1) 初始化环境

```bash
bash scripts/bootstrap.sh
```

如已存在 `.env`，脚本不会覆盖。首次使用请修改 `API_TOKEN` 等变量。

### 2) 使用统一脚本

```bash
bash scripts/up.sh
bash scripts/up.sh booking-api
bash scripts/status.sh
bash scripts/down.sh
```

默认启动 `freelance-api`；传入服务名时会按对应 profile 启动指定子项目。

### 3) 文档与 OpenAPI

- 仓库级文档在 `docs/`
- FastAPI 项目默认在线暴露 `/openapi.json`
- 每个 API README 都包含 Apifox 导入和导出命令

## 文档目录

- [架构说明](docs/ARCHITECTURE.md)
- [API 文档](docs/API.md)
- [部署指南](docs/DEPLOYMENT.md)
- [定制指南](docs/CUSTOMIZATION.md)
- [升级路线](docs/roadmaps/2026-04-29-subproject-delivery-upgrade-plan.md)

## 项目结构

```text
.
├── apps/                     # 独立交付子项目
├── docs/                     # 仓库级文档与路线
├── scripts/                  # 统一启动、停止、状态、导出脚本
├── docker-compose.yml        # 根级编排
├── .env.example             # 演示环境变量模板
└── README.md
```

## 验证建议

- Python API：在项目目录执行 `python -m unittest discover -s tests`
- Java 项目：在 `apps/china-commerce-starter` 执行 `mvn test`
- Docker 环境可用时：配合 `scripts/up.sh` 做容器级联调
