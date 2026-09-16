# M1：持久化与跨进程接手记录

日期：2026-09-12。第一轮已经恢复环境并接通只读 L0 → L1，本轮完成 L1 持久化及 L2 实际读取/结果重启。五仓库进度复核见 [当前进度](PROJECT_STATUS.md)。

## 本轮实际交付

- L1 新的 `SqlAlchemyEnrichmentStore` 与 `process_content`，保留原独立 graph API；分析、输入快照、缓存、处理记录/成本和版本化 outbox 一次事务提交。
- L1 成功请求重启幂等、失败重试、content/graph 变化、明确 request key、历史输入重新激活、并发过时写拒绝；SQLite/PostgreSQL 分开的 SQL 迁移资源。
- L2 的版本化 SQL 输入 adapter 使用实际 L1 快照，不再依赖虚构的上游双表字段；必需数据缺失明确报错。
- L2 持久化状态、成本和完成事件；评分/翻译重启后可见；状态与审核并发更新保护；已完成/取消/待审的重复任务不再次访问上游和模型。
- 已完成/取消/待审产物的写入使用同事务原子状态条件检查，阻止已运行中的迟到重复覆盖评分、翻译和成本；同一内容仍需串行运行，完整图的处理所有权尚未实现。
- 一条可复现的多进程检查，将三个代码仓库和各自虚拟环境实际串起来，避免同进程共享内存掩盖断点。

## 一条命令验证

在 `D:\fayun\code\codepick\codepick-docs` 执行：

```powershell
& ..\seek_data\.venv\Scripts\python.exe scripts/verify_m1.py --report verification/2026-09-12-m1-pipeline.json
```

默认所有数据库、RSS/HTML、对象文件和事件载体都在新建临时目录；完成后清理。各阶段分别使用 deepdata/seek_data/agentic 自己的 `.venv`。不使用继承的 DATABASE_URL，不改现有运行库，不调用模型服务。

需要保留验证数据供查看时，可增加 `--data-dir D:\fayun\code\codepick\codepick-docs\.runtime\m1-demo`；该目录必须不存在，重复使用会拒绝执行。也可以用 `--project-root` 指定另一处保持同级布局的工作区。

| 阶段 | 验证点 |
| --- | --- |
| ingest / L0 | 实际 RSS/HTML 采集、正文/来源存储、整数 content.ingested 事件 |
| enrich / L1 | 从 L0 查询读取并一次事务写 L1；输入正文 hash 和来源一致 |
| replay / 新 L1 进程 | 读取先前处理记录且模型调用为零；模拟投递故障后恢复，事件只确认一次 |
| score / L2 | 只凭 L1 数据库快照读取摘要/标签/语言/正文；评分、双语翻译、完成状态与事件落库 |
| read / 新 L2 进程 | 重启后完成分数、翻译、状态和 outbox 可读；消费者与管道重复任务不调用模型 |
| update / L0 | 修改临时文章并通过实际 L0 采集记录下一内容版本 |
| versions / L1 | 显式重读更新内容、切换 graph、指定重处理 key；产生三个独立通知，重复请求不再调用模型 |

成功输出 `CODEPICK M1: PASS`。本轮七阶段已通过，详细结果在 [流水线记录](verification/2026-09-12-m1-pipeline.json)。

## 检查结果与限制

- L1：112 项测试通过，迁移往返/隔离、失败回滚、重启/版本/并发和 SQL 打包资源已检查。
- L2：94 项测试通过，覆盖 85.68%；类型、代码检查、smoke/契约与增量迁移通过。
- L0/L3 本轮未改产品代码，沿用本日上一轮验证，并单独记录为历史证据。
- 数据库实际运行验证为 SQLite。PG 迁移/SQL 兼容资源已提供，但没有真实 PG/Redis/S3 或模型服务验收。
- 本测试使用本地事件文件作为可检查的投递目标，没有真实持续消费者、Redis worker 或端到端支付/邮件。
- 第一次 L2 评分已持久化，后续 L1 版本通知保留待消费；L2 版本重评分未实现，L0 更新也仍需显式触发 L1。

## 继续开发

优先做 L2 的内容列表/详情 HTTP 服务，让 L3 关闭 stub 后读取这些持久产物，再补无 API mock 的浏览器验证。与此同时，需要为 L0 更新事件、L1 run_id 与 L2 处理版本建立统一生命周期。具体范围见 [开发计划](DEVELOPMENT_PLAN.md)。

各层实现记录：[L1](../seek_data/docs/2026-09-12-m1-persistence.md)、[L2](../agentic/docs/2026-09-12-m1-integration.md)。全部本轮改动尚未提交/推送。
