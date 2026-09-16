# Ubuntu 24.04 本地开发

## 目录与版本

推荐五仓库并列放在 `/srv/codepick`。若没有 `/srv` 写权限，可放在任意可写并列目录；仓库间相对路径不变。

- Python 3.12
- Node.js 20+
- Docker Engine + Compose plugin（外部集成测试）
- 每个 Python 仓库独立 `.venv`

Ubuntu 缺少 `python3.12-venv` 且无法 sudo 时，可下载官方 `https://bootstrap.pypa.io/virtualenv.pyz`，再执行 `python3.12 virtualenv.pyz --python /usr/bin/python3.12 .venv`。

## Python 环境

在 `deepdata`、`seek_data`、`agentic`、`pickblog` 分别执行：

```bash
.venv/bin/python -m pip install -e '.[dev]'
```

随后在 `seek_data` 执行：

```bash
.venv/bin/python -m pip install -e ../deepdata
```

## reader-web

```bash
cd pickblog/apps/reader-web
npm ci
npx playwright install --only-shell chromium
NEXT_TELEMETRY_DISABLED=1 npm run typecheck
NEXT_TELEMETRY_DISABLED=1 npm run build
npm run test:e2e
```

Playwright 默认使用 `127.0.0.1:3100`，可用 `PLAYWRIGHT_PORT` 覆盖。当前最小 Ubuntu 镜像可能缺少浏览器共享库；优先安装 Playwright 建议的系统依赖，不能 sudo 时可将 Ubuntu 官方 deb 解压到用户目录并仅对测试设置 `LD_LIBRARY_PATH`。

## 安全边界

Compose 端口必须绑定 `127.0.0.1`。测试只使用独立 Compose project、测试数据库和测试对象存储；不要加载真实业务 `.env`，不要调用真实模型、真实邮件、支付或生产服务。

## M1 总体验收

Windows M1 已从 `codex/m1-ubuntu-handoff` 恢复并合入 `main`。在五仓库同级目录下执行：

```bash
cd codepick-docs
../seek_data/.venv/bin/python scripts/verify_m1.py --report /tmp/codepick-m1-ubuntu.json
```

预期输出：`CODEPICK M1: PASS (L0 -> durable L1 -> L2; restart and version checks)`。完整的 2026-09-16 Ubuntu 结果见 [Ubuntu 验收记录](UBUNTU_ACCEPTANCE_2026-09-16.md)。