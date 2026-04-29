# Timesheet API

面向接单交付的独立 API 服务，已经补齐基础交付能力：

- `GET /health/live` 与 `GET /health/ready`
- `X-API-Token` 鉴权
- 默认 SQLite 存储，可通过 `DATABASE_URL` 升级
- 在线 OpenAPI 与 Apifox 导入
- `tests/` 下最小自动化验证

## 本地运行

```bash
cd apps/timesheet-api
export API_TOKEN=dev-token
uvicorn app.main:app --host 0.0.0.0 --port 8028 --reload
```

## Docker 运行

```bash
cd <repo-root>
docker compose --profile timesheet up --build timesheet-api
```

## 验证

```bash
cd apps/timesheet-api
python -m unittest discover -s tests
```

## OpenAPI / Apifox

启动后可直接导入：`http://localhost:8028/openapi.json`

也可导出为本地文件：

```bash
cd apps/timesheet-api
python -c 'import json; from app.main import app; print(json.dumps(app.openapi(), ensure_ascii=False, indent=2))' > openapi.json
```

## 关键环境变量

- `APP_NAME`：服务展示名
- `API_PREFIX`：默认 `/api/v1`
- `API_TOKEN`：接口鉴权令牌
- `DATABASE_URL`：默认 `sqlite:///./data/app.db`
