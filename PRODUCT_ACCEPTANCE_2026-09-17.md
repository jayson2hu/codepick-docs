# 真实内容与产品重构：本机验收记录

日期：2026-09-17。当前状态：本轮 R0/R1 第一切片已完成本机验收；不代表 R2/R3 或生产能力完成。

## 交付范围与产品结论

本轮交付第一条可用业务链：公开真实来源 → 可追溯提取 → 规则排序 → 阅读与原文 → 收藏再访问。面向跟进 AI 编程和 Agent 工程的中文/双语开发者，以少量可信信息和可回访工作流为定位假设；没有把工程测试当作真实用户留存或付费研究。分析见 [产品评审](PRODUCT_REVIEW_2026-09-17.md)，后续 R2/R3 见 [实施计划](PRODUCT_REBUILD_PLAN.md)。

保留五仓库分层，不创建五个重复用户网站：L0 采集，L1 通用加工，L2 判断与内容 HTTP，L3 阅读与账户数据，docs 管理契约和跨层验收。L3 不跨层写库、不在上游失败时补演示文章。

## 环境与基线

- Ubuntu 24.04 VMware，工作区 `/home/ubuntu2401/project/codepick`。
- Python 3.12.3，四仓库独立 `.venv`；Node.js 24.21.0，npm 11.19.0。
- 原 main 基线：docs `5aaede1`、deepdata `82d180d`、seek_data `6f40bf2`、agentic `66e8733`、pickblog `8c8c82c`，开始均 clean，fetch 后与 origin/main 一致。
- 读取并遵守 `pickblog/apps/reader-web/AGENTS.md` 和本地 Next.js 文档。历史资料不作为本轮指令。
- Chromium 使用完整 Chrome Headless Shell 和 `/tmp/codepick-playwright-libs` 隔离共享库；临时 CJK 字体配置解决最小镜像中文字形缺失，不改系统/用户配置。
- 所有 API、网页、测试数据库/Redis/MinIO 端口只绑定 `127.0.0.1`。未触碰现有 `anneal` PostgreSQL 5432。

## 问题、原因与修复

| 问题 | 核实原因 | 本轮处理 |
| --- | --- | --- |
| 其他项目根地址 Not Found | Reader/L2 API 有 `/docs`，但 `/` 未定义；五仓库并非五个网站 | API `/` → `/docs`；Web `/` → `/zh`；新增准确的远程转发与服务用途表 |
| 原文夹带导航、相关推荐、超长摘要 | 通用 HTML 抽取把网站 chrome 混入正文，长文切块合并无全局上限 | trafilatura 主体抽取、RSS 标题优先、安全裁剪；提取摘要上限与原文引用检查 |
| SSO/SCIM 误标 AI | `model` 等宽泛关键词误匹配 | 收紧 AI 标签规则并通过正常 graph/version 重处理 |
| 模拟分析看似真实质量 | FakeLLM、占位创新分、缺译文混在同一展示 | source/analysis/scoring provenance；规则模式不生成翻译，隐藏未评估维度仪表 |
| 新正文混旧分数/译文 | HTTP 读最新 L1 投影；升级版本未清理全部旧产物 | 精确读取 accepted run，事务清理旧分数/译文，返回前复核版本与状态 |
| 保存失败却显示成功 | catch 分支伪造本地成功消息 | 真实本机收藏与账户保存分开，成功后再确认，错误明确可重试 |
| 伴读失败 HTTP 200 且扣额度 | 上游惰性生成器在 SSE headers 发出后执行 | 先完成有限 chunks 请求，再发送 SSE/计数；404/配置/故障分流，实际后端额度读取，多行 SSE 保留 |
| 旧 M1 演示库读失败 | 缺少后续版本身份列，非网络故障 | 保留旧库，新建当前 schema 的 M1 对照库；增加 L2 缺 schema 配置检查 |
| 中文回归测试不再匹配 | 页面业务文案已重设计，旧测试仍断言旧句子；负断言中出现字面乱码字符 | 维护同等语义/编码检查，未删除用例或降低覆盖率 |
| 首次故障恢复检查未成功 | SIGCONT 后立即点击，未确认上游恢复就绪；不能单凭该次失败归因按钮 | 按本机 Next 16 `retry()` 契约，确认 feed 200 后同页点击实际恢复成功，未用新开页替代 |
| 手机导航逐字竖排 | 工具与全部导航在窄屏同一行竞争宽度 | 修为独立可横滚导航、nowrap、不压缩；390px 主要入口 44px 高，截图及回归通过 |
| Alembic SQLite 开发登录 500 | 迁移 BIGINT 主键不具 SQLite INTEGER 自动生成语义，ORM 建表测试未覆盖 | `0003_sqlite_generated_ids` 修复 6 表，10 项保留数据/回滚/写入回归通过；真实 PG 升降级通过，本机升级后登录/伴读可用 |
| 登录失败仍显示已登录、邮件前缀推定管理员 | catch 伪造 demo token，客户端根据邮箱猜套餐/权限 | 登录失败保持退出；身份/权限只认 API；同步失败保留真实会话与本机收藏，损坏存储明确报错 |
| API key 撤销失败仍显示已撤销 | DELETE 错误后无条件更新 UI | 真实 key 失败保持 active 并报错，仅显式 `cp_demo_` 允许本机演示撤销 |
| 远程浏览器部分操作请求 8000 失败 | 多个 client component 仍将访问者的 127.0.0.1:8000 当成服务器 API | 统一 clientApiUrl，同源 `/api` 默认路径；登录、收藏、伴读、兴趣、管理和开发工具均使用代理 |
| 启动迁移失败 | 启动器未指定 `pickblog/db/alembic.ini` | 显式配置路径和测试 SQLite，补启动器回归 |

## 真实数据证据

目录：`/tmp/codepick-real-preview-20260917`，不提交原文、数据库、日志或完整报告。

- 请求 3 个公开官方源；GitHub Changelog 与 GitHub Engineering 两个 feed 成功，来自同一发布者，不代表已实现多发布者覆盖。各 5 篇，共 10 篇。
- Google Developers Blog 因本机网络不可达 / TLS EOF 失败，如实记录，没有用 fixture 补数。
- 当前 L0 10 条内容、23 条历史版本、23 条版本 outbox；ID 7/8/10 为 v3，其余为 v2。修复走正常采集和版本流程，不直接改 SQL 产物。
- L1 全部 revision 3 / `extractive-v3`，保留 30 个历史 run 和 30 个 outbox。摘要 299–696 字符，每篇 3 个关键点，30/30 可定位到来源文本。
- L2 全部接受对应 run/revision 3；5 COMPLETED、3 WAIT_REVIEW、2 CANCELLED，无翻译。没有为增加展示条数放宽门禁。
- L0 最终同源重抓：新增内容/版本/outbox 均 0，hash/version 不变。L1 10/10 replay，run/outbox/revision 不变。L2 再处理后 state、score、translation、review 和 outbox 完全不变。
- L2 10 个完成事件包含 5 个历史 revision-1 事件和 5 个当前 revision-3 事件，不等于 10 篇可发布文章。

报告：`l0-report.json`、`l0-replay-report.json`、`l1-report.json`、`l1-replay-report.json`、`l2-report.json`、`l2-replay-report.json`、`cross-layer-report.json`。报告均保留在上述本机目录。

## 已执行检查

测试数量按独立用例计，不把 smoke 内再次运行 pytest 累加，也不把每条 HTTP 断言算成一项测试。

| 范围 | 本轮结果 | 说明 |
| --- | --- | --- |
| L0 全量 | 60 passed，coverage 86.36% | 含 fixture Chromium 和只读看板浏览器；Ruff、mypy strict 45 files、smoke、architecture audit PASS |
| L1 全量 | 131 passed | smoke、DoD、L0 → L1 contract PASS |
| L2 全量 | 201 passed，coverage 85.38% | Ruff、mypy 48 files、smoke、contracts PASS |
| L3 后端 | 最终 166 passed | smoke / development preflight / 独立 SQLite migration 最终均 PASS |
| docs 启动器 | 6 passed，Ruff PASS | 缺库、冲突/特权端口、隔离环境、子进程失败、空 feed、进程清理 |
| M1 | 七阶段 PASS，已复跑并保留当前结构对照库 | `/tmp/codepick-m1-product-20260917`；L1/L2 为 FakeLLM，不是公开源演示 |
| Redis/Arq 版本闭环 | PASS | v1→v2→迟到 v1，独立进程，报告 `/tmp/codepick-version-loop-20260917.json` |
| L0 external DoD | PASS | 独立 PostgreSQL/Redis/MinIO，quick soak 1 iteration，raw=2/content=1/errors=[]；报告 `/tmp/codepick-l0-real-external-dod.json` |
| L3 真实账户 API 与浏览器 | PASS | Alembic 升级后的 SQLite；无 API mock 同源开发登录、/me、账户收藏刷新持久、L2 片段伴读及 SQL 额度 0→1；没有真实身份验证或邮件发送 |
| L2 strict integration | PASS | PostgreSQL migration、Redis、Arq 契约、completion outbox → Redis → ACK persisted；测试 ACK 消费者 |
| 真实跨层 HTTP | PASS，10 imported / 5 readable | 来源/版本、摘要边界、完成态过滤、无假译文、分页/空结果、root redirect、404、只读403 |
| 前端依赖审计 | npm audit 0 vulnerabilities | 本轮执行，不表示未来无漏洞 |
| 前端 build/typecheck/浏览器 | PASS：40 离线回归 + 公开源 1 + 真实账户 1 + M1 对照 1 + 同页恢复 1 | 20 场景 × 桌面/Pixel 5；公开源、账户和 M1 无 API mock；恢复用 SIGSTOP/SIGCONT，确认就绪后点同页 Retry |

本轮按上述口径共 **608 项**：L0 60 + L1 131 + L2 201 + L3 166 + docs 6 + fixture 浏览器 40 + 无 mock 公开源/账户/M1/恢复 4。跨进程阶段、迁移/DoD、lint/build 等另列，不重复累加。M1 浏览器在本轮账号错误反馈补丁前已通过，后续未修改其内容展示路径；最终公开源与账户浏览器、恢复及全量 fixture 已在最终代码复跑。生成的 Next 配置改动已恢复，未把构建产物提交。

核心复验入口：

```bash
cd /home/ubuntu2401/project/codepick/codepick-docs
../seek_data/.venv/bin/python -m unittest discover -s scripts -p 'test_*.py' -v
../seek_data/.venv/bin/python scripts/verify_m1.py --report /tmp/codepick-m1-ubuntu.json
../seek_data/.venv/bin/python scripts/verify_real_preview.py \
  --data-dir /tmp/codepick-real-preview-20260917 \
  --report /tmp/codepick-real-preview-20260917/cross-layer-report.json
```

各仓库命令与日志说明分别见 L0/L1/L2/L3 的 `docs/2026-09-17-*`，前端见 `apps/reader-web/UX_REDESIGN.md`。

## 预览与远程访问

运行入口、停止方法和 SSH 单行命令见 [真实内容预览](REAL_CONTENT_PREVIEW.md)。用户网站 `13200/zh`、`13200/en`；只读看板 `18000`；Reader `18100/docs`；L2 `18230/docs`。L1 没有独立用户网站。

启动器只管理本次四个子进程，日志为测试目录 `logs/`。浏览器请求使用同源 `/api`，不把服务器 loopback 地址当成远程用户机器上的 API。远程电脑须能经同一获授权 Tailscale 网络 SSH 登录 `ubuntu2401@100.68.112.4`。

## 模拟边界与尚未完成

公开源是真实网络内容，L0/L1/L2/L3 使用独立持久 SQLite。L1 是确定性原文提取与词哈希向量，不是生成模型或语义 embedding；L2 是规则排序与原文片段检索，未验证推荐/专家质量。没有付费模型调用或真实翻译。

M1/旧对照测试仍使用 FakeLLM；普通离线前端测试显式使用 demo/mock，真实源浏览器测试不得拦截 API。开发邮箱登录不验证邮箱所有权，邮件 mock，支付 sandbox，MCP transport 不在本轮。公开转载授权、真实用户任务/留存/付费、指标 v2、真实模型质量/成本、真实身份、四层同一 PostgreSQL 链路和长期 soak 仍未验收。短时 DoD 不替代长期运行。

本次 L3 升级前已通过 SQLite backup 保存 `l3-before-generated-ids.db`；迁移保留 64 位历史 ID、全部行、外键和自定义索引，PostgreSQL 的自增类型不变。测试覆盖 FK 开/关、升级/降级和中途异常回滚。生产迁移仍需另行授权，不能复制本机操作直接连接业务库。

当前伴读额度修复保证上游失败不扣费和顺序超额短路，不声称已完成跨进程并发原子额度预留或未来模型真流式协议。分页也不是跨请求事务快照。

## 文档与 Git 交付

按仓库 `main` 提交并非强制推送到各自 `https://github.com/jayson2hu/<repo>.git`，未部署生产。四个源码仓库已推送并核对工作区 clean、HEAD 与 origin/main 一致；docs 以包含本记录的提交同步，避免在文件中引用自身尚未生成的提交号。最终交付再次核对五仓库 `git status --porcelain` 为空、`git rev-list --left-right --count HEAD...origin/main` 为 `0 0`。

| 仓库 | 本轮交付提交 | 分支 |
| --- | --- | --- |
| deepdata | `00bb32b` | main |
| seek_data | `1f60d01` | main |
| agentic | `c95c366` | main |
| pickblog | `19106d9` | main |
| codepick-docs | 包含本记录的 main 提交 | main |

[完整修改文件清单](verification/2026-09-17-changed-files.md) 共 **135 个路径**：docs 15、L0 19、L1 14、L2 22、L3 65。保留既有历史，无 force push 或破坏性 Git 操作。原文、数据库、令牌、日志、依赖和构建产物不入 Git。

当前私有本机预览不需要用户另行提供凭据。后续真实身份、付费模型与预算、邮件、支付、公开发布和来源转载授权仍需单独决定；不自动扩大到生产环境。
