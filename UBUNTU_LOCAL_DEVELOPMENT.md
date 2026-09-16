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

## M2 本地联调

先用 M1 验收保留的 `l1.db` 和 `l2.db`，或自行准备等价的独立测试库。
三个服务均只绑定 `127.0.0.1`。

终端一，启动 L2：

```bash
cd agentic
L2_DATABASE_URL=sqlite:////tmp/codepick-m2/l2.db \
L2_L1_DATABASE_URL=sqlite:////tmp/codepick-m2/l1.db \
L2_HTTP_HOST=127.0.0.1 L2_HTTP_PORT=8200 \
.venv/bin/python -m judgment_graph.scripts.run_http
```

终端二，关闭 L3 stub：

```bash
cd pickblog
L3_USE_STUB_L2=false \
L2_BASE_URL=http://127.0.0.1:8200 \
READER_API_HOST=127.0.0.1 READER_API_PORT=8100 \
.venv/bin/python scripts/run_reader_api.py
```

终端三，关闭前端演示回退并启用同源代理：

```bash
cd pickblog/apps/reader-web
READER_API_BASE=http://127.0.0.1:8100 \
READER_API_PROXY_TARGET=http://127.0.0.1:8100 \
READER_USE_DEMO_FALLBACK=false \
NEXT_TELEMETRY_DISABLED=1 \
npm run dev -- --hostname 127.0.0.1 --port 3200
```

浏览器验收：

```bash
cd pickblog/apps/reader-web
PLAYWRIGHT_PORT=3200 npm run test:e2e:m2
```

正常链路应显示 M1 文章、详情、评分和翻译。停止 L2 后页面应显示
`Content temporarily unavailable` 与 `Retry`；恢复 L2 后再次访问应成功。
完整记录见 [M2 联调记录](M2_INTEGRATION.md)。

## 版本消息闭环验收

启动仅绑定 localhost 的 Redis：

```bash
cd agentic
docker compose -p codepick-version-loop \
  -f docker-compose.integration.yml up -d --wait redis
```

执行跨进程验收：

```bash
cd ../codepick-docs
../seek_data/.venv/bin/python scripts/verify_version_loop.py \
  --report /tmp/codepick-version-loop.json
```

预期输出：

```text
CODEPICK VERSION LOOP: PASS (L0 v2 -> L1 run -> L2 revision; stale v1 ignored)
```

脚本使用 Redis DB 15、临时 SQLite 和文件对象存储、L1/L2 FakeLLM，不调用
外部模型。完成后停止测试 Redis：

```bash
cd ../agentic
docker compose -p codepick-version-loop \
  -f docker-compose.integration.yml down
```

实现和边界见 [版本消息闭环](VERSIONED_EVENT_LOOP.md)。
