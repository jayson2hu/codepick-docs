# CodePick 版本消息闭环

更新：2026-09-16。本轮将 M1 中“显式再次调用”的版本测试升级为真实
Redis/Arq 跨进程事件链路。

## 数据流

```text
L0 content v1/v2
  -> L0 transactional outbox
  -> Redis codepick:l0:events
  -> L1 reliable worker + durable processing run
  -> L1 transactional outbox
  -> Redis codepick:l1:events
  -> L2 Redis bridge
  -> Arq score(content_id, run_id, revision)
  -> versioned L2 state/products/completion outbox
```

## 版本规则

- L0 初始及更新事件使用
  `content.ingested:{content_id}:v{content_version}`。
- payload 包含 `schema_version/content_id/content_version/content_hash/lang`。
- L1 当前快照比事件更新时，旧事件确认成 superseded，不生成旧分析。
- L1 每个成功 run 生成唯一 `content.analyzed:{run_id}`，payload 携带
  `run_id/revision/content_version`。
- L2 只接受更大的 revision。相同 revision 重投幂等，较小 revision忽略。
- L2 从 `l1_processing_runs` 读取事件指定 run，而不是误读当前 head。
- 所有评分、翻译、状态和成本写入检查 accepted revision，迟到 worker
  无法覆盖新版本。
- 完成事件按 `content_id + source_revision` 唯一。

## 可靠队列

L1 worker 和 L2 bridge 使用 Redis source/processing 列表。取消息使用 FIFO
`BLMOVE LEFT RIGHT`；启动时将 processing 中的未确认消息按原顺序恢复。
处理失败重新入队，格式错误进入 `:dead`。数据库提交成功但 Redis 确认前
崩溃会导致至少一次重投，由 run/revision 幂等规则吸收。

## 验收

```bash
cd codepick-docs
../seek_data/.venv/bin/python scripts/verify_version_loop.py \
  --report /tmp/codepick-version-loop.json
```

2026-09-16 在当前 `main` 再次实测，15 个独立进程阶段全部通过；报告写入 `/tmp/codepick-version-loop-current.json`：

1. L0 v1 经 Redis、L1、Redis、Arq 完成 L2 revision 1。
2. 同 URL 正文更新自动创建 L0 v2 事件。
3. L1 创建新的 run 和 revision 2，L2 重新评分并产生第二个完成事件。
4. 再次注入 revision 1 事件，L2 仍保持 revision 2，完成事件仍为两个。
5. M1 七阶段回归继续输出 `CODEPICK M1: PASS`。

测试使用临时 SQLite、文件对象存储、真实本地 Redis/Arq 和 FakeLLM。未调用
付费模型或真实业务数据库。

## 尚未完成

- PostgreSQL 上的相同版本闭环复验。
- L2 completion outbox 已具备 sent/ack/dead-letter；仍缺真实下游消费者。
- 真实模型、长期 worker 监控、积压告警和生产进程编排。
- 评分、翻译、完成仍为多个受 revision 保护的事务，不是全图单事务。
