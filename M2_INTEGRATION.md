# CodePick M2 联调与验收

更新：2026-09-16。M2 首版目标是把 M1 的持久 L2 结果通过真实 HTTP 服务交给
L3，并在浏览器中关闭 API mock 和演示数据回退完成读取与故障恢复验证。

## 实现范围

### L2 HTTP（agentic）

- `GET /content`：状态、vertical、cursor、limit、sort 查询。
- `GET /content/{id}`：详情、六维评分、基础分析和翻译。
- `GET /recommend`：基于持久评分的列表。
- `GET /companion`：复用现有伴读图，返回 chunks。
- HTTP 与 worker 共用 `L2_DATABASE_URL`；内容字段从
  `L2_L1_DATABASE_URL` 指向的版本化 L1 快照读取。
- 可选 `L2_API_KEY` 和 `L2_CORS_ORIGINS`。
- 缺配置为 503 `configuration_error`；不存在为 404
  `content_not_found`；完成记录缺 L1 快照为 502
  `upstream_data_error`；存储故障为带 `Retry-After` 的 503。

### L3 与浏览器（pickblog）

- `L3_USE_STUB_L2=false` 时只使用 L2 HTTP provider。
- L2 404 映射为内容不存在；网络、超时和 L2 5xx 映射为可重试 503。
- `READER_USE_DEMO_FALLBACK=false` 时前端不会用 fixture 掩盖错误。
- Next.js `/api/*` 可代理到 Reader API，浏览器保持同源。
- 新增错误边界和 Retry 按钮。
- 新增 `npm run test:e2e:m2`，测试目录不使用 API mock。

## 实际验收拓扑

```text
M1 L1/L2 SQLite
  -> L2 HTTP 127.0.0.1:8200
  -> L3 Reader API 127.0.0.1:8100 (stub=false)
  -> Next.js 127.0.0.1:3200 (demo fallback=false)
  -> Chromium
```

保留的临时数据目录为 `/tmp/codepick-m2-live-20260916`，由全新 M1 七阶段
生成。它是可删除的本机测试数据，不属于仓库交付物。

## 验收结果

1. 正常链路：列表出现 `AI coding agents with durable data`。
2. 英文详情：标题和六维评分正常显示。
3. 中文详情：持久翻译标题正常显示。
4. 停止 L2：Reader API 返回 503，页面显示
   `Content temporarily unavailable` 和 `Retry`。
5. 恢复 L2：无需重启 Reader API 或 Next.js，页面重新读取成功。

仓库检查：

- agentic：97 passed，coverage 85.57%，Ruff/mypy/smoke/contracts PASS。
- pickblog：114 项后端测试、smoke/preflight/migration PASS。
- reader-web：typecheck、production build、原 26 项 Playwright PASS。
- M2 无 mock 浏览器正常、断链和恢复场景 PASS。

## 已知边界

- 模型仍为 FakeLLM；未调用付费模型。
- 本次跨进程 M2 使用 SQLite。PostgreSQL/Redis 已通过 M1 独立严格集成，
  但尚未用于 M2 HTTP → 浏览器整链复验。
- M1 本地文章 URL 为 `file://tmp/...`，来自 L1 测试快照；生产 HTTP URL
  不受该 fixture 现象影响。
- 真实认证/账户隔离、Paddle、真实邮件、MCP transport 不在本轮范围。
- L0 更新自动通知、L2 按版本重评分和 outbox 持续投递仍待完成。
