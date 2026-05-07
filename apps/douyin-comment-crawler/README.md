# 抖音评论采集 CLI

面向批量账号和视频评论采集的命令行项目。首版运行形态是 CLI，内部用 SQLite 保存任务状态、游标、去重、失败记录和续跑信息，业务交付文件导出为 JSONL 或 CSV。

## 功能范围

- `crawl video`：按视频 URL 或 `aweme_id` 采集评论，可选采集评论回复。
- `crawl account`：按账号 URL 或 `sec_user_id` 遍历作品，再逐个采集评论。
- `crawl replies`：为已有任务补采评论回复，适合二阶段提速。
- `batch`：按文件批量采集视频和账号目标。
- `export`：按任务导出 `jsonl` 或 `csv`，支持按 flags 过滤导出视图。
- `status`：查看指定任务或最近任务状态。
- `resume`：按 SQLite 游标续跑已有任务。

## 合规边界

本项目只提供可验证的采集任务框架和 adapter 边界。实际接入第三方库或平台接口时，仅采集你有权访问或公开可访问的数据。

允许的风控能力：

- 使用用户自有 Cookie 和代理配置。
- 限速、随机抖动、指数退避、断点续跑。
- 遇到验证码、登录失效、频控、权限不足时停止、失败或冷却。

不提供也不应扩展的能力：

- 验证码绕过。
- 凭证抓取。
- 隐蔽规避平台限制。
- 强行突破登录、权限或频控限制。

## 第三方 adapter 说明

首选 adapter 目标是封装 `Evil0ctal/Douyin_TikTok_Download_API` 的公开接口形态，因为方案中要求它支持用户作品、单视频评论和评论回复。当前仓库提供 HTTP adapter，通过 `DOUYIN_API_BASE_URL` 和路径模板对接你私有部署或有权使用的兼容服务。

备选工具 `TikTokDownloader` 功能较多，但使用 GPL-3.0 许可；如把它作为分发依赖或深度集成，请先确认你的交付方式是否满足 GPL 合规要求。

参考项目：

- `https://github.com/Evil0ctal/Douyin_TikTok_Download_API`
- `https://github.com/JoeanAmier/TikTokDownloader`
- `https://github.com/Johnserf-Seed/f2`

## 安装

```bash
cd apps/douyin-comment-crawler
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

当前核心实现只使用 Python 标准库，`requirements.txt` 预留给后续私有 adapter 依赖。

## 配置

复制脱敏模板：

```bash
cp .env.example .env
```

`.env` 不应提交。真实 Cookie、代理、账号分组和私有 API 配置只保存在本地或私有配置系统。

环境变量：

- `COMMENT_CRAWLER_DB_PATH`：SQLite 状态库路径，默认 `data/jobs.db`
- `COMMENT_CRAWLER_EXPORT_DIR`：导出目录，默认 `exports`
- `DOUYIN_COOKIE`：用户自有 Cookie，本仓库不保存真实值
- `DOUYIN_PROXY_URL`：代理地址，本仓库不保存真实值
- `DOUYIN_API_BASE_URL`：私有 Douyin API wrapper 地址
- `DOUYIN_COMMENTS_PATH`：评论接口路径模板
- `DOUYIN_REPLIES_PATH`：回复接口路径模板
- `DOUYIN_USER_POSTS_PATH`：账号作品接口路径模板

## 命令示例

```bash
python3 -m douyin_comment_crawler --help
python3 -m douyin_comment_crawler status

python3 -m douyin_comment_crawler crawl video --url "https://www.douyin.com/video/<aweme-id>" --include-replies
python3 -m douyin_comment_crawler crawl video --aweme-id "<aweme-id>"

python3 -m douyin_comment_crawler crawl account --url "https://www.douyin.com/user/<sec-user-id>"
python3 -m douyin_comment_crawler crawl account --sec-user-id "<sec-user-id>" --include-replies

python3 -m douyin_comment_crawler crawl replies --job-id "<job-id>" --workers 4 --page-size 50

python3 -m douyin_comment_crawler batch --file targets.txt --include-replies --page-size 50 --workers 4 --min-delay 0.5 --max-delay 1.5

python3 -m douyin_comment_crawler export --job-id "<job-id>" --format jsonl
python3 -m douyin_comment_crawler export --job-id "<job-id>" --format csv --exclude-flag empty_text --exclude-flag media_only

python3 -m douyin_comment_crawler resume --job-id "<job-id>" --include-replies
```

注意：未配置 `DOUYIN_API_BASE_URL` 时，真实采集命令会进入 `failed` 状态并提示缺少私有 Douyin API 服务。

完整操作说明见 [docs/OPERATIONS.md](docs/OPERATIONS.md)，差距和演进清单见 [docs/GAPS_EVOLUTION.md](docs/GAPS_EVOLUTION.md)。

## 性能参数

- `--page-size`：传给 Download API 的 `count`，建议从 `50` 小步测试。
- `--workers`：账号作品下的视频并发采集数，建议从 `2` 或 `4` 开始。
- `--min-delay` / `--max-delay`：现在按 HTTP API 请求限速，不再按每条评论限速。
- `status --job-id <job-id>` 会输出 `videos_seen`、`comments_seen`、`comments_saved`、`replies_seen`、`api_requests`，用于判断瓶颈。
- 大任务建议先不加 `--include-replies` 采主评论，再用 `crawl replies --job-id <job-id>` 补回复。

## 字段说明

导出字段保持稳定：

- `job_id`：采集任务 ID
- `platform`：平台，例如 `douyin`
- `video_id`：视频 ID / `aweme_id`
- `comment_id`：评论 ID
- `parent_comment_id`：父评论 ID，主评论为空
- `user_id`：公开用户 ID，如接口可用
- `user_sec_uid`：公开 `sec_uid`，如接口可用
- `user_nickname`：公开昵称
- `raw_text`：原始评论文本，默认保留
- `clean_text`：去 emoji、去 `@` 标记后的清洗文本
- `created_at`：评论发布时间，如接口可用
- `like_count`：点赞数
- `ip_region`：IP 属地或地区字段，如接口可用
- `crawled_at`：采集入库时间
- `flags`：过滤标记

当前 flags：

- `emoji`：包含 emoji
- `mention`：包含 `@`
- `reply`：回复评论或文本以“回复 ”开头
- `empty_text`：空文本
- `media_only`：纯图片、视频或表情占位文本

## 本地脚本

```bash
python3 scripts/crawler.py
bash scripts/crawler.sh
bash scripts/up.sh
bash scripts/status.sh
bash scripts/down.sh
```

`crawler.py` 是推荐入口，提供方向键菜单、表格化结果、全局任务状态栏、彩色重点状态、面包屑返回、默认性能参数、实时状态监控、Resume、补采回复和导出快捷操作。

`crawler.sh` 是兼容入口，适合没有可用 TTY 或需要纯 Bash 的环境。

`up.sh` 会创建本地目录并做 CLI smoke check；`down.sh` 不删除数据库和导出文件，只输出说明。

## 验证

```bash
python3 -m unittest discover -s tests
python3 -m douyin_comment_crawler --help
python3 -m douyin_comment_crawler status
python3 - <<'PY'
import yaml
with open("openapi/comment-crawler.openapi.yaml", encoding="utf-8") as fh:
    data = yaml.safe_load(fh)
print(data["openapi"])
PY
```

如果本机没有 `PyYAML`，可用任意 OpenAPI/Apifox 工具导入 `openapi/comment-crawler.openapi.yaml` 检查。

## API 合同

`openapi/comment-crawler.openapi.yaml` 是未来 FastAPI 服务化的接口合同，当前 CLI v1 不启动 Web 服务。Apifox 可直接导入该 YAML。
