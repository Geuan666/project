# Output-Route Decision Refine 主报告

## 模块目标

这次不重做整个模块，只把两个对象钉死：`route score` 的正式定义，以及 decision spine 到下游的边级传递。

## 这次只解决的两个问题

1. 把 `route score / route preference` 定义成一个可计算、可验证、可干预的对象。
2. 给 `MLP11 -> MLP16 -> MLP19` 到下游的指定边补强因果传递证据，并区分主边、并行冗余边和暂时不能强写的边。

## route score 的正式定义

对任意节点 `n`，记首个输出位置的节点激活为 `h_n(x)`。定义：

- 节点均值：`mu_n^clean = E[h_n(x_clean)]`，`mu_n^corrupt = E[h_n(x_corrupt)]`。
- local route direction：`d_n = (mu_n^clean - mu_n^corrupt) / ||mu_n^clean - mu_n^corrupt||`。
- 中心点：`m_n = (mu_n^clean + mu_n^corrupt) / 2`。
- local route score：`r_n(x) = <h_n(x) - m_n, d_n> / <mu_n^clean - m_n, d_n>`。

这个定义有两个直接性质：

- `r_n(mu_n^clean) = +1`，`r_n(mu_n^corrupt) = -1`。
- 对所有节点统一用同一符号约定：`r_n > 0` 表示更偏 tool-route，`r_n < 0` 表示更偏 direct-answer route。

因此，统一对象不是“所有层共享一条固定方向”，而是“每个节点各自有一条 local route direction，但它们都实现同一个同号标量对象 `r_n`”。
跨层几何也支持这点：`MLP11↔MLP16` cosine `0.041`，`MLP11↔MLP19` `0.051`，`MLP16↔MLP19` `-0.005`。三者几乎不共线，所以更合理的对象是“逐层重编码的连续状态”，而不是“固定向量搬运”。

进一步定义模块级对象：`R_module(x) = mean(r_MLP11(x), r_MLP16(x), r_MLP19(x))`。

## route score 的验证结果

- `MLP11`: clean `1.042`, corrupt `-1.014`, AUC `0.967`, clean>0 比例 `0.901`, corrupt<0 比例 `0.869`, 与最终 route margin 的 Spearman `0.770`。
- `MLP16`: clean `0.969`, corrupt `-0.997`, AUC `0.996`, clean>0 比例 `0.949`, corrupt<0 比例 `0.980`, 与最终 route margin 的 Spearman `0.852`。
- `MLP19`: clean `0.896`, corrupt `-1.024`, AUC `0.994`, clean>0 比例 `0.928`, corrupt<0 比例 `0.978`, 与最终 route margin 的 Spearman `0.862`。
- `R_module`: clean `1.004`, corrupt `-1.039`, AUC `0.995`, 与最终 route margin 的 Spearman `0.849`。

这些结果说明 clean/corrupt 不只在 logits 上分开，也在三个 anchor 的局部 route score 上稳定分开。

对 anchor 的 direction-only 干预结果：

- `MLP11`: patch-promote 后 route margin 变化 `1.568`，patch-erase 后 `-0.579`；inject 后本地 score 变化 `1.928`，`R_module` 变化 `0.778`，最终 route margin 变化 `1.293`；erase 后分别为 `-1.928` / `-0.771` / `-0.493`。
- `MLP16`: patch-promote 后 route margin 变化 `2.564`，patch-erase 后 `-1.532`；inject 后本地 score 变化 `1.889`，`R_module` 变化 `0.688`，最终 route margin 变化 `2.480`；erase 后分别为 `-1.889` / `-0.706` / `-1.430`。
- `MLP19`: patch-promote 后 route margin 变化 `2.517`，patch-erase 后 `-1.285`；inject 后本地 score 变化 `1.813`，`R_module` 变化 `0.604`，最终 route margin 变化 `2.528`；erase 后分别为 `-1.813` / `-0.604` / `-1.279`。

因此，`route score` 不是纯描述量；沿着 local route direction 做 inject / erase，会同时改动节点本地 score、模块平均 score 和最终输出边界。

## 边级传递结果

下面的边结论只基于这次新做的强因果审计：source-only patch、target block、以及 target local route score mediation。

- `MLP11->MLP16`: promote route mediation `0.154`, erase route mediation `0.053`, promote target-score mediation `0.145`, erase target-score mediation `0.150`, 标签 `strong`。
- `MLP16->MLP19`: promote route mediation `0.095`, erase route mediation `0.059`, promote target-score mediation `0.105`, erase target-score mediation `0.128`, 标签 `strong`。
- `MLP16->MLP17`: promote route mediation `0.148`, erase route mediation `0.094`, promote target-score mediation `0.209`, erase target-score mediation `0.245`, 标签 `strong`。
- `MLP19->L20H5`: promote route mediation `0.044`, erase route mediation `0.035`, promote target-score mediation `0.260`, erase target-score mediation `0.356`, 标签 `weak`。
- `MLP19->L21H12`: promote route mediation `0.058`, erase route mediation `0.028`, promote target-score mediation `0.127`, erase target-score mediation `0.178`, 标签 `weak`。
- `MLP19->MLP27`: promote route mediation `0.145`, erase route mediation `0.059`, promote target-score mediation `0.279`, erase target-score mediation `0.206`, 标签 `weak`。
- `MLP19->L23H6`: promote route mediation `0.052`, erase route mediation `0.033`, promote target-score mediation `0.155`, erase target-score mediation `0.267`, 标签 `weak`。

与 group block 对照：

- `MLP19->tool_out_group`: promote group mediation `0.196`, erase group mediation `0.090`。
- `MLP19->full_out_group`: promote group mediation `0.212`, erase group mediation `0.103`。

如果 group block 明显强于单边 block，说明单边更像并行冗余入口，而不是唯一瓶颈。

## 强写结论

- anchor node: `MLP11`
- anchor node: `MLP16`
- anchor node: `MLP19`
- strong edge: `MLP11->MLP16`
- strong edge: `MLP16->MLP19`
- strong edge: `MLP16->MLP17`

## 弱写结论

- support node: `L2H14`
- support node: `MLP12`
- support node: `L20H5`
- support node: `L21H12`
- support node: `MLP17`
- support node: `MLP27`
- support node: `L23H6`
- weak edge: `MLP19->L20H5`
- weak edge: `MLP19->L21H12`
- weak edge: `MLP19->MLP27`
- weak edge: `MLP19->L23H6`

## 需要降级的旧说法

- 不能把 `route score` 写成一条固定跨层向量；现在只能写成“逐层重编码的同号标量对象”。
- 不能把 `MLP19` 直接写成 single bottleneck to construction；如果 group block 远强于单边 block，就只能写它是 late fanout hub。
- `MLP16 -> MLP17` 若只有分支级证据而缺更强的 route mediation，就只能写成 shared-to-suppress fork，不写成唯一主边。

## 仍未解决的问题

- `MLP11` 的 local route direction 还能不能进一步分解成更窄的语义子方向，目前没有必要的新证据。
- `MLP19 -> MLP27` 若保留强 mediation，但和 group block 相比仍不构成唯一瓶颈，那么还需要更细的 exclusion patch 才能区分 direct edge 与 parallel receipt。
- `L20H5` 与 `L21H12` 的并行冗余程度目前只能相对比较，不能写成精确比例分解。

## 论文主文可用结论

我们将 Output-Route Decision 的核心对象定义为一个节点局部、符号统一的 route score：在每个 anchor 节点上，用 clean 与 corrupt 均值差定义 local route direction，并用 midpoint-centered projection 定义 local route score，使正值表示 tool-route 偏好、负值表示 direct-answer 偏好。`MLP11`、`MLP16` 和 `MLP19` 并不共享同一跨层向量，但它们都稳定实现同一个逐层重编码的连续 route state；该 state 在 clean/corrupt 条件下可稳定分离，并在 direction-only inject / erase 后同步改变模块平均 score 与最终 route margin。边级上，`MLP11 -> MLP16` 与 `MLP16 -> MLP19` 构成最可信的 decision spine 主边；`MLP16 -> MLP17` 表明 route state 已经开始分叉到 direct-answer 分支，但其唯一性仍弱于主 spine。到 late stage，`MLP19` 通过多个并行接收边把 route state 分发到 tool-side 与 suppressive-side，下游表现更像 fanout hub 而不是单边瓶颈。

