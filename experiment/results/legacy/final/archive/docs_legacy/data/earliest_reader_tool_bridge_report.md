# Earliest Reader Tool Bridge Report

## Updated End-To-End Chain

1. `L2H14` is the strongest current earliest head-level candidate inside the 24-node circuit.
2. It reads an early user-side object bundle that includes the instruction opening and answer-delivery scaffold, not a naked first verb token.
3. Its tool-side effect enters the earliest strong scaffold through `MLP11`.
4. `MLP11 -> MLP16 -> MLP19` amplifies that state into a shared answer-opening scaffold.
5. That scaffold then enters the already-established late tool route `L20H5 -> L21H1/L21H12 -> L24H6 -> MLP27`.
6. The no-tool competitive route remains `L16H4 -> MLP17 -> L23H6`; this audit does not re-open that story.

## Earliest Reader Evidence

- `L2H14` / L2: best causal span `lead_phrase`, `q/z/v = 0.004/0.042/0.038`, clean top tokens ` query,  the, \n\n, assistant,  below,  how`
- `L16H8` / L16: best causal span `tail_suffix`, `q/z/v = 0.095/0.272/0.000`, clean top tokens `\n,  based, }\n,  function,  {\n,  call`
- `L17H2` / L17: best causal span `file_target`, `q/z/v = 0.234/0.251/0.000`, clean top tokens `<|im_start|>, \n`
- `L17H8` / L17: best causal span `file_target`, `q/z/v = 0.292/0.318/0.008`, clean top tokens `<|im_start|>, \n`
- `L20H5` / L20: best causal span `function_body_anchor`, `q/z/v = 0.156/0.308/0.000`, clean top tokens `></, .py, .cpp, </think>, .java`
- `L2H14` clean span densities: lead `0.0161`, file `0.0085`, function-body `0.0055`, tail `0.0069`, task `0.0016`.
- `L20H5` clean span densities: lead `0.0002`, file `0.0378`, function-body `0.0111`, tail `0.0040`, task `0.0006`.

## Reader To MLP11 Transmission

- `L2H14` source-only rescue `0.042`; blocking `MLP11` leaves `0.030`; mediated drop `0.009`.
- `L2H14` source-only rescue `0.042`; blocking `MLP16` leaves `0.042`; mediated drop `0.000`.
- `L2H14` source-only rescue `0.042`; blocking `MLP19` leaves `0.044`; mediated drop `0.000`.
- `L16H8` with `MLP11` blocked: source `0.272`, blocked `0.272`, mediated `0.000`.
- `L17H2` with `MLP11` blocked: source `0.251`, blocked `0.251`, mediated `0.000`.
- `L17H8` with `MLP11` blocked: source `0.318`, blocked `0.318`, mediated `0.000`.
- `L20H5` with `MLP11` blocked: source `0.308`, blocked `0.308`, mediated `0.000`.

## Scaffold Writer Evidence

- `MLP11`: `<tool_call>` delta `0.750`, distractor delta `-0.875`, top increased tokens `<tool_call>,  threads, ewe,  τ, .hashCode, from`.
- `MLP16`: `<tool_call>` delta `1.125`, distractor delta `-1.750`, top increased tokens `<tool_call>, 扺,  τ, ":[", opup, 抵`.
- `MLP19`: `<tool_call>` delta `1.250`, distractor delta `-1.500`, top increased tokens ` τ, <tool_call>,  �, 拉开, .equal,  lắm`.

## Tool-Side Accumulation

- stage 1 / `L2H14`: rescue `0.042`, tool-top1 `0.000`, boundary `0.000`.
- stage 2 / `L2H14|MLP11`: rescue `0.350`, tool-top1 `0.037`, boundary `0.036`.
- stage 3 / `L2H14|MLP11|MLP16`: rescue `0.577`, tool-top1 `0.131`, boundary `0.127`.
- stage 4 / `L2H14|MLP11|MLP16|MLP19`: rescue `0.846`, tool-top1 `0.405`, boundary `0.427`.
- stage 5 / `L2H14|MLP11|MLP16|MLP19|L20H5`: rescue `0.902`, tool-top1 `0.545`, boundary `0.578`.
- stage 6 / `L2H14|MLP11|MLP16|MLP19|L20H5|L21H1`: rescue `0.954`, tool-top1 `0.739`, boundary `0.808`.
- stage 7 / `L2H14|MLP11|MLP16|MLP19|L20H5|L21H1|L21H12`: rescue `0.990`, tool-top1 `0.913`, boundary `0.959`.
- stage 8 / `L2H14|MLP11|MLP16|MLP19|L20H5|L21H1|L21H12|L24H6`: rescue `0.993`, tool-top1 `0.947`, boundary `0.985`.
- stage 9 / `L2H14|MLP11|MLP16|MLP19|L20H5|L21H1|L21H12|L24H6|MLP27`: rescue `0.998`, tool-top1 `0.989`, boundary `1.000`.

## Bottom Line

The strongest full-chain statement remains: `L2H14 -> MLP11 -> MLP16 -> MLP19 -> L20H5 -> L21H1/L21H12 -> L24H6 -> MLP27`.
What is now strong is the bridge from `L2H14` into `MLP11`: it is structurally unique inside the circuit and its effect is specifically reduced by `MLP11` block.
What is still not fully solved is the exact object-language feature that `L2H14` reads first. It still looks like an early user-side object bundle rather than a single isolated minimal-cue token.
