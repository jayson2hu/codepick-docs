# Public API 服务端搜索验收

更新：2026-09-16。本记录覆盖 `agentic` 与 `pickblog` 的
`codex/public-api-search` 切片；验收后快进合入远端 `main`。

## 实现范围

- L2 `GET /content` 新增最长 200 字符的 `q`，对标题和摘要执行不区分大小写的
  包含匹配，并在排序、游标分页之前过滤。
- L3 `GET /v1/search` 与 MCP `search` 通过共享 `ContentReadProvider` 下推查询，
  不再只过滤当前页。
- stub 与真实 HTTP provider 使用相同的非负整数游标和分页前搜索语义。
- Public API 和 Reader API 区分无效请求、配置/鉴权错误、详情不存在和可重试
  上游故障。关闭 stub 后不会静默回退 fixture。

## 自动化结果

```text
L2: 114 passed, coverage 81.49%; Ruff, mypy, smoke, contracts PASS
L3: 126 backend passed; migration/smoke/preflight/typecheck/build PASS
Reader Web: 26 Playwright passed
L3 VERIFY: PASS
```

L3 专项回归入口：

```bash
cd /home/ubuntu2401/project/codepick/pickblog
.venv/bin/python -m pytest -c pytest.ini tests/test_public_api_search.py
```

该测试覆盖分页前搜索、Public API/MCP 一致性、`q` 长度、非法游标、HTTP 参数
转发、上游 400/401/404/5xx、畸形响应和详情 404。

## 无 API mock 跨进程检查

本轮使用包含两篇文章的临时 SQLite L1/L2 数据，启动：

- L2 HTTP：`127.0.0.1:18220`
- Public API：`127.0.0.1:18001`
- L3：`L3_USE_STUB_L2=false`

查询只匹配第二篇文章，结果为：

```text
CODEPICK PUBLIC SEARCH: PASS {'ids': ['2'], 'next_cursor': None}
```

停止 L2 后重复请求，Public API 返回 503、`l2_unavailable`、`retryable=true` 和
`Retry-After: 2`：

```text
CODEPICK PUBLIC SEARCH OUTAGE: PASS {'code': 'l2_unavailable', 'message': 'L2 provider request failed: /content', 'retryable': True}
```

非法游标另验证为 400 `invalid_request`。所有进程只绑定 `127.0.0.1`，验收结束
后已停止。

## 验收边界

该检查使用真实跨进程 HTTP 和持久查询代码，但数据位于临时 SQLite，评分来自
FakeLLM。未连接生产 PostgreSQL、真实模型、真实身份、邮件、Paddle 或 MCP
protocol transport；这些仍需独立凭据和目标环境验收。
