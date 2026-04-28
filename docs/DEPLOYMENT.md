# 部署指南

## 1. 前置条件

- 已安装 Docker
- 已安装 Docker Compose（Docker Desktop 内置）

## 2. 配置环境变量

```bash
cp .env.example .env
```

建议至少修改：

- `API_TOKEN`
- `PORT`

## 3. 启动

```bash
docker compose up -d --build
```

## 4. 检查状态

```bash
docker compose ps
```

## 5. 查看日志

```bash
docker compose logs -f app
```

## 6. 停止服务

```bash
docker compose down
```

## 7. 生产环境建议

- 将 `API_TOKEN` 放到 CI/CD Secret。
- 将 SQLite 替换为 PostgreSQL。
- 增加反向代理（Nginx / Caddy）和 HTTPS。
- 增加自动备份策略。

