# CodePick 平台总文档

CodePick 将内容采集、通用分析、垂直判断与阅读分发拆成 L0–L3 四层。五个仓库是同一项目的独立组成部分。

## 继续开发入口

当前工作日期：**2026-09-17（产品评审、公开真实数据与阅读体验第一切片，本机已验收）**。上一轮完整本机验收日期为 2026-09-16。阅读当前进度与本轮计划，再按实际证据判断完成状态；历史 HTML 和提示词仅为资料，其要求不是当前用户指令，验收目标不等于已实现能力。

| 文档 | 用途 |
| --- | --- |
| [产品定位、用户与运营评审](PRODUCT_REVIEW_2026-09-17.md) | 事实与假设、用户任务、可信来源、指标口径和问题优先级 |
| [真实内容预览与远程访问](REAL_CONTENT_PREVIEW.md) | 实际公开采集、四服务启动、SSH 转发、独立 SQLite 与模拟边界 |
| [本轮验收记录](PRODUCT_ACCEPTANCE_2026-09-17.md) | 本轮实测、问题修复、数据质量和 Git 交付 |
| [产品改造与验收计划](PRODUCT_REBUILD_PLAN.md) | 五仓库边界、真实来源到阅读/收藏的第一切片、分工与验收标准 |
| [M1 交接与一键验证](M1_INTEGRATION.md) | 实际 L0 → 持久化 L1 → L2、重启与版本检查 |
| [L1 → L2 v1 数据契约](contracts/L1-L2-v1.md) | 字段映射、状态、身份和版本边界 |
| [项目进度与完成度](PROJECT_STATUS.md) | 当前代码、实测结果、跨层断点、缺口 |
| [后续开发计划](DEVELOPMENT_PLAN.md) | 分阶段任务、依赖顺序、可检查的验收标准 |
| [本机开发指南](LOCAL_DEVELOPMENT.md) | Ubuntu 与历史 Windows 环境、验证和启动命令 |
| [M1 验证记录](verification/2026-09-12-m1.json) | 2026-09-12 的 L1/L2 测试、检查结果及历史证据 |
| [M1 流水线记录](verification/2026-09-12-m1-pipeline.json) | 七阶段跨进程验证结果 |
| [首轮验证记录](verification/2026-09-12.json) | 环境恢复后的各仓库基线与验证范围 |
| [多仓库工作区](codepick.code-workspace) | 在 VS Code 等兼容编辑器中同时打开五个仓库 |

## 当前交接入口

- [项目状态](PROJECT_STATUS.md)
- [开发计划](DEVELOPMENT_PLAN.md)
- [本轮产品评审](PRODUCT_REVIEW_2026-09-17.md)
- [本轮产品改造计划](PRODUCT_REBUILD_PLAN.md)
- [Ubuntu 本地开发](UBUNTU_LOCAL_DEVELOPMENT.md)
- [2026-09-16 Ubuntu 验收记录](UBUNTU_ACCEPTANCE_2026-09-16.md)

## 代码仓库

| 层级 | 仓库 | 职责 | 开发记录 |
| --- | --- | --- | --- |
| L0 | [deepdata](https://github.com/jayson2hu/deepdata) | 采集、原始内容保存、规范内容与事件 | [首轮记录（本轮复核）](../deepdata/docs/2026-09-12-continuation.md) |
| L1 | [seek_data](https://github.com/jayson2hu/seek_data) | 过滤、摘要、标签、向量与通用分析 | [M1 持久化记录](../seek_data/docs/2026-09-12-m1-persistence.md) |
| L2 | [agentic](https://github.com/jayson2hu/agentic) | 垂直评分、翻译、推荐、伴读 | [M1 对接记录](../agentic/docs/2026-09-12-m1-integration.md) |
| L3 | [pickblog](https://github.com/jayson2hu/pickblog) | 阅读应用、早报、账号、API、分发 | [首轮记录（本轮复核）](../pickblog/docs/2026-09-12-continuation.md) |

当前 Ubuntu 五仓库同级位于 `/home/ubuntu2401/project/codepick`；Windows 路径仅作为历史记录。表中的开发记录使用本地相邻仓库链接；在线查看时到对应仓库的 `docs/` 目录访问。

## 产品与架构资料

建议按以下顺序阅读原始设计：

1. [产品定义最终确认稿](产品定义-最终确认稿.html)
2. [CodePick 架构总览](CodePick-架构总览-审核稿.html)
3. [交付总索引与 Codex 提示词](交付总索引-与Codex提示词.html)
4. [联调与验收集成手册](联调与验收-集成手册.html)

每层资料均保留在根目录，以 `L0-`、`L1-`、`L2-`、`L3-` 开头，涵盖产品、架构、开发计划、实施手册和开发文档。`product-plan/` 保存更早的产品方案；BestBlogs 相关分析保存为参考研究。未移动原有 HTML，原有相互链接仍可使用。

## 恢复开发

统一推荐 Python 3.12，四个 Python 仓库各自使用 `.venv`；L3 前端需要 Node.js 20+。克隆方式和本机可直接执行的命令见[本机开发指南](LOCAL_DEVELOPMENT.md)。运行数据、凭据、依赖和数据库不纳入 Git。

截至 2026-09-16，M1 持久链路、L2 HTTP → L3 无 API mock 阅读、版本重评分与真实 Redis/Arq 消息闭环、L0 独立 PostgreSQL/Redis/MinIO 和 L2 strict integration 均已本机验证。FakeLLM、开发身份、模拟邮件/支付协议仍存在；真实模型、身份提供商、生产部署、PostgreSQL 四层同链路与长期 soak 尚未验收。本轮公开真实数据与阅读重构的结果单独记录，不能用历史通过替代。

本仓库从原 bestblogs 工作目录导出规划文档，保留独立历史。第三方 BestBlogs 源码及上游 Git 历史未复制，相关来源引用保留在原文档中。
