# TODO: `/root/autodl-tmp/project`

## 第 1 部分：动机与我们已经完成的工作

### 1.1 动机

我们构造了一个非常干净的数据集。

- 每个 `clean / corrupt` 对只差用户指令开头的一个动词或极小词组。
- `clean` 会在首个生成位置产生 `<tool_call>`。
- `corrupt` 不会产生 `<tool_call>`，而会落到 `no_tool` 一侧。

这个数据集的意义，不是让我们再去证明“第一词很重要”，而是给我们一个**最小干预接口**：

**只改一个极小 cue，就会导致最终决策翻转。**

因此，这个数据集天然适合做 mechanistic reverse engineering：

- 既然只改了一个极小 cue
- 却导致了首 token 决策的巨大变化
- 那么模型内部一定存在一条把局部差异逐层放大并最终写成决策的电路

### 1.2 我们的方法

我们不是先猜机制，再去找节点。

我们的顺序是：

1. 先用一种 **module-level circuit localization** 方法定位电路。
2. 这个方法通过 **正向和反向两个方向** 运行，同时暴露：
   - 促进 `<tool_call>` 的支路
   - 抑制 `<tool_call>`、推动 `no_tool` 的支路
3. 把两边合成为一张 signed circuit。
4. 对这张 circuit 做充分性和必要性验证。
5. 再对 circuit 中的节点和边做语义分组、功能验证和逆向工程。

### 1.3 已有结果

当前主结果已经整理到：

- [results/final](/root/autodl-tmp/project/results/final)
- [FINAL_PACKAGE.md](/root/autodl-tmp/project/results/final/FINAL_PACKAGE.md)

我们已经完成的部分是：

- 定位出最终 signed circuit：`24` 个节点，`64` 条边
- 通过双向运行定位出促进和抑制两类真实支路
- 对 final circuit 做了充分性和必要性验证，结果很好
- 对节点和边做了初步语义分组
- 提出了一个当前最像真实机制的工作假说

也就是说：

**我们已经算出了 circuit，也已经证明了这张 circuit 是对的。**

当前真正还没做透的，不是 circuit correctness，而是：

**circuit 中每个关键节点和边到底在机制上做了什么。**

---

## 第 2 部分：当前进展、当前假说、当前缺口

### 2.1 当前工作进度

当前进展可以概括成一句话：

**电路已经找到，也验证过了；但电路中的节点和边还没有被充分解释成论文级别的对象语言机制。**

更具体地说：

- 已经定位出真实参与决策的 circuit
- 已经证明这张 circuit 对行为恢复是 faithful 的
- 已经有一条工作中的机制链假说
- 但还缺少足够强的语义分组和功能验证证据

### 2.2 当前机制假说

当前我们最像真实机制的工作假说是：

1. 模型首先从用户第一句 instruction 中读取一个 **instruction-level commitment cue**。
   这个 cue 区分的是：
   - “要求把结果交付到外部文件/环境里”
   - 还是“仅要求把函数体写出来”

2. 这个 cue 通过晚层 user-conditioned ingress 路径  
   `L20H5 -> L21H1/L21H12 -> L24H6 -> MLP27`  
   进入 tool-call 写出链。

3. `MLP27` 是主要的晚层 writer，它把这条状态写成 `<tool_call>` 倾向。

4. 同时存在一条竞争性的 no-tool 链  
   `L16H4 -> MLP17 -> L23H6`
   它会把相同工具环境下的请求压回 `no_tool`，并且压制 tool ingress。

简单说，就是：

- 有一条促进链
- 有一条抑制链
- 两条链在晚层共同决定首 token

### 2.3 当前真正未解决的两个问题

现在真正要解决的，只剩两个 mechanistic question。

#### 问题 1：正向问题

**为什么只改这一个 token / 极小 lead phrase，模型内部就会发生级联变化，最后在首个生成位置从 `<tool_call>` 翻到 `no_tool`？**

这里真正要解释的是：

- 这个最小 cue 先被哪个 head 读到
- 它读到的是词面、位置、对象组合，还是更抽象的语义
- 它通过哪条路径进入促进链
- 哪些节点负责逐层放大
- 最后由谁写成 `<tool_call>` 偏置

#### 问题 2：反向问题

**`no-tool` 链到底是如何实现抑制的？**

这里真正要解释的是：

- `L16H4` 读了什么
- `MLP17` 写了什么
- `L23H6` 如何把 suppressive state 送到输出附近
- 这条链到底是在直接抬高 `no_tool`
- 还是在压低 `<tool_call>`
- 还是两者同时发生

### 2.4 当前缺的不是“更多正确性证据”，而是“机制证据”

当前有一个必须时刻记住的区分：

#### A. 定位证据

这些证据回答的是：

- 这个节点是不是在促进系统里
- 这个节点是不是在抑制系统里
- 动这个节点之后，行为会不会变化

目前已经有很多这类证据：

- forward / reverse discovery
- reverse overlap / forward overlap
- patch rescue
- stepwise rescue
- edge mediation
- sufficiency / necessity

这些证据当然重要，它们证明了：

**电路是对的，节点和边也确实在起作用。**

但它们没有自动回答：

**这些节点和边具体是如何实现机制的。**

#### B. 机制证据

这才是当前真正缺的部分。

机制证据必须回答：

- 它读了什么对象
- 它写了什么方向
- 它通过什么方式影响下游
- 它如何实现促进或抑制

这里不能只局限于反向链，**正向和反向两边都要有机制证据**。

### 2.5 我们真正想要的机制证据长什么样

只要能说明机制，都可以作为机制证据，但至少要优先寻找下面这些。

#### 1. Reader evidence

用于回答“它读了什么”。

可接受形式包括：

- attention heatmap
- span attention density
- top attended tokens
- clean / corrupt 下的读入差分可视化
- token / position / object-composition counterfactual

这类证据要回答：

- 它读的是首词本身
- 还是首词和 `solve.py / solve.cpp / solve.java / function body` 的组合对象
- 还是句首位置 / instruction 边界
- 还是更抽象的“交付承诺”语义

#### 2. Writer evidence

用于回答“它写了什么”。

可接受形式包括：

- logit lens
- direct logit effect
- residual projection to `<tool_call>` direction
- residual projection to `no_tool` direction
- decision score trajectory before / after the node

这类证据要回答：

- 它是在拉高 `<tool_call>`
- 还是在拉高 `no_tool`
- 还是主要在压低对侧方向
- 还是两者同时发生

#### 3. Transmission evidence

用于回答“它怎样把状态传给下游”。

可接受形式包括：

- Q/K/V/Z decomposition
- blocked path vs unblocked path
- downstream activation comparison
- per-edge mediated effect visualization

这类证据要回答：

- 它主要靠 `Q`
- 还是 `K`
- 还是 `V`
- 还是最终 `Z`
- 它到底把什么状态送到了哪个下游节点

#### 4. Amplification evidence

用于回答“最小 cue 如何被逐层放大”。

可接受形式包括：

- stagewise decision score plot
- stagewise top-1 flip plot
- per-layer residual trajectory
- node-by-node accumulation visualization

这类证据要回答：

- 这个局部差异在哪一层开始出现
- 在哪一层被明显放大
- 在哪一层被写成最终决策

#### 5. Suppression evidence

用于回答“抑制到底怎样发生”。

可接受形式包括：

- no-tool 节点前后，`<tool_call>` 方向投影变化
- no-tool 节点前后，`no_tool` 方向投影变化
- tool ingress 节点在 suppressive intervention 前后的状态可视化
- downstream suppression heatmap

这类证据要回答：

- 它是在直接写 `no_tool`
- 还是在压 tool route
- 还是两者同时做

### 2.6 我们想要的最终机制结论，应该长什么样

后续所有解释，都应该尽量写成 **对象语言**，而不是“判断 / 仲裁 / 模式切换”这种控制论语言。

我们想要的结论，应该长得像这样：

#### Reader 型表述模板

- `LxHy` 在目标位置主要读取 `lead verb / file target / function body anchor / instruction boundary` 中的某个具体对象。
- 在 clean 与 corrupt 的对照下，它对这个对象的注意力或读取强度发生系统变化。
- 这个读取不是单纯的位置效应，而是和 `X` 对象绑定。

#### Router / Transmission 型表述模板

- `LxHy` 不是主要 writer，而是通过 `Q / K / V / Z` 中的某个成分，把 `A` 节点读到的状态送到 `B`。
- 它改变的是下游节点对什么对象进行读取，或者把某种 residual state 路由到下游模块。

#### Writer 型表述模板

- `MLPz` 或 `LxHy` 在经过该节点后，系统性地拉高 `<tool_call>` 方向，或系统性地拉高 `no_tool` 方向。
- 如果是抑制链，则要明确写成：
  - 它压低了 `<tool_call>` 方向
  - 或拉高了 `"I"`、`"The"` 这类 no-tool token 的概率
  - 或两者同时发生

#### 完整机制链模板

最终我们想要的不是：

- “模型做了仲裁”
- “模型切换到了工具模式”

而是类似下面这种论文式表述：

1. `Head A` 在首 token 位置读取 `X`
2. 它通过 `Q/K/V/Z` 的某一部分把 `X` 写入 `Node B`
3. `Node B` 改变了 `Node C` 的读取或 residual state
4. `MLP D` 直接把 `<tool_call>` 方向拉高，或者把 `no_tool` 方向拉高
5. 因此首 token 决策被翻转

这类表述才更接近 NeurIPS / ICML / ICLR 机制解释论文中的语言风格。

---

## 第 3 部分：规范、数据与系统配置

### 3.1 结果目录

当前主结果统一位于：

- [results/final](/root/autodl-tmp/project/results/final)

最重要的文件：

- [FINAL_PACKAGE.md](/root/autodl-tmp/project/results/final/FINAL_PACKAGE.md)

### 3.2 数据

- 数据是 clean / corrupt 成对构造的最小干预数据
- 关键差异是用户指令开头的一个动词或极小词组
- 当前主结果使用的是 `1722` 对样本

### 3.3 环境

- Conda 环境：`base`
- Python：`3.12.3`
- 主项目路径：`/root/autodl-tmp/project`

### 3.4 硬件

- GPU：`NVIDIA GeForce RTX 4090 D`
- 显存：`24GB`

### 3.5 后续讨论规范

从现在开始，后续围绕 [results/final](/root/autodl-tmp/project/results/final) 的提问，默认都应服务于下面这个核心目标：

**这个已知最小 cue，究竟如何在当前已发现的 circuit 中被读取、传播、放大，并最终写成 `<tool_call>` / `no_tool` 决策。**

后续任何新的机制结论，都应该满足：

1. 先说明它属于哪一类节点：reader / router / writer / suppressor
2. 再说明它读什么、写什么、如何影响下游
3. 证据尽量使用对象语言，不要只停留在 patch 正确性
