# Within-Opening Matched Counterfactual Audit

## Main Result

This audit holds the full prompt fixed and changes only the instruction opening with matched tool-like and no-tool-like openings.
It asks whether `L2H14` and `MLP11` group variants by semantic class or by local opening frame.

## Behavior

- `original_clean`: decision `3.391`, tool-top1 `1.000`, no-tool-top1 `0.000`, L2H14 lead density `0.0213`.
- `original_corrupt`: decision `-4.734`, tool-top1 `0.000`, no-tool-top1 `1.000`, L2H14 lead density `0.0460`.
- `tool_out`: decision `4.745`, tool-top1 `1.000`, no-tool-top1 `0.000`, L2H14 lead density `0.0316`.
- `no_tool_out`: decision `-3.122`, tool-top1 `0.050`, no-tool-top1 `0.950`, L2H14 lead density `0.0159`.
- `tool_manually`: decision `2.283`, tool-top1 `0.900`, no-tool-top1 `0.100`, L2H14 lead density `0.0133`.
- `no_tool_manually`: decision `-4.396`, tool-top1 `0.050`, no-tool-top1 `0.950`, L2H14 lead density `0.0148`.
- `tool_properly`: decision `3.467`, tool-top1 `1.000`, no-tool-top1 `0.000`, L2H14 lead density `0.0125`.
- `no_tool_properly`: decision `-3.290`, tool-top1 `0.050`, no-tool-top1 `0.900`, L2H14 lead density `0.0105`.

## Semantic vs Frame Clustering

- `l2h14_lead_k`: same-semantic cross-frame cosine `0.924`, same-frame opposite-semantic cosine `0.965`, gap `-0.042`, semantic-wins `0.000`.
- `l2h14_lead_k_centered`: same-semantic cross-frame cosine `-0.295`, same-frame opposite-semantic cosine `0.484`, gap `-0.779`, semantic-wins `0.000`.
- `l2h14_z`: same-semantic cross-frame cosine `0.988`, same-frame opposite-semantic cosine `0.993`, gap `-0.005`, semantic-wins `0.000`.
- `l2h14_z_centered`: same-semantic cross-frame cosine `-0.230`, same-frame opposite-semantic cosine `0.378`, gap `-0.608`, semantic-wins `0.000`.
- `mlp11_out`: same-semantic cross-frame cosine `0.993`, same-frame opposite-semantic cosine `0.994`, gap `-0.000`, semantic-wins `0.400`.
- `mlp11_out_centered`: same-semantic cross-frame cosine `-0.029`, same-frame opposite-semantic cosine `-0.018`, gap `-0.009`, semantic-wins `0.400`.

## Centroid Alignment

- `l2h14_lead_k` / `original_clean`: semantic-margin `0.020`, semantic-correct `0.700`.
- `l2h14_lead_k_centered` / `original_clean`: semantic-margin `0.543`, semantic-correct `0.700`.
- `l2h14_z` / `original_clean`: semantic-margin `-0.000`, semantic-correct `0.500`.
- `l2h14_z_centered` / `original_clean`: semantic-margin `-0.068`, semantic-correct `0.500`.
- `mlp11_out` / `original_clean`: semantic-margin `0.004`, semantic-correct `1.000`.
- `mlp11_out_centered` / `original_clean`: semantic-margin `1.147`, semantic-correct `1.000`.
- `l2h14_lead_k` / `original_corrupt`: semantic-margin `-0.000`, semantic-correct `0.500`.
- `l2h14_lead_k_centered` / `original_corrupt`: semantic-margin `-0.031`, semantic-correct `0.500`.
- `l2h14_z` / `original_corrupt`: semantic-margin `-0.004`, semantic-correct `0.400`.
- `l2h14_z_centered` / `original_corrupt`: semantic-margin `-0.512`, semantic-correct `0.400`.
- `mlp11_out` / `original_corrupt`: semantic-margin `0.003`, semantic-correct `0.950`.
- `mlp11_out_centered` / `original_corrupt`: semantic-margin `0.702`, semantic-correct `0.950`.
- `l2h14_lead_k` / `tool_out`: semantic-margin `-0.013`, semantic-correct `0.000`.
- `l2h14_lead_k_centered` / `tool_out`: semantic-margin `0.005`, semantic-correct `1.000`.
- `l2h14_z` / `tool_out`: semantic-margin `-0.005`, semantic-correct `0.000`.
- `l2h14_z_centered` / `tool_out`: semantic-margin `-0.042`, semantic-correct `0.000`.
- `mlp11_out` / `tool_out`: semantic-margin `0.003`, semantic-correct `1.000`.
- `mlp11_out_centered` / `tool_out`: semantic-margin `0.669`, semantic-correct `1.000`.
- `l2h14_lead_k` / `no_tool_out`: semantic-margin `-0.023`, semantic-correct `0.000`.
- `l2h14_lead_k_centered` / `no_tool_out`: semantic-margin `-0.368`, semantic-correct `0.000`.
- `l2h14_z` / `no_tool_out`: semantic-margin `-0.002`, semantic-correct `0.000`.
- `l2h14_z_centered` / `no_tool_out`: semantic-margin `-0.369`, semantic-correct `0.000`.
- `mlp11_out` / `no_tool_out`: semantic-margin `-0.001`, semantic-correct `0.050`.
- `mlp11_out_centered` / `no_tool_out`: semantic-margin `0.140`, semantic-correct `0.600`.
- `l2h14_lead_k` / `tool_manually`: semantic-margin `-0.047`, semantic-correct `0.000`.
- `l2h14_lead_k_centered` / `tool_manually`: semantic-margin `-1.099`, semantic-correct `0.000`.
- `l2h14_z` / `tool_manually`: semantic-margin `-0.006`, semantic-correct `0.000`.
- `l2h14_z_centered` / `tool_manually`: semantic-margin `-1.347`, semantic-correct `0.000`.
- `mlp11_out` / `tool_manually`: semantic-margin `0.002`, semantic-correct `1.000`.
- `mlp11_out_centered` / `tool_manually`: semantic-margin `0.838`, semantic-correct `1.000`.
- `l2h14_lead_k` / `no_tool_manually`: semantic-margin `0.004`, semantic-correct `1.000`.
- `l2h14_lead_k_centered` / `no_tool_manually`: semantic-margin `0.355`, semantic-correct `1.000`.
- `l2h14_z` / `no_tool_manually`: semantic-margin `0.002`, semantic-correct `1.000`.
- `l2h14_z_centered` / `no_tool_manually`: semantic-margin `0.969`, semantic-correct `1.000`.
- `mlp11_out` / `no_tool_manually`: semantic-margin `0.002`, semantic-correct `1.000`.
- `mlp11_out_centered` / `no_tool_manually`: semantic-margin `0.679`, semantic-correct `1.000`.
- `l2h14_lead_k` / `tool_properly`: semantic-margin `-0.035`, semantic-correct `0.000`.
- `l2h14_lead_k_centered` / `tool_properly`: semantic-margin `-0.712`, semantic-correct `0.000`.
- `l2h14_z` / `tool_properly`: semantic-margin `-0.007`, semantic-correct `0.000`.
- `l2h14_z_centered` / `tool_properly`: semantic-margin `-0.777`, semantic-correct `0.000`.
- `mlp11_out` / `tool_properly`: semantic-margin `-0.001`, semantic-correct `0.050`.
- `mlp11_out_centered` / `tool_properly`: semantic-margin `0.158`, semantic-correct `0.700`.
- `l2h14_lead_k` / `no_tool_properly`: semantic-margin `0.007`, semantic-correct `1.000`.
- `l2h14_lead_k_centered` / `no_tool_properly`: semantic-margin `0.505`, semantic-correct `1.000`.
- `l2h14_z` / `no_tool_properly`: semantic-margin `0.002`, semantic-correct `1.000`.
- `l2h14_z_centered` / `no_tool_properly`: semantic-margin `1.005`, semantic-correct `1.000`.
- `mlp11_out` / `no_tool_properly`: semantic-margin `0.004`, semantic-correct `1.000`.
- `mlp11_out_centered` / `no_tool_properly`: semantic-margin `0.887`, semantic-correct `1.000`.

## L2H14 Top Tokens

- `original_clean` rank-1 tokens: ` query,  the, \n\n,  below`
- `original_corrupt` rank-1 tokens: ` the,  query`
- `tool_out` rank-1 tokens: ` query,  the, \n\n`
- `no_tool_out` rank-1 tokens: ` query, \n\n,  below`
- `tool_manually` rank-1 tokens: ` query, \n\n`
- `no_tool_manually` rank-1 tokens: ` query, \n\n`
- `tool_properly` rank-1 tokens: ` query, \n\n`
- `no_tool_properly` rank-1 tokens: ` query, \n\n`

## Bottom Line

If `L2H14` and `MLP11` group same-semantic openings across different local frames more tightly than matched frame-opposites, then the earliest reader is tracking opening semantics rather than only lexical surface.
