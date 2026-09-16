# M3 账户隔离与前端安全基线

日期：2026-09-16
仓库分支：`codex/m3-user-isolation`

## 交付范围

- L3 开发邮箱登录从固定 `user_id=1` 改为规范化邮箱到稳定用户记录的映射。
- 内存和 SQLAlchemy repository 共用 `get_or_create_user` 契约。
- 兴趣、关注、书签、阅读事件聚合、订阅、API key、撤销和使用量按用户隔离。
- JWT 对篡改、过期、畸形和缺失必需声明统一返回 401。
- `L3_AUTH_LOGIN_MODE=external` 关闭开发邮箱登录；最终预检要求此模式。
- Reader Web 升级到 Next.js 16.3.5、PostCSS 8.5.28、Playwright 1.63.0，
  迁移异步 `params/searchParams`，安全审计归零。
- Playwright 支持可选 `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH`，默认行为不变。

## 验收结果

| 检查 | 结果 |
| --- | --- |
| L3 后端 | 119 passed |
| L3 smoke | `L3 PIPELINE: PASS` |
| 开发预检 | `status=ready`，含 auth check |
| SQLite 迁移 | `L3 MIGRATION: PASS` |
| PostgreSQL 16 迁移 | Alembic upgrade/head + downgrade/base PASS |
| PostgreSQL 双用户 API | `CODEPICK M3 POSTGRES: PASS` |
| npm 锁文件恢复 | `npm ci` PASS |
| npm 安全审计 | 0 vulnerabilities |
| Reader typecheck | PASS |
| Next 16 production build | PASS |
| Playwright | 26 passed，桌面和移动端 |

PostgreSQL 验收使用独立容器和
`postgresql+psycopg://codepick_test:***@127.0.0.1:55439/codepick_m3_test`。
数据库和端口未公开到公网，容器已停止并自动删除。验收最终持久记录为 2 用户、
10 兴趣、2 书签、2 阅读事件和 2 API key。

## 明确边界

`development` 登录仍未验证邮箱所有权，只适合本地开发。`external` 当前用于
关闭该入口和阻止生产误配置，并不实现 OIDC、magic link 或会话刷新。正式身份、
Paddle、邮件、MCP、真实模型和生产数据库均未在本轮调用。

Playwright 系统库因当前账户无 sudo，验收时将 Ubuntu deb 只解压到 `/tmp` 并通过
`LD_LIBRARY_PATH` 使用；这些二进制和临时库不属于仓库交付物。
