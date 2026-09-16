# CodePick 开发计划

## P0：恢复真实 M1 交接

1. 从 Windows 工作区推送或导出五仓库的 M1 提交，优先恢复 `codex/m1-ubuntu-handoff`。
2. 恢复 `PROJECT_STATUS.md` 之外的原始 M1 集成文档、`contracts/L1-L2-v1.md` 和 `scripts/verify_m1.py`。
3. 在不覆盖本轮 Ubuntu 修复的前提下合并交接代码。
4. 使用 Python 3.12 重新安装四个 Python 仓库，运行 `verify_m1.py` 并取得 `CODEPICK M1: PASS`。
5. 复核 L1 112 项、L2 94 项测试以及重复任务保护、重启和版本检查。

P0 未完成前，不根据摘要猜测 M1 schema、事件 payload 或持久化行为。

## P1：M2

在真实 M1 基线上实现：

1. L2 HTTP `/content`、`/content/{id}`、`/recommend`、`/companion`。
2. HTTP 与 worker 共享数据库配置，读取持久化 L2 结果。
3. 明确区分 404、上游不可用、配置错误和数据缺失。
4. L3 增加真实 L2 provider；关闭 stub 时禁止静默回退演示数据。
5. 处理同源代理或 CORS，增加无 API mock 的浏览器测试。
6. 验证 L2 停止时的可重试错误和恢复后的继续使用。

## P2：后续集成

- L0 内容更新通知和 L2 按版本重评分。
- 真实模型成本与质量验收。
- PostgreSQL/Redis/MinIO 的长期 soak。
- 真实认证、支付、邮件和 MCP；除非阻塞 M2，否则不提前展开。
