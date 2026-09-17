# CodePick 项目进度核验

更新：2026-09-17，产品评审、公开真实数据与阅读体验第一切片已完成本机验收。
上一轮完整验收日期为 2026-09-16；M1、M2、版本消息闭环和 M3 基础能力是本轮继续开发的工程基线。

## 当前阶段

用户已要求修复 API 访问入口、重新审视定位和用户价值、按业务场景调整五仓库，
获取公开真实数据并重做阅读体验。本轮第一切片为：**真实来源 → 可追溯内容 →
阅读详情与原文 → 收藏与再访问**。产品评审、五仓库增量重构及该切片本机
集成验收已完成；后续 R2/R3 与真实生产能力不在本次通过范围。

| 本轮工作 | 状态 | 文档 / 退出条件 |
| --- | --- | --- |
| 定位、用户、运营、竞争替代与商业假设 | 评审文档已形成；无真实用户调研结论 | [产品评审](PRODUCT_REVIEW_2026-09-17.md) |
| 五仓库业务边界与实施计划 | 文档已形成 | [产品改造计划](PRODUCT_REBUILD_PLAN.md) |
| API 根路径 Not Found、真实来源导入 | 已实测通过 | 10 篇实际采集，5 篇完成态可读；来源/版本/分页/404/只读403通过 |
| 阅读/收藏重构与最终故障恢复 | 已验收 | 双语移动页面、真实开发账户持久收藏、伴读 SQL 额度和同页故障恢复通过 |
| 本轮测试、进度同步与上传代码 | 已完成 | 具体测试数、五仓库 main 提交及模拟边界见本轮验收记录 |

本轮 L0 60、L1 131、L2 201、L3 166 全量通过；前端和 docs 检查及交付详情见 [本轮验收记录](PRODUCT_ACCEPTANCE_2026-09-17.md) 为准。查看环境请用 [真实内容预览](REAL_CONTENT_PREVIEW.md)，不要把 API 当作五个独立网站。

当前 north_star 仍是累计事件占比，不是去重周活阅读闭环率；真实内容不代表真实
模型分析。新页面须区分来源摘录、模拟/规则分析、真实翻译及不可用功能。

## 已验收工程基线（2026-09-16）

**M3 的 Public API 搜索/分页与上游失败边界已完成：`/v1/search` 和 MCP
`search` 将查询下推 L2，在排序与游标分页前过滤标题/摘要。** Public API 明确区分
无效请求、内容不存在、不可重试配置错误和可重试上游故障；关闭 stub 后不会静默
回退演示数据。

**M3 首个公开多用户门槛也已完成：开发登录不再固定 user 1，内存与
SQLAlchemy 后端都按规范化邮箱稳定解析独立用户。** 兴趣、关注、书签、阅读事件
指标、订阅、API key、撤销和使用量均按认证用户隔离；篡改、过期和畸形 JWT 返回
401。

生产型配置必须使用 `L3_AUTH_LOGIN_MODE=external`，该模式关闭任意邮箱开发登录。
这是一道误配置门禁，不等于真实身份提供商已经接入。Reader Web 已升级到 Next.js
16.3.5 / Playwright 1.63.0，`npm audit` 为 0；Next 16 异步路由参数、生产构建和
26 项桌面/移动浏览器回归均通过。

M1/M2 与版本消息闭环仍保持通过。L1/L2 仍使用 FakeLLM；真实 OIDC/magic link、
正式 Paddle、真实邮件、生产数据库以及 PostgreSQL 上的四层版本闭环仍待验证。

## 五个仓库进度

Ubuntu 工作区：`/home/ubuntu2401/project/codepick`。本轮从五仓库 `main` 基线继续；2026-09-16 的文档同步已在 `5aaede1` 合入 `main`。本轮工作区与最终提交以新的验收记录为准。

| 仓库 | 已有能力 | 2026-09-16 基线新增/核对 | 历史待验收项 |
| --- | --- | --- | --- |
| codepick-docs | 产品架构资料、项目进度、开发计划、本机指南 | 新增版本化数据契约、M1 跨进程脚本与验证记录，更新总索引 | 随真实服务接入补端到端证据 |
| deepdata（L0） | 采集、raw/对象存储、正文、去重/版本、查询与 outbox | 更新自动发带 content_version/hash 的独立事件；查询暴露版本身份 | TREND 版本语义；生产 PG/S3 持续运行 |
| seek_data（L1） | 持久分析/快照/缓存/状态成本/outbox | Redis reliable worker、持续 relay；校验 L0 版本；迟到旧版 superseded | 真实模型、PostgreSQL 全链路、进程监控 |
| agentic（L2） | 评分、翻译、HTTP、SQL 状态成本和完成事件 | completion relay；`/content?q=` 在分页前搜索标题/摘要 | 接真实下游消费者；真实模型和 PostgreSQL 四层链路 |
| pickblog（L3） | 双语阅读应用、Reader/Public API、早报/配额、M2 真实读取 | Public/MCP 搜索下推；上游请求、配置、404、可重试故障分流 | 接真实身份提供商；随后支付、邮件与 MCP transport |

## 上一轮验证（2026-09-16，保留历史证据）

| 范围 | 2026-09-16 结果 | 边界 |
| --- | --- | --- |
| L0 | 46 项测试通过；覆盖率 86.39%；Ruff、mypy 通过 | 含读取仓库内 `file://` fixture 的 Playwright 集成测试，不访问外部站点 |
| L1 | 128 项测试通过；smoke/DoD、L0 → L1 smoke、版本 worker/relay 检查通过 | SQLite 真事务与真实 Redis 消息；模型为 FakeLLM |
| L2 | 114 项测试通过；覆盖率 81.49%；Ruff、mypy、smoke/contracts 通过 | 含 completion relay 和分页前标题/摘要搜索；真实模型仍待验证 |
| L3 | 127 项后端测试通过；smoke/preflight/migration、typecheck/build、26 项浏览器测试通过 | 包含 Public/MCP 搜索、启动配置、账户隔离和上游错误分类 |
| M1 综合检查 | 7 个独立进程阶段全部通过，输出 `CODEPICK M1: PASS` | 三个 SQLite 库、实际 L0 文件采集和更新、持久 L1 与 L2；事件文件是验证载体，不是 Redis worker |
| L0 external DoD | PostgreSQL migration、L0 pipeline、Redis relay 幂等、MinIO/S3 和 quick soak 全部 PASS | PostgreSQL 16、Redis 7、MinIO 均为 loopback 一次性容器；已删除容器和卷 |
| Public API 搜索跨进程 | SQLite 断链/恢复边界及 PostgreSQL API key/配额持久化均 PASS | L1/L2 为 SQLite/FakeLLM；L3 PostgreSQL 16；服务仅绑定 127.0.0.1 |
| M2 跨进程 | 无 API mock 浏览器读取、L2 停止错误页、L2 恢复后再次读取共 2 项场景全部通过 | L1/L2 SQLite；三个服务仅绑定 127.0.0.1 |
| 版本消息闭环 | 15 个独立进程阶段全部通过；L0 v1/v2、L1 worker/relay、L2 Redis bridge/Arq、迟到 v1 重放全部 PASS | SQLite + 真实 Redis/Arq；L1/L2 为 FakeLLM |
| L2 completion relay | 严格集成输出 PostgreSQL outbox → Redis → ACK persisted PASS | PostgreSQL 16 + Redis 7，仅本机端口；ACK 由测试消费者模拟 |
| M3 PostgreSQL | 独立 PostgreSQL 16 Alembic 升降级与双用户 API 验收 PASS | 2 用户、10 兴趣、2 书签、2 事件、2 API key；仅绑定 127.0.0.1:55439，容器已删除 |
| M3 前端安全 | `npm ci`、`npm audit --audit-level=low`、typecheck、Next 16 build、26 项 Playwright PASS | 临时 Chrome for Testing；未部署生产 |

2026-09-16 不重复自动化基线为 L0 46、L1 128、L2 114、L3 后端 127、原浏览器
26 和 M2 浏览器 2 项，共 **443 项**。版本闭环另执行 15 个独立进程阶段，
最终输出 `CODEPICK VERSION LOOP: PASS`；M1 七阶段回归输出
`CODEPICK M1: PASS`。该日已完成当时既定的本机验收范围；不表示新提出的真实数据、
产品体验或后续 PostgreSQL 四层同链路、长期 soak 已经完成。

## 当前跨层边界

| 边界 | 现在能做什么 | 尚不能声称完成 |
| --- | --- | --- |
| L0 → L1 | 版本化事件经 Redis reliable worker 消费；更新自动通知；迟到旧版有明确策略 | TREND 无正文分支；PostgreSQL/S3 上的持续闭环 |
| L1 → L2 | run_id/revision 经 durable outbox 和 Redis 传递；L2 读对应历史快照 | PostgreSQL 上同链路；真实模型成本 |
| L2 进程间 | 新 revision 重评分；completion outbox 支持稳定 ID、sent/ACK、超时重投和 dead-letter | 全图一次性提交；真实下游消费者、监控与长时 soak |
| L2 → L3 | 四个 HTTP 接口读取持久结果；服务端搜索先过滤再分页；L3 区分 400、404、配置 503 与可重试 503 | PostgreSQL 上的 M2 端到端、真实模型和持续服务运行尚未验证 |
| 浏览器/真实账户 | M2 真实读取和断链/恢复已验证；开发邮箱稳定映射独立持久用户，账户数据隔离 | 开发邮箱仍不验证所有权；真实身份提供商、正式 Paddle、邮件和 MCP 协议未完成 |

L2 当前仍要求同一内容串行处理。已完成/取消/待审产物具有原子写入保护，迟到任务不能再改写产物或成本；双方都尚在处理时的完整图执行所有权和一致发布仍需后续机制，不能用状态条件更新代替。

## 下一步

真实来源与可信阅读第一切片已完成，访问、收藏和错误反馈已修复并保存实测结果。
下一步按 [产品改造计划](PRODUCT_REBUILD_PLAN.md) 的 R2 完善来源运营与指标口径。
真实身份提供商、L2 completion 真实下游消费者、PostgreSQL 四层版本闭环仍是后续
工程门槛；正式 Paddle、邮件与 MCP transport 沿用 M4 范围，不能用本轮页面改造替代。

上一轮完整结果见 [Ubuntu 验收记录](UBUNTU_ACCEPTANCE_2026-09-16.md)，开发详情见 [版本消息闭环](VERSIONED_EVENT_LOOP.md)、[M1 交接](M1_INTEGRATION.md)、
[M2 联调记录](M2_INTEGRATION.md)、[M3 账户隔离](M3_ACCOUNT_ISOLATION.md) 与
[L2 completion relay](L2_COMPLETION_RELAY.md)、[Public API 搜索验收](PUBLIC_API_SEARCH.md)，字段与数据所有权见
[L1 → L2 v1 契约](contracts/L1-L2-v1.md)。
