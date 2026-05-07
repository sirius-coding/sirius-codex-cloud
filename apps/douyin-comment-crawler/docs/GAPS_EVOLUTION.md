# Gaps 与 Evolution

## 已补齐内容

- HTTP Douyin adapter：通过 `DOUYIN_API_BASE_URL` 和路径模板对接私有 API 服务。
- 批量采集：`batch --file targets.txt` 支持 `video` 和 `account` 混合目标。
- 配置加载：支持本地 `.env`，进程环境变量优先级更高。
- 风控状态：任务支持 `cooldown_until`，Cookie/账号组支持健康状态记录。
- 性能控制：支持 `--page-size`、`--workers`，并把限速移动到 HTTP 请求级。
- 任务指标：状态输出视频数、评论数、回复数、API 请求页数。
- 二阶段回复：支持 `crawl replies --job-id`，先采主评论再补回复。
- 测试覆盖：字段标准化、flags、SQLite 去重/游标、fake adapter、HTTP adapter、批量任务、429 冷却。
- 操作说明：新增 `docs/OPERATIONS.md`。

## 仍不应在公开仓库补的内容

- 真实 Cookie、代理、账号池、私有 API host。
- 验证码处理、登录态抓取、绕过频控或权限限制的逻辑。
- 对特定私有部署环境的真实路径、账号名或主机名。

## 投产前仍需在私有层完成

- 部署或接入私有 Douyin API 服务。
- 用真实小样本验证接口路径模板和响应字段。
- 建立 Cookie/账号组轮换策略，但只能做健康冷却和人工维护，不做隐蔽规避。
- 准备脱敏录制 fixture，用于回归测试分页、回复、403、429、登录失效。
- 明确数据保留周期、授权依据和删除流程。

## 后续演进建议

- 增加 `fixtures/` 脱敏样本和集成测试，覆盖账号作品分页、评论分页、回复分页。
- 增加 `inspect response` 诊断命令，帮助适配不同 Douyin API wrapper 返回结构。
- 增加导出清单文件，记录任务参数、过滤条件、导出时间和记录数。
- 增加回复补采进度统计，例如主评论总数、已尝试回复数、已完成回复数。
- 如需要长期运行，再把 CLI 包一层 FastAPI 或任务队列；当前 OpenAPI 已预留合同。
- 把私有 adapter、部署参数和运行日志放进私有 overlay，公开仓库只保留抽象接口和脱敏模板。
