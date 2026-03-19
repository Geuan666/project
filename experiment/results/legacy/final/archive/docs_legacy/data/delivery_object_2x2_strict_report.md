# Delivery Object 2x2 Audit

## Main Result

This audit isolates `opening frame` and `delivery object` by constructing `Write/Develop x in solve.py/below` variants.

## Behavior

- `write_file`: decision `1.316`, tool-top1 `0.540`, no-tool-top1 `0.456`, L2H14 opening density `0.0284`, object density `0.0082`.
- `write_answer`: decision `0.092`, tool-top1 `0.239`, no-tool-top1 `0.749`, L2H14 opening density `0.0259`, object density `0.0270`.
- `develop_file`: decision `-1.994`, tool-top1 `0.000`, no-tool-top1 `0.990`, L2H14 opening density `0.0175`, object density `0.0099`.
- `develop_answer`: decision `-4.062`, tool-top1 `0.001`, no-tool-top1 `0.879`, L2H14 opening density `0.0153`, object density `0.0343`.

## Object vs Frame Grouping

- `l2h14_lead_k`: same-object cross-frame `0.897`, same-frame cross-object `1.000`, gap `-0.103`, object-wins `0.000`.
- `l2h14_lead_k_centered`: same-object cross-frame `-1.000`, same-frame cross-object `1.000`, gap `-2.000`, object-wins `0.000`.
- `l2h14_z`: same-object cross-frame `0.953`, same-frame cross-object `0.966`, gap `-0.014`, object-wins `0.137`.
- `l2h14_z_centered`: same-object cross-frame `-0.282`, same-frame cross-object `0.272`, gap `-0.554`, object-wins `0.060`.
- `mlp11_out`: same-object cross-frame `0.992`, same-frame cross-object `0.974`, gap `0.018`, object-wins `1.000`.
- `mlp11_out_centered`: same-object cross-frame `0.540`, same-frame cross-object `-0.615`, gap `1.155`, object-wins `1.000`.

## Object-Axis Patch

- frame `develop` / node `L2H14`: file-rescue `0.000`, object-decision `-0.108`, boundary `0.000`.
- frame `develop` / node `MLP11`: file-rescue `0.053`, object-decision `-0.010`, boundary `0.463`.
- frame `write` / node `L2H14`: file-rescue `-0.019`, object-decision `-0.409`, boundary `0.009`.
- frame `write` / node `MLP11`: file-rescue `0.332`, object-decision `0.141`, boundary `0.604`.

## L2H14 Top Tokens

- `write_file` rank-1 tokens: ` the`
- `write_answer` rank-1 tokens: ` the,  answer`
- `develop_file` rank-1 tokens: ` the,  how`
- `develop_answer` rank-1 tokens: ` the,  answer,  below,  how,  query`

## Bottom Line

If `MLP11` groups same-object variants across different openings and object-axis patching at `MLP11` is stronger than at `L2H14`, then delivery-object semantics first stabilizes at `MLP11`, not `L2H14`.
