# Freelance API

面向私活交付管理的参考 API，也是本仓库的 Python 服务基线实现。

- `Authorization: Bearer <API_TOKEN>` 鉴权
- `GET /health/live` 与 `GET /health/ready`
- 客户与项目两类核心资源
- 默认 SQLite，可通过 `DATABASE_URL` 切换
- 在线 OpenAPI 与 unittest 验证

## 本地运行

```bash
cd apps/freelance-api
export API_TOKEN=dev-token
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 验证

```bash
cd apps/freelance-api
python -m unittest discover -s tests
```

## OpenAPI / Apifox

启动后可直接导入：`http://localhost:8000/openapi.json`

导出命令：

```bash
cd apps/freelance-api
python -c 'import json; from app.main import app; print(json.dumps(app.openapi(), ensure_ascii=False, indent=2))' > openapi.json
```
