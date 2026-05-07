# 抖音评论采集 CLI 操作说明书

## 1. 投产结论

当前项目已经具备投产前联调所需的 CLI、SQLite 状态库、断点游标、去重、导出、批量任务、账号组冷却和 HTTP adapter。

但它不能在没有私有 Douyin API 服务的情况下直接采集真实抖音数据。投产必须先准备一个你有权使用的 API 服务，例如私有部署的 `Evil0ctal/Douyin_TikTok_Download_API` 兼容服务，并配置 `DOUYIN_API_BASE_URL` 与接口路径模板。

## 2. 环境准备

```bash
cd apps/douyin-comment-crawler
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`，只在本地保存真实值：

```bash
COMMENT_CRAWLER_DB_PATH=data/jobs.db
COMMENT_CRAWLER_EXPORT_DIR=exports
DOUYIN_API_BASE_URL=https://<your-private-api-host>
DOUYIN_COOKIE=<your-own-cookie>
```

如果私有 API 路径不同，调整：

```bash
DOUYIN_COMMENTS_PATH=/api/douyin/web/fetch_video_comments?aweme_id={aweme_id}&cursor={cursor}&count={count}
DOUYIN_REPLIES_PATH=/api/douyin/web/fetch_video_comment_replies?item_id={aweme_id}&comment_id={comment_id}&cursor={cursor}&count={count}
DOUYIN_USER_POSTS_PATH=/api/douyin/web/fetch_user_post_videos?sec_user_id={sec_user_id}&max_cursor={cursor}&count={count}
```

## 3. 启动检查

```bash
bash scripts/up.sh
python3 -m douyin_comment_crawler --help
python3 -m douyin_comment_crawler status
```

预期：

- `up.sh` 输出 `douyin-comment-crawler ready`
- `--help` 能看到 `crawl`、`batch`、`export`、`status`、`resume`
- 首次 `status` 输出 `暂无任务`

## 4. 单视频采集

```bash
python3 -m douyin_comment_crawler crawl video \
  --aweme-id "<aweme-id>" \
  --include-replies \
  --min-delay 2 \
  --max-delay 6 \
  --cookie-group primary
```

也可以传 URL：

```bash
python3 -m douyin_comment_crawler crawl video \
  --url "https://www.douyin.com/video/<aweme-id>"
```

命令会输出：

```text
job_id=<job-id>
status=<completed|failed|cooldown>
```

## 5. 账号作品批量采集

```bash
python3 -m douyin_comment_crawler crawl account \
  --sec-user-id "<sec-user-id>" \
  --include-replies \
  --min-delay 3 \
  --max-delay 8 \
  --cookie-group primary
```

也可以传账号 URL：

```bash
python3 -m douyin_comment_crawler crawl account \
  --url "https://www.douyin.com/user/<sec-user-id>"
```

## 6. 批量文件采集

创建 `targets.txt`：

```text
# type,target
video,<aweme-id-1>
video,https://www.douyin.com/video/<aweme-id-2>
account,<sec-user-id-1>
account,https://www.douyin.com/user/<sec-user-id-2>
```

执行：

```bash
python3 -m douyin_comment_crawler batch \
  --file targets.txt \
  --include-replies \
  --min-delay 3 \
  --max-delay 10 \
  --cookie-group primary
```

## 7. 查看状态

查看最近任务：

```bash
python3 -m douyin_comment_crawler status
```

查看指定任务：

```bash
python3 -m douyin_comment_crawler status --job-id "<job-id>"
```

查看账号组健康/冷却：

```bash
python3 -m douyin_comment_crawler status --health
```

如果任务进入 `cooldown`，先检查 `cooldown_until` 和 `last_error`。不要立即提高频率重试。

## 8. 断点续跑

```bash
python3 -m douyin_comment_crawler resume \
  --job-id "<job-id>" \
  --include-replies \
  --min-delay 5 \
  --max-delay 12
```

续跑会使用 SQLite 中保存的账号、评论和回复游标。

## 9. 导出交付文件

导出 JSONL：

```bash
python3 -m douyin_comment_crawler export \
  --job-id "<job-id>" \
  --format jsonl
```

导出 CSV，并过滤空文本和纯媒体评论：

```bash
python3 -m douyin_comment_crawler export \
  --job-id "<job-id>" \
  --format csv \
  --exclude-flag empty_text \
  --exclude-flag media_only
```

默认导出目录是 `exports/`。

## 10. 日常验证

```bash
python3 -m unittest discover -s tests
ruby -e 'require "yaml"; data = YAML.load_file("openapi/comment-crawler.openapi.yaml"); puts data["openapi"]'
```

## 11. 停止与数据保留

```bash
bash scripts/down.sh
```

当前 CLI 没有后台服务，`down.sh` 不删除 `data/` 和 `exports/`。这两个目录用于续跑和交付文件，已被 `.gitignore` 忽略。

## 12. 投产检查清单

- 已确认采集范围是公开可访问或你有权访问的数据。
- 已确认私有 API 服务可用，接口路径模板匹配实际返回结构。
- `.env` 未提交，真实 Cookie、代理、账号组只在本地或私有系统保存。
- 已先用小样本视频跑通评论和回复采集。
- 已确认 `status --health` 不显示异常冷却。
- 已设置保守限速，例如 `--min-delay 3 --max-delay 10`。
- 已导出 JSONL 和 CSV，并抽样检查中文、emoji、空文本和回复字段。
- 已跑 `python3 -m unittest discover -s tests`。
