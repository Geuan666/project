# Focused Mechanism Report

This report is now aligned to the paper-facing package.

It addresses the two remaining mechanism questions inside the existing
24-node signed circuit:

1. how a tiny lead-phrase cue is read, transmitted, amplified, and finally
   written into `<tool_call>`
2. how the no-tool chain suppresses that route

It does **not** re-argue circuit correctness.

## 1. Forward Mechanistic Chain

The strongest paper-ready forward chain is:

`minimal cue -> L2H14 -> MLP11 -> MLP16 -> MLP19 -> L20H5 -> L21H12 -> L24H6 -> MLP27`

The correct strength boundaries are:

1. `L2H14` is the earliest retained head-level reader inside the circuit.
   It already carries a weak shared file-vs-answer component, but it is still
   frame-dominant and not yet a stable writer.

2. `MLP11` is the first stable delivery-object writer.
   This is now supported not only by representation clustering, but by
   direction-level causal intervention:
   editing only `MLP11`'s shared file-vs-answer direction strongly changes
   object score, `<tool_call>`, `no_tool`, and downstream projections in
   `MLP16`, `MLP19`, `L20H5`, `L21H12`, `L24H6`, and `MLP27`.

3. `MLP11 -> MLP16 -> MLP19` is the earliest strong amplification segment.
   This is where the shared file-vs-answer state becomes a robust scaffold
   rather than a weak reader-side component.

4. The late writer bridge for that shared object axis is dominated by
   `L20H5 -> L21H12 -> L24H6 -> MLP27`.
   `L21H1` remains part of the late tool route overall, but it is not the
   cleanest monotonic carrier of the shared file-vs-answer direction in the
   updated projection-based audit.

5. `MLP27` remains the primary late writer for the `<tool_call>` side.

## 2. No-Tool Suppression Chain

The strongest paper-ready suppressive chain is:

`L16H4 -> MLP17 -> L23H6`

The correct object-language reading is:

1. `L16H4` reads user-side ordinary-answer evidence concentrated in the
   task-body / tail-suffix region rather than tool schema tokens.
   Its strongest span-level read is task-body-like content, and its strongest
   transmission component is `z`, not `q/k`.

2. `MLP17` is the main suppressive writer.
   It does not only write a `no_tool`-favoring residual direction.
   It also lowers `<tool_call>` and pushes the late tool ingress route toward
   local no-tool directions.

3. `L23H6` is a late suppressive relay.
   It is not the main semantic reader, but a late-output carrier of the
   already-written suppressive state.

4. The suppressive story is stagewise, not single-node:
   `L16H4` introduces a weak suppressive bias,
   `MLP17` makes that bias strongly token-effective,
   and `L23H6` carries it into the output-adjacent region.

## 3. What Is Strong Enough To Write

Strong-write:

- `L2H14` is the earliest retained head-level reader.
- `MLP11` is the first stable delivery-object writer.
- `MLP11 -> MLP16 -> MLP19` is the earliest strong amplification segment.
- `L20H5 -> L21H12 -> L24H6 -> MLP27` is the cleanest late writer bridge for
  the shared file-vs-answer axis.
- `L16H4 -> MLP17 -> L23H6` is the suppressive no-tool chain.
- `MLP17` both raises `no_tool` and lowers `<tool_call>`.
- `MLP17` also disturbs `L20H5 / L21H1 / L21H12 / L24H6 / MLP27`.

Medium-write:

- `L2H14`'s exact microfeature is still not uniquely named.
- `L16H4`'s exact microfeature is still not uniquely named.
- `L21H1` still participates in the late tool route, but not as the cleanest
  carrier of the shared file-vs-answer axis.

## 4. What Still Is Not Fully Solved

The remaining unresolved questions are now narrow and non-blocking:

- the exact microfeature label inside `L2H14`
- the exact microfeature label inside `L16H4`

These do not block the paper-ready story because reader identity, first stable
writer identity, amplification path, suppressive writer identity, late relay,
and figure package are already in place.

## 5. Primary Entry Points

For the harmonized paper-facing package, use:

- `paper_facing_main_report.md`
- `paper_facing_focused_evidence_table.csv`
- `paper_facing_claim_tiers.json`
- `paper_facing_still_unsolved.csv`
- `figures/figure_18_earliest_reader_vs_mlp11.png`
- `figures/figure_19_stagewise_object_axis_accumulation.png`
- `figures/figure_20_mlp11_projection_trajectory_heatmap.png`
- `figures/figure_21_mlp11_final_writer_effect.png`
- `figures/figure_22_suppressive_residual_projection.png`
- `figures/figure_23_tool_ingress_disturbance.png`
- `figures/figure_24_downstream_suppression_heatmap.png`
- `figures/figure_25_suppression_stagewise_trajectory.png`
