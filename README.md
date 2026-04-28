# 程序员私活项目模板（Freelance Starter）

这是一个面向 **程序员接私活** 的生产级模板仓库，默认包含：
- 一个可直接上线的 `freelance-api` 项目
- 一个可独立运行的 `web-crawler` 爬虫项目  
并且仓库结构已调整为 **可扩展多项目（Monorepo-ready）**。

你可以把它当作一个“起步盘”，快速扩展为：
- 外包项目管理系统
- 小型 CRM
- 工单/需求跟踪系统
- 预约/服务交付后台
- 后续新增 Web、管理后台、任务服务等独立项目

## 核心目标

- **多项目可扩展**：`apps/` 目录可持续新增服务，不影响现有项目。
- **生产级默认配置**：健康检查、结构化日志、CORS、DB 可用性探针、容器非 root 运行。
- **可交付与可运维**：开箱即用 docker-compose，默认配置适合演示与小规模生产。
- **文档完整**：含架构、API、部署、二次开发说明。

## 技术栈

- Python 3.12
- FastAPI
- SQLAlchemy
- SQLite（默认，可替换 PostgreSQL）
- Docker / Docker Compose
- MkDocs（可选：文档站点）

## 快速开始

### 1) 准备环境变量

```bash
cp .env.example .env
```

> 请修改 `.env` 里的 `API_TOKEN`，用于接口鉴权。

### 2) 启动项目

```bash
docker compose up -d --build
```

### 3) 访问服务

- API 根地址: http://localhost:8000
- 健康检查（liveness）: http://localhost:8000/health/live
- 健康检查（readiness）: http://localhost:8000/health/ready
- Swagger 文档: http://localhost:8000/docs

### 5) 启动爬虫项目（可选）

```bash
docker compose --profile crawler up --build web-crawler
```

> 爬虫参数可在 `.env` 中配置：`CRAWLER_URL`、`CRAWLER_MAX_PAGES`、`CRAWLER_INTERVAL_SECONDS`。

### 4) 调用受保护接口示例

```bash
curl -X GET 'http://localhost:8000/api/v1/clients' \
  -H 'Authorization: Bearer replace-with-your-token'
```

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
│   └── freelance-api/
│       ├── app/
│       │   ├── routes/
│       │   ├── config.py
│       │   ├── db.py
│       │   ├── main.py
│       │   ├── models.py
│       │   └── schemas.py
│       ├── Dockerfile
│       └── requirements.txt
│   └── web-crawler/
│       ├── Dockerfile
│       ├── README.md
│       ├── main.py
│       └── requirements.txt
├── docs/
├── scripts/
├── .env.example
├── docker-compose.yml
├── mkdocs.yml
└── README.md
```

## 后续新增项目建议

- 在 `apps/` 下新增独立目录，例如：`apps/admin-web`、`apps/report-worker`。
- 每个项目独立维护其启动方式、Dockerfile、依赖与 README。
- 通过根目录 `docker-compose.yml` 聚合编排。
