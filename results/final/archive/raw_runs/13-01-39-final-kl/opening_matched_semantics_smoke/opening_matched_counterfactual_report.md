# Within-Opening Matched Counterfactual Audit

## Main Result

This audit holds the full prompt fixed and changes only the instruction opening with matched tool-like and no-tool-like openings.
It asks whether `L2H14` and `MLP11` group variants by semantic class or by local opening frame.

## Behavior

- `original_clean`: decision `4.656`, tool-top1 `1.000`, no-tool-top1 `0.000`, L2H14 lead density `0.0131`.
- `original_corrupt`: decision `-5.453`, tool-top1 `0.000`, no-tool-top1 `1.000`, L2H14 lead density `0.0460`.
- `tool_out`: decision `4.549`, tool-top1 `1.000`, no-tool-top1 `0.000`, L2H14 lead density `0.0317`.
- `no_tool_out`: decision `-5.101`, tool-top1 `0.000`, no-tool-top1 `1.000`, L2H14 lead density `0.0156`.
- `tool_manually`: decision `1.822`, tool-top1 `0.800`, no-tool-top1 `0.200`, L2H14 lead density `0.0131`.
- `no_tool_manually`: decision `-4.540`, tool-top1 `0.000`, no-tool-top1 `1.000`, L2H14 lead density `0.0145`.
- `tool_properly`: decision `3.047`, tool-top1 `1.000`, no-tool-top1 `0.000`, L2H14 lead density `0.0120`.
- `no_tool_properly`: decision `-3.790`, tool-top1 `0.100`, no-tool-top1 `0.800`, L2H14 lead density `0.0104`.

## Semantic vs Frame Clustering

- `l2h14_z`: same-semantic cross-frame cosine `0.988`, same-frame opposite-semantic cosine `0.992`, gap `-0.005`, semantic-wins `0.000`.
- `mlp11_out`: same-semantic cross-frame cosine `0.994`, same-frame opposite-semantic cosine `0.994`, gap `-0.000`, semantic-wins `0.400`.

## Centroid Alignment

- `l2h14_z` / `original_clean`: semantic-margin `-0.002`, semantic-correct `0.400`.
- `mlp11_out` / `original_clean`: semantic-margin `0.005`, semantic-correct `1.000`.
- `l2h14_z` / `original_corrupt`: semantic-margin `-0.004`, semantic-correct `0.300`.
- `mlp11_out` / `original_corrupt`: semantic-margin `0.002`, semantic-correct `0.900`.
- `l2h14_z` / `tool_out`: semantic-margin `-0.005`, semantic-correct `0.000`.
- `mlp11_out` / `tool_out`: semantic-margin `0.003`, semantic-correct `1.000`.
- `l2h14_z` / `no_tool_out`: semantic-margin `-0.002`, semantic-correct `0.000`.
- `mlp11_out` / `no_tool_out`: semantic-margin `-0.001`, semantic-correct `0.100`.
- `l2h14_z` / `tool_manually`: semantic-margin `-0.006`, semantic-correct `0.000`.
- `mlp11_out` / `tool_manually`: semantic-margin `0.002`, semantic-correct `1.000`.
- `l2h14_z` / `no_tool_manually`: semantic-margin `0.002`, semantic-correct `1.000`.
- `mlp11_out` / `no_tool_manually`: semantic-margin `0.002`, semantic-correct `1.000`.
- `l2h14_z` / `tool_properly`: semantic-margin `-0.008`, semantic-correct `0.000`.
- `mlp11_out` / `tool_properly`: semantic-margin `-0.001`, semantic-correct `0.000`.
- `l2h14_z` / `no_tool_properly`: semantic-margin `0.002`, semantic-correct `1.000`.
- `mlp11_out` / `no_tool_properly`: semantic-margin `0.004`, semantic-correct `1.000`.

## L2H14 Top Tokens

- `original_clean` rank-1 tokens: ` query, \n\n,  the,  below`
- `original_corrupt` rank-1 tokens: ` the,  query`
- `tool_out` rank-1 tokens: ` the,  query, \n\n`
- `no_tool_out` rank-1 tokens: ` query, \n\n,  below`
- `tool_manually` rank-1 tokens: ` query, \n\n`
- `no_tool_manually` rank-1 tokens: ` query, \n\n`
- `tool_properly` rank-1 tokens: ` query, \n\n`
- `no_tool_properly` rank-1 tokens: ` query, \n\n`

## Bottom Line

If `L2H14` and `MLP11` group same-semantic openings across different local frames more tightly than matched frame-opposites, then the earliest reader is tracking opening semantics rather than only lexical surface.
