# Within-Opening Matched Counterfactual Audit

## Main Result

This audit holds the full prompt fixed and changes only the instruction opening with matched tool-like and no-tool-like openings.
It asks whether `L2H14` and `MLP11` group variants by semantic class or by local opening frame.

## Behavior

- `original_clean`: decision `3.203`, tool-top1 `1.000`, no-tool-top1 `0.000`, L2H14 lead density `0.0161`.
- `original_corrupt`: decision `-4.562`, tool-top1 `0.000`, no-tool-top1 `0.999`, L2H14 lead density `0.0402`.
- `tool_out`: decision `4.535`, tool-top1 `0.994`, no-tool-top1 `0.006`, L2H14 lead density `0.0312`.
- `no_tool_out`: decision `-3.343`, tool-top1 `0.026`, no-tool-top1 `0.965`, L2H14 lead density `0.0158`.
- `tool_manually`: decision `1.462`, tool-top1 `0.793`, no-tool-top1 `0.203`, L2H14 lead density `0.0130`.
- `no_tool_manually`: decision `-4.394`, tool-top1 `0.005`, no-tool-top1 `0.987`, L2H14 lead density `0.0145`.
- `tool_properly`: decision `2.856`, tool-top1 `0.941`, no-tool-top1 `0.059`, L2H14 lead density `0.0120`.
- `no_tool_properly`: decision `-4.082`, tool-top1 `0.035`, no-tool-top1 `0.941`, L2H14 lead density `0.0101`.

## Semantic vs Frame Clustering

- `l2h14_lead_k`: same-semantic cross-frame cosine `0.924`, same-frame opposite-semantic cosine `0.965`, gap `-0.042`, semantic-wins `0.000`.
- `l2h14_lead_k_centered`: same-semantic cross-frame cosine `-0.295`, same-frame opposite-semantic cosine `0.484`, gap `-0.779`, semantic-wins `0.000`.
- `l2h14_z`: same-semantic cross-frame cosine `0.989`, same-frame opposite-semantic cosine `0.993`, gap `-0.004`, semantic-wins `0.000`.
- `l2h14_z_centered`: same-semantic cross-frame cosine `-0.234`, same-frame opposite-semantic cosine `0.377`, gap `-0.611`, semantic-wins `0.000`.
- `mlp11_out`: same-semantic cross-frame cosine `0.993`, same-frame opposite-semantic cosine `0.993`, gap `-0.000`, semantic-wins `0.400`.
- `mlp11_out_centered`: same-semantic cross-frame cosine `-0.038`, same-frame opposite-semantic cosine `-0.019`, gap `-0.018`, semantic-wins `0.456`.

## Centroid Alignment

- `l2h14_lead_k` / `original_clean`: semantic-margin `0.013`, semantic-correct `0.663`.
- `l2h14_lead_k_centered` / `original_clean`: semantic-margin `0.427`, semantic-correct `0.663`.
- `l2h14_z` / `original_clean`: semantic-margin `-0.001`, semantic-correct `0.408`.
- `l2h14_z_centered` / `original_clean`: semantic-margin `-0.268`, semantic-correct `0.408`.
- `mlp11_out` / `original_clean`: semantic-margin `0.004`, semantic-correct `1.000`.
- `mlp11_out_centered` / `original_clean`: semantic-margin `1.120`, semantic-correct `1.000`.
- `l2h14_lead_k` / `original_corrupt`: semantic-margin `-0.006`, semantic-correct `0.407`.
- `l2h14_lead_k_centered` / `original_corrupt`: semantic-margin `-0.247`, semantic-correct `0.407`.
- `l2h14_z` / `original_corrupt`: semantic-margin `-0.005`, semantic-correct `0.331`.
- `l2h14_z_centered` / `original_corrupt`: semantic-margin `-0.797`, semantic-correct `0.323`.
- `mlp11_out` / `original_corrupt`: semantic-margin `0.003`, semantic-correct `0.923`.
- `mlp11_out_centered` / `original_corrupt`: semantic-margin `0.615`, semantic-correct `0.935`.
- `l2h14_lead_k` / `tool_out`: semantic-margin `-0.013`, semantic-correct `0.000`.
- `l2h14_lead_k_centered` / `tool_out`: semantic-margin `0.005`, semantic-correct `1.000`.
- `l2h14_z` / `tool_out`: semantic-margin `-0.005`, semantic-correct `0.000`.
- `l2h14_z_centered` / `tool_out`: semantic-margin `-0.039`, semantic-correct `0.006`.
- `mlp11_out` / `tool_out`: semantic-margin `0.003`, semantic-correct `1.000`.
- `mlp11_out_centered` / `tool_out`: semantic-margin `0.662`, semantic-correct `1.000`.
- `l2h14_lead_k` / `no_tool_out`: semantic-margin `-0.023`, semantic-correct `0.000`.
- `l2h14_lead_k_centered` / `no_tool_out`: semantic-margin `-0.368`, semantic-correct `0.000`.
- `l2h14_z` / `no_tool_out`: semantic-margin `-0.002`, semantic-correct `0.000`.
- `l2h14_z_centered` / `no_tool_out`: semantic-margin `-0.406`, semantic-correct `0.000`.
- `mlp11_out` / `no_tool_out`: semantic-margin `-0.001`, semantic-correct `0.152`.
- `mlp11_out_centered` / `no_tool_out`: semantic-margin `0.027`, semantic-correct `0.539`.
- `l2h14_lead_k` / `tool_manually`: semantic-margin `-0.047`, semantic-correct `0.000`.
- `l2h14_lead_k_centered` / `tool_manually`: semantic-margin `-1.099`, semantic-correct `0.000`.
- `l2h14_z` / `tool_manually`: semantic-margin `-0.006`, semantic-correct `0.000`.
- `l2h14_z_centered` / `tool_manually`: semantic-margin `-1.348`, semantic-correct `0.000`.
- `mlp11_out` / `tool_manually`: semantic-margin `0.002`, semantic-correct `0.999`.
- `mlp11_out_centered` / `tool_manually`: semantic-margin `0.810`, semantic-correct `1.000`.
- `l2h14_lead_k` / `no_tool_manually`: semantic-margin `0.004`, semantic-correct `1.000`.
- `l2h14_lead_k_centered` / `no_tool_manually`: semantic-margin `0.354`, semantic-correct `1.000`.
- `l2h14_z` / `no_tool_manually`: semantic-margin `0.002`, semantic-correct `1.000`.
- `l2h14_z_centered` / `no_tool_manually`: semantic-margin `0.969`, semantic-correct `1.000`.
- `mlp11_out` / `no_tool_manually`: semantic-margin `0.002`, semantic-correct `0.999`.
- `mlp11_out_centered` / `no_tool_manually`: semantic-margin `0.679`, semantic-correct `1.000`.
- `l2h14_lead_k` / `tool_properly`: semantic-margin `-0.035`, semantic-correct `0.000`.
- `l2h14_lead_k_centered` / `tool_properly`: semantic-margin `-0.712`, semantic-correct `0.000`.
- `l2h14_z` / `tool_properly`: semantic-margin `-0.007`, semantic-correct `0.000`.
- `l2h14_z_centered` / `tool_properly`: semantic-margin `-0.781`, semantic-correct `0.000`.
- `mlp11_out` / `tool_properly`: semantic-margin `-0.001`, semantic-correct `0.116`.
- `mlp11_out_centered` / `tool_properly`: semantic-margin `0.133`, semantic-correct `0.734`.
- `l2h14_lead_k` / `no_tool_properly`: semantic-margin `0.007`, semantic-correct `1.000`.
- `l2h14_lead_k_centered` / `no_tool_properly`: semantic-margin `0.505`, semantic-correct `1.000`.
- `l2h14_z` / `no_tool_properly`: semantic-margin `0.002`, semantic-correct `1.000`.
- `l2h14_z_centered` / `no_tool_properly`: semantic-margin `1.012`, semantic-correct `1.000`.
- `mlp11_out` / `no_tool_properly`: semantic-margin `0.004`, semantic-correct `1.000`.
- `mlp11_out_centered` / `no_tool_properly`: semantic-margin `0.851`, semantic-correct `1.000`.

## L2H14 Top Tokens

- `original_clean` rank-1 tokens: ` query,  the, \n\n, assistant,  below,  how`
- `original_corrupt` rank-1 tokens: ` the,  query, \n\n, assistant,  below,  how`
- `tool_out` rank-1 tokens: ` query,  the, \n\n,  how, assistant,  below`
- `no_tool_out` rank-1 tokens: ` query, \n\n, assistant,  below,  the,  how`
- `tool_manually` rank-1 tokens: ` query, \n\n, assistant,  how,  below, What`
- `no_tool_manually` rank-1 tokens: ` query, \n\n, assistant,  how,  the,  below`
- `tool_properly` rank-1 tokens: ` query, \n\n, assistant,  how,  below,  choices`
- `no_tool_properly` rank-1 tokens: ` query, \n\n, assistant,  how,  below,  choices`

## Bottom Line

If `L2H14` and `MLP11` group same-semantic openings across different local frames more tightly than matched frame-opposites, then the earliest reader is tracking opening semantics rather than only lexical surface.
