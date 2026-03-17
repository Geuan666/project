# L2H14 -> MLP11 Component Bridge Report

## Main Result

Inside the fixed 24-node circuit, `L2H14` is the only earliest-priority head that both precedes `MLP11` and retains non-zero `MLP11`-mediated tool transmission.

## Read vs Write Split

- Clean rank-1 tokens: ` query,  the,  below`
- Base rank-1 tokens: ` query,  the`
- Clean span density `file_target`: `0.0083`
- Clean span density `function_body_anchor`: `0.0047`
- Clean span density `lead_phrase`: `0.0131`
- Clean span density `tail_suffix`: `0.0074`
- Clean span density `task_body`: `0.0013`

- `k`: source rescue `0.064`, blocked-by-MLP11 `0.019`, mediated `0.098`.
- `q`: source rescue `0.051`, blocked-by-MLP11 `-0.069`, mediated `0.064`.
- `v`: source rescue `0.100`, blocked-by-MLP11 `0.034`, mediated `0.113`.
- `z`: source rescue `0.130`, blocked-by-MLP11 `-0.051`, mediated `0.010`.

- `MLP11 resid_mid`: `<tool_call>` delta `0.000`, distractor delta `0.137`.
- `MLP11 resid_post`: `<tool_call>` delta `-0.031`, distractor delta `0.035`.

## Bottom Line

The strongest mechanistic split is: `L2H14` reads the instruction opening on the lead-phrase side, and the part that reaches `MLP11` is carried by the resulting head output rather than by a later downstream carrier.
