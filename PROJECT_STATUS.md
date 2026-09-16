# CodePick 项目进度核验

更新：2026-09-16，Ubuntu 24.04 M3 用户隔离与前端安全基线验收。
M1、M2、版本消息闭环和本轮 M3 改动均基于五仓库远端 `main` 继续开发。

## 当前阶段

**M3 首个公开多用户门槛已完成：开发登录不再固定 user 1，内存与
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

Ubuntu 工作区：`/home/ubuntu2401/project/codepick`。五仓库以远端 `main` 为共同基线；本轮 L2 completion relay 已从 `codex/l2-completion-relay` 快进合入 `agentic` 和 `codepick-docs` 的远端 `main`。

| 仓库 | 当前已完成 | 本轮新增/核对 | 主要下一步 |
| --- | --- | --- | --- |
| codepick-docs | 产品架构资料、项目进度、开发计划、本机指南 | 新增版本化数据契约、M1 跨进程脚本与验证记录，更新总索引 | 随真实服务接入补端到端证据 |
| deepdata（L0） | 采集、raw/对象存储、正文、去重/版本、查询与 outbox | 更新自动发带 content_version/hash 的独立事件；查询暴露版本身份 | TREND 版本语义；生产 PG/S3 持续运行 |
| seek_data（L1） | 持久分析/快照/缓存/状态成本/outbox | Redis reliable worker、持续 relay；校验 L0 版本；迟到旧版 superseded | 真实模型、PostgreSQL 全链路、进程监控 |
| agentic（L2） | 评分、翻译、HTTP、SQL 状态成本和完成事件 | completion 稳定事件 ID、Redis relay、ACK、重试/dead-letter；0004 迁移 | 接真实下游消费者；真实模型和 PostgreSQL 四层链路 |
| pickblog（L3） | 双语阅读应用、Reader/Public API、早报/配额、M2 真实读取 | 独立持久用户、账户隔离、JWT 失败边界、认证模式门禁；Next 16.3.5 与零漏洞审计 | 接真实身份提供商；随后支付、邮件与 MCP |

## 本轮验证

| 范围 | 本轮结果 | 边界 |
| --- | --- | --- |
| L1 | 128 项测试通过；smoke/DoD、L0 → L1 smoke、版本 worker/relay 检查通过 | SQLite 真事务与真实 Redis 消息；模型为 FakeLLM |
| L2 | 113 项测试通过；覆盖率 81.46%；Ruff、mypy、smoke/contracts 通过 | 含 completion relay、0004 迁移、ACK/重试/dead-letter；真实模型仍待验证 |
| M1 综合检查 | 7 个独立进程阶段全部通过 | 三个 SQLite 库、实际 L0 文件采集和更新、持久 L1 与 L2；事件文件是验证载体，不是 Redis worker |
| M2 L2 | 97 项测试通过；覆盖率 85.57%；Ruff、mypy、smoke/contracts 通过 | HTTP 服务读取真实 SQL 快照；模型仍为 FakeLLM |
| M2/M3 L3 | 119 项后端测试通过；smoke/preflight/migration、typecheck/build、26 项浏览器测试通过 | M2 provider 边界保持；新增双用户隔离、JWT 失败、认证门禁、Next 16 与 0 漏洞审计 |
| M2 跨进程 | 无 API mock 浏览器读取、L2 停止错误页、L2 恢复继续读取全部通过 | L1/L2 SQLite；三个服务仅绑定 127.0.0.1 |
| 版本消息闭环 | L0 v1/v2、L1 worker/relay、L2 Redis bridge/Arq、迟到 v1 重放全部 PASS | SQLite + 真实 Redis/Arq；L1/L2 为 FakeLLM |
| L2 completion relay | 严格集成输出 PostgreSQL outbox → Redis → ACK persisted PASS | PostgreSQL 16 + Redis 7，仅本机端口；ACK 由测试消费者模拟 |
| M3 PostgreSQL | 独立 PostgreSQL 16 Alembic 升降级与双用户 API 验收 PASS | 2 用户、10 兴趣、2 书签、2 事件、2 API key；仅绑定 127.0.0.1:55439，容器已删除 |
| M3 前端安全 | `npm ci`、`npm audit --audit-level=low`、typecheck、Next 16 build、26 项 Playwright PASS | 临时 Chrome for Testing；未部署生产 |

最新不重复自动化基线为 L0 45、L1 128、L2 113、L3 后端 119、原浏览器
26 和 M2 浏览器 2 项，共 **433 项**。版本闭环另执行 15 个独立进程阶段，
最终输出 `CODEPICK VERSION LOOP: PASS`；M1 七阶段回归仍为 PASS。

## 当前跨层边界

| 边界 | 现在能做什么 | 尚不能声称完成 |
| --- | --- | --- |
| L0 → L1 | 版本化事件经 Redis reliable worker 消费；更新自动通知；迟到旧版有明确策略 | TREND 无正文分支；PostgreSQL/S3 上的持续闭环 |
| L1 → L2 | run_id/revision 经 durable outbox 和 Redis 传递；L2 读对应历史快照 | PostgreSQL 上同链路；真实模型成本 |
| L2 进程间 | 新 revision 重评分；completion outbox 支持稳定 ID、sent/ACK、超时重投和 dead-letter | 全图一次性提交；真实下游消费者、监控与长时 soak |
| L2 → L3 | 四个 HTTP 接口读取持久 L2 和版本化 L1 快照；L3 能区分 404 与可重试 503 | PostgreSQL 上的 M2 端到端、真实模型和持续服务运行尚未验证 |
| 浏览器/真实账户 | M2 真实读取和断链/恢复已验证；开发邮箱稳定映射独立持久用户，账户数据隔离 | 开发邮箱仍不验证所有权；真实身份提供商、正式 Paddle、邮件和 MCP 协议未完成 |

L2 当前仍要求同一内容串行处理。已完成/取消/待审产物具有原子写入保护，迟到任务不能再改写产物或成本；双方都尚在处理时的完整图执行所有权和一致发布仍需后续机制，不能用状态条件更新代替。

## 下一步

M3 的用户记录、账户隔离、JWT 失败边界、开发登录生产门禁和前端依赖升级已完成。
下一优先级是接入真实身份提供商并做会话生命周期验证，同时接入 L2 completion
事件的真实下游消费者并完成 PostgreSQL 上的四层版本闭环。正式 Paddle、邮件与 MCP
协议仍按 M4 推进，未获得凭据前只做本地协议和失败边界。

本轮开发详情见 [版本消息闭环](VERSIONED_EVENT_LOOP.md)、[M1 交接](M1_INTEGRATION.md)、
[M2 联调记录](M2_INTEGRATION.md)、[M3 账户隔离](M3_ACCOUNT_ISOLATION.md) 与
[L2 completion relay](L2_COMPLETION_RELAY.md)，字段与数据所有权见
[L1 → L2 v1 契约](contracts/L1-L2-v1.md)。
