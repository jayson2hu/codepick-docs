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
