# Tool-Call Construction Refine 主报告

## 范围

- 这份 refine 报告基于 `1722` 个有效样本的 full run。
- 先修正 stagewise / top1 口径 bug，再在此基础上补两个最小必要的 full-run 定向实验。
- bug 说明见 `stagewise_bug_note.md`。

## 修 bug 后，哪些原结论保留

- 主线仍保留：`MLP19 -> L20H5 -> (L21H1 / L21H12) -> L24H6 -> MLP27`。
- `<tool_call>` 的 logit margin 首次翻正仍在 `plus_L21H1`。
- `<tool_call>` 的 top-1 首次过半也仍在 `plus_L21H1`，但现在是实值 `0.503`，不再是旧 summary 里错误的 `1.0`。
- `MLP27` 仍是主 writer，`L24H6` 仍更像 formatter / protocol commitment，`L20H5` 仍更像 construction ingress。

## 修 bug 后，哪些原表述需要收紧

- 旧报告里关于 `plus_L21H1 / plus_L21H12 / plus_L24H6 / plus_MLP27` 的 “top-1 已到 1.0” 都必须回收成真实比例。
- 现在可以强写的是“`plus_L21H1` 首次过半”，不能再写成“从 `L21H1` 开始几乎所有样本都已经是 `<tool_call>` top-1”。
- `MLP19 -> MLP27` 仍不能强写成独立 bypass 主路；这次只把它提高到‘强 parallel receipt 候选’，而不是冻结成单独 construction 子模块。

## 修正后的 stagewise 重审

- `corrupt_full`: route margin `-4.562`，logit margin `-5.000`，`<tool_call>` top1 `0.000`，boundary flip `0.000`，top token `I`。
- `plus_MLP19`: route margin `-1.924`，logit margin `-2.250`，`<tool_call>` top1 `0.045`，boundary flip `0.031`，top token `I`。
- `plus_L20H5`: route margin `-1.099`，logit margin `-1.375`，`<tool_call>` top1 `0.150`，boundary flip `0.128`，top token `I`。
- `plus_L21H1`: route margin `0.117`，logit margin `0.125`，`<tool_call>` top1 `0.503`，boundary flip `0.549`，top token `<tool_call>`。
- `plus_L21H12`: route margin `1.431`，logit margin `1.500`，`<tool_call>` top1 `0.859`，boundary flip `0.920`，top token `<tool_call>`。
- `plus_L24H6`: route margin `1.747`，logit margin `1.875`，`<tool_call>` top1 `0.923`，boundary flip `0.976`，top token `<tool_call>`。
- `plus_MLP27`: route margin `2.301`，logit margin `2.500`，`<tool_call>` top1 `0.977`，boundary flip `0.999`，top token `<tool_call>`。

## L21H1 vs L21H12：限制性比较

- 固定 `MLP19 + L20H5` 之后，只加 `L21H1` 时，`<tool_call>` top1 为 `0.503`，logit margin 为 `0.125`。
- 固定 `MLP19 + L20H5` 之后，只加 `L21H12` 时，`<tool_call>` top1 为 `0.683`，logit margin 为 `0.750`。
- 加上 `L24H6` 后，`L21H1` 分支到 `0.738` / `0.750`，`L21H12` 分支到 `0.840` / `1.250`。
因此 `L21H1` 仍应该放在 support：它确实能把 `<tool_call>` 推过决策边界，但单独分支强度、与 `L24H6` 的配合强度、以及旧的 `-> MLP27` transmission 都仍弱于 `L21H12`。`L21H12` 仍更像 protocol-heavy router / binder，因此保留 anchor 更稳。

## MLP19 -> MLP27：parallel fanout 还是 bypass

- `MLP19 + MLP27` 这条 shortcut node-set 的 `<tool_call>` top1 为 `0.690`，logit margin 为 `0.625`。
- `MLP19 + late_heads` 为 `0.923` / `1.875`；`late_heads + MLP27` 为 `0.937` / `2.125`；完整链 `full_chain` 为 `0.977` / `2.500`。
- 再结合旧的 fanout 审计，`MLP19 -> MLP27` 的 route mediated ratio 为 `0.145`，确实是强接收之一。
当前最稳的写法是：`MLP19 -> MLP27` 存在明显 direct receipt，但它更像与 late-head 链并行的强 fanout，而不是已经能独立冻结成 bypass 主路。因为一旦只保留 shortcut node-set，恢复效果仍不如包含 `L20H5/L21H12/L24H6` 的链。

## 更新后的节点分层

- anchor nodes: `L20H5, L21H12, L24H6, MLP27`
- support nodes: `MLP19, L21H1`
- candidate nodes: `L25H10, L25H13, L26H15, L27H7, MLP24, MLP25, MLP26`

## 当前最可信的机制描述

`MLP19` 先把上游 route state 扇出到 construction 区；`L20H5` 把这份状态绑定到文件名和函数体对象；随后 `L21H1` 与 `L21H12` 分化成两条 late routing，其中 `L21H1` 更偏 output-start/example，`L21H12` 更偏 tool-call example / instruction tail / protocol；`L24H6` 把已绑定状态压进调用起始格式；`MLP27` 最终把 `<tool_call>` 方向强写成首词偏好。`<tool_call>` 从 `L20H5` 开始被推向目标方向，在 `plus_L21H1` 首次过决策边界，在 `plus_L21H1` 首次过半，并在 `MLP27` 达到最强。

## 哪些说法可以强写

- `MLP27` 是主 writer。证据最强：clean direct margin `10.852`，平均 direct-logit lens rank=`1`。
- `L24H6` 更像 formatter / protocol commitment。证据最强：clean direct margin `2.255`，并且它把 stagewise top1 从 `0.859` 推到 `0.923`。
- `L20H5` 是 construction ingress / payload binder。证据最强：`MLP19 -> L20H5` mediated `0.044`，同时 `L20H5` 的 delta margin 为 `0.018`。
- `L21H1` 与 `L21H12` 功能不同，不是简单冗余。

## 哪些说法必须弱写

- `MLP19 -> MLP27` 是独立 bypass 主路：当前证据还不够。
- `L21H1` 可以升格成 anchor：当前限制性比较仍不支持。
- 候选晚层头可以升格：当前 candidate patch 与写出证据仍然偏弱。

## 论文风格总结

修正 stagewise 布尔汇总 bug 之后，Tool-Call Construction 的主线并没有被推翻，但它的强度表述被校正了：`<tool_call>` 不是在 `L21H1` 之后立刻接近满比例成形，而是在 `L21H1` 首次过半、在 `L21H12/L24H6` 进一步稳固、最终由 `MLP27` 写到最强。当前最可信的机制仍是：`MLP19` 提供 tool-route state 的 late fanout，`L20H5` 做 payload 绑定，`L21H1/L21H12` 做分化的 late routing，`L24H6` 做 protocol commitment，`MLP27` 做最终 writer。最强证据来自三组 full-run 结果的收敛：其一，修正后的 stagewise trajectory 和 top-token 变化图直接给出了 `<tool_call>` 从弱偏置到稳定首词的轨迹；其二，writeout / residual projection 仍显示 `L24H6` 与 `MLP27` 是最强的 late writer 节点；其三，限制性比较显示 `L21H12` 分支比 `L21H1` 分支更稳定、更接近 protocol binder，而 `MLP19 -> MLP27` 虽强，但仍更像 parallel fanout，而不是已经独立成路的 bypass。
