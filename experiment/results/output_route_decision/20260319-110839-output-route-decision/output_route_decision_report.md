# Output-Route Decision 主报告

## 模块定义

这里把 Output-Route Decision 定义为：在首个输出词生成前，把已经整合好的任务表征压缩成一个可被逐层重编码的“输出路线状态”，其正向对应 tool-mediated route，反向对应 direct-answer route。这个模块的最小 anchor spine 必须满足三个条件：

- 自身改动会显著改变 route score。
- 该状态会在相邻层持续存在并被放大，而不是一次性局部扰动。
- 该状态能同时改变 tool construction 一侧和 no-tool suppression 一侧的下游投影。

在当前证据下，最小模块定义收缩为 `MLP11 -> MLP16 -> MLP19`。

## 节点分层

- anchor nodes: `MLP11`, `MLP16`, `MLP19`
- support nodes: `L2H14`, `MLP12`, `L20H5`, `L21H12`, `L16H4`, `MLP17`
- candidate nodes: `L12H6`, `L13H9`, `L17H8`

解释：anchor nodes 属于模块最小闭环；support nodes 主要位于边界，负责把状态送进模块或从模块接走；candidate nodes 仍缺直接因果闭环。

跨层方向几何上并不共享同一向量：`MLP11↔MLP16` cosine `0.041`，`MLP11↔MLP19` `0.051`，`MLP16↔MLP19` `-0.005`。因此更稳的说法不是“单一残差向量被原样搬运”，而是“同一个 route score 被不同节点用各自局部方向重编码”。

support/candidate 的当前定位如下：

- `L2H14` 更像上游 ingress，能把开头提示差异送进 `MLP11`，但还不能单独证明它已经写出稳定 route state。
- `MLP12` 更像早期相邻偏置分支，可能参与 direct-answer 倾向，但当前缺少它作为共享 route state 主干的证据。
- `L20H5/L21H12/L16H4/MLP17` 主要是模块边界接收者：它们说明 route state 已经被接走，但不说明它们本身是 decision writer。
- `L12H6/L13H9/L17H8` 仍保留为 candidate shared-backbone nodes，因为现在缺模块级必要性和方向干预闭环。

## 核心结论

当前最可信的机制是：`MLP11` 首次把 route score 写成一个稳定的局部方向，`MLP16` 对这条状态做主要放大并重新编码，`MLP19` 把它稳定成可分发的后期路由状态；随后这条状态一边提高 `L20H5/L21H1/L21H12/L24H6/MLP27` 的 tool-side 投影，一边降低 `L16H4/MLP17/L23H6` 的 no-tool 投影。

更具体地说，这个模块写出的更像一个连续的 route score / route preference，而不是某个单点上的离散二元开关；它决定的不是“是否立刻输出 `<tool_call>` 这个单一 token”，而是“接下来答案要经由工具协议输出，还是直接用自然语言回答”的输出路线。

## Anchor Nodes

### MLP11

- 写出证据: 全局方向对齐中位数 `0.671`，clean-corrupt 投影差 `3.720`。
- 单节点 patching: promote rescue `0.208`，promote 边界翻转率 `0.020`；erase route drop `-0.579`。
- 方向干预: inject 到 corrupt 后 route delta `1.291`，tool 边界翻转率 `0.000`；erase clean 后 route delta `-0.492`。
- 下游传递: `MLP11` 注入后 `MLP16` 投影变化 `1.872`，`MLP19` 投影变化 `2.422`。
- 结论: `MLP11` 是最早的稳定 route writer，不是下游 construction token 的直接拼装器。

### MLP16

- 写出证据: 全局方向对齐中位数 `0.638`，clean-corrupt 投影差 `12.429`。
- 单节点 patching: promote rescue `0.323`，promote 边界翻转率 `0.073`；erase route drop `-1.532`。
- 方向干预: inject 到 corrupt 后 route delta `2.482`，tool 边界翻转率 `0.022`；erase clean 后 route delta `-1.430`。
- 下游传递: `MLP16` 注入后 `MLP19` route 投影 `3.927`，`MLP17` no-tool 投影 `-4.035`。
- 结论: `MLP16` 是主放大器，也是两条后续路线分叉前最后一个共享主干。

### MLP19

- 写出证据: 全局方向对齐中位数 `0.686`，clean-corrupt 投影差 `38.996`。
- 单节点 patching: promote rescue `0.335`，promote 边界翻转率 `0.031`；erase route drop `-1.285`。
- 方向干预: inject 到 corrupt 后 route delta `2.528`，tool 边界翻转率 `0.027`；erase clean 后 route delta `-1.279`。
- 下游传递: `MLP19` 注入后 `L20H5/L21H12/MLP27` 的 tool 投影分别为 `3.994` / `3.782` / `141.607`，而 suppressive side 上它最直接改变的是 `L23H6` 的 late no-tool 投影 `-4.309`。
- 结论: `MLP19` 更像 late route relay / stabilizer；它已经位于分叉后段，因此不会回头改写更早的 `L16H4/MLP17`。

## 模块级验证

### promote_tool_route

- `MLP11`: rescue `0.208`, route delta `1.568`, boundary flip `0.020`.
- `MLP11+MLP16`: rescue `0.349`, route delta `2.763`, boundary flip `0.116`.
- `MLP11+MLP16+MLP19`: rescue `0.560`, route delta `4.108`, boundary flip `0.396`.

### erase_tool_route

- `MLP11`: rescue `0.061`, route delta `-0.579`, boundary flip `0.012`.
- `MLP11+MLP16`: rescue `0.205`, route delta `-1.721`, boundary flip `0.096`.
- `MLP11+MLP16+MLP19`: rescue `0.346`, route delta `-2.844`, boundary flip `0.366`.

解读：如果只 patch `MLP11` 还不能稳定跨过边界，而加上 `MLP16` 和 `MLP19` 后才出现明显更多的边界翻转，说明这三者是在共同形成和稳定 route choice。但边界翻转率仍远不到 1，所以更准确的说法是“它们构成了主要的 route-decision spine”，而不是“它们单独就足以完全决定首词”。

## 下游传递

当前结果支持一个双向分流图景：`MLP19` 之后，tool route 和 no-tool route 的投影同时被改写。在 tool direction 侧，最稳定的接受者是 `L20H5/L21H1/L21H12/L24H6/MLP27`；在 no-tool direction 侧，`L16H4/MLP17/L23H6` 的 no-tool 投影会在 tool-route 注入时下降，在 route 擦除时上升。

这意味着 Output-Route Decision 更像一个被逐层重编码的上游 route score，而不是两条路线各自独立的局部开关。

## 热图辅助证据

### L20H5
- 旧 span 汇总里，`L20H5` 的最高密度读取是 `file_target` (density `0.052`)。
- 旧 QKV 因果拆分里，`L20H5` 最强分量是 `z` (rescue `0.308`)。
- 当前全量 attention 聚合中，clean 下 `decision row` 最偏向 `file_target` (density `0.042`)。
- 同一头在 corrupt 下 `decision row` 最偏向 `file_target` (density `0.056`)。

### L21H12
- 旧 span 汇总里，`L21H12` 的最高密度读取是 `tail_suffix` (density `0.005`)。
- 旧 QKV 因果拆分里，`L21H12` 最强分量是 `z` (rescue `0.707`)。
- 当前全量 attention 聚合中，clean 下 `decision row` 最偏向 `tool_call_example` (density `0.023`)。
- 同一头在 corrupt 下 `decision row` 最偏向 `tool_call_example` (density `0.011`)。

### L16H4
- 旧 span 汇总里，`L16H4` 的最高密度读取是 `tail_suffix` (density `0.010`)。
- 旧 QKV 因果拆分里，`L16H4` 最强分量是 `z` (rescue `0.198`)。
- 当前全量 attention 聚合中，clean 下 `decision row` 最偏向 `assistant_prefix` (density `0.043`)。
- 同一头在 corrupt 下 `decision row` 最偏向 `assistant_prefix` (density `0.037`)。

### L23H6
- 旧 span 汇总里，`L23H6` 的最高密度读取是 `file_target` (density `0.001`)。
- 旧 QKV 因果拆分里，`L23H6` 最强分量是 `z` (rescue `0.280`)。
- 当前全量 attention 聚合中，clean 下 `decision row` 最偏向 `assistant_prefix` (density `0.057`)。
- 同一头在 corrupt 下 `decision row` 最偏向 `assistant_prefix` (density `0.048`)。

这些 heatmap 只用于说明边界节点在看什么，不单独承担功能定性。

## 旧结论保留与降级

- 可保留: `MLP11 -> MLP16 -> MLP19` 作为 Output-Route Decision 的最小 anchor spine。
- 可保留: `MLP16` 是两条后续路线分叉前的共享主干。
- 需要收缩: 不能再把 `MLP11` 叫作具体的 file/object writer；当前更稳的说法是 earliest stable route writer。
- 需要收缩: 不能把 `MLP19` 直接等同于 tool construction；它更像把 route state 分发给 construction 与 suppression 的 late relay。
- 需要降级成候选: `L12H6/L13H9/L17H8` 仍像 shared backbone，但现在缺模块级强因果闭环。

## 未解决问题

- `MLP11` 写出的 route state 是否还能进一步分解成更窄的语义子方向，目前证据不足。
- `MLP16 -> MLP17` 的传递目前主要靠下游投影变化支持，若要升到最强说法，还应补显式 edge mediation。
- `MLP19` 到 `L20H5/L21H1/L21H12` 的分发是否一条主边就足够，还是并行冗余，目前仍需补限制性 patching。

## 论文风格结论

综合当前证据，我们认为 Output-Route Decision 最可信的实现不是某个单独节点上的 yes/no 开关，也不是一条在所有层保持同向的固定残差向量，而是一条在 `MLP11 -> MLP16 -> MLP19` 上逐层成形、放大并重编码的 route score。`MLP11` 首次把 clean/corrupt 的最小提示差异写成稳定的局部 route state，`MLP16` 对该状态进行主放大并保持两条后续路线尚未分叉的共享骨架，`MLP19` 则把这条状态转成可向下游分发的 late route signal。当沿各自局部方向注入 tool-side 状态时，tool construction 一侧的多个节点同步增强，而 no-tool suppression 一侧的投影同步减弱；当擦除这些局部方向时，现象反向出现。因此，这个模块决定的不是单一 `<tool_call>` token 是否被写出，而是模型接下来采用工具协议输出还是直接回答的输出路线偏好。当前最强的证据来自模块级 patching 与方向干预；相对薄弱的部分是个别共享 backbone 候选节点和部分精确边级分工，它们目前只能保留为支持或候选说法。

