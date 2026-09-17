# Ubuntu 24.04 本地开发

## 2026-09-17 真实来源预览

本轮推荐入口：[真实内容预览与远程访问](REAL_CONTENT_PREVIEW.md)，验收见 [日期化记录](PRODUCT_ACCEPTANCE_2026-09-17.md)。五仓库当前工作目录是 `/home/ubuntu2401/project/codepick`。四个服务只监听 loopback，由 SSH 转发到访问者电脑；不开放数据库、缓存或对象存储的公网端口。

下文 2026-09-16 的 443 项和 46 项 L0 数据保留为历史，不代表本轮测试数量。最新 L0 60、L1 131、L2 201、L3 后端 166 已通过；前端与交付最终结果以本轮记录为准。

最小 Ubuntu 的中文截图需要 CJK 字体。本机已将官方 `fonts-noto-cjk` deb 隔离解压到 `/tmp/codepick-fonts.2vIbAN`；浏览器测试设置 `FONTCONFIG_FILE=/tmp/codepick-fonts.2vIbAN/fonts.conf` 后中文字形正常。未修改系统/用户字体配置；重建方法见 [L0 看板记录](../deepdata/docs/2026-09-17-readonly-dashboard.md)。远程浏览器使用访问者本机字体。

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

L0 的 Python Playwright 集成测试只访问仓库内 `file://` fixture。若官方浏览器下载不可用，可复用完整 Chrome Headless Shell：为当前 Playwright revision 建立临时 `PLAYWRIGHT_BROWSERS_PATH/chromium_headless_shell-<revision>/chrome-headless-shell-linux64` 布局，并用 `LD_LIBRARY_PATH` 指向本地解压的 Ubuntu 共享库。本机以 revision 1243 运行全量 L0，结果为 46 passed、coverage 86.39%；临时目录已清理。

## 安全边界

Compose 端口必须绑定 `127.0.0.1`。测试只使用独立 Compose project、测试数据库和测试对象存储；不要加载真实业务 `.env`，不要调用真实模型、真实邮件、支付或生产服务。

## 当前完整复验结果

2026-09-16 当前五仓库 `main` 基线已完成本机全部无需外部凭据的安全验收：L0 46、L1 128、L2 114、L3 后端 127、Reader Web 26、M2 无 mock 浏览器 2，共 443 项不重复自动化。M1 七阶段、版本闭环 15 阶段、L0 external DoD 和 L2 strict integration 也全部 PASS。完整报告、端口、模拟组件和未验证真实服务见 [Ubuntu 验收记录](UBUNTU_ACCEPTANCE_2026-09-16.md)。

## 外部基础服务验收

L0 使用 `deepdata/deploy/docker-compose.yml` 的 PostgreSQL、Redis 和 MinIO。`minio-init` 是成功后退出 0 的 one-shot 容器；当前 Compose 可能让整体 `up -d --wait` 因它正常退出而返回非零。使用 `up -d` 后分别等待三个服务 healthy，并确认 `minio-init` 为 `exited (0)`，再运行 migration、`core_data.scripts.external_dod --skip-soak` 和 quick soak。完成后 `docker compose down -v`。

L2 使用 `agentic/docker-compose.integration.yml`，服务 healthy 后设置 `L2_INTEGRATION_STRICT=1` 并运行 `judgment_graph.scripts.integration_check`。当前检查还覆盖 PostgreSQL completion outbox → Redis → 测试 ACK 持久化。两套 Compose 只绑定 loopback，且本轮容器和卷均已清理。

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
