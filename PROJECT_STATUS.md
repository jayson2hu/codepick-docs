# CodePick 项目状态

更新日期：2026-09-16（Ubuntu 24.04 交接审计）

## 结论

GitHub 上五个仓库目前都只有 `main`，没有 `codex/m1-ubuntu-handoff`。公开代码不包含用户描述的 Windows M1 完整交接：`scripts/verify_m1.py`、`l1_data_processing.l0_smoke`、`M1_INTEGRATION.md` 和 `contracts/L1-L2-v1.md` 均不存在，L1/L2 测试规模也分别只有 55/32，而不是 112/94。

因此不能根据文字描述重写 M1，也不能在不确定的 SQL schema 和事件契约上继续 M2。需要先取得 Windows 未推送的提交、分支或补丁。

## 公开 main 的已验证能力

- L0：离线采集、SQLite/文件存储、PostgreSQL、Redis、MinIO、事务性 outbox 和快速 soak 已通过。
- L1：StubContentProvider、FakeLLM、内存持久化/缓存/成本记录的独立管线通过；真实 L0 集成入口缺失。
- L2：Stub/SQLAlchemy analysis provider、FakeLLM、评分/翻译/推荐/伴读服务函数、PostgreSQL 迁移和 Redis/ARQ 契约通过；不是 Windows M1 的持久化跨进程版本。
- L3：后端 109 项测试、SQLite 迁移、前端构建和 26 项 stub 模式浏览器测试通过。

## Ubuntu 修复

- L0 修复 POSIX/Windows `file:` URI 转换和硬编码 Windows 缺失文件测试。
- L2 修复 ruff/mypy 门禁问题，不改变功能契约。
- Docker Compose 端口仅绑定 `127.0.0.1`；L0 改用可用的 MinIO Quay 官方镜像和无冲突测试端口。
- reader-web 移除 Windows 绝对路径，使用可配置的独立 Playwright 端口，避免复用宿主机 3000 端口上的其他服务。

## 当前模拟组件

FakeLLM、L1/L2 stub provider、L3 stub L2、内存 repository/quota、沙箱计费、mock 邮件和部分浏览器 API route mock 仍在使用。

## 未验证

Windows M1 七阶段验证、真实模型、真实 M1 L0→L1→L2 跨进程链路、L2 HTTP、L3 真实 L2 provider、无 API mock 的 M1 文章浏览器验证、真实认证/支付/邮件/MCP 均未验证。
