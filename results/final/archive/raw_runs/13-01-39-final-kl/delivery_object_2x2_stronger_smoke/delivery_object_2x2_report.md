# Delivery Object 2x2 Audit

## Main Result

This audit isolates `opening frame` and `delivery object` by constructing `Write/Develop x in solve.py/below` variants.

## Behavior

- `write_file`: decision `1.277`, tool-top1 `0.600`, no-tool-top1 `0.400`, L2H14 opening density `0.0290`, object density `0.0092`.
- `write_answer`: decision `0.181`, tool-top1 `0.300`, no-tool-top1 `0.650`, L2H14 opening density `0.0270`, object density `0.0289`.
- `develop_file`: decision `-2.648`, tool-top1 `0.000`, no-tool-top1 `1.000`, L2H14 opening density `0.0177`, object density `0.0114`.
- `develop_answer`: decision `-4.531`, tool-top1 `0.000`, no-tool-top1 `0.950`, L2H14 opening density `0.0159`, object density `0.0371`.

## Object vs Frame Grouping

- `l2h14_lead_k`: same-object cross-frame `0.897`, same-frame cross-object `1.000`, gap `-0.103`, object-wins `0.000`.
- `l2h14_lead_k_centered`: same-object cross-frame `-1.000`, same-frame cross-object `1.000`, gap `-2.000`, object-wins `0.000`.
- `l2h14_z`: same-object cross-frame `0.953`, same-frame cross-object `0.960`, gap `-0.011`, object-wins `0.200`.
- `l2h14_z_centered`: same-object cross-frame `-0.249`, same-frame cross-object `0.238`, gap `-0.486`, object-wins `0.050`.
- `mlp11_out`: same-object cross-frame `0.992`, same-frame cross-object `0.973`, gap `0.019`, object-wins `1.000`.
- `mlp11_out_centered`: same-object cross-frame `0.532`, same-frame cross-object `-0.606`, gap `1.136`, object-wins `1.000`.

## Object-Axis Patch

- frame `develop` / node `L2H14`: file-rescue `-0.050`, object-decision `-0.074`, boundary `0.000`.
- frame `develop` / node `MLP11`: file-rescue `-0.205`, object-decision `-0.011`, boundary `0.400`.
- frame `write` / node `L2H14`: file-rescue `-0.034`, object-decision `-0.393`, boundary `0.000`.
- frame `write` / node `MLP11`: file-rescue `0.118`, object-decision `0.227`, boundary `0.550`.

## L2H14 Top Tokens

- `write_file` rank-1 tokens: ` the`
- `write_answer` rank-1 tokens: ` the,  answer`
- `develop_file` rank-1 tokens: ` the`
- `develop_answer` rank-1 tokens: ` the,  answer`

## Bottom Line

If `MLP11` groups same-object variants across different openings and object-axis patching at `MLP11` is stronger than at `L2H14`, then delivery-object semantics first stabilizes at `MLP11`, not `L2H14`.
