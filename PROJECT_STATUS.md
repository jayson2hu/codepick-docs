# CodePick 项目进度核验

更新：2026-09-16，Ubuntu 24.04 版本消息闭环复验。M1/M2 已在远端
`main`；当前开发分支继续完成 **L0 自动更新事件 → Redis → L1 durable
run/outbox → Redis → Arq → L2 按 revision 重评分**。

## 当前阶段

**新文章和同 URL 更新均已通过实际 L0 → Redis → L1 worker → L1 outbox
relay → Redis → L2 Arq worker。** v1 完成后，L0 v2 更新会自动触发 L1 新 run
和 L2 revision 2 重评分；随后重放迟到 revision 1，评分、翻译、成本、状态和
完成事件均保持 revision 2。

M2 浏览器链路仍保持通过。模型仍使用 FakeLLM；版本闭环数据库使用独立
SQLite、消息与任务使用真实本地 Redis/Arq。PostgreSQL 版本闭环、真实模型和
生产进程编排仍待验证。

## 五个仓库进度

Ubuntu 工作区：`/home/ubuntu2401/project/codepick`。五仓库的 `codex/m1-ubuntu-handoff` 已与 Ubuntu 可移植性修复合入本地 `main`，验收通过后推送远端 `main`。

| 仓库 | 当前已完成 | 本轮新增/核对 | 主要下一步 |
| --- | --- | --- | --- |
| codepick-docs | 产品架构资料、项目进度、开发计划、本机指南 | 新增版本化数据契约、M1 跨进程脚本与验证记录，更新总索引 | 随真实服务接入补端到端证据 |
| deepdata（L0） | 采集、raw/对象存储、正文、去重/版本、查询与 outbox | 更新自动发带 content_version/hash 的独立事件；查询暴露版本身份 | TREND 版本语义；生产 PG/S3 持续运行 |
| seek_data（L1） | 持久分析/快照/缓存/状态成本/outbox | Redis reliable worker、持续 relay；校验 L0 版本；迟到旧版 superseded | 真实模型、PostgreSQL 全链路、进程监控 |
| agentic（L2） | 评分、翻译、HTTP、SQL 状态成本和完成事件 | 按 run_id 读历史快照；revision 重评分；旧任务写保护；Redis→Arq bridge；0003 迁移 | L2 completion outbox 投递确认；真实模型和 PostgreSQL 全链路 |
| pickblog（L3） | 双语阅读应用、Reader/Public API、开发账号/早报/配额、SQLite 迁移 | 真实 L2 provider；Next 同源代理；显式 demo fallback；可重试错误页；无 mock M2 浏览器测试 | 真实身份隔离、依赖升级；随后支付、邮件与 MCP |

## 本轮验证

| 范围 | 本轮结果 | 边界 |
| --- | --- | --- |
| L1 | 128 项测试通过；smoke/DoD、L0 → L1 smoke、版本 worker/relay 检查通过 | SQLite 真事务与真实 Redis 消息；模型为 FakeLLM |
| L2 | 106 项测试通过；覆盖率 81.80%；Ruff、mypy、smoke/contracts 通过 | 含 revision 并发保护、0003 迁移和 Redis→Arq bridge；真实模型仍待验证 |
| M1 综合检查 | 7 个独立进程阶段全部通过 | 三个 SQLite 库、实际 L0 文件采集和更新、持久 L1 与 L2；事件文件是验证载体，不是 Redis worker |
| M2 L2 | 97 项测试通过；覆盖率 85.57%；Ruff、mypy、smoke/contracts 通过 | HTTP 服务读取真实 SQL 快照；模型仍为 FakeLLM |
| M2 L3 | 114 项后端测试通过；smoke/preflight/migration、typecheck/build、原 26 项浏览器测试通过 | 新增 provider 404/503 回归和显式无回退配置 |
| M2 跨进程 | 无 API mock 浏览器读取、L2 停止错误页、L2 恢复继续读取全部通过 | L1/L2 SQLite；三个服务仅绑定 127.0.0.1 |
| 版本消息闭环 | L0 v1/v2、L1 worker/relay、L2 Redis bridge/Arq、迟到 v1 重放全部 PASS | SQLite + 真实 Redis/Arq；L1/L2 为 FakeLLM |

最新不重复自动化基线为 L0 45、L1 128、L2 106、L3 后端 114、原浏览器
26 和 M2 浏览器 2 项，共 **421 项**。版本闭环另执行 15 个独立进程阶段，
最终输出 `CODEPICK VERSION LOOP: PASS`；M1 七阶段回归仍为 PASS。

## 当前跨层边界

| 边界 | 现在能做什么 | 尚不能声称完成 |
| --- | --- | --- |
| L0 → L1 | 版本化事件经 Redis reliable worker 消费；更新自动通知；迟到旧版有明确策略 | TREND 无正文分支；PostgreSQL/S3 上的持续闭环 |
| L1 → L2 | run_id/revision 经 durable outbox 和 Redis 传递；L2 读对应历史快照 | PostgreSQL 上同链路；真实模型成本 |
| L2 进程间 | 新 revision 重评分；旧任务无法覆盖；每 revision 独立完成事件 | 全图一次性提交；L2 completion outbox sent/ack/dead-letter |
| L2 → L3 | 四个 HTTP 接口读取持久 L2 和版本化 L1 快照；L3 能区分 404 与可重试 503 | PostgreSQL 上的 M2 端到端、真实模型和持续服务运行尚未验证 |
| 浏览器/真实账户 | 同源代理和关闭 demo fallback 的真实读取已通过；断链/恢复已验证 | 任意邮箱仍共用 user_id=1；真实认证/隔离、正式 Paddle、邮件和 MCP 协议未完成 |

L2 当前仍要求同一内容串行处理。已完成/取消/待审产物具有原子写入保护，迟到任务不能再改写产物或成本；双方都尚在处理时的完整图执行所有权和一致发布仍需后续机制，不能用状态条件更新代替。

## 下一步

版本消息闭环首版已完成。下一步进入 **M3 公开多用户门槛**：真实用户记录和
账户隔离、前端依赖升级、开发默认值生产门禁；并行补 L2 completion outbox
投递确认和 PostgreSQL 版本闭环复验。

本轮开发详情见 [版本消息闭环](VERSIONED_EVENT_LOOP.md)、[M1 交接](M1_INTEGRATION.md)
与 [M2 联调记录](M2_INTEGRATION.md)，字段与数据所有权见
[L1 → L2 v1 契约](contracts/L1-L2-v1.md)。
