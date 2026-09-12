# CodePick 平台总文档

CodePick 把内容采集、通用分析、垂直判断与阅读分发拆成 L0–L3 四层。这里集中保存产品、架构、开发计划和集成文档，并提供异地继续开发的入口。

## 代码仓库

| 层级 | 仓库 | 职责 |
|---|---|---|
| L0 | [deepdata](https://github.com/jayson2hu/deepdata) | CodePick L0 content ingestion, storage and data foundation |
| L1 | [seek_data](https://github.com/jayson2hu/seek_data) | CodePick L1 content enrichment and structured analysis |
| L2 | [agentic](https://github.com/jayson2hu/agentic) | CodePick L2 scoring, translation, recommendation and reading agents |
| L3 | [pickblog](https://github.com/jayson2hu/pickblog) | CodePick L3 reader application, newsletters, billing, API and MCP |

数据流：deepdata → seek_data → agentic → pickblog。每个项目的 DEVELOPMENT.md 提供安装、测试和启动入口。

## 在新电脑恢复开发

```sh
mkdir codepick
cd codepick
git clone https://github.com/jayson2hu/codepick-docs.git
git clone https://github.com/jayson2hu/deepdata.git
git clone https://github.com/jayson2hu/seek_data.git
git clone https://github.com/jayson2hu/agentic.git
git clone https://github.com/jayson2hu/pickblog.git
```

L0/L2 需要 Python 3.12+，L1/L3 需要 Python 3.11+；统一使用 Python 3.12 可满足版本要求。L3 前端需要 Node.js 20+。各 Python 项目建立独立 .venv，按各 DEVELOPMENT.md 安装依赖。真实 PostgreSQL、Redis、对象存储及模型凭据在新环境配置。

## 阅读顺序

1. [产品定义最终确认稿](产品定义-最终确认稿.html)
2. [CodePick 架构总览](CodePick-架构总览-审核稿.html)
3. [交付总索引与 Codex 提示词](交付总索引-与Codex提示词.html)
4. [联调与验收集成手册](联调与验收-集成手册.html)

根目录另有每层的产品文档、架构设计、开发计划、实施手册和提示词；product-plan/ 保留早期产品方案。HTML 下载后可直接用浏览器打开。

## 文档与代码状态

这些设计文档形成于 2026 年 5 月；其中的规划、验收目标和配置名称需结合当前代码核对。当前代码支持各层独立开发，部分默认路径仍使用 stub、FakeLLM、内存存储或沙箱服务。公开仓库交接不表示已完成真实环境全链路联调。

本仓库从原本的 bestblogs 工作目录导出 CodePick 规划文档，采用独立历史。原目录中的第三方 BestBlogs 源码与上游 Git 历史未复制；相关第三方来源引用保留在文档中。
