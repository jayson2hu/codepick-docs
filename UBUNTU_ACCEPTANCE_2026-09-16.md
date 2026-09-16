# Ubuntu 验收记录（2026-09-16）

## 环境

- Ubuntu 24.04，Python 3.12.3，Node.js 24.21.0，npm 11.19.0，Docker 29.8.0。
- 实际工作区：`/home/ubuntu2401/project/codepick`；`/srv/codepick` 因 sudo 密码不可用未创建。
- 四个 Python `.venv` 已创建并安装 `.[dev]`；L1 环境额外安装相邻 L0。

## Git 基线

| 仓库 | 分支 | HEAD |
|---|---|---|
| codepick-docs | main | a3c2f9bbd102a1f7c3235671e885049c7eef0e18 |
| deepdata | main | ab0cd79176fa865ffac4868f78b882dfcd49b9a6 |
| seek_data | main | dcbb21572a84ae5c9943bda638774116d3fffef3 |
| agentic | main | c05be050228872a429c9fda0be77dda1fa613327 |
| pickblog | main | 5554ba89e2b428d47aa12257f803dca5b5ebc940 |

远端均只有 `main`，没有 `codex/m1-ubuntu-handoff`。

## 结果

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

## 阻塞

M2 未开始。需要提供 Windows M1 未推送提交/分支/补丁，尤其是 L1 持久化实现、L2 完整持久化 worker、L1-L2 契约、M1 验证脚本和交接文档。
