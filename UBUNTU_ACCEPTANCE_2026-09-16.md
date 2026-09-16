# Ubuntu 验收记录（2026-09-16）

## 环境

- Ubuntu 24.04，Python 3.12.3，Node.js 24.21.0，npm 11.19.0，Docker 29.8.0。
- 实际工作区：`/home/ubuntu2401/project/codepick`；`/srv/codepick` 因 sudo 密码不可用未创建。
- 四个 Python `.venv` 已创建并安装 `.[dev]`；L1 环境额外安装相邻 L0。

## 恢复前 Git 基线

| 仓库 | 分支 | HEAD |
|---|---|---|
| codepick-docs | main | a3c2f9bbd102a1f7c3235671e885049c7eef0e18 |
| deepdata | main | ab0cd79176fa865ffac4868f78b882dfcd49b9a6 |
| seek_data | main | dcbb21572a84ae5c9943bda638774116d3fffef3 |
| agentic | main | c05be050228872a429c9fda0be77dda1fa613327 |
| pickblog | main | 5554ba89e2b428d47aa12257f803dca5b5ebc940 |

该表记录 Windows M1 推送前的首次 Ubuntu 审计基线。随后五仓库的 `codex/m1-ubuntu-handoff` 已成功获取并合入本地 `main`。

## 恢复前公开 main 基线结果

| 范围 | 结果 |
|---|---|
| M1 `scripts/verify_m1.py` | 未执行：文件不存在 |
| L0 pytest | 36 passed，1 integration deselected，coverage 85.77% |
| L0 ruff/mypy | PASS |
| L0 external DoD | PASS：PostgreSQL、Redis、MinIO、relay 幂等 |
| L0 quick soak | PASS：1 iteration，new raw=2，new content=1，errors=[] |
| L1 pytest | 55 passed |
| L1 smoke / DoD | PASS |
| L1 `l0_smoke` | 未执行：模块不存在 |
| L2 pytest | 32 passed，coverage 84.22% |
| L2 ruff/mypy/smoke/contracts | PASS |
| L2 strict integration | PASS：PostgreSQL migration、Redis ping、ARQ worker contract |
| L3 backend | 109 passed；smoke/preflight/migration PASS |
| reader-web typecheck/build | PASS |
| reader-web E2E | 26 passed（Chromium desktop + Pixel 5） |

当前公开基线共有 258 项互不重复的自动化测试通过（36+55+32+109+26）。这不等于 Windows M1 的 206 项，也不能替代缺失的七阶段 M1 验收。

## 关键诊断

- L0 初始 3 项失败来自 POSIX `file:` URI 和硬编码 Windows 路径，修复后全绿。
- L2 初始失败仅为 ruff/mypy 门禁，最小类型和导入修复后全绿。
- reader-web 初始误连宿主机 3000 端口上的其他服务并收到 401；改用独立 3100 端口后 26 项全绿。
- Playwright CDN 极慢；最终从 Google Chrome-for-Testing 官方源下载相同版本并校验 MD5，浏览器运行库使用 Ubuntu 官方包。

## M1 恢复后复验

| 范围 | Ubuntu 24.04 结果 |
|---|---|
| M1 七阶段跨进程 | PASS：输出 `CODEPICK M1: PASS` |
| L0 | 45 passed，1 deselected，coverage 85.90%；ruff/mypy PASS |
| L1 | 112 passed；smoke、DoD、L0 → L1 contract PASS |
| L2 | 94 passed，coverage 85.63%；ruff/mypy/smoke/contracts PASS |
| L3 后端 | 112 passed；smoke/preflight/migration PASS |
| reader-web | typecheck/build PASS；26 passed |
| L0 external DoD | PostgreSQL、Redis、MinIO、relay 幂等 PASS |
| L0 quick soak | PASS：new raw=2，new content=1，errors=[] |
| L2 strict integration | PostgreSQL migration、Redis、ARQ worker PASS |

本轮完整仓库测试共有 389 项通过（45+112+94+112+26），另有 M1 七阶段和各 smoke/严格集成入口通过。L1 的两项初始失败来自 SQLAlchemy 版本间 DDL 空白格式差异；修复为规范化空白后比较完整 DDL，未降低断言语义。

## 当前边界

M1 已在 Ubuntu 通过。

## M2 复验

| 范围 | Ubuntu 24.04 结果 |
|---|---|
| L2 | 97 passed，coverage 85.57%；ruff/mypy/smoke/contracts PASS |
| L3 后端 | 114 passed；smoke/preflight/migration PASS |
| reader-web 回归 | typecheck/build PASS；原有 26 passed |
| M2 正常链路 | Chromium 无 API mock 读取 M1 文章、详情、六维评分和中文翻译 PASS |
| M2 故障链路 | 停止 L2 后可重试错误页 PASS；恢复 L2 后继续读取 PASS |

M2 实际链路为保留的 M1 L1/L2 SQLite → L2 HTTP `:8200` → 关闭
stub 的 L3 Reader API `:8100` → 关闭 demo fallback 的 Next.js `:3200`
→ Chromium，所有端口只绑定 `127.0.0.1`。

FakeLLM、SQLite、模拟账号/邮件/计费仍在使用。PostgreSQL、Redis 和 MinIO
已分别通过 M1 严格基础集成，但 M2 HTTP 浏览器链路尚未用 PostgreSQL 端到端
复验；真实模型、真实认证、支付、邮件和 MCP 仍未验证。完整过程见
[M2 联调记录](M2_INTEGRATION.md)。

## 当前 main 汇总复验

在后续 M2/M3、版本消息闭环和 Public API 改动全部合入后，2026-09-16 又从五仓库当前 `main` 基线完整重跑了本机可安全执行的验收。

| 范围 | 当前结果 |
|---|---|
| L0 | 46 passed，coverage 86.39%；Ruff、mypy PASS。包含只读取仓库内 `file://` fixture 的 Playwright 集成测试，不访问外部站点 |
| L1 | 128 passed；pipeline smoke、DoD、L0 → L1 contract PASS |
| L2 | 114 passed，coverage 81.49%；Ruff、mypy、smoke、contracts PASS |
| L3 后端 | 127 passed；smoke、preflight、migration PASS |
| Reader Web | typecheck、production build、原有 26 项 Playwright PASS |
| M2 无 mock 浏览器 | 正常读取、L2 断链错误页、L2 恢复后再次读取共 2 项场景 PASS |

不重复自动化基线为 **443 项**（46 + 128 + 114 + 127 + 26 + 2）。此外：

- M1 七阶段从全新临时数据重跑，输出 `CODEPICK M1: PASS (L0 -> durable L1 -> L2; restart and version checks)`；报告为 `/tmp/codepick-m1-current.json`。
- 版本消息闭环 15 个独立进程阶段重跑，覆盖 L0 v1/v2、L1 worker/relay、L2 Redis bridge/Arq 与迟到 v1，输出 `CODEPICK VERSION LOOP: PASS`；报告为 `/tmp/codepick-version-loop-current.json`。
- L0 external DoD 使用一次性 PostgreSQL `127.0.0.1:55432`、Redis `127.0.0.1:56379`、MinIO `127.0.0.1:59000/59001`，migration、pipeline、relay 幂等、S3 和 quick soak 全部 PASS。quick soak 为 1 iteration、new raw=2、new content=1、errors=[]；报告为 `/tmp/codepick-l0-external-dod.json`。
- L2 strict integration 使用一次性 PostgreSQL `127.0.0.1:54329` 和 Redis `127.0.0.1:6389`，Alembic 升降级、Redis ping、Arq worker contract，以及 PostgreSQL completion outbox → Redis → ACK persisted 全部 PASS。
- M2 使用 `/tmp/codepick-m2-live-20260916/l1.db` 和 `l2.db`，依次在 `127.0.0.1:18230`、`:18100`、`:13200` 启动 L2 HTTP、Reader API 和 Next.js。正常读取通过，停止 L2 后可重试错误页通过，恢复 L2 后再次正常读取通过，最终记录为 `CODEPICK M2 BROWSER RECOVERY: PASS`。

所有 Docker 服务、卷、Redis 测试数据和本地 HTTP 进程均在验收后清理；端口只绑定 loopback。`/tmp` 报告和 M2 SQLite 是本机临时证据，不是仓库或生产数据。

### L0 浏览器说明

Playwright 官方 CDN 在本机下载停滞，因此没有把网络下载失败误判为源码失败。验收复用了已完整下载的 Chrome Headless Shell，并按 Playwright 期望目录布局建立临时链接，配合从 Ubuntu 官方包解压的共享库运行；46 项全量测试均通过。临时目录随后删除。

### 模拟组件与未验证服务

本轮仍使用：

- L1/L2 FakeLLM；没有调用付费模型。
- M1、版本闭环和 M2 HTTP 浏览器链路中的临时 SQLite。
- 开发认证、mock 邮件和支付沙箱/协议级实现。
- L2 completion ACK 的测试消费者。

本轮没有声称完成：

- 真实模型及其成本/失败边界。
- 真实 OIDC 或 magic-link 身份提供商、正式 Paddle、真实邮件投递。
- 真正持续运行的 MCP transport 和真实 MCP 客户端验收。
- 生产数据库、生产对象存储或任何真实业务数据。
- PostgreSQL 上 L0 → L1 → L2 → L3 四层完整链路与 M2 浏览器整链。
- 真实 completion 下游消费者、长期 worker 监控和 24 小时 soak。

截至该次复验，本机不需要外部凭据且可安全执行的验收均已完成，没有需要用户提供凭据或立即决策的阻塞项。
