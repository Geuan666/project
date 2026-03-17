# Delivery Object 2x2 Audit

## Main Result

This audit isolates `opening frame` and `delivery object` by constructing `Write/Develop x in solve.py/below` variants.

## Behavior

- `write_file`: decision `1.105`, tool-top1 `0.600`, no-tool-top1 `0.300`, L2H14 opening density `0.0270`, object density `0.0090`.
- `write_below`: decision `0.249`, tool-top1 `0.400`, no-tool-top1 `0.600`, L2H14 opening density `0.0260`, object density `0.0525`.
- `develop_file`: decision `-1.863`, tool-top1 `0.000`, no-tool-top1 `1.000`, L2H14 opening density `0.0179`, object density `0.0105`.
- `develop_below`: decision `-2.207`, tool-top1 `0.000`, no-tool-top1 `0.900`, L2H14 opening density `0.0164`, object density `0.0445`.

## Object vs Frame Grouping

- `l2h14_lead_k`: same-object cross-frame `0.897`, same-frame cross-object `1.000`, gap `-0.103`, object-wins `0.000`.
- `l2h14_lead_k_centered`: same-object cross-frame `-1.000`, same-frame cross-object `1.000`, gap `-2.000`, object-wins `0.000`.
- `l2h14_z`: same-object cross-frame `0.947`, same-frame cross-object `0.994`, gap `-0.047`, object-wins `0.000`.
- `l2h14_z_centered`: same-object cross-frame `-0.839`, same-frame cross-object `0.832`, gap `-1.672`, object-wins `0.000`.
- `mlp11_out`: same-object cross-frame `0.992`, same-frame cross-object `0.989`, gap `0.004`, object-wins `1.000`.
- `mlp11_out_centered`: same-object cross-frame `0.165`, same-frame cross-object `-0.280`, gap `0.452`, object-wins `1.000`.

## Object-Axis Patch

- frame `develop` / node `L2H14`: file-rescue `-0.010`, object-decision `-0.060`, boundary `0.000`.
- frame `develop` / node `MLP11`: file-rescue `0.115`, object-decision `-0.036`, boundary `0.300`.
- frame `write` / node `L2H14`: file-rescue `0.034`, object-decision `-0.319`, boundary `0.000`.
- frame `write` / node `MLP11`: file-rescue `-0.099`, object-decision `-0.625`, boundary `0.200`.

## L2H14 Top Tokens

- `write_file` rank-1 tokens: ` the`
- `write_below` rank-1 tokens: ` the`
- `develop_file` rank-1 tokens: ` the`
- `develop_below` rank-1 tokens: ` the`

## Bottom Line

If `MLP11` groups same-object variants across different openings and object-axis patching at `MLP11` is stronger than at `L2H14`, then delivery-object semantics first stabilizes at `MLP11`, not `L2H14`.
