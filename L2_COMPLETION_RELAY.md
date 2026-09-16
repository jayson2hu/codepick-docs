# L2 Completion Relay 验收

日期：2026-09-16
开发分支：`codex/l2-completion-relay`

## 实现

- `agentic` 新增 `20260916_0004`，为 `judgment_outbox` 增加稳定事件 ID、发送尝试、
  `sent_at`、`acked_at`、`dead_lettered_at` 和错误记录，并回填历史行。
- relay 通过数据库条件更新领取事件，发布稳定 Redis 信封；发布失败释放重试，
  缺失 ACK 超时重投，达到上限进入持久 dead-letter。
- 相同事件 ID 允许在 ACK 超时后再次入队，下游必须按 `idempotency_key` 幂等接收。
- 下游只有在持久接收后才把 `idempotency_key` 写入 ACK 队列。

## 验收证据

| 检查 | 结果 |
| --- | --- |
| L2 pytest | 113 passed |
| 覆盖率 | 81.46%，门槛 80% |
| Ruff / mypy | PASS |
| smoke / contracts | `L2 PIPELINE: PASS` / `L2 CONTRACTS: PASS` |
| SQLite + Redis | 发布 `content.completed:501-r0`，ACK 持久化 PASS |
| PostgreSQL 16 + Redis 7 | 0004 升降级、发布、ACK 持久化 PASS |
| 严格集成 | `PASS: completion-relay - PostgreSQL outbox -> Redis -> ACK persisted` |

PostgreSQL/Redis 仅绑定 `127.0.0.1:54329/6389`。验收后数据库降级到 base，容器与
网络已删除。SQLite 验收使用 `/tmp` 临时数据库。未连接生产数据库、真实模型或
真实业务消费者。

## 边界

本轮完成 relay 和确认协议，但 ACK 由测试消费者模拟；尚未指定 L3 或其他业务服务
作为真实消费者。生产前仍需消费者幂等落库、dead-letter 告警/重放工具、队列保留
策略和长时 soak。
