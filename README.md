# 程序员私活项目模板（Freelance Starter）

这是一个面向 **程序员接私活** 的通用项目模板，默认用途是：

> 为中小企业/个体商家快速交付「客户 + 项目 + 预算 + 截止日期」管理后台 API。

你可以把它当作一个“起步盘”，在 1~2 天内改造成：
- 外包项目管理系统
- 小型 CRM
- 工单/需求跟踪系统
- 预约/服务交付后台

## 核心目标

- **通用性**：默认建模覆盖常见私活交付场景。
- **可扩展**：基于 FastAPI + SQLAlchemy，便于后续加模块。
- **部署便捷**：开箱即用 docker-compose。
- **文档完整**：含架构、API、部署、二次开发说明。

## 技术栈

- Python 3.12
- FastAPI
- SQLAlchemy
- SQLite（默认，可替换）
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
- 健康检查: http://localhost:8000/health
- Swagger 文档: http://localhost:8000/docs

### 4) 调用受保护接口示例

```bash
curl -X GET 'http://localhost:8000/api/clients' \
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

## 项目结构

```text
.
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── Dockerfile
│   └── requirements.txt
├── docs/
├── .env.example
├── docker-compose.yml
├── mkdocs.yml
└── README.md
```

## 适合谁用

- 想搭建「可交付、可演示、可上线」私活基础盘的开发者。
- 想减少重复造轮子的全栈/后端工程师。

