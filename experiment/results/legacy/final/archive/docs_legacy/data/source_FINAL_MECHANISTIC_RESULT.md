# Final Mechanistic Result

## Core Claim

In this fixed tool environment, the decisive variable is an instruction-side
delivery cue that is introduced by a tiny lead-phrase change and then routed
through a specific forward chain into the first generated token decision.

The resulting signed circuit remains highly faithful:
full-circuit KL recovery `1.000` / `0.998`, top-1 `0.999` / `0.997`.

## Final Mechanistic Story

### Question 1: Why does a tiny cue flip `<tool_call>` to `no_tool`?

The strongest paper-ready forward chain is:

`minimal cue -> L2H14 -> MLP11 -> MLP16 -> MLP19 -> L20H5 -> L21H12 -> L24H6 -> MLP27`

The correct strength boundaries are:

1. `L2H14` is the earliest retained head-level reader.
   It already carries a weak shared file-vs-answer component, but it is not yet
   the first stable delivery-object writer.

2. `MLP11` is the first stable delivery-object writer.
   This is supported by both representation-level grouping and direction-level
   causal intervention.

3. `MLP11 -> MLP16 -> MLP19` amplifies that shared file-vs-answer direction into
   a robust scaffold.

4. That scaffold then enters a late writer bridge dominated by
   `L20H5 -> L21H12 -> L24H6 -> MLP27`.

5. `MLP27` is the primary late writer for the `<tool_call>` side.

### Question 2: How does the no-tool chain suppress the tool route?

The strongest paper-ready suppressive chain is:

`L16H4 -> MLP17 -> L23H6`

The correct object-language reading is:

1. `L16H4` reads user-side ordinary-answer evidence concentrated in task-body /
   tail-suffix content rather than tool schema.

2. `MLP17` is the main suppressive writer.
   It both raises `no_tool` and lowers `<tool_call>`.

3. `MLP17` also disturbs the late tool ingress route by pushing
   `L20H5`, `L21H1`, `L21H12`, `L24H6`, and `MLP27` toward their local no-tool
   directions.

4. `L23H6` is a late suppressive relay that carries the already-written
   suppressive state into the output-adjacent region.

5. The suppressive story is stagewise:
   `L16H4` introduces a weak suppressive bias,
   `MLP17` makes it strongly token-effective,
   `L23H6` carries it late.

## What We Can Write Strongly

- The forward chain is paper-ready.
- The suppression chain is paper-ready.
- `MLP11` is the first stable delivery-object writer.
- `MLP17` is the main suppressive writer.
- `MLP17` both raises `no_tool` and lowers `<tool_call>`.
- `MLP17` also weakens the late tool route.

## What Must Stay Narrow

- Do not write `L2H14` as a pure earliest delivery-semantics writer.
- Do not write `L16H4` as a uniquely named microfeature reader.
- Do not write `L23H6` as the main no-tool writer.

## Remaining Non-Blocking Gaps

- the exact microfeature inside `L2H14`
- the exact microfeature inside `L16H4`

These do not block the main-text mechanism story.

## Primary Entry Points

- `paper_facing_main_report.md`
- `paper_facing_focused_evidence_table.csv`
- `paper_facing_claim_tiers.json`
- `paper_facing_still_unsolved.csv`
- `suppression_mechanism_report.md`
- `figures/figure_18_earliest_reader_vs_mlp11.png`
- `figures/figure_19_stagewise_object_axis_accumulation.png`
- `figures/figure_20_mlp11_projection_trajectory_heatmap.png`
- `figures/figure_21_mlp11_final_writer_effect.png`
- `figures/figure_22_suppressive_residual_projection.png`
- `figures/figure_23_tool_ingress_disturbance.png`
- `figures/figure_24_downstream_suppression_heatmap.png`
- `figures/figure_25_suppression_stagewise_trajectory.png`
