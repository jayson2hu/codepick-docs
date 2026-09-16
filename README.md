# CodePick 平台总文档

CodePick 将内容采集、通用分析、垂直判断与阅读分发拆成 L0–L3 四层。五个仓库是同一项目的独立组成部分。

## 继续开发入口

本轮核验日期：**2026-09-12（M1 持久化与跨进程对接）**。阅读当前进度，再按开发计划继续；历史 HTML 和提示词保留作为产品与架构资料，其中的验收目标不等于当前已实现能力。

| 文档 | 用途 |
| --- | --- |
| [M1 交接与一键验证](M1_INTEGRATION.md) | 实际 L0 → 持久化 L1 → L2、重启与版本检查 |
| [L1 → L2 v1 数据契约](contracts/L1-L2-v1.md) | 字段映射、状态、身份和版本边界 |
| [项目进度与完成度](PROJECT_STATUS.md) | 当前代码、实测结果、跨层断点、缺口 |
| [后续开发计划](DEVELOPMENT_PLAN.md) | 分阶段任务、依赖顺序、可检查的验收标准 |
| [本机开发指南](LOCAL_DEVELOPMENT.md) | Windows 路径、已恢复的环境、验证和启动命令 |
| [M1 验证记录](verification/2026-09-12-m1.json) | 本轮 L1/L2 测试、检查结果及复用的历史证据 |
| [M1 流水线记录](verification/2026-09-12-m1-pipeline.json) | 七阶段跨进程验证结果 |
| [首轮验证记录](verification/2026-09-12.json) | 环境恢复后的各仓库基线与验证范围 |
| [多仓库工作区](codepick.code-workspace) | 在 VS Code 等兼容编辑器中同时打开五个仓库 |

## 当前交接入口

- [项目状态](PROJECT_STATUS.md)
- [开发计划](DEVELOPMENT_PLAN.md)
- [Ubuntu 本地开发](LOCAL_DEVELOPMENT.md)
- [2026-09-16 Ubuntu 验收记录](UBUNTU_ACCEPTANCE_2026-09-16.md)

## 代码仓库

| 层级 | 仓库 | 职责 | 开发记录 |
| --- | --- | --- | --- |
| L0 | [deepdata](https://github.com/jayson2hu/deepdata) | 采集、原始内容保存、规范内容与事件 | [首轮记录（本轮复核）](../deepdata/docs/2026-09-12-continuation.md) |
| L1 | [seek_data](https://github.com/jayson2hu/seek_data) | 过滤、摘要、标签、向量与通用分析 | [M1 持久化记录](../seek_data/docs/2026-09-12-m1-persistence.md) |
| L2 | [agentic](https://github.com/jayson2hu/agentic) | 垂直评分、翻译、推荐、伴读 | [M1 对接记录](../agentic/docs/2026-09-12-m1-integration.md) |
| L3 | [pickblog](https://github.com/jayson2hu/pickblog) | 阅读应用、早报、账号、API、分发 | [首轮记录（本轮复核）](../pickblog/docs/2026-09-12-continuation.md) |

本机五个仓库位于 `D:\fayun\code\codepick` 下，同级放置。表中的开发记录使用本地相邻仓库链接；在线查看时到对应仓库的 `docs/` 目录访问。

## 产品与架构资料

建议按以下顺序阅读原始设计：

1. [产品定义最终确认稿](产品定义-最终确认稿.html)
2. [CodePick 架构总览](CodePick-架构总览-审核稿.html)
3. [交付总索引与 Codex 提示词](交付总索引-与Codex提示词.html)
4. [联调与验收集成手册](联调与验收-集成手册.html)

每层资料均保留在根目录，以 `L0-`、`L1-`、`L2-`、`L3-` 开头，涵盖产品、架构、开发计划、实施手册和开发文档。`product-plan/` 保存更早的产品方案；BestBlogs 相关分析保存为参考研究。未移动原有 HTML，原有相互链接仍可使用。

## 恢复开发

统一推荐 Python 3.12，四个 Python 仓库各自使用 `.venv`；L3 前端需要 Node.js 20+。克隆方式和本机可直接执行的命令见[本机开发指南](LOCAL_DEVELOPMENT.md)。运行数据、凭据、依赖和数据库不纳入 Git。

当前已验证实际 L0 采集 → 持久化 L1 → 独立 L2 评分及重启读取，L1 的版本通知与幂等处理已有回归。FakeLLM、L3 模拟账号和邮件仍存在；真实队列、L2 HTTP、版本重评分及生产联调尚未完成。

本仓库从原 bestblogs 工作目录导出规划文档，保留独立历史。第三方 BestBlogs 源码及上游 Git 历史未复制，相关来源引用保留在原文档中。
