对，这一步通常叫“**给电路做功能解释**”或者“**把元件整理成机制模块**”。结论先说在前面：**现在主流做法并不是先聚类、再猜语义；而是先用可视化和解码判断每个元件“在读什么、在写什么、什么时候起作用”，再把因果作用相近的元件并成一组。** 也就是说，语义分组本质上是一个 **读入模式 + 写出模式 + 因果作用** 的联合判断问题，而不只是看图长得像不像。像 IOI 那篇经典工作，就是先用因果干预找到 26 个 attention heads，再把它们按功能整理成 7 类；作者强调，他们分组靠的是一组 interpretability methods 和 causal interventions，而不是只靠肉眼看图。([arXiv][1])

你提到的 heatmap 和 logit lens，确实就是这件事里最常见的两个入口，但它们各自只回答一半问题。**attention heatmap** 更偏向回答“这个头在**读哪里**”；**logit lens / tuned lens / attention lens** 更偏向回答“这个头或这个层在**往输出方向写什么**”。真正可靠的语义命名，通常还要再加一层因果验证：把这个头 patch 掉、ablate 掉、或者只保留它所在子图，看任务行为到底怎么变。没有这一步，你看到的往往只是“相关”，不一定是“功能”。这个思路在 IOI、factual recall、Attention Lens、Anthropic attribution graphs 这些工作里都很明显。

## 1. 对 attention head，大家一般怎么做语义解释

最传统的第一步，是看 **attention pattern**，也就是你说的 heatmap。它最直接回答的问题是：**这个 head 在当前 token 位置，会去读上下文中的哪一类位置。** 比如 induction heads 那条线里，研究者就是通过看注意模式发现：有一类头会从当前位置读前一个 token；另一类头则利用这个信息，去寻找“前面哪里出现过与当前 token 相同的 token，并复制其后续模式”。这就是为什么它们最后会被命名成 “previous-token head” 和 “induction head”——这个名字首先来自“它读哪里、按什么模式读”。([变压器电路][2])

但只看 heatmap 不够，因为“读哪里”不等于“干什么”。所以第二步通常会看 **这个 head 把什么信息写回 residual stream**。早期很多人会直接把某层 residual 用 **logit lens** 投到词表空间，看当前层最像在推动哪些 token；但这对单个 attention head 不总是好用，因为 head 的输出不是专门为直接 unembed 设计的。于是 2023 年的 **Attention Lens** 专门把这个思路改成了“给每个 attention head 学一个 head-specific 的变换，再把 head 输出映到词表空间”，这样就能直接看某个 head 更像在写入哪类词、哪类概念。论文里明确说，这个工具能解释单个 attention head deem relevant 的概念，并展示很多 head 有高度专门化的角色，比如 knowledge retrievers、induction heads、name-mover heads 等。换句话说，**heatmap 负责看‘读’，attention lens / logit lens 负责看‘写’**。

第三步才是“定名字”。真正常见的命名方式不是抽象聚类，而是**按功能链条命名**。最典型的例子就是 IOI。那篇工作最后不是简单说“这是第 9 层的一组头”，而是把它们整理成接近人能理解的步骤：先识别句子中出现过哪些名字，再去掉重复项，再把剩下那个名字搬到输出位置。OpenReview 版本直接把这个算法写出来，并说他们的电路里有几大类 head 分别对应这几个步骤；比如一类负责检测重复名字，一类负责抑制不该被复制的名字，一类负责把正确名字搬到输出位。这里的“语义分组”其实不是按几何相似性，而是按**机制中的职责分工**。([OpenReview][3])

所以对 attention heads，比较成熟的工作流其实是：
先用 heatmap 看读入位置；
再用 logit lens / attention lens 看写出内容；
再用 patching / ablation 看它对下游行为是不是因果关键；
最后把 **读入模式相似、写出方向相似、因果职责相近** 的头并成一类。
这时分组名往往不是“cluster 1 / cluster 2”，而是“induction-like”“name mover-like”“delimiter-like”“sequence-member detector”这种功能名字。类似地，在 sequence continuation 那条线里，研究者最后也把子电路整理成“sequence member detection”和“next member prediction”等功能模块，而不是只按层号列元件。([arXiv][4])

## 2. 对 MLP，大家一般怎么做语义解释

MLP 的解释方式和 attention head 有点不一样。因为 attention head 天然有“读哪里”的结构，而 MLP 更像是在当前位置做一种内容变换。所以对 MLP，大家通常先做的是 **定位**：到底是哪个层、哪个 token 位置的 MLP 在关键时刻起决定作用。比如 ROME / factual recall 这条线，就先用 causal mediation analysis 去做 tracing，结果发现处理中层 MLP、尤其是 subject name 最后一个 token 附近的 MLP，对事实回忆特别关键。也就是说，MLP 的语义解释第一步通常不是 heatmap，而是 **“关键位置 + 关键层”定位图**。

定位完以后，MLP 常见的解释方式是 **key-value memory 视角**。ROME 这篇非常明确地把 transformer MLP 看成两层 key–value memory：前半部分像 key，后半部分像 value；当 subject 对应的 key 被激活，就会检索出对应事实的 value。这个视角的好处是，它能把“这个 MLP 在干什么”说成一句接近语义的话：**它在当前位置根据 subject 检索某条事实，并把对象方向的信息写回 residual stream。** 更重要的是，这不是纯可视化猜测，因为作者后面真的做了 rank-one model editing，直接改写这个 key-value 关联，模型的事实就跟着变。也就是说，MLP 的语义命名往往来自“它检索哪类内容、写出什么值、修改后行为是否真变了”。

所以 MLP 的“语义分组”通常会比 attention heads 更粗一点。attention head 常被分成“previous-token”“induction”“name mover”这种细角色；MLP 更常见的是“事实检索模块”“属性写入模块”“中间表征重编码模块”。如果再进一步细化，研究者会看 top activating contexts、最近邻样本、投到词表空间后的高分词，或者看编辑某个 MLP 后哪些 factual association 一起变化，从而给它一个更具体的语义标签。ROME 这条线虽然重点是定位与编辑，不是做漂亮的语义 taxonomy，但它实际上给出了 MLP 语义解释最经典的套路：**先找 decisive MLP，再用 key-value view 解释它写入的是什么。** 

## 3. 为什么老方法常常停在“head 级语义”，而后来大家转向 feature 级语义

这里有个很关键的现实问题：**attention head 和单个 neuron 往往是 polysemantic 的**，也就是一个元件可能同时混着几种含义。于是你就会遇到一个尴尬局面：heatmap 看着像在找重复 token，但写出的方向又混着别的信息；或者一个 MLP 看起来跟事实检索有关，但内部其实混着很多不相干功能。这也是为什么后来很多人不满足于“给整个 head 起一个名字”，而转向 **feature-level** 的解释。Sparse Feature Circuits 这篇就直接说了：以前找到的 circuits 常常基于 polysemantic、难解释的 unit，比如 attention heads 或 neurons；他们改用人更容易理解的 sparse features 来构图。([arXiv][5])

一旦切到 feature 层，语义分组的做法也变了。不是再去说“第 9 层第 6 个头是什么头”，而是先用 SAE 或类似方法把激活拆成更稀疏的 feature，然后看每个 feature 的 **top activating examples、典型上下文、对输出的影响方向**，再给 feature 起名，最后再把 feature 按图结构并成模块。Sparse Feature Circuits 这篇还进一步走到应用上：它提出 SHIFT，让人类判断哪些 feature 是 task-irrelevant，再把这些 feature 删掉来改善泛化。这个点很关键，因为它说明 feature-level 语义不只是“看起来更好解释”，而是已经可以进入人工筛选和下游干预。([arXiv][5])

换句话说，**老方法的语义分组单位是 head/MLP，后来新方法的语义分组单位是 feature。** 旧范式比较像“给粗粒度模块命名”，新范式更像“先得到很多更细的、接近单义的语义碎片，再把这些碎片连成电路”。这也是为什么你现在看新的电路论文，会感觉展示方式从 heatmap 和单头分析，逐渐变成 feature graph、attribution graph、feature browser。([arXiv][5])

## 4. Anthropic 这一线具体怎么做“语义分组”

Anthropic 2025 的 attribution graphs，做法又比 SAE 论文更工程化一些。它们的重点不是“给每个 head 起名字”，而是先在 replacement model 里追踪 **feature-to-feature** 的边，再对图做 pruning，只保留对某个输出 token 最重要的节点和边，然后提供一个交互界面让研究者去高亮、检查和命名关键机制。论文方法页里写得很清楚：他们先剪枝得到稀疏、可解释的图，再通过交互界面快速识别关键机制，最后还会用 perturbation experiments 验证图中 feature 之间的关系是否和模型输出变化一致。也就是说，在这条线里，“语义分组”已经不是单独的一张热力图，而是 **在图上圈出一块功能子图并给它命名**。([变压器电路][6])

Anthropic 后续关于 attention 的更新里，还有一个对你这个问题特别关键的发现：他们发现把 attention feature 按 **head-loading vectors** 去聚类，会得到语义上有意义的簇。例如，有些簇跟 induction 有关，有些簇跟识别当前 token 在句子/从句中的位置有关，有些簇和分隔符预测有关。这个结果很重要，因为它说明新一代工作已经不只是“看一个头的 heatmap，然后手工起名字”，而是开始用更结构化的方法，把 feature 按“依赖哪些 heads 搬运信息”来分组，而且这些簇是有语义可读性的。([变压器电路][7])

所以在 Anthropic 这条线上，语义分组更像三步：
先得到 feature graph；
再按贡献大小剪枝出局部机制；
再结合 feature 的典型激活、邻接关系、head-loading 相似性，把一串 feature 合并成更大一点的“机制模块”。
这和老式 “head heatmap + 人工命名” 的确已经不一样了。([变压器电路][7])

## 5. 你如果自己要做，这件事最稳的流程是什么

我会建议你把“语义分组”当成一个 **四步流程**，而不是一步聚类。

第一步，**找职责入口**：
对 attention heads，看它主要读哪些位置；
对 MLP，看它在哪个 token、哪个层最关键。
这一层主要靠 attention pattern、causal tracing、patching。

第二步，**看它写什么**：
对 residual / MLP 用 logit lens 或 tuned lens 一类方法；
对单个 attention head，更建议用 Attention Lens 这种专门为 head 输出设计的解码器。

第三步，**做因果验证**：
把这个组件单独 ablate、只保留它所在子图、或者 patch 它的输出，确认它不是“看起来像”，而是真的在推动下游机制。IOI、ROME、Anthropic 都把这一层看得很重。([arXiv][1])

第四步，**按机制职责而不是按几何相似性分组**：
把那些“读相似对象、写相似方向、在因果链里承担相似角色”的组件并成一组。
如果你做的是 feature-level 方法，再额外加上 top activating examples、head-loading vectors、图邻接关系来辅助聚类。([变压器电路][7])

## 6. 我给你一个最简洁的结论

如果把你这个问题压成一句最有用的话，就是：

**电路找到之后，语义分组不是靠“看图猜名字”，而是靠“这个元件读什么、写什么、对谁起因果作用”，最后再把功能相近的元件合成一个机制模块。**
老方法主要对 head/MLP 这么做，所以常用 attention heatmap、logit lens、causal tracing；新方法主要对 feature 这么做，所以常用 top examples、feature graph、head-loading clustering、perturbation validation。

如果你愿意，我下一条可以直接把这个问题进一步落成一个 **“语义标注模板”**：比如你每发现一个 head 或 MLP，应该记录哪 6 项信息，最后就能比较系统地把 circuit 组织成模块。

[1]: https://arxiv.org/abs/2211.00593?utm_source=chatgpt.com "Interpretability in the Wild: a Circuit for Indirect Object Identification in GPT-2 small"
[2]: https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html?utm_source=chatgpt.com "In-context Learning and Induction Heads"
[3]: https://openreview.net/pdf?id=NpsVSN6o4ul&utm_source=chatgpt.com "INTERPRETABILITY IN THE WILD A CIRCUIT FOR I O ... - OpenReview"
[4]: https://arxiv.org/pdf/2311.04131v1?utm_source=chatgpt.com "Locating Cross-Task Sequence Continuation Circuits in Transformers"
[5]: https://arxiv.org/abs/2403.19647 "[2403.19647] Sparse Feature Circuits: Discovering and Editing Interpretable Causal Graphs in Language Models"
[6]: https://transformer-circuits.pub/2025/attribution-graphs/methods.html "Circuit Tracing: Revealing Computational Graphs in Language Models"
[7]: https://transformer-circuits.pub/2025/attention-update/index.html "Progress on Attention"
