---
title: "Looped Transformer 深度调研：把模型深度变成可伸缩的计算轴"
date: 2026-09-04 00:00:00 +0800
categories: [技术调研]
tags: [LLM, Transformer, Looped Transformer, Latent Reasoning, Test-Time Compute, Model Architecture]
permalink: /reports/looped-transformer/
math: true
toc: true
---

Looped Transformer（循环式 Transformer，也常被称为 Recursive Transformer、Depth-Recurrent Transformer）正在从一个反复出现的研究想法，成长为一条相对完整的架构路线。它最吸引人的地方，是把传统 Transformer 中“增加深度必须增加参数”的绑定关系拆开：同一组层可以重复运行多次，用更多计算换取更深的有效网络，而不同比例地增加权重内存。本文的核心判断是：**Looped Transformer 已经证明了显著的参数效率潜力，但还没有证明它普遍拥有更好的计算效率；更多循环并不必然更强；所谓 latent reasoning 也不能自动等同于可解释的隐式思维链。**

## 结论先行

1. **Looped Transformer 最确定的优势是参数效率。** 同一组参数跨深度复用，使有效深度可以远大于物理参数深度；对显存受限、边缘部署和小模型尤其有吸引力。
2. **它并不天然节省 FLOPs 或延迟。** 循环次数增加时，顺序计算通常线性增加；如果没有并行循环、提前退出或专门 Kernel，权重变少并不等于推理更快。
3. **循环次数是一个需要训练和校准的超参数，不是免费的 Test-Time Scaling 旋钮。** 多篇工作都发现收益会饱和、振荡甚至回退；LoopCoder-v2 的三次及以上循环就明显弱于两次循环。
4. **现代方法的关键不是“简单重复同一层”，而是让共享参数在不同循环承担不同功能。** Loop embedding、时间条件、Layer-wise LoRA、Hyper-Connection、MoE、输入锚定和深监督都在恢复被权重共享压缩掉的功能多样性。
5. **Latent reasoning 的证据正在增加，但“循环隐藏状态 = 隐式 CoT”仍然是过度解释。** 一些模型能随循环提升推理表现，也有工作能从 latent 中读出中间步骤；另一些严格 probing 则只发现有限的可解释思维链证据。
6. **它更可能先成为混合架构中的一个组件，而不是立刻替代标准 Transformer。** 最现实的形态是：少量独立 Prelude/Coda 层 + 可循环 Core + 自适应退出 + KV 压缩或共享，而不是把完整模型所有层简单绑成一个循环。

---

## 1. 为什么这个旧想法在 2026 年突然升温

### 1.1 它并不是 2026 年才出现

2018 年的 [Universal Transformers](https://arxiv.org/abs/1807.03819) 已经把 Transformer 层沿深度方向重复执行，并加入按位置动态停止机制。它试图结合 Transformer 的并行序列处理与循环网络的迭代归纳偏置，在算法任务、语言理解和机器翻译上展示了潜力。

2023 年的 [Looped Transformers are Better at Learning Learning Algorithms](https://arxiv.org/abs/2311.12424) 又给出一个很有影响力的结果：在多类 in-context data-fitting 任务中，循环模型可以用不到标准 Transformer 10% 的参数达到相近表现。这强化了一个直觉：**很多推理过程本来就是重复执行某个更新规则，循环结构可能比堆叠完全不同的层更贴近算法本身。**

真正让这条路线进入大模型语境的，是 2025 年前后的两类工作：

- [Huginn / Scaling up Test-Time Compute with Latent Reasoning](https://arxiv.org/abs/2502.05171) 将可递归深度模型扩展到 3.5B 参数和 800B 训练 token，并展示了测试时增加递归深度带来的推理收益；
- [Ouro / Scaling Latent Reasoning via Looped Language Models](https://arxiv.org/abs/2510.25741) 从预训练阶段直接训练 Looped Language Model，在 1.4B 和 2.6B 规模上把循环、深监督和学习式深度分配组合起来。

到了 2026 年，研究重点明显从“循环能不能工作”转向六个更工程化的问题：**如何稳定训练、如何让不同循环分工、如何动态退出、如何降低顺序延迟、如何控制 KV Cache、如何验证 latent reasoning 到底学到了什么。**

### 1.2 最近的 X 热议里混入了未经证实的模型传闻

2026 年 9 月初，X 上出现了一批围绕“OpenAI 某内部模型可能采用 recurrent depth / looped architecture”的讨论。代表性帖子包括 [@steph_palazzolo](https://x.com/steph_palazzolo/status/2094954680765829533)、[@bindureddy](https://x.com/bindureddy/status/2094985749657723272) 以及持怀疑态度的 [@max_paperclips](https://x.com/max_paperclips/status/2094973170046693712)。

这里必须把两件事分开：

- **事实：** Looped Transformer 在过去一年确实形成了密集论文簇，并且多个开放模型和代码项目可以核验；
- **未证实说法：** 截至本文发布，公开的 OpenAI 官方论文、模型卡或技术博客并未确认相关内部模型采用了哪一种循环架构。

因此，X 上的传闻可以解释“为什么社区突然集中讨论”，却不能作为 Looped Transformer 有效性的技术证据。本文以下结论只建立在公开论文、代码和可复核实验上。

---

## 2. Looped Transformer 到底改变了什么

### 2.1 标准 Transformer：深度与参数一起增长

普通深层 Transformer 可以写成：

$$
h_{l+1}=F_{\theta_l}(h_l),\qquad l=0,1,\ldots,L-1
$$

每一层有独立参数 $\theta_l$。增加层数 $L$，通常同时增加：

- 存储参数；
- 权重读取带宽；
- 前向 FLOPs；
- KV Cache 层数；
- 训练激活与优化器状态。

### 2.2 Looped Transformer：把一段网络重复运行

一个典型的 Looped Transformer 可以写成：

$$
z_0=P(x)
$$

$$
z_{r+1}=G_{\theta}\left(z_r,\,P(x),\,e_r\right),\qquad r=0,1,\ldots,R-1
$$

$$
y=C(z_R)
$$

其中：

- $P$ 是只运行一次的 Prelude；
- $G_\theta$ 是重复运行的共享 Core；
- $C$ 是只运行一次的 Coda；
- $e_r$ 是循环编号、时间或步长条件；
- $R$ 是循环次数。

有效深度近似为：

$$
D_{\text{eff}}=D_P+R\cdot D_G+D_C
$$

而存储参数近似为：

$$
P_{\text{stored}}=P_P+P_G+P_C
$$

不会随 $R$ 线性增长。但计算量通常仍然是：

$$
C_{\text{forward}}\approx C_P+R\cdot C_G+C_C
$$

这就是它最重要的交换关系：

> **用时间维度上的重复计算，替代空间维度上的独立权重。**

### 2.3 一个容易被忽略的事实：参数效率不等于计算效率

假设一个 12 层独立 Transformer 与一个 3 层 Core 循环 4 次的模型具有相同有效深度。后者可能只存储约四分之一的 Core 权重，但它仍需要完成接近 12 层的矩阵计算，而且循环之间存在数据依赖，难以像独立请求那样完全并行。

因此评价 Looped Transformer 至少要同时报告：

| 维度 | 应报告指标 |
|---|---|
| 参数效率 | Stored parameters、权重显存、量化后大小 |
| 计算效率 | 训练 FLOPs、推理 FLOPs、GPU-ms/token |
| 延迟 | TTFT、单 token decode latency、P50/P99 |
| 吞吐 | tokens/s、batch capacity、continuous batching 利用率 |
| 内存 | 权重、激活、KV Cache、峰值 HBM |
| 质量 | Perplexity、下游任务、固定计算预算下准确率 |

只报告“参数更少但有效深度一样”，不足以证明系统更高效。

---

## 3. 这不是一种单一架构：六类循环范式

| 类型 | 代表工作 | 核心特征 | 主要优点 | 主要风险 |
|---|---|---|---|---|
| 全栈循环 | Universal Transformer、Ouro | 大部分层跨循环共享 | 参数最省、结构直接 | 功能多样性不足，训练容易不稳 |
| 中段循环 | Hyperloop、MoR | Prelude/Core/Coda，仅 Core 重复 | 输入、迭代、输出可以分工 | 仍需选择 Core 大小和循环数 |
| 弹性深度 | LoopFormer | 训练可变循环轨迹，预算条件化 | 一个模型覆盖多个计算预算 | 未训练深度可能漂移或退化 |
| Token 级动态循环 | Mixture-of-Recursions | 不同 token 走不同递归深度 | 把计算集中到困难 token | 路由、KV 管理和 Kernel 更复杂 |
| 并行循环 | Parallel Loop Transformer、LoopCoder-v2 | 跨循环位置偏移、共享 KV 等 | 缓解顺序延迟 | 位置失配，循环过多可能退化 |
| 固定点／收敛式循环 | Attractor Models | 迭代到收敛，用隐式微分训练 | 深度可由收敛决定 | 求解器成本、稳定性和泛化仍待验证 |

还要区分一个邻近概念：有些 Recurrent Transformer 在**时间方向**复用状态或让每层读取自身前序激活，而 Looped Transformer 通常指**深度方向**重复共享模块。它们都使用“recurrent”这个词，但计算图、KV 行为和训练目标可能完全不同。

---

## 4. 技术演进：从“重复一层”到“可控的潜在计算”

### 4.1 第一阶段：证明迭代归纳偏置有价值

[Universal Transformers](https://arxiv.org/abs/1807.03819) 和 2023 年的学习算法实验说明，循环结构在复制、逻辑、迭代优化和 in-context data fitting 上具有合理的归纳偏置。这个阶段回答的是：

> 一个共享更新算子，能否通过重复应用模拟多步算法？

答案是可以，但早期证据主要来自较小模型和结构化任务。

### 4.2 第二阶段：把循环扩展到语言模型预训练

[Huginn](https://arxiv.org/abs/2502.05171) 证明递归深度可以扩展到十亿级参数，并在测试时增加隐空间计算。它的重要意义不是某个单项分数，而是把“生成更多思维 token”之外的第二种 Test-Time Compute 路线做到了真实语言模型规模：

$$
\text{更多显式 token}
\quad\text{vs.}\quad
\text{更多隐空间迭代}
$$

[Ouro](https://arxiv.org/abs/2510.25741) 则把 Looped LM 从 proof of concept 推向完整预训练：论文报告 1.4B/2.6B 模型在多项任务上达到更大普通模型的水平，并通过逐循环监督和深度分配机制，让模型在中间循环也形成可用表示。

需要注意，Ouro 的作者把收益主要解释为“知识操作能力”增强，而不是存储更多事实。这个结论来自其控制实验，仍需要更多独立复现。

### 4.3 第三阶段：修复权重共享带来的能力损失

简单地让同一层运行四次，意味着四个深度位置被迫执行完全相同的函数。标准 Transformer 中，不同深度往往自然形成不同功能：低层偏局部形式，中层整合语义，高层准备输出。完全绑权重会损失这种分工。

现代方法普遍加入“循环身份”：

- 循环编号 embedding；
- 每轮独立 LayerNorm 或尺度参数；
- Layer-wise / Depth-wise LoRA；
- 输入条件化的低秩调制；
- Hyper-Connection；
- MoE 路由；
- 每轮重新注入原始输入或上下文锚点。

[Relaxed Recursive Transformers](https://arxiv.org/abs/2410.20672) 用 depth-wise LoRA 放松严格权重共享，并展示了把已训练的标准模型压缩为递归模型的路径。[Hyperloop Transformers](https://arxiv.org/abs/2604.21254) 则在循环边界引入矩阵值残差流，论文报告其在多个规模上用约 50% 更少参数超过有效深度匹配的普通 Transformer。

这些方法背后的共同逻辑是：

$$
F_r(h)=F_{\theta}(h; e_r)
$$

参数主体共享，但第 $r$ 次访问不必执行完全相同的功能。

---

## 5. 六个真正决定成败的瓶颈

### 5.1 容量瓶颈：同一组权重能否承担多种深度功能

权重共享天然施加了低秩式约束。假如一个普通 24 层模型需要 24 组高度不同的变换，那么用 6 层循环 4 次未必能恢复相同函数族。

当前修复路线大致分为三类：

1. **弱共享：** 主权重共享，每轮保留少量独立参数，如 LoRA、Norm、gate；
2. **结构性多流：** Hyper-Connection、MoE 或并行残差流为不同循环提供不同路径；
3. **输入条件化：** 根据样本或当前状态动态生成每轮调制参数。

[Ouroboros: Dynamic Weight Generation for Looped Language Models](https://arxiv.org/abs/2604.02051) 尝试为不同 recurrence 生成输入条件化 LoRA，但其 held-out 文本实验中 controller 并未稳定超过基线。这是一个有价值的负结果：**给循环增加更多自由度，不代表优化就会自动变容易。**

### 5.2 稳定性瓶颈：共享参数会被重复访问和重复更新

循环模型的梯度不是简单经过不同参数层，而是多次经过同一组参数。重复访问可能带来：

- 梯度方向在不同循环间振荡；
- 残差范数逐轮放大；
- 表示快速收敛到无信息固定点；
- 后续循环发生震荡，而不是持续细化；
- 训练循环数与推理循环数不一致时分布外失稳。

[Simply Stabilizing the Loop via Fully Looped Transformer](https://arxiv.org/abs/2605.18797) 将问题归因于 gradient oscillation 和 residual explosion，并通过全循环信号分配和 Attention Injection 把稳定训练扩展到 12 次循环。

[DeepLoop](https://arxiv.org/abs/2607.13491) 则指出，传统 DeepNorm 只看名义深度，没有考虑同一参数被访问多次；它为 tied depth 推导了更强的残差缩放。其结果目前仍停留在 GPT-2 small/medium 尺度，说明理论修复是必要进展，但还不是大规模结论。

### 5.3 深度控制瓶颈：更多循环为什么会变差

很多宣传把 $R$ 描述成一个随时可调的“智能旋钮”——题难就多循环几次。但模型只在固定 $R$ 上训练时，推理阶段直接改变循环数会遇到典型的分布外问题。

[LoopFormer](https://arxiv.org/abs/2602.11451) 的贡献正在于此：它用可变长度轨迹训练，并通过 shortcut consistency 对齐不同循环预算，使短轨迹保留可用信息、长轨迹继续细化。官方代码已公开在 [armenjeddi/loopformer](https://github.com/armenjeddi/loopformer)。

但“循环越多越好”已经被明确否定。[LoopCoder-v2](https://arxiv.org/abs/2606.18023) 在 7B 代码模型、18T token 预训练中发现，两次循环表现最好；SWE-bench Verified 从非循环模型的 43.0 提高到 64.4，Multi-SWE 从 14.0 提高到 31.0，但三次及更多循环反而回退。作者的诊断显示：第二轮提供主要有效细化，后续更新逐渐振荡、表示多样性降低，而跨循环位置偏移成本没有同步下降。

因此一个可靠的循环模型至少需要：

- 训练覆盖目标循环范围；
- 每轮边际收益估计；
- 提前退出或停止 gate；
- 超出训练深度时的回归测试；
- 对表示收敛、振荡和 logit 变化的监控。

### 5.4 延迟瓶颈：深度循环本质上仍是顺序计算

标准自回归已经在 token 维度串行；如果每个 token 内部还需要 $R$ 次 Core 迭代，decode latency 会进一步放大。

这也是为什么“参数更少”可能只降低权重带宽，却没有降低端到端延迟。尤其在 batch 很小、Core 已能驻留显存时，额外循环的矩阵计算可能成为主导成本。

缓解路线包括：

- [Parallel Loop Transformer](https://arxiv.org/abs/2510.24824) 一类跨循环并行方法；
- Continuous Depth-wise Batching，将不同样本的递归深度放进同一批次；
- 自适应退出，让简单 token 或简单请求少循环；
- 将部分循环变成低分辨率或稀疏计算；
- 为共享 Core 编写更适合权重驻留与循环复用的 Kernel。

这些技术决定 Looped Transformer 能否从“参数压缩方法”进入“生产推理架构”。

### 5.5 KV Cache 瓶颈：权重共享不代表 Cache 自动共享

Decoder-only 模型在每个层和每个历史 token 上保存 K/V。即使同一个 Core 权重重复使用，循环产生的隐藏状态不同，对应 K/V 也不同。朴素实现中：

$$
M_{KV}\propto R\cdot L_{\text{core}}\cdot T
$$

所以增加 latent depth 可能把省下来的权重显存重新消耗在 KV Cache 上。

2026 年出现了两条重要路线：

- [MELT](https://arxiv.org/abs/2605.07721) 每层只维护一份跨循环共享的 KV，并用学习式 gate 更新，从而让迭代深度与 KV 内存近似解耦；
- [Looped Latent Attention](https://arxiv.org/abs/2607.15456) 观察到同一 token 的 K/V 在循环轴上近似低秩，用 SVD 初始化和蒸馏学习压缩 codec。论文报告平均 21.3 倍压缩，并在一张 H200 上把 4k context 的 batch capacity 从 32 提高到 768；这些数字仍是作者报告，且包含专门 codec 与训练过程。

关键结论是：

> Looped Transformer 的 Serving 优势，必须和 KV 策略一起设计；只共享权重远远不够。

### 5.6 监督瓶颈：隐藏状态为什么会学会“思考”

如果只在最后一个循环输出位置计算语言模型损失，早期循环容易只学到模糊的过渡状态。现代方法经常使用：

- 每轮 LM loss；
- 中间表示蒸馏；
- 与显式 CoT token 对齐；
- 随机深度训练；
- 对不同循环路径做一致性约束；
- 奖励后期循环相对早期循环的边际改进。

[LOTUS](https://arxiv.org/abs/2606.31779) 用显式 CoT 的每一步对多个 latent block 做并行监督，在 3B 模型上报告相对显式 CoT 的 2.5—6.9 倍思考阶段延迟缩短，并能通过 LM head 从 latent 中恢复中间推理步骤。

这是一条很有价值的路线，但它也揭示了一个悖论：为了让“隐式推理”可靠，训练时往往仍需要显式推理监督。Latent reasoning 并没有消除 CoT 数据需求，只是把部分推理从推理期 token 序列搬回隐藏状态。

---

## 6. 2026 年代表性工作地图

| 工作 | 核心贡献 | 最强证据 | 主要局限 |
|---|---|---|---|
| [LoopFormer](https://arxiv.org/abs/2602.11451) | 可变循环轨迹与 shortcut consistency | 一个模型随预算弹性运行 | 对大规模真实 Serving 的收益仍未知 |
| [SpiralFormer](https://arxiv.org/abs/2602.11698) | 多分辨率循环 | 160M—1.4B 上改善参数/计算效率 | 复杂度转移到分辨率调度 |
| [Hyperloop](https://arxiv.org/abs/2604.21254) | 中段循环 + Hyper-Connection | 约 50% 少参数仍超过深度匹配基线 | 主要规模仍在约十亿参数级 |
| [Fully Looped Transformer](https://arxiv.org/abs/2605.18797) | 抑制梯度振荡和残差爆炸 | 可稳定训练到 12 loops | 稳定不等于循环越多越有用 |
| [MELT](https://arxiv.org/abs/2605.07721) | 跨循环共享 KV | 迭代深度近似常量 KV 内存 | 依赖从 Ouro 蒸馏与专门训练 |
| [LT2](https://arxiv.org/abs/2605.20670) | 循环 + 线性/稀疏注意力 | 转换 Ouro-1.4B 后约 1B token 适配 | 质量和 Kernel 生态仍需扩大验证 |
| [LoopCoder-v2](https://arxiv.org/abs/2606.18023) | 7B 并行循环代码模型 | 18T token，代码与 Agent benchmark 明显提升 | 三次以上循环回退，揭示非单调性 |
| [LOTUS](https://arxiv.org/abs/2606.31779) | latent 与显式 CoT 并行监督 | 3B 规模缩小 latent/explicit gap | 依赖 CoT 监督和作者自建评测流程 |
| [Loopie](https://arxiv.org/abs/2607.16051) | Looped MoE | 20B/2B active 与 6B/0.6B active，论文报告同计算优势 | 新预印本，缺少独立复现和完整系统成本 |
| [Looped Latent Attention](https://arxiv.org/abs/2607.15456) | 循环轴 KV 低秩压缩 | 大幅降低 cache、提高 batch capacity | codec、蒸馏和硬件实现增加复杂度 |
| [DeepLoop](https://arxiv.org/abs/2607.13491) | tied-depth-aware 残差缩放 | 为重复参数访问给出稳定性解释 | 当前实验规模较小 |
| [Jacobian Lens](https://arxiv.org/abs/2609.01924) | 分析递归模型的可读/可控 workspace | 对 Ouro、Huginn 做因果读写分析 | 刚发布的解释性预印本，结论仍待复核 |

这张表也说明，所谓“Looped Transformer 热潮”并非单一模型刷榜，而是训练、架构、推理、Cache、监督和可解释性同时开始补齐。

---

## 7. 现有证据到底支持哪些结论

### 7.1 参数效率：证据最强

从 Universal Transformer、2023 年算法学习实验，到 Relaxed Recursive Transformer、Hyperloop、Ouro 和 Loopie，越来越多结果表明：在一部分任务和规模上，共享深度参数可以显著缩小模型，同时保留大部分甚至超过深度匹配模型的质量。

这个结论最可信，因为它直接由模型文件大小和参数量决定，不依赖复杂的成本换算。

### 7.2 固定计算下的质量：开始出现正证据，但并不普适

Loopie 和 SpiralFormer 等工作声称在固定训练计算下超过普通 Transformer；LoopCoder-v2 也提供了较大规模、长训练和多类代码任务证据。

但 [CART](https://arxiv.org/abs/2606.01495) 给出了必要的反例：其 Context-Anchored Recurrent Transformer 在参数匹配比较中没有超过 dense baseline，变量循环推理在训练循环数两侧都退化。这个负结果提醒我们：

> “循环”不是免费归纳偏置，具体的锚定、Core/Coda 划分和训练配方可能吞掉理论优势。

### 7.3 Test-Time Scaling：真实存在，但必须在训练分布内

Huginn、Ouro、LoopFormer 等都表明，增加递归深度有时能继续提高结果。更合理的表述是：

> Looped Transformer 提供了一条潜在的测试时计算轴，但有效区间、收益曲线和停止规则必须通过训练建立。

它不是任意把 $R=4$ 改成 $R=64$ 就能得到更强模型。LoopCoder-v2 的非单调曲线正说明，超出有效区间后继续循环可能是在反复改坏答案。

### 7.4 Latent reasoning：可以发生，但不能直接叫作隐式思维链

性能随循环增加，最多说明隐藏状态中的额外计算有价值，并不能证明模型形成了人类可读的推理步骤。

[Latent Chain-of-Thought? Decoding the Depth-Recurrent Transformer](https://arxiv.org/abs/2507.02199) 对 Huginn 的 probing 只找到有限且不稳定的可解释 latent CoT 证据，额外 recurrence 的收益也明显低于显式 CoT。另一方面，LOTUS 通过显式监督能让 latent 更可读；最新的 [Jacobian Lens](https://arxiv.org/abs/2609.01924) 又发现 Ouro 和 Huginn 都形成某种功能性 workspace，但信息跨循环传播方式显著不同。

因此当前最稳妥的结论是：

$$
\text{有用的隐空间迭代}
\not\Rightarrow
\text{可解释的隐式思维链}
$$

### 7.5 生产就绪度：仍是最薄弱的一环

目前大部分论文关注参数量、perplexity 和离线 benchmark。生产系统还必须回答：

- 同一 batch 内不同样本需要不同循环数时如何调度？
- 循环 Core 能否保持高 GPU 利用率？
- KV Cache 是逐循环存储、共享还是压缩？
- 提前退出是否校准，错误退出的代价是什么？
- Speculative decoding、prefix cache、tensor parallel 如何适配？
- 量化后重复误差是否在循环中累积？
- P99 latency 和每个正确答案的 GPU-ms 是否真的更优？

在这些问题得到系统级数据之前，把 Looped Transformer 称为“下一代主流架构”还太早。

---

## 8. 安全与可解释性：循环模型真的更难监控吗

X 上最近的争议把 recurrent depth 与“不可监控的 neuralese”直接绑定，这个推论目前证据不足。

循环模型确实会把一部分计算放在隐藏状态中，外部看不到逐 token 的自然语言 CoT；但标准 Transformer 的大部分内部计算同样不可见。真正需要比较的是：

1. 隐状态是否能被稳定 readout；
2. 中间表征是否具有因果作用；
3. 增加循环时目标、欺骗或错误行为如何演化；
4. 显式 CoT 监控减少后，其他监控方法能否补位；
5. 不同循环之间是否出现难以察觉的状态漂移。

现有结果并不单向支持“更不可解释”。Huginn probing 给出悲观证据；LOTUS 显示强监督可以恢复可读步骤；Jacobian Lens 则发现不同训练方式会形成不同的 workspace 访问模式。

我更倾向于把它视为一个新的监控对象：

```text
Loop 级 logit / value 变化
隐藏状态收敛与振荡
每轮因果贡献
退出 gate 的置信度
不同循环的安全分类器分数
```

这比争论“模型是否在说 neuralese”更可操作。

---

## 9. 它会成为下一代主流 LLM 架构吗

### 9.1 我认为不会以“纯循环替代所有层”的形式发生

标准 Transformer 的优势不只是效果，还包括成熟的训练配方、并行策略、Kernel、量化、KV 管理和 Serving 生态。完全循环模型需要同时重做这些工程基础，转换成本很高。

### 9.2 更可能出现三种混合形态

**形态一：内存受限的小模型。** 通过共享 Core，把更多有效深度塞进手机、PC 和边缘设备的权重预算；Hyperloop 和量化兼容性尤其符合这个方向。

**形态二：带弹性计算的推理模型。** 简单请求运行 1—2 次，困难请求运行更多次；LoopFormer、MoR 和提前退出技术会在这里汇合。

**形态三：标准主干中的局部循环模块。** 保留独立的输入、输出和部分深层，只在某个中间区间循环，用较低架构风险换取参数效率和额外计算深度。

### 9.3 决定它能否突破的不是下一个 benchmark，而是三个 Pareto 前沿

未来真正有说服力的模型必须同时画出：

$$
\text{Quality}\;\text{vs.}\;\text{Stored Parameters}
$$

$$
\text{Quality}\;\text{vs.}\;\text{GPU-ms}
$$

$$
\text{Quality}\;\text{vs.}\;\text{Peak HBM}
$$

只有第一条更优，说明它是参数压缩架构；三条都更优，才说明它可能成为通用的新基础架构。

---

## 10. 一个适合个人研究者的 4080 实验方案

不建议一上来复现 7B/18T token 的 LoopCoder。更合理的实验是用 50M—300M 级 decoder，严格拆开参数、FLOPs 和延迟三个维度。

### 10.1 模型组

| 组别 | 结构 | 目的 |
|---|---|---|
| Dense-Small | 4—6 个独立层 | 参数匹配基线 |
| Dense-Deep | 12—24 个独立层 | 有效深度匹配基线 |
| Loop-Fixed | Prelude 1 + Core 2 × R + Coda 1 | 基础循环模型 |
| Loop-Conditioned | 在 Loop-Fixed 上加入 loop embedding / per-loop norm | 测功能分化 |
| Loop-RandomDepth | 训练时随机采样 $R$ | 测弹性深度 |

循环次数建议：

$$
R\in\{1,2,4,8\}
$$

### 10.2 三种公平比较口径

1. **固定存储参数：** 同参数量下谁的质量更高；
2. **固定训练 FLOPs：** 同计算预算下谁的质量更高；
3. **固定线上延迟：** 同 GPU-ms/token 或 P95 latency 下谁的质量更高。

不要只选择对循环模型最有利的“固定参数”口径。

### 10.3 最小前向结构

```python
class LoopedDecoder(nn.Module):
    def forward(self, tokens, loops: int):
        x = self.embed(tokens)
        anchor = self.prelude(x)
        h = anchor

        for r in range(loops):
            # loop embedding / time conditioning lets the shared core
            # behave differently at different recurrent depths.
            h = self.core(h, anchor=anchor, loop_id=r)

        return self.lm_head(self.coda(h))
```

训练时可以随机采样循环数：

```python
loops = random.choice([1, 2, 4, 8])
loss = lm_loss(model(tokens, loops), targets)
```

再加入相邻预算的一致性损失：

$$
L=L_{LM}^{(R)}+\lambda\,D_{KL}\left(p_{R/2}\;\|\;p_R\right)
$$

这只是最小原型，不应直接当作最佳配方。

### 10.4 必须记录的诊断

除了 validation loss 和下游准确率，还应记录：

- 每轮 $\Delta$loss；
- 每轮 logit KL；
- 隐状态 cosine similarity；
- 隐状态范数；
- 相邻循环更新量 $\|h_{r+1}-h_r\|$；
- 预测答案在第几轮发生改变；
- loops/s、tokens/s、GPU-ms/token；
- peak VRAM；
- KV Cache 随 $R$ 的变化；
- 提前退出 gate 的 ECE / Brier score。

一个很实用的停止判据是：

$$
\frac{\|h_{r+1}-h_r\|}{\|h_r\|}<\epsilon
$$

但必须同时检查“表示收敛”是否真的对应“答案已经正确”。模型也可能稳定地收敛到错误答案。

### 10.5 最值得做的消融

1. 去掉 loop embedding；
2. 去掉 input anchor；
3. per-loop norm 改为共享 norm；
4. 固定 $R$ 训练与 random-depth 训练对比；
5. 最终循环监督与每轮深监督对比；
6. 2、4、8 loops 的 KV Cache 与延迟曲线；
7. 训练外循环数，如 train $R\le4$、test $R=8$。

如果结果出现：

```text
R=1 → R=2 明显提升
R=2 → R=4 很小
R=4 → R=8 回退
```

这并不是实验失败，而是非常有价值的非单调证据。下一步应研究退出策略和循环分工，而不是继续把 $R$ 拉大。

---

## 11. 我的最终判断

Looped Transformer 不是“一种更深但免费的 Transformer”。更准确的定位是：

> **一种把存储参数、有效深度和测试时计算解耦的架构工具。**

它已经相当有力地证明：深度不必与独立参数一一绑定；小模型可以通过重复计算获得比参数规模暗示的更强能力；循环深度可以成为继 token 数量、宽度、MoE 激活参数之后的另一条计算轴。

它还没有证明：共享权重在所有规模和任务上优于独立层；latent recurrence 普遍比显式 CoT 更强；增加循环能可靠提升结果；生产延迟、KV 内存和调度成本已经解决。

所以当前最合理的态度既不是“下一代架构已经确定”，也不是“只是把 RNN 换了个名字”。这条路线正在从学术归纳偏置，变成一个可以被系统性工程化的设计空间。接下来最值得追踪的信号是：

- 是否出现 30B+ 或大规模 MoE 的独立复现；
- 是否公开 compute-matched、latency-matched 的完整曲线；
- 动态退出能否在真实 batch serving 中兑现收益；
- KV 共享与压缩是否进入 vLLM、SGLang 等主流推理栈；
- 循环模型在长程 Agent、代码和自我修正任务上的优势是否稳定；
- latent state 的可解释性和安全监控是否形成标准评测。

在这些问题解决之前，我会把 Looped Transformer 评为：**高潜力、证据快速积累，但仍处于架构与基础设施共同探索期。**

---

## 推荐阅读顺序

想用 60—90 分钟建立主干理解，可以按下面顺序阅读：

1. [Universal Transformers](https://arxiv.org/abs/1807.03819)：理解深度循环和动态停止的起点；
2. [Scaling up Test-Time Compute with Latent Reasoning](https://arxiv.org/abs/2502.05171)：理解 recurrent depth 为什么重新进入 LLM；
3. [Scaling Latent Reasoning via Looped Language Models](https://arxiv.org/abs/2510.25741)：看完整预训练模型 Ouro；
4. [LoopFormer](https://arxiv.org/abs/2602.11451)：理解弹性循环深度；
5. [Hyperloop Transformers](https://arxiv.org/abs/2604.21254)：理解如何恢复循环间功能差异；
6. [LoopCoder-v2](https://arxiv.org/abs/2606.18023)：重点看“更多循环反而更差”的大规模证据；
7. [MELT](https://arxiv.org/abs/2605.07721) 与 [Looped Latent Attention](https://arxiv.org/abs/2607.15456)：理解 KV Cache 为什么是生产瓶颈；
8. [Latent Chain-of-Thought?](https://arxiv.org/abs/2507.02199)：给 latent reasoning 降温；
9. [Looped Transformers under the Jacobian Lens](https://arxiv.org/abs/2609.01924)：了解最新的因果可解释性分析。

## 主要参考资料

1. [Universal Transformers](https://arxiv.org/abs/1807.03819)
2. [Looped Transformers are Better at Learning Learning Algorithms](https://arxiv.org/abs/2311.12424)
3. [Relaxed Recursive Transformers](https://arxiv.org/abs/2410.20672)
4. [Scaling up Test-Time Compute with Latent Reasoning](https://arxiv.org/abs/2502.05171)
5. [Latent Chain-of-Thought? Decoding the Depth-Recurrent Transformer](https://arxiv.org/abs/2507.02199)
6. [Mixture-of-Recursions](https://arxiv.org/abs/2507.10524)
7. [Scaling Latent Reasoning via Looped Language Models](https://arxiv.org/abs/2510.25741)
8. [Parallel Loop Transformer](https://arxiv.org/abs/2510.24824)
9. [LoopFormer](https://arxiv.org/abs/2602.11451)
10. [SpiralFormer](https://arxiv.org/abs/2602.11698)
11. [Ouroboros: Dynamic Weight Generation for Looped Language Models](https://arxiv.org/abs/2604.02051)
12. [Hyperloop Transformers](https://arxiv.org/abs/2604.21254)
13. [Memory-Efficient Looped Transformer](https://arxiv.org/abs/2605.07721)
14. [Simply Stabilizing the Loop via Fully Looped Transformer](https://arxiv.org/abs/2605.18797)
15. [LT2: Linear-Time Looped Transformers](https://arxiv.org/abs/2605.20670)
16. [CART: Context-Anchored Recurrent Transformer](https://arxiv.org/abs/2606.01495)
17. [LoopCoder-v2](https://arxiv.org/abs/2606.18023)
18. [LOTUS](https://arxiv.org/abs/2606.31779)
19. [DeepLoop](https://arxiv.org/abs/2607.13491)
20. [Looped Latent Attention](https://arxiv.org/abs/2607.15456)
21. [Loop the Loopies!](https://arxiv.org/abs/2607.16051)
22. [Looped Transformers under the Jacobian Lens](https://arxiv.org/abs/2609.01924)
23. [LoopFormer 官方代码](https://github.com/armenjeddi/loopformer)

*本文截至 2026-09-04。论文中的性能数字均按作者公开结果表述；尚未独立复现的结果不应被视为已建立的通用规律。*
