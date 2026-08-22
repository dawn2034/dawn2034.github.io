# DailyEpoch 每日计划与 Markdown 内容规范

本文件是每日 AI 技术简报的长期写作、检索、发布和定时任务执行规范。新日报在生成、整理和写入 `DailyEpoch/YYYY-MM-DD.md` 时必须遵守。

## 每日内容目标

每天生成一份面向资深 AI／推荐算法从业者的中文技术简报，重点覆盖：

1. 大模型与 Agent 的前沿论文和技术进展；
2. 值得精读的深度文章、课程、代码仓库与学习资源；
3. X.com 上近期讨论度高、技术含量高的 AI 帖子与 Thread。

优先关注 LLM 训练与推理、Agent、自我进化、RAG、量化、长上下文、强化学习与对齐、推荐系统、开源模型和基础设施。避免泛泛新闻、重复摘要和营销内容。

每个主题必须说明：发生了什么、为什么重要、可信度或局限、最值得继续追踪的点，并附原始来源。结尾必须包含“今日最值得花 30 分钟阅读的一项”和“今日可立即实践的一件事”。

---

## 定时任务执行规则：X.com 独立高召回检索

X.com 必须作为与 arXiv、GitHub、官方技术博客平行的**独立信息源**处理，不能只围绕当天已经入选的论文做补充检索。

### 0. 禁止“形式化合规”

不能只在日报里写：

> 已完成 Broad Topic Search、机构搜索、Event-driven Search 和双语搜索。

如果没有记录实际查询数量、候选数量和原始帖子 URL 数量，这种表述不算完成检索。

以下行为不符合规则：

- 用当天入选论文的名称代替 Broad Topic Search；
- 只搜索机构名称，如 `OpenAI`、`Anthropic`，却没有组合具体技术主题或账号；
- 把 `X.com/i/trending`、X 官方历史文章、搜索结果摘要当成原始帖子；
- 搜索少量关键词后直接宣布“今天没有 X 热帖”；
- 声称形成了 20—40 条候选，却不记录候选数和原帖 URL 数；
- 只列执行步骤，不展示可核验的检索审计。

Event-driven Search 最多占本轮查询预算的 **30%**。至少 70% 的查询必须独立于当天论文名单。

### 1. 时间窗口

- **优先窗口：过去 24 小时**；
- **召回窗口：过去 48 小时**；
- **零结果回退窗口：过去 72 小时**，仅当 48 小时内没有合格帖子时启用，并将结果标记为“持续发酵／延迟索引发现”。

公共搜索引擎对 X.com 的索引可能延迟，因此允许收录 24—48 小时内首次被高置信发现的高价值帖子，但必须展示真实发布时间。

超过 48 小时的帖子不能描述成“今日新帖”。72 小时回退项必须明确写出原帖日期和为什么现在仍值得追踪。

### 2. 固定执行顺序

X.com 检索必须按照下面的顺序执行，不能先选论文、再把论文名包装成热点搜索。

```text
Phase A：独立 Broad Topic Search
→ Phase B：Researcher / Engineer Search
→ Phase C：中文技术圈搜索
→ Phase D：Event-driven Search
→ 去重、核验、排名
```

#### Phase A：独立 Broad Topic Search

在使用当天论文、模型或项目名称之前，至少执行 **8 个独立主题查询**，其中至少 5 个英文查询、3 个中文查询。

建议按下面的主题桶轮换组合，不得把所有词塞进一个超长 Query：

| 主题桶 | 推荐查询词 |
|---|---|
| Reasoning / TTS | `LLM reasoning`、`reasoning model`、`test-time scaling` |
| RL / Alignment | `RLHF`、`RLVR`、`GRPO`、`on-policy RL`、`distillation` |
| Agent | `coding agent`、`tool agent`、`computer use`、`agent harness` |
| Context / Memory | `context engineering`、`agent memory`、`self-evolving agent` |
| RAG / Long Context | `RAG`、`long context`、`KV cache`、`sparse attention` |
| Inference / Systems | `LLM inference`、`LLM serving`、`GPU inference` |
| Open Models | `open-source LLM`、`open weights model`、`model release` |
| Recommendation | `recommendation system`、`generative recommendation`、`agentic recommendation` |

英文查询示例：

```text
site:x.com "LLM reasoning" benchmark
site:x.com "RLVR" OR "GRPO"
site:x.com "coding agent" harness
site:x.com "context engineering" agent
site:x.com "KV cache" inference
site:x.com "open weights" model
site:x.com "generative recommendation"
```

中文查询示例：

```text
site:x.com 大模型 推理
site:x.com 强化学习 大模型
site:x.com Agent 智能体
site:x.com 上下文工程 长期记忆
site:x.com 长上下文 推理加速
site:x.com 推荐系统 大模型
```

优先保留 URL 路径中包含 `/status/` 的结果。普通 X 主页、趋势页、帮助页或历史 Article 不能计入原始帖子候选数。

#### Phase B：Researcher / Engineer Search

至少执行 **6 个账号／作者方向查询**：

- 至少 3 个官方团队或实验室账号；
- 至少 3 个个人研究者或工程师账号；
- 中外团队都要覆盖；
- 账号应根据近期论文作者、GitHub 项目作者和高质量历史帖子动态更新。

必须使用“账号或作者 + 技术主题”的组合。单独搜索机构名不算完成，例如：

```text
site:x.com OpenAI reasoning
site:x.com Anthropic agent
site:x.com DeepMind inference
site:x.com HuggingFace open model
site:x.com Qwen agent
site:x.com DeepSeek RL
```

如果能够确认账号 Handle，应优先查询该账号的 `/status/` 页面，而不是只搜索机构名称。

#### Phase C：中文技术圈搜索

除 Phase A 的中文 Broad Search 外，至少再执行 **3 个中文作者／社区方向查询**，重点寻找：

- 国内模型团队研究员和工程师的一线解释；
- 论文作者的中文补充；
- 开源模型、推理框架、训练框架的复现和踩坑；
- 推荐系统、Agent、RL 后训练的工程讨论。

不能把中文媒体转载或营销号摘要作为最终候选。

#### Phase D：Event-driven Search

完成前三阶段后，再对当天最重要的 2—4 个论文、模型、项目或 Benchmark 做补充搜索。每个事件选择 1—2 个真正有区分度的查询，不要机械地为每个项目执行全部后缀。

```text
<name> critique
<name> replication
<name> benchmark
<name> limitation
<name> ablation
<name> failure
<name> production
```

Event-driven Search 用于捕捉复现、质疑、失败案例、机制解释和工程反馈，不能替代独立热点发现。

### 3. 最低查询预算与候选阈值

每轮 X.com 检索必须满足：

- **至少 17 个独立查询**：8 个 Broad Topic、6 个账号／作者、3 个中文作者／社区；
- Event-driven 查询另计，但不得超过总查询数的 30%；
- 目标获得至少 **15 条原始搜索结果**；
- 目标获得至少 **8 个去重后的原始 `/status/` URL**；
- 最终正常输出 2—5 条高质量帖子。

如果原始 `/status/` URL 少于 8 个，必须执行一次回退搜索：

1. 更换同义词，如 `reasoning` → `inference-time compute`；
2. 从主题查询切换为具体作者／账号查询；
3. 从 24 小时扩大到 48 小时；
4. 仍为零时才扩大到 72 小时，并明确标记。

“20—40 条候选”是目标，不是可以无证据自报的数字。必须以实际去重结果为准。

### 4. 强制检索审计

日报的 X.com 栏必须包含一个简洁的审计块。即使最终收录了帖子，也必须报告实际检索规模。

推荐格式：

```markdown
<details>
<summary>本轮 X.com 检索审计</summary>

| 项目 | 数量 |
|---|---:|
| Broad Topic 查询 | 8 |
| 账号／作者查询 | 6 |
| 中文作者／社区查询 | 3 |
| Event-driven 查询 | 4 |
| 搜索结果总数 | 26 |
| 去重后的原始 `/status/` URL | 11 |
| 通过硬条件的帖子 | 4 |

主要淘汰原因：超过时间窗口、正文无法读取、只有二手摘要、技术增量不足。

</details>
```

数字必须来自本轮实际执行，禁止填写模板数字。

如果最终没有合格帖子，审计块还必须列出：

- 实际执行的查询数量；
- 获得多少个原始 `/status/` URL；
- 是否执行 48h 和 72h 回退；
- 最常见的淘汰原因。

不再允许只写一段无法核验的“已经完成四路检索”。

### 5. 硬性准入条件

一条帖子进入最终栏目之前，必须能够确认：

1. 原始 X.com `/status/` URL；
2. 作者账号或作者身份；
3. 可以读取和理解的帖子／Thread 技术正文；
4. 发布时间至少核验到日期，并能确认处于相应时间窗口。

时间精度规则：

- 能看到精确时间时，写明时间和时区；
- 只能可靠核验日期时，标记“发布时间仅核验到日期”；
- 无法判断是否落在 72 小时以内时，不进入近期热点栏目。

相比旧规则，**精确到分钟不再是硬门槛**，但时间窗口必须可核验。这样可以减少公共索引没有暴露完整时间造成的误杀。

### 6. 互动量不是硬门槛

Views、Likes、Reposts、Replies 属于热度排序信号，但不是收录的硬性条件。

- 能够可靠获得时，记录近似互动数据；
- 只能看到部分数据时，标记“互动数据部分可见”；
- 无法可靠获得时，可以正常收录，并标记“互动数据未完整核验，按技术信号收录”；
- 严禁猜测或虚构互动量。

### 7. 排名规则

候选帖子按照以下维度综合判断：

```text
Technical Value       40%
Discussion Signal     25%
Novelty               20%
DailyEpoch Relevance  15%
```

$$
S=0.40T+0.25H+0.20N+0.15R
$$

其中：

- $T$：技术信息量；
- $H$：热度与讨论信号；
- $N$：是否提供新的实验、反例、机制或经验；
- $R$：与 LLM／Agent／推荐算法读者的相关性。

高热度营销帖可以低于互动量较小、但包含真实实验或生产经验的技术帖子。

优先收录：

- 新技术洞察和反常识实验；
- Benchmark／Evaluation 质疑；
- 论文作者补充实现细节；
- Production lesson、复现、失败案例和 Ablation；
- 系统性能数据和高质量长 Thread；
- 有证据支持的研究方向争论。

降低优先级：

- 单纯转发论文标题；
- 模型营销文案；
- 没有技术细节的赞叹；
- 新闻媒体二手摘要；
- 纯情绪化争论；
- 只有 Benchmark 截图却没有实验上下文。

### 8. 去重与连续追踪

收录前检查最近 **7 天**日报中的 X.com 栏：

- 同一帖子不得重复收录；
- 同一作者重复相同观点时不重复；
- 出现新实验、新数据、新反驳或重要修正时，可以作为“后续进展”再次出现；
- 连续讨论应说明相较上一日发生了什么变化。

### 9. 每条帖子的固定输出格式

```markdown
### @Author：一句话概括核心观点

**原帖：** [X.com](原始 URL)  
**发布时间：** YYYY-MM-DD HH:mm（注明时区），或“仅核验到日期”  
**热度信号：** 可核验数据／部分可见／未完整核验

**他在讨论什么**

用 2—4 句话解释帖子或 Thread 的核心技术内容。

**为什么值得看**

说明它相对论文、官方博客或常规认知新增了什么信息。

**我的判断**

明确区分：已验证事实、作者个人观察、合理推断、尚未验证的机制解释和局限。
```

### 10. “未找到”的判定标准

只有同时满足下面条件，才允许写“本轮未发现值得高置信收录的 X.com 技术讨论”：

- 完成至少 17 个独立查询；
- Event-driven 查询不超过总量的 30%；
- 完成 48 小时召回；
- 原始 `/status/` URL 少于 8 时已经执行回退搜索；
- 零合格结果时已经执行 72 小时延迟索引回退；
- 已在审计块中报告真实查询数、候选数和淘汰原因。

并附上限定说明：

> 公共 Web Search 对 X.com 的实时索引覆盖有限，因此这表示本轮无法高置信核验，不代表 X.com 当天不存在相关热门讨论。

---

## Markdown 结构规范

### Front Matter

每篇文章必须包含：

```yaml
---
title: "每日 AI 技术简报｜YYYY-MM-DD"
date: YYYY-MM-DD
categories: [DailyEpoch]
tags: [AI, LLM, Agent]
permalink: /DailyEpoch/YYYY-MM-DD/
---
```

### 正文层级

- 正文只保留一个文章标题；布局已经显示页面标题时，正文 H1 可省略。
- 开头使用一段简短的 `> **今日主线：** ...`，不要再写与“今日核心判断”高度重复的长摘要。
- H2 用于日报主要章节；H3 用于固定分析维度。
- 论文或项目章节优先使用：
  - `### 发生了什么`
  - `### 关键结果`（有三项以上可比较数据时）
  - `### 为什么重要`
  - `### 可信度与局限`
  - `### 最值得继续追踪`
- 保持以下结尾章节：
  - `## 今日值得收藏的代码 / 学习资源`
  - `## X.com｜近期高信号技术讨论`
  - `## 今日最值得花 30 分钟阅读的一项`
  - `## 今日可立即实践的一件事`
  - `## 参考来源`

## 可读性规范

- 每个主主题在标题后优先给出一行 `> **一句话结论：** ...`。
- 单段尽量控制在 3—5 句；复杂论证拆成短段，不堆成大块文字墙。
- 三项及以上可比较的实验数据优先用 Markdown 表格。
- 列表只用于真正并列的信息，避免把完整文章写成几十条碎片化 Bullet。
- 重要判断使用引用框或粗体，不使用展示公式充当排版强调。
- 仅在表达真实数学关系时使用 LaTeX。

## LaTeX 与代码规范

- 行内公式使用 `$...$`。
- 块级公式使用独立的 `$$...$$`，前后保留空行。
- 不使用 `\(...\)` 或 `\[...\]` 作为最终 Markdown 分隔符。
- 概念性表达应写成普通正文或引用框，而不是 `\text{...}` 展示公式。
- 美元价格中的 `$` 必须转义为 `\$`。
- 代码围栏使用标准三反引号和语言名，不保留 ChatGPT 临时 `id="..."` 属性。
- 公式分隔符、代码围栏必须成对闭合。

## 来源与引用规范

- 正文和“参考来源”均使用普通 Markdown 链接：`[标题](原始链接)`。
- 优先链接论文原文、官方技术报告、官方代码仓库、官方博客或原作者 Thread。
- 不使用搜索结果页、内容农场或二手搬运作为核心来源。
- 不保留 `cite...`、`navlist`、内部引用 ID 等 ChatGPT UI 标记。
- 无法准确恢复原始链接时，明确说明“未能高置信核验”，不要猜测性补链。
- X.com 趋势页、Grok 自动摘要和媒体二手摘要只能作为发现线索；技术事实必须回到原帖或主来源核验。

## 内容质量检查

发布前必须检查：

1. 标题、日期、文件名和 permalink 一致；
2. 开头摘要与“今日核心判断”没有大段重复；
3. 每个主主题都包含事实、重要性、局限和追踪点；
4. 事实、合理推断、不确定性和个人判断明确区分；
5. 表格、列表、公式和代码块能在 Jekyll/Kramdown 中正常渲染；
6. 没有内部 Citation 标记或失效占位链接；
7. 所有原始来源链接与正文主题准确对应；
8. “今日实践”可以在有限时间内执行，并包含明确评估指标与停止条件；
9. X.com 栏包含实际检索审计，而不是只声称执行了检索；
10. X.com Event-driven 查询没有超过总查询量的 30%。

## 推荐模板

```markdown
> **今日主线：** Agent Memory · Autoresearch · Test-Time Scaling · Recommendation

## 今日核心判断

1. **判断一。** 简要解释。
2. **判断二。** 简要解释。

---

## 1. Paper / Project：一句中文结论

> **一句话结论：** 该工作真正解决的问题和适用边界。

### 发生了什么

正文。

### 关键结果

| 指标 | Baseline | New |
|---|---:|---:|
| ... | ... | ... |

### 为什么重要

正文。

### 可信度与局限

正文。

### 最值得继续追踪

正文。
```