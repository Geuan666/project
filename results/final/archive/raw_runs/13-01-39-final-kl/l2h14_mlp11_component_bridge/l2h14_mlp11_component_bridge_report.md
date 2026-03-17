# L2H14 -> MLP11 Component Bridge Report

## Main Result

Inside the fixed 24-node circuit, `L2H14` is the only earliest-priority head that both precedes `MLP11` and retains non-zero `MLP11`-mediated tool transmission.

## Read vs Write Split

- Clean rank-1 tokens: ` query,  the, \n\n, assistant,  below,  how`
- Base rank-1 tokens: ` the,  query, \n\n, assistant,  below,  how`
- Clean span density `file_target`: `0.0085`
- Clean span density `function_body_anchor`: `0.0055`
- Clean span density `lead_phrase`: `0.0161`
- Clean span density `tail_suffix`: `0.0069`
- Clean span density `task_body`: `0.0016`

- `k`: source rescue `0.066`, blocked-by-MLP11 `0.055`, mediated `0.009`.
- `q`: source rescue `0.004`, blocked-by-MLP11 `0.000`, mediated `0.000`.
- `v`: source rescue `0.038`, blocked-by-MLP11 `0.060`, mediated `-0.018`.
- `z`: source rescue `0.042`, blocked-by-MLP11 `0.030`, mediated `0.009`.

- `MLP11 resid_mid`: `<tool_call>` delta `0.031`, distractor delta `0.107`.
- `MLP11 resid_post`: `<tool_call>` delta `0.000`, distractor delta `0.070`.

## Bottom Line

The strongest mechanistic split is: `L2H14` reads the instruction opening on the lead-phrase side, and the part that reaches `MLP11` is carried by the resulting head output rather than by a later downstream carrier.
