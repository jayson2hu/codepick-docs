# 真实内容本机预览

更新：2026-09-17。业务与架构依据见 [产品评审](PRODUCT_REVIEW_2026-09-17.md) 和 [改造计划](PRODUCT_REBUILD_PLAN.md)。本页是可重复运行的私有开发流程，不是生产部署说明。

## 页面与服务

| 地址 | 用途 |
| --- | --- |
| http://127.0.0.1:13200/zh | 用户阅读网站，中文界面 |
| http://127.0.0.1:13200/en | 用户阅读网站，英文界面 |
| http://127.0.0.1:18000 | L0 采集运营看板，只读预览 |
| http://127.0.0.1:18100/docs | L3 Reader API 文档 |
| http://127.0.0.1:18230/docs | L2 内容 API 文档 |

五个仓库不是五个独立用户网站。L1 是后台加工模块；L2 是后台判断与 HTTP 服务；终端阅读在 L3。API 根路径现在跳转到文档，Reader Web 根路径跳转中文首页。未知内容和未知页面仍返回 404。

## 远程访问

这台 Ubuntu 是 Windows 宿主机里的 VMware 虚拟机。已知 Tailscale 地址是 `100.68.112.4`，节点名为 `ubuntu2401`。远程电脑需接入同一个获授权的 Tailscale 网络，并能通过 SSH 登录该 Ubuntu。

在远程电脑 PowerShell / 终端运行下列单行命令，并保持窗口开启：

```bash
ssh -N -o ExitOnForwardFailure=yes -L 13200:127.0.0.1:13200 -L 18000:127.0.0.1:18000 -L 18100:127.0.0.1:18100 -L 18230:127.0.0.1:18230 ubuntu2401@100.68.112.4
```

随后访问上表的地址。这里浏览器的 `127.0.0.1` 是你的远程电脑，由 SSH 转发到虚拟机。只转发 13200 足够使用阅读网站；其他端口用于看板和接口文档。若本机端口已占用，可改变 `-L` 左边的端口，并使用相应新地址。首次 SSH 连接应通过可信方式核对主机指纹。

## 准备独立真实数据

在五仓库的同级目录执行。`/tmp/codepick-real-preview-20260917` 是本次测试路径；新建预览应选新路径。不会连接业务数据库。首次 L0 导入拒绝已有目录；重复导入需明确增加 `--reuse`，通过正常去重和版本流程执行。

```bash
cd /home/ubuntu2401/project/codepick/deepdata
.venv/bin/python -m core_data.scripts.real_preview \
  --data-dir /tmp/codepick-real-preview-20260917/l0 \
  --manifest deploy/real-preview-sources.json \
  --report /tmp/codepick-real-preview-20260917/l0-report.json

cd ../seek_data
.venv/bin/python -m l1_data_processing.real_preview \
  --l0-database-url sqlite:////tmp/codepick-real-preview-20260917/l0/l0.db \
  --l0-object-store /tmp/codepick-real-preview-20260917/l0/objects \
  --l1-database-url sqlite:////tmp/codepick-real-preview-20260917/l1/l1.db \
  --report /tmp/codepick-real-preview-20260917/l1-report.json

cd ../agentic
.venv/bin/python -m judgment_graph.scripts.prepare_preview \
  --l1-db /tmp/codepick-real-preview-20260917/l1/l1.db \
  --l2-db /tmp/codepick-real-preview-20260917/l2.db \
  --report /tmp/codepick-real-preview-20260917/l2-report.json
```

输入来自公开订阅源及其公开文章；采集有条数/超时/频率限制。L1 只提取原文句子并使用确定性词哈希向量，不声称语义向量或模型生成。L2 `heuristic-v1` 用词数、主题词和实践线索估计阅读排序，未评估的创新性维度是兼容占位，不作为用户质量评价。低规则优先级保持 `WAIT_REVIEW`；只有 `COMPLETED` 才向阅读页面提供。

规则模式不生成翻译。中文界面会保留外文原文并说明无翻译；伴读仅检索现有分析片段，找不到时明确报告无匹配，不生成猜测答案。真实文章不等于真实模型质量已验收。

抓取正文、数据库、日志、令牌和完整运行报告放在本机测试目录，不提交到 Git。该预览不授予文章的公开再分发权；页面保留原文链接，后续公开发布前需逐来源核对展示与摘要授权。

## 跨层验收

四个服务启动后可执行只读一致性检查（只读 L0 写入门禁使用一个预期被拒绝的 POST）：

```bash
cd /home/ubuntu2401/project/codepick/codepick-docs
../seek_data/.venv/bin/python scripts/verify_real_preview.py \
  --data-dir /tmp/codepick-real-preview-20260917 \
  --report /tmp/codepick-real-preview-20260917/cross-layer-report.json
```

本次输出 `CODEPICK REAL PREVIEW: PASS (10 imported; 5 readable)`。数据源最终为 `extractive-v3`；重新抓取和加工的版本身份由正常流程决定，不手工指定 revision。Google 来源本机联网失败，已保留在报告；两个成功 GitHub feed 属于同一发布者。

## 一键启动与停止

停止此前占用上表端口的旧测试服务后执行：

```bash
cd /home/ubuntu2401/project/codepick/codepick-docs
../seek_data/.venv/bin/python scripts/run_preview.py \
  --data-dir /tmp/codepick-real-preview-20260917
```

启动器检查端口，升级独立 `l3.db` 的本层表，启动只读 L0 看板、L2、Reader API 和 Reader Web，检查真实内容可读后输出 `status=ready`。全部绑定 `127.0.0.1`。按 Ctrl+C 会停止本次启动的四个服务；数据保留供再启动。日志在测试目录的 `logs/`。端口可通过 `--web-port`、`--l0-port`、`--reader-port`、`--l2-port` 调整。

故障恢复脚本只允许操作经 `/proc` 验证身份、数据库和 loopback 端口匹配的当前测试 L2 进程。先用 `ss -ltnp` 确认 18230 的 PID，再执行：

```bash
node scripts/verify_preview_recovery.mjs \
  --l2-pid <已核实的测试L2_PID> \
  --data-dir /tmp/codepick-real-preview-20260917 \
  --report /tmp/codepick-real-preview-20260917/recovery-report.json
```

脚本临时 SIGSTOP/SIGCONT，验证错误页无演示回退及同页 Retry 恢复，finally 保证恢复进程。最小 Ubuntu 需同时设置开发指南中的浏览器路径、共享库与字体环境变量；不要传入其他服务 PID。

收藏存储边界由页面说明：游客收藏在当前浏览器，账户收藏在本次 L3 SQLite。登录是开发邮箱模式，不验证邮箱所有权。邮件为 mock，支付为 sandbox；真实模型、真实认证和支付均不在本预览验收范围。
