# Paper Mechanism Readiness Audit

## Scope

This audit checks whether the current `results/final` package satisfies the
mechanistic-goal standard stated in `/root/autodl-tmp/project/todo.md`.

The standard is not:

- circuit correctness
- patch rescue quality
- localization faithfulness

The standard is:

- a human-understandable, object-language mechanism chain
- enough evidence to answer the two core mechanistic questions
- figures/tables that can support a paper narrative

## The Two Required Questions

1. Why does changing only a tiny lead phrase flip the first generated token from
   `<tool_call>` to `no_tool`?
2. How does the no-tool chain actually suppress the tool route?

## Audit Verdict

### Overall

`COMPLETE FOR PAPER MECHANISM USE`

### Why

- The forward chain is now paper-ready mechanistically and visually.
- The no-tool suppression chain now has a dedicated suppression-specific
  mechanism package.
- The package now contains an official figure set for the strongest new forward
  and suppression evidence.
- The formal package now has a paper-facing harmonized entrypoint and updated
  readiness verdict.

The only remaining open items are microfeature-label questions that do **not**
block the main-text mechanism story.

## Pass / Fail Checklist

| Criterion | Status | Notes |
|---|---|---|
| Circuit localization / correctness complete | PASS | Final signed circuit and validation were already done before this audit. |
| Forward mechanistic chain exists in object language | PASS | `L2H14 -> MLP11 -> MLP16 -> MLP19 -> L20H5 -> L21H12 -> L24H6 -> MLP27` is now defensible. |
| Forward chain has strong writer / transmission evidence | PASS | `MLP11` direction-level intervention strongly moves downstream and final writer. |
| Forward chain is paper-figure-ready | PASS | Official figures `18-21` now package the delivery-object and direction-level evidence. |
| No-tool chain localization exists | PASS | `L16H4 -> MLP17 -> L23H6` is consistently localized. |
| No-tool chain has object-language reader / writer / transmission story | PASS | `L16H4` reads ordinary-answer evidence, `MLP17` writes the suppressive direction, `L23H6` relays it late. |
| No-tool chain has suppression-specific mechanism evidence | PASS | Dedicated projection, ingress-disturbance, suppression heatmap, and stagewise trajectory figures now exist. |
| Whole package is internally consistent for paper use | PASS | The paper-facing report, claim tiers, unresolved-items table, figure plan, and `FINAL_PACKAGE.md` have been updated to the new story. |

## What Is Strong Enough Right Now

### Forward Chain

These claims are strong enough for paper main text:

- `L2H14` is the earliest retained head-level reader inside the 24-node circuit.
- `L2H14` is **not** the first stable delivery-object writer.
- `MLP11` is the first stable delivery-object writer.
- `MLP11 -> MLP16 -> MLP19` amplifies the shared file-vs-answer direction.
- That direction then enters a late writer bridge dominated by
  `L20H5 -> L21H12 -> L24H6 -> MLP27`.

Most important supporting files:

- `paper_facing_main_report.md`
- `paper_facing_focused_evidence_table.csv`
- `paper_facing_claim_tiers.json`
- `figure_18_earliest_reader_vs_mlp11.png`
- `figure_19_stagewise_object_axis_accumulation.png`
- `figure_20_mlp11_projection_trajectory_heatmap.png`
- `figure_21_mlp11_final_writer_effect.png`

### No-Tool Suppression Chain

These claims are strong enough for paper main text:

- `L16H4` reads user-side ordinary-answer evidence concentrated in the task body
  / tail-suffix region rather than tool schema.
- `MLP17` is the main suppressive writer in the no-tool chain.
- `MLP17` both raises `no_tool` and lowers `<tool_call>`.
- `MLP17` also disturbs the late tool ingress path
  (`L20H5 / L21H1 / L21H12 / L24H6 / MLP27`) by pushing those nodes toward
  their local no-tool directions.
- `L23H6` is a late suppressive relay that carries the already-written no-tool
  state into the output-adjacent region.
- The stagewise suppressive story can be written as
  `L16H4 -> MLP17 -> L23H6`.

Most important supporting files:

- `suppression_mechanism_report.md`
- `suppression_focused_evidence_table.csv`
- `suppression_claim_tiers.json`
- `figure_22_suppressive_residual_projection.png`
- `figure_23_tool_ingress_disturbance.png`
- `figure_24_downstream_suppression_heatmap.png`
- `figure_25_suppression_stagewise_trajectory.png`

## Direct Answer To The Paper Question

If the paper claim is:

- "We have a persuasive forward mechanistic chain from minimal cue to final writer"

Current answer:

`YES`

If the paper claim is:

- "We have fully answered both the forward flip and the suppressive no-tool mechanism with paper-grade figures and object-language evidence"

Current answer:

`YES`

If the paper claim is:

- "We have uniquely named the exact earliest reader microfeature on both sides"

Current answer:

`NO, BUT THIS IS NON-BLOCKING`

## Remaining Non-Blocking Gaps

The remaining unresolved questions are now narrow:

1. the exact microfeature label inside `L2H14`
2. the exact microfeature label inside `L16H4`

These remain in:

- `paper_facing_still_unsolved.csv`

They do **not** block the paper-ready mechanism story because the causal chain,
writer identity, transmission pattern, and figure package are already locked.

## Bottom Line

The project is now complete by the paper-mechanism standard in `todo.md`.

What is already genuinely strong:

- the forward mechanistic bridge from earliest reader to final writer, centered
  on `MLP11` as first stable delivery-object writer
- the suppression mechanism story centered on
  `L16H4 -> MLP17 -> L23H6`, with explicit evidence that `MLP17` both raises
  `no_tool` and lowers `<tool_call>`, while also disturbing tool ingress

What remains open:

- only non-blocking microfeature naming questions
