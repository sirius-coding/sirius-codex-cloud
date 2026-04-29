# 部署指南

## 1. 前置条件

- Docker / Docker Compose，可用于容器级启动
- Python 3.12+，用于本地执行 CLI / Worker / unittest
- Java 17+ 与 Maven，供 `china-commerce-starter` 使用

## 2. 初始化

```bash
bash scripts/bootstrap.sh
```

建议至少检查：

- `API_TOKEN`
- `DATABASE_URL`
- `CRAWLER_URL`
- 目标服务对应端口

## 3. 启动方式

### 根级统一脚本

```bash
bash scripts/up.sh
bash scripts/up.sh booking-api
bash scripts/status.sh
```

### 原生命令

```bash
docker compose up -d --build
docker compose --profile booking up -d --build booking-api
```

## 4. 停止与清理

```bash
bash scripts/down.sh
bash scripts/down.sh booking-api
```

## 5. 生产建议

- 演示或轻量交付默认可继续使用 SQLite。
- 正式生产建议通过 `DATABASE_URL` 切换 PostgreSQL。
- 将密钥放入环境变量或 CI/CD Secret，不要写入仓库。
- API 前建议增加反向代理、TLS、日志归档和备份。
- 高价值项目可继续补充迁移工具、监控和限流。
