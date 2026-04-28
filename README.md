# 程序员私活项目模板（Freelance Starter）

这是一个面向 **程序员接私活** 的生产级模板仓库，默认包含多个可独立交付的中型项目，并且仓库结构已调整为 **可扩展多项目（Monorepo-ready）**。

## 当前内置项目

- `freelance-api`：客户与项目管理 API（FastAPI）
- `web-crawler`：可配置的通用爬虫任务
- `booking-api`：预约/排期管理 API（冲突检测 + 状态流转）
- `expense-tracker`：自由职业者支出管理 CLI（流水 + 月报）
- `file-backup-worker`：增量备份 Worker（哈希去重 + 保留策略）

这些项目都可以直接作为外包交付的起点，或作为你自己的工具链组件。

## 核心目标

- **多项目可扩展**：`apps/` 目录可持续新增服务，不影响现有项目。
- **生产级默认配置**：健康检查、结构化日志、CORS、DB 可用性探针、容器非 root 运行。
- **可交付与可运维**：开箱即用 docker-compose，默认配置适合演示与小规模生产。
- **文档完整**：含架构、API、部署、二次开发说明。

## 技术栈

- Python 3.12
- FastAPI / SQLModel / SQLite
- Docker / Docker Compose
- MkDocs（可选：文档站点）

## 快速开始

### 1) 准备环境变量

```bash
cp .env.example .env
```

> 请修改 `.env` 里的 `API_TOKEN`，用于接口鉴权。

### 2) 启动核心项目

```bash
docker compose up -d --build
```

默认启动 `freelance-api`。

### 3) 按需启动其他项目

```bash
# 爬虫
docker compose --profile crawler up --build web-crawler

# 预约 API
docker compose --profile booking up --build booking-api

# 支出管理 CLI（展示帮助）
docker compose --profile expense up --build expense-tracker

# 文件备份 Worker（展示帮助）
docker compose --profile backup up --build file-backup-worker
```

### 4) API 访问示例

- Freelance API 根地址: http://localhost:8000
- Booking API 根地址: http://localhost:8010

## 文档目录

- [架构说明](docs/ARCHITECTURE.md)
- [API 文档](docs/API.md)
- [部署指南](docs/DEPLOYMENT.md)
- [定制指南](docs/CUSTOMIZATION.md)

## 一键预览文档站（可选）

```bash
docker compose --profile docs up docs
```

文档地址： http://localhost:9000

## 项目结构（Monorepo-ready）

```text
.
├── apps/
│   ├── freelance-api/
│   ├── web-crawler/
│   ├── booking-api/
│   ├── expense-tracker/
│   └── file-backup-worker/
├── docs/
├── scripts/
├── .env.example
├── docker-compose.yml
├── mkdocs.yml
└── README.md
```

## 后续新增项目建议

- 在 `apps/` 下继续新增独立目录，例如：`apps/admin-web`、`apps/report-worker`。
- 每个项目独立维护其启动方式、Dockerfile、依赖与 README。
- 通过根目录 `docker-compose.yml` 聚合编排。
