# Output-Route Decision 主报告

## 模块定义

这里把 Output-Route Decision 定义为：在首个输出词生成前，把已经整合好的任务表征压缩成一个可沿残差方向传播的“输出路线状态”，其正向对应 tool-mediated route，反向对应 direct-answer route。这个模块的最小 anchor spine 必须满足三个条件：

- 自身改动会显著改变 route score。
- 该状态会在相邻层持续存在并被放大，而不是一次性局部扰动。
- 该状态能同时改变 tool construction 一侧和 no-tool suppression 一侧的下游投影。

在当前证据下，最小模块定义收缩为 `MLP11 -> MLP16 -> MLP19`。

## 节点分层

- anchor nodes: `MLP11`, `MLP16`, `MLP19`
- support nodes: `L2H14`, `MLP12`, `L20H5`, `L21H12`, `L16H4`, `MLP17`
- candidate nodes: `L12H6`, `L13H9`, `L17H8`

解释：anchor nodes 属于模块最小闭环；support nodes 主要位于边界，负责把状态送进模块或从模块接走；candidate nodes 仍缺直接因果闭环。

## 核心结论

当前最可信的机制是：`MLP11` 首次把 route score 写成一个稳定残差方向，`MLP16` 对这条方向做主要放大，`MLP19` 把它稳定成可分发的后期路由状态；随后这条状态一边提高 `L20H5/L21H1/L21H12/L24H6/MLP27` 的 tool-side 投影，一边降低 `L16H4/MLP17/L23H6` 的 no-tool 投影。

更具体地说，这个模块决定的不是“是否立刻输出 `<tool_call>` 这个单一 token”，而是“接下来答案要经由工具协议输出，还是直接用自然语言回答”的输出路线。

## Anchor Nodes

### MLP11

- 写出证据: 全局方向对齐中位数 `0.676`，clean-corrupt 投影差 `3.912`。
- 单节点 patching: promote rescue `0.176`，promote 边界翻转率 `0.000`；erase route drop `-0.377`。
- 方向干预: inject 到 corrupt 后 route delta `0.956`，tool 边界翻转率 `0.000`；erase clean 后 route delta `-0.306`。
- 下游传递: `MLP11` 注入后 `MLP16` 投影变化 `1.217`，`MLP19` 投影变化 `1.472`。
- 结论: `MLP11` 是最早的稳定 route writer，不是下游 construction token 的直接拼装器。

### MLP16

- 写出证据: 全局方向对齐中位数 `0.685`，clean-corrupt 投影差 `15.916`。
- 单节点 patching: promote rescue `0.363`，promote 边界翻转率 `0.125`；erase route drop `-1.734`。
- 方向干预: inject 到 corrupt 后 route delta `3.213`，tool 边界翻转率 `0.000`；erase clean 后 route delta `-1.839`。
- 下游传递: `MLP16` 注入后 `MLP19` route 投影 `5.921`，`MLP17` no-tool 投影 `-5.777`。
- 结论: `MLP16` 是主放大器，也是两条后续路线分叉前最后一个共享主干。

### MLP19

- 写出证据: 全局方向对齐中位数 `0.739`，clean-corrupt 投影差 `52.344`。
- 单节点 patching: promote rescue `0.362`，promote 边界翻转率 `0.000`；erase route drop `-1.280`。
- 方向干预: inject 到 corrupt 后 route delta `3.480`，tool 边界翻转率 `0.000`；erase clean 后 route delta `-1.448`。
- 下游传递: `MLP19` 注入后 `L20H5/L21H12/MLP27` 的 tool 投影分别为 `4.821` / `5.325` / `165.372`，`L16H4/MLP17` no-tool 投影分别为 `0.000` / `0.000`。
- 结论: `MLP19` 更像 late route relay / stabilizer，而不是最终 `<tool_call>` writer 本身。

## 模块级验证

### promote_tool_route

- `MLP11`: rescue `0.176`, route delta `1.044`, boundary flip `0.000`.
- `MLP11+MLP16`: rescue `0.391`, route delta `3.617`, boundary flip `0.125`.
- `MLP11+MLP16+MLP19`: rescue `0.582`, route delta `4.605`, boundary flip `0.500`.

### erase_tool_route

- `MLP11`: rescue `0.039`, route delta `-0.377`, boundary flip `0.000`.
- `MLP11+MLP16`: rescue `0.212`, route delta `-1.633`, boundary flip `0.000`.
- `MLP11+MLP16+MLP19`: rescue `0.348`, route delta `-3.279`, boundary flip `0.500`.

解读：如果只 patch `MLP11` 还不能稳定跨过边界，而加上 `MLP16` 和 `MLP19` 后明显跨过边界，说明这三者不是松散相关，而是在共同形成和稳定 route choice。

## 下游传递

当前结果支持一个双向分流图景：`MLP19` 之后，tool route 和 no-tool route 的投影同时被改写。在 tool direction 侧，最稳定的接受者是 `L20H5/L21H1/L21H12/L24H6/MLP27`；在 no-tool direction 侧，`L16H4/MLP17/L23H6` 的 no-tool 投影会在 tool-route 注入时下降，在 route 擦除时上升。

这意味着 Output-Route Decision 更像一个共享的上游 residual state，而不是两条路线各自独立的局部开关。

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

综合当前证据，我们认为 Output-Route Decision 最可信的实现不是某个单独节点上的 yes/no 开关，而是一条在 `MLP11 -> MLP16 -> MLP19` 上逐层成形、放大并稳定的残差方向。`MLP11` 首次把 clean/corrupt 的最小提示差异写成稳定的 route state，`MLP16` 对该状态进行主放大并保持两条后续路线尚未分叉的共享骨架，`MLP19` 则把这条状态转成可向下游分发的 late route signal。当沿该方向注入 tool-side 状态时，tool construction 一侧的多个节点同步增强，而 no-tool suppression 一侧的投影同步减弱；当擦除该方向时，现象反向出现。因此，这个模块决定的不是单一 `<tool_call>` token 是否被写出，而是模型接下来采用工具协议输出还是直接回答的输出路线。当前最强的证据来自模块级 patching 与方向干预；相对薄弱的部分是个别共享 backbone 候选节点和部分精确边级分工，它们目前只能保留为支持或候选说法。

