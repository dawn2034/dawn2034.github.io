---
title: "RSI 递归自改进技术图谱：论文、机制、实现与证据"
date: 2026-09-22 00:00:00 +0800
categories: [技术调研]
tags: [LLM, RSI, Agent, Self-Improvement, Automated Research, Reinforcement Learning]
permalink: /reports/rsi-technology-map/
description: "整理 197 条 RSI 及支撑研究，覆盖自改写、训练、自博弈、自动科研、程序演化和评测；提供中文导读、GitHub 入口、检索与机制比较。"
math: false
toc: true
---

这份技术图谱围绕 **RSI（Recursive Self-Improvement，递归自改进）**，整理了 arXiv 论文、会议和期刊原文、公开技术文章及 GitHub 实现。检索截止 **2026 年 9 月 22 日**。

**[打开完整交互技术图谱 →](/research/rsi-atlas/)**

## 收录了什么

| 内容 | 范围 |
| --- | --- |
| 研究与资源 | 去重后 197 条，包含核心、支撑组件、邻近研究和基础工作 |
| 直接 RSI 相关 | 41 条，包含理论、方法、综述及社区材料；不表示均已实现 RSI |
| 技术分类 | 14 类，覆盖代码、提示、工作流、记忆、harness、训练、数据、自博弈、奖励、科研、程序演化及评测 |
| 代码入口 | 92 个条目附实现，逐项说明官方代码、独立框架或部分开放范围 |
| 发表依据 | 48 个条目有已核对来源，区分主会、Findings、期刊与 Workshop |
| 中文导读 | 每条均包含机制、改进对象、反馈、固定部分、局限与核验深度 |

这是一份按技术分支展开的定向调研，追求广覆盖，不声称穷尽全部相关文献。摘要核验、全文核验与实验复现具有不同含义；本次没有运行论文实验。

## 判断 RSI，先问三个问题

1. **改进了什么？** 是当前回答、持久记忆、代理代码、模型权重，还是产生改进的程序？
2. **改进结果是否回流？** 新版本是否参与产生、评估或选择下一代改进？
3. **改进能力是否被单独测量？** 任务得分上升，能否在等预算、独立任务上转化为更好的后继系统？

工作定义落在闭环：持久变化是否增强下一轮的改进过程。固定评价目标与可修改机制是不同维度；[Gödel Machine](https://arxiv.org/abs/cs/0309048) 的形式化设定和现实中的有限轮次代理演化也具有不同证据边界。

## 推荐先读的技术链

- **自改写与元层递归**：[STOP](https://arxiv.org/abs/2310.02304) → [DGM](https://arxiv.org/abs/2505.22954) → [HGM](https://arxiv.org/abs/2510.21614) → [Hyperagents](https://arxiv.org/abs/2603.19461)。关注任务性能和后代改进潜力的区别。
- **Agent 系统优化**：[Reflexion](https://arxiv.org/abs/2303.11366) → [DSPy](https://arxiv.org/abs/2310.03714) → [GEPA](https://arxiv.org/abs/2507.19457) → [ACE](https://arxiv.org/abs/2510.04618)。定位提示、流程、记忆和底座各自的变化。
- **学习与自博弈**：[STaR](https://arxiv.org/abs/2203.14465) → [Self-Rewarding](https://arxiv.org/abs/2401.10020) → [SEAL](https://arxiv.org/abs/2506.10943)；结合 [Absolute Zero](https://arxiv.org/abs/2505.03335) 阅读反馈来源与课程设计。
- **自动科研**：[AI Scientist](https://arxiv.org/abs/2408.06292)、[AlphaEvolve](https://arxiv.org/abs/2506.13131)、[ScienceBuddy](https://arxiv.org/abs/2609.17523)。分别评估科研产物、研究流程和研究者自身。
- **评测与失效**：[RE-Bench](https://arxiv.org/abs/2411.15114)、[PaperBench](https://arxiv.org/abs/2504.01848)、[PostTrainBench](https://arxiv.org/abs/2603.08640) 及 [Harness 评测反思](https://arxiv.org/abs/2607.12227)。对齐隐藏测试、预算、任务分布和人工介入。

9 月新增收录包括 Dream-RSI、MetaRSI、ScienceBuddy、RRSI 等。新近预印本的强结论，仍需回看实际轮数、可修改对象、固定组件和验证范围。

## 如何使用网页

交互图谱分为技术全景、文献库、阅读路线、工程实现、证据评测和收录说明。可以：

- 按关键词、类别、年份、RSI 关系和材料类型检索；
- 筛选重点文献、代码入口与发表依据；
- 选择最多 3 项并排比较机制、反馈和固定部分；
- 导出 JSON / CSV，或下载单文件 HTML 离线阅读。

<a href="/research/rsi-atlas/index.html" download="RSI_技术图谱_2026-09-22.html">下载单文件 HTML</a>；访问论文和 GitHub 原文仍需联网。

**[进入 RSI 递归自改进技术图谱](/research/rsi-atlas/)**
