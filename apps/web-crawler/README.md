# web-crawler

一个轻量的 Python 爬虫示例项目（单域名 BFS 抓取），适合作为 Monorepo 中的第二个独立服务。

## 功能

- 从指定起始 URL 开始抓取（默认限制在同一域名）。
- 抓取页面标题、状态码、发现的同域链接数量。
- 支持单次运行或按固定间隔持续运行。

## 本地运行

```bash
cd apps/web-crawler
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py --url https://example.com --max-pages 5
```

## Docker Compose 运行

在仓库根目录执行：

```bash
docker compose --profile crawler up --build web-crawler
```

可通过根目录 `.env` 中的以下参数调整：

- `CRAWLER_URL`
- `CRAWLER_MAX_PAGES`
- `CRAWLER_INTERVAL_SECONDS`
