# Web Crawler

轻量 Python 爬虫示例项目，适合单域名抓取、演示或二次开发。

- 同域名 BFS 抓取
- 标题、状态码、链接计数输出
- 支持单次执行与定时执行
- 自动化测试覆盖 URL 规范化、链接过滤和参数校验

## 本地运行

```bash
cd apps/web-crawler
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py --url https://example.com --max-pages 5
```

## 验证

```bash
cd apps/web-crawler
python -m unittest discover -s tests
```

## 环境变量

- `CRAWLER_USER_AGENT`：覆盖默认 User-Agent
