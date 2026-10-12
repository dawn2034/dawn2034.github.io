---
title: "LLM OPD 文献地图：同策略蒸馏论文、技术脉络与阅读路线"
date: 2026-09-20 00:00:00 +0800
categories: [技术调研]
tags: [LLM, OPD, Knowledge Distillation, Post-Training, Reinforcement Learning, Agent]
permalink: /reports/llm-opd-literature-map/
description: "收录 599 条 LLM 同策略蒸馏及相关文献，含 91 条中文重点导读、19 项技术资源，支持交互检索与分类筛选。"
math: false
toc: true
---

这份文献地图整理了 LLM **On-Policy Distillation（OPD，同策略蒸馏）**的论文、公开技术文章与实现入口，覆盖基础目标、自蒸馏、特权信息、多教师、Agent、跨 tokenizer、训练效率及失效分析。

**[打开完整交互文献地图 →](/research/llm-opd-atlas/)**

> 文献检索截止 **2026 年 9 月 8 日**，本页于 2026 年 9 月 20 日发布。页面保留研究快照的日期，后续论文和发表状态变化尚未补入。
{: .prompt-info }

## 收录内容

| 内容 | 数量与说明 |
| --- | --- |
| 分层文献索引 | 599 条论文、报告与综述，包含直接 OPD、任务扩展及相关对照 |
| 中文重点导读 | 91 条，附方法要点、适用条件与阅读提醒 |
| 研究方向 | 20 类，可按题名、作者、缩写、编号与中文导读检索 |
| 技术文章与实现 | 19 项团队文章、官方文档及公开代码入口 |
| 正式会刊依据 | 27 条已匹配官方会刊记录，区分主会与 Findings |

599 条是此次分层整理的总量，包含前置和邻近工作。页面可以单独筛选“OPD 方法与分析”，也可以仅查看重点导读。书目元数据核对、摘要层面的导读和全文评读具有不同深度，具体核验范围在每条记录及“收录与核验说明”中标注。

## 如何使用

完整页面提供五个视图：

1. **文献库**：按关键词、研究方向、年份、发表状态及收录层级筛选。
2. **技术脉络**：梳理采样分布、教师信息、蒸馏目标与反馈粒度，以及主要研究分歧。
3. **阅读路线**：从 GKD、MiniLLM 到 OPSD、SDPO，再进入效率、多教师和 Agent 等专题。
4. **技术文章与实现**：查找官方训练文档与论文代码入口。
5. **收录与核验说明**：查看去重规则、证据层级和正式会刊来源。

交互页面完整托管在本博客域名下，可直接访问。也可以<a href="/research/llm-opd-atlas/index.html" download="LLM_OPD_文献地图_2026-09-08.html">下载单文件 HTML</a>，用浏览器离线搜索；访问论文和代码原文仍需联网。

## 建议先读的材料

- [GKD：On-Policy Distillation of Language Models](https://arxiv.org/abs/2306.13649)：建立“轨迹来源”和“蒸馏目标”两个独立维度。
- [MiniLLM](https://arxiv.org/abs/2306.08543)：理解序列级 Reverse KL 与策略梯度的关系。
- [Self-Distilled Reasoner / OPSD](https://arxiv.org/abs/2601.18734)：理解同一模型在特权上下文下如何产生教师信号。
- [Self-Distillation Policy Optimization / SDPO](https://arxiv.org/abs/2601.20802)：理解文字反馈、环境反馈与自蒸馏的结合。

随后可按交互页面中的专题路线，交叉阅读机制分析和负面结果。比较论文时，应分别记录模型与教师、生成和打分预算、推理长度、pass@k、OOD 表现及旧能力保持情况。

**[进入 LLM OPD 文献地图](/research/llm-opd-atlas/)**
