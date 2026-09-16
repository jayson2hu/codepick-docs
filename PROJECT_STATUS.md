# CodePick 项目进度核验

更新：2026-09-16，Ubuntu 24.04 M2 联调复验。五仓库 M1 已合入并推送远端 `main`；本轮继续完成 **L2 HTTP → L3 真实 provider → 无 API mock 浏览器读取与断链恢复**。

## 当前阶段

**新文章已通过实际 L0 采集 → L1 数据库分析快照 → 独立 L2 进程评分 → L2 HTTP → L3 Reader API → Next.js/Chromium。** 关闭 L3 stub 和前端 demo fallback 后，页面可读取 M1 文章、评分和翻译；停止 L2 时显示可重试错误，恢复 L2 后无需重建下游即可继续读取。

模型仍使用 FakeLLM，本次 M2 端到端数据使用独立 SQLite。自动 L0 更新事件、L2 按版本重评分、真实模型以及 PostgreSQL 上的 M2 浏览器全链路属于后续工作，未计为完成。

## 五个仓库进度

Ubuntu 工作区：`/home/ubuntu2401/project/codepick`。五仓库的 `codex/m1-ubuntu-handoff` 已与 Ubuntu 可移植性修复合入本地 `main`，验收通过后推送远端 `main`。

| 仓库 | 当前已完成 | 本轮新增/核对 | 主要下一步 |
| --- | --- | --- | --- |
| codepick-docs | 产品架构资料、项目进度、开发计划、本机指南 | 新增版本化数据契约、M1 跨进程脚本与验证记录，更新总索引 | 随真实服务接入补端到端证据 |
| deepdata（L0） | 采集、raw/对象存储、正文、去重/版本、查询与 outbox，上一轮消息可靠性修复 | 只读复核；本轮综合检查实际调用采集与同 URL 更新 | 更新正文后的 content.ingested 新通知；真实消息消费、Redis/PG/S3；TREND 与平台适配 |
| seek_data（L1） | 独立加工流程、实际 L0 provider；现有持久化分析/输入快照/缓存/处理状态与成本/outbox | 一次事务提交；跨重启幂等；失败重试；版本与 request key；过时并发写拒绝；SQL 迁移 | 持续消费 worker、真实模型/PG；和上下游共同完成版本生命周期 |
| agentic（L2） | 评分、翻译、推荐/伴读；实际 L1 SQL 快照；SQL 状态、成本、完成事件 | 新增四个 FastAPI 查询接口；worker/API 共用 L2 数据库配置；404、配置、上游快照和存储故障分类 | 版本重评分、完成事件投递确认、真实模型与 PostgreSQL 运行验证 |
| pickblog（L3） | 双语阅读应用、Reader/Public API、开发账号/早报/配额、SQLite 迁移 | 真实 L2 provider；Next 同源代理；显式 demo fallback；可重试错误页；无 mock M2 浏览器测试 | 真实身份隔离、依赖升级；随后支付、邮件与 MCP |

## 本轮验证

| 范围 | 本轮结果 | 边界 |
| --- | --- | --- |
| L1 | 112 项测试通过；独立 smoke/DoD、原 L0 → L1 smoke、迁移/资源打包检查通过 | SQLite 真事务与失败注入；模型为 FakeLLM；PG 未在线验证 |
| L2 | 94 项测试通过；覆盖率 85.63%；Ruff、mypy、smoke/contracts 等检查通过 | 含实际 SQLite 重启/并发与增量迁移回归；PostgreSQL 迁移和 Redis 已通过本机严格集成，真实模型仍待验证 |
| M1 综合检查 | 7 个独立进程阶段全部通过 | 三个 SQLite 库、实际 L0 文件采集和更新、持久 L1 与 L2；事件文件是验证载体，不是 Redis worker |
| M2 L2 | 97 项测试通过；覆盖率 85.57%；Ruff、mypy、smoke/contracts 通过 | HTTP 服务读取真实 SQL 快照；模型仍为 FakeLLM |
| M2 L3 | 114 项后端测试通过；smoke/preflight/migration、typecheck/build、原 26 项浏览器测试通过 | 新增 provider 404/503 回归和显式无回退配置 |
| M2 跨进程 | 无 API mock 浏览器读取、L2 停止错误页、L2 恢复继续读取全部通过 | L1/L2 SQLite；三个服务仅绑定 127.0.0.1 |

本轮重新执行 L0 45、L1 112、L2 94、L3 后端 112 和浏览器 26 项，共 **389 项测试通过**；L0 有 1 项专用浏览器 integration 测试按既定标记排除。L0 external DoD/quick soak 与 L2 strict integration 也已使用仅绑定 localhost 的独立 Docker 测试服务通过。完整记录：[M1 验证](verification/2026-09-12-m1.json)、[跨进程实测输出](verification/2026-09-12-m1-pipeline.json)、[上一轮基线](verification/2026-09-12.json)。

## 当前跨层边界

| 边界 | 现在能做什么 | 尚不能声称完成 |
| --- | --- | --- |
| L0 → L1 | 实际 get_content 读取；规范正文连同来源、语言快照持久化 | 真实 Redis 持续消费；L0 同 URL 更新自动发新版事件；TREND 无正文分支 |
| L1 → L2 | 从 L1 自有 content_base_analysis 表读取 schema_version=1 快照；正确映射正文/标签/语言/来源 | L2 还不按 run_id 处理历史版本；旧版本延迟事件和最新快照的协调仍待实现 |
| L2 进程间 | 评分、翻译、完成/待审状态、成本和完成 outbox 持久化；重启重复不会重新调模型 | 全图所有步骤一次性提交、持久完成事件的投递/确认、分布式执行与真实模型成本 |
| L2 → L3 | 四个 HTTP 接口读取持久 L2 和版本化 L1 快照；L3 能区分 404 与可重试 503 | PostgreSQL 上的 M2 端到端、真实模型和持续服务运行尚未验证 |
| 浏览器/真实账户 | 同源代理和关闭 demo fallback 的真实读取已通过；断链/恢复已验证 | 任意邮箱仍共用 user_id=1；真实认证/隔离、正式 Paddle、邮件和 MCP 协议未完成 |

L2 当前仍要求同一内容串行处理。已完成/取消/待审产物具有原子写入保护，迟到任务不能再改写产物或成本；双方都尚在处理时的完整图执行所有权和一致发布仍需后续机制，不能用状态条件更新代替。

## 下一步

M2 首版已完成。下一步优先补 **版本与消息闭环**：L0 更新自动通知、L1/L2 持久 outbox 持续投递、L2 按 run/version 重评分和旧事件策略；并行推进真实用户隔离与前端依赖升级。不能把 M1 显式版本检查当作自动闭环。

本轮开发详情见 [M1 交接](M1_INTEGRATION.md) 与 [M2 联调记录](M2_INTEGRATION.md)，字段与数据所有权见 [L1 → L2 v1 契约](contracts/L1-L2-v1.md)。
