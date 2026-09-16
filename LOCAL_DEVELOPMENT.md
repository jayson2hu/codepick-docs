# CodePick 本机开发指南

更新：2026-09-16。以下先记录当前 Ubuntu 24.04 验收环境；后半部分保留 Windows
历史恢复说明供异地开发参考。

## Ubuntu 24.04 当前基线

工作区为 `/home/ubuntu2401/project/codepick`，五仓库同级；Python 仓库使用各自
`.venv/bin/python`，Reader Web 要求 Node.js 20.9 或更高版本。

## 完整本机验收

2026-09-16 当前 `main` 基线实际通过 443 项不重复自动化，以及 M1 七阶段、版本闭环 15 阶段、L0 external DoD、L2 strict integration 和 M2 无 mock 断链/恢复。完整证据与模拟边界见 [Ubuntu 验收记录](UBUNTU_ACCEPTANCE_2026-09-16.md)。核心离线入口如下：

```bash
cd /home/ubuntu2401/project/codepick/codepick-docs
../seek_data/.venv/bin/python scripts/verify_m1.py \
  --report /tmp/codepick-m1-current.json

cd ../deepdata
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy --config-file pyproject.toml src

cd ../seek_data
.venv/bin/python -m pytest
.venv/bin/python -m l1_data_processing.smoke
.venv/bin/python -m l1_data_processing.dod
.venv/bin/python -m l1_data_processing.l0_smoke

cd ../agentic
.venv/bin/python -m pytest --cov=judgment_graph \
  --cov-report=term-missing --cov-fail-under=80
.venv/bin/python -m ruff check packages/judgment_graph
.venv/bin/python -m mypy packages/judgment_graph/judgment_graph
.venv/bin/python -m judgment_graph.scripts.smoke
.venv/bin/python -m judgment_graph.scripts.verify_contracts

cd ../pickblog
unset DATABASE_URL L3_MIGRATION_SMOKE_DATABASE_URL
.venv/bin/python -m pytest -c pytest.ini
.venv/bin/python scripts/l3_smoke.py
.venv/bin/python scripts/l3_preflight.py
.venv/bin/python scripts/l3_migration_smoke.py
```

L0 的 Playwright 集成测试只读取仓库内 fixture。标准环境直接安装 Playwright Chromium 后运行全量 pytest。若受限 Ubuntu 已有完整的 Chrome Headless Shell，可建立 Playwright 期望的临时目录布局并注入本地共享库：

```bash
browser_root=$(mktemp -d /tmp/codepick-l0-playwright.XXXXXX)
mkdir -p "$browser_root/chromium_headless_shell-1243"
ln -s /path/to/chrome-headless-shell-linux64 \
  "$browser_root/chromium_headless_shell-1243/chrome-headless-shell-linux64"

PLAYWRIGHT_BROWSERS_PATH="$browser_root" \
LD_LIBRARY_PATH=/path/to/local/ubuntu-libs \
.venv/bin/python -m pytest
```

版本 `1243` 必须与当前 Python Playwright 期望的 revision 一致；不要用不完整下载目录冒充浏览器安装。本机复验用此方式得到 46 passed、coverage 86.39%，随后删除临时链接目录。

L0 external DoD 使用 `deepdata/deploy/docker-compose.yml`，所有端口已绑定 `127.0.0.1`。`minio-init` 是成功后退出 0 的 one-shot 容器；某些 Compose 版本会因此让整体 `up -d --wait` 返回非零。应使用 `up -d`，分别等待 PostgreSQL、Redis、MinIO healthy，并确认 `minio-init` 为 `exited (0)`，再执行：

```bash
export DATABASE_URL=postgresql+psycopg://codepick:dev@127.0.0.1:55432/codepick
export REDIS_URL=redis://127.0.0.1:56379/0
export OBJECT_STORE_BACKEND=s3
export S3_ENDPOINT=http://127.0.0.1:59000
export S3_ACCESS_KEY=minio
export S3_SECRET_KEY=minio123
export S3_BUCKET=codepick-raw
.venv/bin/python -m alembic -c alembic.ini upgrade head
.venv/bin/python -m core_data.scripts.external_dod --skip-soak
.venv/bin/python -m core_data.scripts.external_dod \
  --soak-hours 0 --interval-sec 0 --report /tmp/codepick-l0-external-dod.json
```

L2 strict integration 使用 `agentic/docker-compose.integration.yml` 的 loopback PostgreSQL/Redis。服务 healthy 后以 `L2_INTEGRATION_STRICT=1` 运行 `judgment_graph.scripts.integration_check`，完成后执行 `docker compose down -v`。不要连接 5432 上的现有数据库，也不要加载真实业务 `.env`。
L3 M3 快速验收：

```bash
cd /home/ubuntu2401/project/codepick/pickblog
unset DATABASE_URL L3_MIGRATION_SMOKE_DATABASE_URL L3_AUTH_LOGIN_MODE
.venv/bin/python scripts/l3_smoke.py
.venv/bin/python scripts/l3_preflight.py
.venv/bin/python scripts/l3_migration_smoke.py

cd apps/reader-web
npm ci
npm audit --audit-level=low
NEXT_TELEMETRY_DISABLED=1 npm run typecheck
NEXT_TELEMETRY_DISABLED=1 npm run build
npm run test:e2e
```

默认 `L3_AUTH_LOGIN_MODE=development` 提供开发邮箱登录，但不同邮箱对应独立用户。
生产型预检必须设置 `L3_AUTH_LOGIN_MODE=external`，此时开发登录端点关闭；真实
身份提供商尚未接入。

标准 Ubuntu 建议运行 `npx playwright install --with-deps chromium`。无 sudo 的
受限环境可使用已有 Chrome/Chromium，并设置：

```bash
LD_LIBRARY_PATH=/path/to/local/libs PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/path/to/chrome-headless-shell npm run test:e2e
```

本轮临时 PostgreSQL 16 只绑定 `127.0.0.1:55439`，使用独立测试数据库；完成
Alembic 升降级和双用户验收后容器已删除。不要复用 5432 上的现有业务或其他项目
数据库。

Public API 搜索专项验收：

```bash
cd /home/ubuntu2401/project/codepick/pickblog
.venv/bin/python -m pytest -c pytest.ini tests/test_public_api_search.py
```

无 mock 跨进程检查应让 L2 HTTP 和 Public API 分别只绑定 loopback，设置
`L3_USE_STUB_L2=false` 与 `L2_BASE_URL=http://127.0.0.1:<L2端口>`，再请求
`/v1/search?q=...&limit=...`。搜索必须在 L2 分页前发生；停止 L2 后应返回带
`Retry-After: 2` 的可重试 503，不能回退 stub。完整命令与本轮证据见
[Public API 搜索验收](PUBLIC_API_SEARCH.md)。

`scripts/run_public_api.py` 支持 `PUBLIC_API_HOST`、`PUBLIC_API_PORT` 和
`PUBLIC_API_RELOAD`，reload 默认关闭。2026-09-16 另用仅绑定
`127.0.0.1:55440` 的一次性 PostgreSQL 16 验证 SQLAlchemy 用户/API key/配额，
两次真实搜索后 `api_usage_daily.count=2`；容器和服务均已停止。


## Windows 历史恢复记录


更新：2026-09-12。当前根目录为 `D:\fayun\code\codepick`，五个仓库同级放置。以下命令为 Windows PowerShell；使用仓库自身 Python，避免系统 PATH 的旧 Python 3.7。

## 当前已准备好

- 四个 Python 仓库均有 `.venv`，使用 Python 3.12.14，已安装 `.[dev]`。
- L1 环境另安装相邻 L0 包，用于真实内容 provider 和本地契约检查。
- L3 `apps/reader-web/node_modules` 已由 `npm ci` 安装；本机 Node 24.20.0、npm 11.19.0。
- 本机使用已有 Chrome 执行 Playwright；专用 Chromium 下载未完成。
- 当前未配置真实 PostgreSQL/Redis/MinIO、模型、邮件或支付服务，也没有新增凭据。

在编辑器中打开 `codepick.code-workspace` 可同时查看全部仓库。根目录本身不管理 Git；提交时进入相应仓库。

## M1 跨进程检查

```powershell
Set-Location D:\fayun\code\codepick\codepick-docs
& ..\seek_data\.venv\Scripts\python.exe scripts/verify_m1.py --report verification/2026-09-12-m1-pipeline.json
```

实际 L0 采集、持久化 L1、独立 L2 评分和重启/重复投递/版本检查共七阶段。默认全新临时目录；不使用现有业务库。详细说明见 [M1 交接](M1_INTEGRATION.md)。L1 已新增SQLAlchemy依赖，在其他机器从本次源码安装 `.[dev]` 即可；接实际L0仍需相邻包。

## 各层验证

### L0

```powershell
Set-Location D:\fayun\code\codepick\deepdata
& .\.venv\Scripts\python.exe -m pytest -m 'not integration'
& .\.venv\Scripts\python.exe -m ruff check .
& .\.venv\Scripts\python.exe -m mypy --config-file pyproject.toml src
```

以上排除未装专用浏览器的集成测试。本层 `smoke` 会重置其配置的 SQLite/文件对象存储，因此运行它时必须使用独立验证目录；本轮已在 `.runtime/verification/` 下隔离运行。配置变量实际为 `OBJECT_STORE_PATH`。如需跨层快速验证，优先运行下述使用全新临时目录的 L0 → L1 命令。

### L1 与 L0 → L1

```powershell
Set-Location D:\fayun\code\codepick\seek_data
& .\.venv\Scripts\python.exe -m pytest
& .\.venv\Scripts\python.exe -m l1_data_processing.smoke
& .\.venv\Scripts\python.exe -m l1_data_processing.dod
& .\.venv\Scripts\python.exe -m l1_data_processing.l0_smoke
```

最后一项会生成临时 RSS/HTML，用实际 L0 采集代码写入临时 SQLite 和文件对象存储，再通过 `L0ContentProvider` 驱动 L1 并验证重复投递。不会读取 `DATABASE_URL` 来选择测试库，不调用真实模型；L1 产物仍在内存中，临时数据结束后清理。成功输出 `L0 -> L1 CONTRACT: PASS`。

### L2

```powershell
Set-Location D:\fayun\code\codepick\agentic
& .\.venv\Scripts\python.exe -m pytest --cov=judgment_graph --cov-report=term-missing --cov-fail-under=80
& .\.venv\Scripts\python.exe -m judgment_graph.scripts.smoke
& .\.venv\Scripts\python.exe -m judgment_graph.scripts.verify_contracts
```

该层默认仍使用 StubAnalysisProvider/FakeLLM。`release_check` 等真实集成门禁需要 PostgreSQL 和 Redis；当前不要将离线测试通过视为 release check 通过。

Ubuntu 上 completion relay 与 worker/HTTP 共用同一 `L2_DATABASE_URL`：

```bash
cd /home/ubuntu2401/project/codepick/agentic
L2_DATABASE_URL=sqlite:////tmp/codepick/l2.db \
L2_REDIS_URL=redis://127.0.0.1:6379/0 \
L2_COMPLETION_QUEUE=codepick:l2:events \
L2_COMPLETION_ACK_QUEUE=codepick:l2:events:acks \
.venv/bin/python -m judgment_graph.scripts.relay_completed --once
```

下游持久接收后将信封 `idempotency_key` 写入 ACK 队列。无 ACK 会按相同 ID
超时重投，达到 `L2_COMPLETION_MAX_ATTEMPTS` 后进入数据库 dead-letter。严格本机
检查可运行 `docker compose -f docker-compose.integration.yml up -d --wait` 后设置
`L2_INTEGRATION_STRICT=1` 执行 `judgment_graph.scripts.integration_check`；服务仅绑定
`127.0.0.1:54329/6389`，完成后执行 Compose down。

### L3

```powershell
Set-Location D:\fayun\code\codepick\pickblog
# 以下在独立验证终端执行，避免继承真实服务配置。
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:L3_MIGRATION_SMOKE_DATABASE_URL -ErrorAction SilentlyContinue
& .\.venv\Scripts\python.exe scripts/l3_smoke.py
& .\.venv\Scripts\python.exe scripts/l3_preflight.py
# 迁移检查应使用默认临时 SQLite；不要指向已有业务库。
Remove-Item Env:L3_MIGRATION_SMOKE_DATABASE_URL -ErrorAction SilentlyContinue
& .\.venv\Scripts\python.exe scripts/l3_migration_smoke.py
$env:NEXT_TELEMETRY_DISABLED = '1'
npm --prefix apps/reader-web run typecheck
npm --prefix apps/reader-web run build
$env:PLAYWRIGHT_BROWSER_CHANNEL = 'chrome'
npm --prefix apps/reader-web run test:e2e
```

本轮修复后，迁移 smoke 显式选择的临时库不会再被 `DATABASE_URL` 覆盖；普通 Alembic CLI 的环境配置行为保留。显式设置 `L3_MIGRATION_SMOKE_DATABASE_URL` 仍会对自选测试库执行升级/降级，因此上例先清除此变量。

系统 Chrome 不存在时，在前端目录执行 `npx playwright install chromium`，移除 `PLAYWRIGHT_BROWSER_CHANNEL` 后使用默认浏览器。本机关闭 Next 遥测是为了避开配置文件写入的 EXDEV，并非前端产品设置。现有 E2E 有 API mock，仅证明其覆盖的界面和开发合同。

## 启动本地阅读应用

终端一：

```powershell
Set-Location D:\fayun\code\codepick\pickblog
& .\.venv\Scripts\python.exe scripts/run_reader_api.py
```

终端二：

```powershell
Set-Location D:\fayun\code\codepick\pickblog\apps\reader-web
$env:NEXT_TELEMETRY_DISABLED = '1'
npm run dev -- --hostname 127.0.0.1 --port 3000
```

界面：[英文](http://127.0.0.1:3000/en)、[中文](http://127.0.0.1:3000/zh)。Reader API：[开发接口文档](http://127.0.0.1:8000/docs)。按 Ctrl+C 结束各自服务。本轮没有留后台服务常驻。

当前界面可查看演示数据；开发账户隔离和浏览器同源 API 代理已经完成，真实身份
提供商仍未接入。启动成功不表示生产认证已完成。Public API 可另运行
`scripts/run_public_api.py`，本地端口为 8001。`scripts/run_mcp_server.py` 当前只是 smoke，不是真正持续运行的 MCP 协议服务。

## 在其他电脑重新安装

克隆五仓库到任意同级根目录。先选定 Python 3.12，再在四个代码仓库分别执行：

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e '.[dev]'
```

在 L1 仓库额外执行跨层开发安装：

```powershell
& .\.venv\Scripts\python.exe -m pip install -e ../deepdata
```

在 `pickblog/apps/reader-web` 执行 `npm ci`。仅独立开发 L1 时无需安装 L0；相关跨层测试会明确跳过。

本机创建环境使用的 Python 位于 `C:\Users\Brook\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`。这是本机路径，不应写死为所有电脑的要求。若环境路径移动或该解释器不再存在，按上述步骤重建 `.venv`。

各仓库依赖版本、真实服务配置、剩余功能及验证限制详见各自 DEVELOPMENT/README 和本轮 `docs/2026-09-12-continuation.md`。
