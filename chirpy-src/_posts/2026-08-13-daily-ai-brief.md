---
title: "每日 AI 技术简报｜2026-08-13"
date: 2026-08-13
categories: [DailyEpoch]
tags: [AI, LLM, Agent, Autoresearch, Memory, Recommendation]
permalink: /DailyEpoch/2026-08-13/
---

# 每日 AI 技术简报｜2026-08-13

最新 arXiv 批次是 **8 月 12 日**：cs.AI 211 篇、cs.CL 95 篇、cs.LG 164 篇、cs.IR 22 篇；分类存在大量交叉收录，不能直接相加。今天高信号内容相当集中：**Agent 长期记忆的主要问题正在从“忘记”转向“记得太多却忘了为什么”；Autoresearch 的瓶颈可能不是不会想新方案，而是大量计算浪费在重复踩环境坑；Test-Time Scaling 开始从“继续想”转向“检索相似推理轨迹”；搜索 Agent 的 Memory 需要依赖关系和可回滚性；推荐系统则出现了一篇很值得警惕的评测审计——完全相同的模型分数，仅换 tie-breaking，HR@1 可以从 0.97 变成接近 0。**

## 今日核心判断

- **长期 Agent 的 Memory/Skill 不应该只保存“该做什么”，还应保存“为什么当初要这么做”。**没有 rationale / provenance，规则几乎只有新增路径，没有可靠删除路径。
- **Autoresearch 的第一性瓶颈可能是 useful-compute ratio。**同一个模型，与其增加搜索分支，不如先阻止所有分支重复解决同一个 CUDA、API、库版本或数据格式问题。
- **“思考更久”不是一个完整的 Test-Time Scaling 策略。**困难题上，与其反复 self-reflect，不如在 reasoning trajectory 中动态检索结构相似的已解问题。
- **Agent Memory 的正确数据结构可能更接近版本控制图，而不是摘要字符串。**证据被推翻后，需要知道哪些结论依赖它，并一起失效。
- **推荐模型的离线指标首先是软件系统输出，其次才是模型能力。**排序稳定性、数值精度、候选顺序和 tie-breaking 都可以制造“模型进步”。今天的 RecSys 论文给出了一个极端但很有教育意义的案例。

---

## 1. Catastrophic Remembering：CLAUDE.md 为什么只会越来越长？

### 发生了什么

《Why Does CLAUDE.md Keep Growing?》追踪了 **1,867 个 GitHub 仓库、247,694 条指令生命周期**。作者发现 agentic context file——包括 `CLAUDE.md`、`AGENTS.md`、`copilot-instructions.md`——在生命周期内指令数量平均增长 **226%**；排除大规模 rewrite 后，每次 commit 平均净增约 4.9 条指令。更有意思的是，指令越老反而越不容易被删除：删除 log-hazard 对年龄的斜率为 −0.032/commit。

而所谓“删除”大部分也不是真正判断某条规则已经没用：约 **77.3% 的 instruction death 来自整体 rewrite 或迁移**。一次大 rewrite 后，文件会缩到原来的约 59.5%，但 10 个 commit 后又恢复到约 91.5%，而且之后增长得更快。

作者把机制称为 **catastrophic remembering**。新增一条：

```text
Always run foo before bar.
```

很便宜；半年之后想删它，却已经没人知道：

> 当时是哪次事故导致这条规则出现？
> 它防的是哪个 failure mode？
> 现在底层条件是否已经变化？

于是最安全的操作变成：**不删。**

论文提出的解决办法非常朴素：给 Agent 指令增加不会传给 executor 的 **comment/rationale channel**。在其 inverted-IFEval 控制实验中，保存“为什么加入这条指令”的 comment，将 excess instructions 从 +211.3% 压到 +1.4%，即消除了 99.3% 的冗余增长；在 WildIFEval replication 中，指令遵循最高提高 11.6 个百分点（相对 +23.1%）。

### 为什么重要

这和最近几天看到的 Skill contamination / Skill gate 其实是同一个更深的问题：

$$
\text{长期经验系统}
\neq
\text{不断 append 文本}
$$

真正应该存的是：

$$
\boxed{
\text{Rule}
+
\text{Rationale}
+
\text{Trigger}
+
\text{Evidence}
+
\text{Scope}
+
\text{Invalidation Condition}
}
$$

否则 Agent 具备的是**写入能力**，而不是**维护能力**。

论文还给出一个理论化解释：如果没有每条规则的来源信息，在存在冗余交互的情况下，作者模型中的“诚实删除审计”最坏需要检查规则子集，复杂度可达到 $O(2^{|D|})$；保存写入时的 rationale 则可以极大减少这种逆向归因成本。这个复杂度结论依赖论文的形式化假设，不应该解读为真实 CLAUDE.md 删除操作存在普适计算复杂度定理。

### 可信度与局限

**实证部分强于一般理论结论。**1,867 个仓库的纵向数据量相当可观，且作者又用可控环境做了因果实验；但 GitHub 观察数据本身仍不能完全排除不同组织习惯等未观测因素。所谓“无限增长”是模型与观测趋势的表述，不代表每个项目真的数学意义上无限增长。WildIFEval 也测的是 instruction following，并非真实 SWE-Bench 工程产出。

### 最值得继续追踪

我更关心的不是“以后 CLAUDE.md 加 comment”这么表层，而是 **Agent Memory 是否会开始出现真正的 provenance schema**：

$$
rule\_id,
\quad
created\_because,
\quad
evidence,
\quad
scope,
\quad
depends\_on,
\quad
expires\_when
$$

如果没有这层元信息，自动 Skill Evolution 最终大概率仍会重演同一类 ratchet。

---

## 2. Recovering Wasted Compute：Autoresearch Agent 可能并不缺“研究能力”，而是在重复交学费

这是今天我最推荐深入读的一篇。

### 发生了什么

作者分析 ML Autoresearch Agent 后，发现大量计算并没有投入模型创新，而浪费在四类事情上：

1. 不同 search branch 反复遇到并修同一个 runtime bug；
2. 明明还有大量预算，却过早停止 HPO；
3. tree search 名义上有很多 branch，实际探索多样性很低；
4. Agent 做了 EDA，却没有把发现转化成后续模型决策。

其中最简单的 intervention 是一个 **global debug consultant**：任何分支发现的环境事实，例如某库版本、deprecated API、合法参数、container constraint，都同步给所有其他分支，而不是让每个 branch 自己重新发现。

保持 backbone 为 GPT-5-mini、固定两小时计算预算，在 9 个 MLE-bench competition × 10 seeds 上，AIDE 的 gold medal 从 **22 → 38**，17 个无法生成有效 submission 的 run 全部消失，valid submission 从 81% → 100%；ML-Master 的 gold 从 18 → 29。

更能解释机制的是内部数据：

$$
\text{重复遇到已知 bug}:
46.0\%\rightarrow7.8\%
$$

$$
\text{可正常执行的 search node}:
54.7\%\rightarrow79.0\%
$$

第一次得到 valid submission 的中位 step 则：

$$
6\rightarrow0
$$

也就是说，模型不是突然“更聪明”，而是终于不用每个 branch 都重新学习 Python 环境。

作者还显式提示 Agent 更认真地做 HPO。在 9 个任务中的多数任务有收益，其中一些任务的 graded score 提升非常大，例如 S5E8 约 +0.38、S5E12 约 +0.218，但 GNSS 上略有下降，说明“更多 HPO”也并非无条件有效。

### 为什么重要

现在 Autoresearch 很容易陷入一个错误优化目标：

$$
\text{每小时实验数量}
$$

真正应该优化的可能是：

$$
\boxed{
\text{Useful Compute Ratio}
=
\frac{
\text{用于有效假设检验的计算}
}{
\text{总计算}
}
}
$$

1000 个实验并不比 100 个实验好，如果其中 600 个在重复解决：

```text
package version mismatch
missing column
wrong metric direction
unsupported parameter
OOM
```

这也解释了为什么单纯把 tree-search branch 数量拉大可能没有价值：**知识如果不能跨 branch 传播，并行只会并行重复犯错。**

### 可信度与局限

这篇实验控制比较干净：同一 backbone、相同任务和固定计算预算，9 个 competition、10 个 seed。最终结果使用 benchmark 的实际 OOS score，而不是仅靠 LLM Judge。

但范围也很明确：主要是结构化 ML / MLE-bench 风格任务，runtime constraint 容易共享。Coding Agent 中一个 branch 的 bug 可能本来就是它自己改代码产生的，不应该全局传播；研究假设更不能像 Python 版本信息一样直接共享。因此应区分：

$$
\text{Global environment fact}
$$

和：

$$
\text{Branch-local hypothesis}
$$

否则 global memory 本身会成为污染源。

### 最值得继续追踪

如果这条线继续发展，我更想看 Autoresearch benchmark 开始统一报告：

- duplicate experiment rate；
- repeated known-failure rate；
- fraction of compute spent on valid experiments；
- time-to-first-valid-result；
- HPO budget utilization；
- best-so-far regret。

比单独报告最终 benchmark score 信息量大得多。

---

## 3. ThinkRetrieve：Test-Time Scaling 与其“再想一次”，不如找一个真正相似的已解问题

### 发生了什么

ThinkRetrieve 针对 sequential TTS 的一个常见失败：

$$
\text{错误推理}
\rightarrow
\text{Wait, think again}
\rightarrow
\text{沿着错误假设继续想更久}
$$

它在每一个 reasoning step 后，让模型生成当前 intermediate answer，再用：

$$
(\text{原问题},\text{当前中间答案})
$$

去一个 solved-example corpus 中检索结构相似的题目及完整推理过程，把该 exemplar 插入下一轮 thinking trace。

这里检索的不是事实知识：

> “圆周率是多少？”

而是 procedure：

> “这个问题和以前哪类解题路径类似？”

在 1.5B–8B 的五个 reasoning model 上，GSM8K、MATH-500、AIME 2025 均优于普通 sequential TTS。最明显的是 Qwen3-1.7B 的 AIME 2025：

$$
22.2\%\rightarrow35.6\%
$$

而 DeepSeek-R1-Distill-Qwen-1.5B 在 GSM8K 上，普通 TTS 随预算增到约 22K token 时从约 83% **反而跌到 52%**，ThinkRetrieve 仍约 84%。

有个实验设计值得肯定：retrieved exemplar 的 token 也计入同一个 thinking budget，因此收益不是偷偷给了额外 context budget。作者还针对 NuminaMath corpus 做 exact-match 和 embedding-similarity 去污染，并报告 retained neighbor 的最大 similarity 未超过其 0.90 阈值。

### 为什么重要

它提示 Test-Time Scaling 其实有至少三条独立轴：

$$
\text{更多生成}
$$

$$
\text{更好的验证}
$$

$$
\boxed{\text{更好的外部推理先验}}
$$

过去大家常把 compute 全砸在第一项。

而 ThinkRetrieve 更像案例推理：

$$
\text{当前思路}
\rightarrow
\text{找到相似成功轨迹}
\rightarrow
\text{重新校准下一步}
$$

这和 Agent Skill Retrieval、experience replay、case-based reasoning 很可能最终会汇流。

### 可信度与局限

论文结果主要来自**数学题和 SciQ**，example corpus 对数学题尤其友好。AIME 只有 30 题，即使做三 seed，大幅百分比变化的统计稳定性也需要谨慎解释。

更关键的是，这并不证明“动态检索 reasoning trace 普遍优于自我反思”。如果任务没有结构化、可复用的已解案例库——例如开放科研、产品设计、复杂代码重构——检索到的 exemplar 可能反而 anchor 模型到错误范式。

### 最值得继续追踪

真正值得试的是：

$$
\text{Retrieve Successful Trajectory}
+
\text{Retrieve Failed Trajectory}
$$

不仅告诉模型“类似问题怎么做对”，还告诉它“类似情况下什么路径曾经失败”。这会把 TTS 和 Agent Experience Memory 真正接起来。

---

## 4. ReTree：搜索 Agent 的 Memory 应该支持“git revert”，而不只是不断改摘要

### 发生了什么

ReTree 把 Search Agent 的历史组织成 tree。每个节点保存：

- bounded state summary；
- evidence；
- revision history；
- evidence 的引入节点和依赖关系。

如果后续搜索发现旧事实错误，系统不是简单地：

```text
memory["fact"] = new_fact
```

而是回溯到旧事实最早进入 reasoning tree 的位置，替换 evidence、重新生成相关 summary，并 prune 依赖错误事实发展的 downstream branch。

在 Qwen3-8B、相同 Google Search API、每题最多 8 次搜索的设置下，2,149 道题上：

- Full-Trajectory ReAct：judge accuracy 30.1%，EM 20.6%；
- ReportMemory：40.9% / 22.0%；
- FlatUpdate：40.4% / 25.5%；
- **ReTree：44.0% / 28.0%**。

相对 Full ReAct，pooled judge accuracy +13.9pp，EM +7.4pp；相对更公平的 FlatUpdate，四个数据集均高 2.2–4.7pp。最大 per-step policy context 也从 Full ReAct 的 1,677 chars 降到 1,190。

### 为什么重要

长期 Agent 的状态很可能需要从：

$$
\text{facts}
$$

升级为：

$$
\boxed{
\text{facts}
+
\text{provenance}
+
\text{dependencies}
}
$$

因为：

> “X 是 CEO。”

不只是一个字符串。

后面可能已经基于它产生：

- X 的履历搜索；
- X 的公司战略判断；
- X 的采访引用；
- 最终报告中的三个结论。

如果第一条事实被更新，仅仅覆盖 `CEO=X→Y` 并没有修复后面三个已经被污染的 inference。

### 可信度与局限

实验统一 backbone、search backend 和搜索预算，FlatUpdate 是一个很好的 mechanism-matched baseline。

但只有 **一个 seed**；主 Accuracy 又由 GPT-5 Judge 评估，虽然同时有 EM。Conflict Judge 本身也是系统潜在故障点：false negative 会保留污染，false positive 会错误 prune 有效分支。论文也明确承认这一点。

### 最值得继续追踪

我认为最终形态不是“tree memory”这个具体结构，而是：

$$
\text{dependency-aware invalidation}
$$

它应该被应用到：

- Deep Research citation graph；
- Coding Agent assumptions；
- SQL/Data Agent derived variables；
- Autoresearch experiment conclusions；
- 用户长期 profile。

---

## 5. SkillZip：Skill 不一定要靠重新跑几十个任务才能压缩

### 发生了什么

SkillZip 针对另一个越来越明显的问题：Self-Evolving Agent 的 Skill 文本自己也会膨胀。

作者观察到，SkillOpt 经过 5 轮 evolution 后，在 BFCL-V4、LiveMath 和 Spreadsheet 上 Skill 长度分别达到最初约 **5.6×、3.1×、6.7×**，平均约 5.2×。

SkillZip 不直接问：

> “删掉这句话，benchmark 会不会下降？”

而是先把 Skill 解构成 typed contract，例如：

- requirements；
- scopes；
- guards；
- tool constraints；
- output fields；
- workflows；

然后做 Minimum-Description-Length 风格的结构合并，同时要求抽取出的 contract 全部得到覆盖。

三个模型、三个 benchmark 上，SkillZip 平均压缩 **31.2%**；task macro score 为 0.577，而未压缩 evolved skill 为 0.570，SkillReducer 为 0.544。它在 compression 阶段不访问 task、rollout 或 verifier；SkillReducer 则需要 40–80 次 validation rollout。平均 compression time 286 秒，约快 3.5×。

### 为什么重要

Skill 治理现在逐渐出现两条互补路线：

$$
\text{Behavioral Verification}
$$

和：

$$
\text{Structural Compression}
$$

前者可靠但贵；后者便宜但依赖结构抽取质量。

最合理的系统可能不是二选一，而是：

$$
\text{频繁 SkillZip}
\rightarrow
\text{低频 behavioral regression gate}
$$

而不是每改一句 Skill 都重新跑 80 条 trajectory。

### 可信度与局限

这里的 **“evaluation-free”容易被误读。**

它只是说 compression 时**不用 benchmark rollout/verifier**；仍然需要 LLM 做结构抽取和 consolidation。更重要的是，所谓 hard coverage 只能保证：

> 被成功抽取到 typed contract 中的 requirement 不被删除。

如果一开始 parser 没识别出一条隐含规则，它依然可能被压掉。因此它不是行为等价性的形式证明。

### 最值得继续追踪

真正有价值的是：

$$
\text{Compression Ratio}
\quad vs.\quad
\text{Rare-but-critical Rule Recall}
$$

尤其是只在 0.1% 请求触发的 safety guard，不能因为平均 benchmark 不掉分就被合并掉。

---

## 6. 推荐系统｜Tie-Breaking Illusion：完全一样的预测分数，可以得到完全不同的 SOTA

这是今天推荐方向最应该看的论文。

### 发生了什么

RecSys 2026 论文《Are We Really Making Progress in Group Recommendation?》发现，一批 Group Recommendation 实现存在一个很隐蔽的组合问题。

正常 BPR：

$$
-\log\sigma(s^+-s^-)
$$

部分代码却先做：

$$
\tilde s=\sigma(s)
$$

再：

$$
-\log\sigma(\tilde s^+-\tilde s^-)
$$

额外 sigmoid 将 score 动态范围压缩，在有限数值精度下制造大量**完全相同的 top score**。与此同时，这些评测代码又先把 held-out positive 放在 candidate list 最前，再调用 deterministic sort；发生 tie 时，positive 因原始位置获得系统性优势。

作者做了一个非常干净的诊断：**模型和所有 prediction score 完全不变，只改变正样本在 tied block 中取第一还是最后。**

CAMRa2011 上：

- AlignGroup HR@1：0.7890 → **0.0028**；
- DHMAE HR@1：0.9717 → **0**；
- ITR HR@1：0.6517 → **0.0248**。

对应降幅分别约 99.65%、100%、96.19%。

更严谨的 tie-aware evaluator 不随机模拟，而是直接计算 uniform random tie-breaking 下 HR@K / NDCG@K 的**精确期望**。使用同一 checkpoint 和同一批 predictions 重算后，部分已发表方法的优势大幅缩水，甚至相对排名发生变化；例如 CAMRa2011 上 DHMAE 原协议 HR@1 为 0.9782，tie-aware 只有 0.0002。

### 为什么重要

这是一个很好的提醒：

$$
\boxed{
\text{Offline Metric}
=
f(
\text{Model},
\text{Candidate Construction},
\text{Numerics},
\text{Sorting},
\text{Metric Implementation}
)
}
$$

绝不是只由 Model 决定。

在工业推荐中类似问题很多：

- stable sort；
- FP16/FP32 score quantization；
- padding candidate 的默认分；
- equal score 下 item_id secondary key；
- 正负样本构造顺序；
- sampled negative 是否重复；
- masking 顺序。

0.1% 的指标涨幅，如果没有先把这些 evaluator artifact 清掉，意义可能比想象中脆弱。

### 可信度与局限

这篇论文的证据相当强：作者重训了五种代表方法，在 CAMRa2011 / Mafengwo 上做三 seed，并且 original/tie-aware 结果都基于**同一份预测值**，因此把模型训练差异完全隔离掉。论文已被 RecSys 2026 接收。

但结论范围必须收住：这不是说“最近 Group Recommendation 研究都是假的”，而是**受额外 pre-BPR sigmoid + 特定 deterministic tie-breaking 影响的实现**存在严重偏差；例如论文仓库明确指出 GroupIM、HHGR、CubeRec 并没有这一实现问题。

### 最值得继续追踪

我建议以后所有 ranking offline report 至少增加：

$$
\text{Top-score Tie Rate}
$$

$$
\text{Mean Tie Block Size}
$$

以及随机打乱 candidate initial order 后的 metric variance。

如果一个模型：

$$
\text{shuffle candidate order}
\Rightarrow
\Delta NDCG\gg0
$$

它首先有 evaluator 问题，而不是模型问题。

---

## 今日值得收藏的代码 / 学习资源

**TieAwareGroupRec 官方仓库**今天值得直接 clone。它不仅有 tie-aware HR/NDCG evaluator，还包含 ConsRec、AlignGroup、DHMAE、ITR、DGGVAE 和多种 baseline 的 patched reproduction，以及 temperature-scaled BPR 对照。作者特意保持 FP32，因为数值精度本身会影响 tie inflation；这是一个很适合拿来审计自家 ranking evaluator 的小工具箱。

**SKILLER**则值得关注“强模型生成 Skill → 小模型执行”的路线。它把 small-model agent 当 RL environment，由更强模型担任 actor/critic，通过自然语言传递优化信号；Qwen3.5-9B / 4B 在五个 benchmark 上相对若干 Skill generation/evolution baseline 报告了 4.3–20.4pp 和 1.8–13.3pp 的绝对提升，并已公开项目代码。需要注意：它的执行模型虽然小，但训练环仍依赖强模型，所以不能简单理解为“低成本小模型自我进化”。

---

## X.com 近 24 小时技术信号

**今天没有足够可靠的数据可列“近 24 小时技术热帖榜”。**

我分别按今天几篇论文的精确标题和关键词检索 X，精确标题没有返回可核验结果；扩大到 `CLAUDE.md / autoresearch / agent memory / RecSys tie-breaking` 后，公开网页索引主要返回的是 **4–5 个月前**的帖子，而不是 8 月 12–13 日的新讨论，例如 CLAUDE.md 讨论和 autoresearch-RL 帖子均明显过期。

因此今天不把“能搜到的旧帖子”冒充 24 小时热度。值得在 X 站内手动追的技术关键词是 **`catastrophic remembering`、`autoresearch debug consultant`、`ThinkRetrieve`、`tie-aware recommendation`、`ReTree memory`**。目前无法可靠比较它们的当天浏览、点赞或转发量。

---

## 今日最值得花 30 分钟阅读的一项

### Recovering Wasted Compute in Autoresearch Agents

我今天优先选它，而不是 Catastrophic Remembering。

原因是它对做 **LLM/推荐算法自动实验 Agent** 有非常直接的工程意义：当前大家很容易盯着“模型能不能产生更好的研究 idea”，却忽略了：

$$
\boxed{
\text{研究 Agent 的能力上限}
\neq
\text{模型智力上限}
}
$$

很可能先受制于：

$$
\text{实验预算利用率}
\times
\text{知识跨分支复用率}
\times
\text{有效实验比例}
$$

建议 30 分钟这样看：

**前 6 分钟**看四类 wasted compute，判断自己的 Autoresearch workflow 有没有同样问题。

**接下来 8 分钟**重点看 Debug Consultant。不要只记 22→38 gold，更值得看：

$$
46\%\rightarrow7.8\%
$$

的重复 bug rate。

**再 8 分钟**看 HPO intervention。特别注意 GNSS 上出现负收益，说明显式要求“多调参”本身也会浪费预算；关键仍是 budget allocation，而非 HPO 越多越好。

**最后 8 分钟**看 case study：环境问题消除后，Agent 才开始把 compute 用在 ensemble、calibration、problem reformulation 等真正的建模工作。

---

## 今日可立即实践的一件事

给你的任何 **Autoresearch / AutoML / LLM 后训练实验 Agent** 加一个 **Global Debug & Constraint Ledger**。

不要保存成一段不断增长的自然语言 Memory，而是结构化为：

```text
constraint_id
signature
scope
observed_failure
validated_fix
why_it_exists
evidence
environment_version
confidence
invalidated_when
```

例如：

```text
signature:
transformers>=X + flash_attn=Y causes kernel error

scope:
all training branches on image abc123

validated_fix:
use attention_impl="sdpa"

why_it_exists:
3 independent branches failed with identical stack trace

invalidated_when:
container image changes
```

每一个新 search branch 启动前，只注入与当前环境匹配的高置信 constraint。遇到 runtime error 时，先做 signature lookup：

$$
\text{Known Error}
\Rightarrow
\text{直接采用 validated fix}
$$

而不是：

$$
\text{Known Error}
\Rightarrow
\text{重新让 LLM debug 一次}
$$

然后开始记录四个指标：

$$
\text{RepeatBugRate}
=
\frac{
\text{再次遇到已解决 bug 的次数}
}{
\text{全部 runtime bug 次数}
}
$$

$$
\text{ValidExperimentRate}
=
\frac{
\text{真正完成训练并产生可比较指标的实验}
}{
\text{总实验数}
}
$$

以及 **Steps-to-First-Valid** 和 **Compute-on-Valid-Experiments**。

做一个完全同模型、同 token、同实验时间预算的 A/B：

$$
A:\ \text{branch-local memory}
$$

$$
B:\ \text{global constraint ledger}
$$

如果 B 只是“跑了更多实验”但最终 best-so-far 不变，说明瓶颈不在 debug；如果像论文一样，RepeatBugRate 大幅下降、ValidExperimentRate 上升，同时 best held-out metric 也提高，才说明你真正回收了 wasted compute。

这里我会额外吸收今天 CLAUDE.md 那篇论文的一点：**每条 constraint 必须保存 `why_it_exists` 和失效条件。**否则这个 Ledger 运行半年后，又会从“共享知识库”退化成另一个没人敢删的 CLAUDE.md。

---

## 参考来源

1. [Why Does CLAUDE.md Keep Growing? Catastrophic Remembering in Agentic Coding](https://arxiv.org/abs/2608.11095)
2. [Recovering Wasted Compute in Autoresearch Agents](https://arxiv.org/abs/2608.10424)
3. [ThinkRetrieve: Retrieval-Augmented Reasoning Traces for Test-Time Scaling](https://arxiv.org/abs/2608.10928)
4. [Self-Correcting Long-Horizon Search Agents via Tree-Structured Memory](https://arxiv.org/abs/2608.10676)
5. [SkillZip: Evaluation-Free Skill Compression for Self-Evolving Agents by Discovering Reusable Structure](https://arxiv.org/abs/2608.11079)
6. [Are We Really Making Progress in Group Recommendation? Unmasking the Tie-Breaking Illusion](https://arxiv.org/abs/2608.11190)
7. [TieAwareGroupRec 官方代码](https://github.com/songduoma/TieAwareGroupRec)
8. [SKILLER: Language-Level Reinforcement Learning for Reusable Skill Extraction in Small Language Models](https://arxiv.org/abs/2608.10538)
9. [SKILLER 官方代码](https://github.com/DANG-ai/SKILLER)
