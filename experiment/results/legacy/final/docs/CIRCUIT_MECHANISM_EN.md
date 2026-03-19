# Tool-Call Decision Circuit: Main Mechanism Document

## 1. Scope and Core Conclusion

This document does one thing:

explain why a minimal instruction-opening cue causes a cascade inside the
signed circuit and ultimately flips the first generated token between
`<tool_call>` and `no_tool`.

It does **not** re-argue circuit localization or correctness. The focus here is
only:

1. what the modules are, and
2. what objects each module reads, writes, or transports.

The cleanest paper-ready story is not "a direction gets amplified." It is a
four-module story:

1. **Opening-request reader** `L2H14`  
   reads the instruction-opening phrase and distinguishes prompts that ask for
   **external-file delivery** from prompts that ask for a **direct inline
   answer**.
2. **Delivery-format writer** `MLP11 -> MLP16 -> MLP19`  
   writes that opening difference into a persistent state that says how the
   answer should be delivered.
3. **Tool-call assembly module** `L20H5 -> L21H12 -> L24H6 -> MLP27`  
   combines the external-file-delivery state with the file target, function
   body, and tool protocol prefix, and writes `<tool_call>`.
4. **Plain-answer suppression module** `L16H4 -> MLP17 -> L23H6`  
   reads plain-answer evidence from the task body, writes a `no_tool`-favoring
   state, and suppresses the late tool path.

The full mechanism can therefore be stated as:

> the minimal cue first changes what `L2H14` reads at the opening; then
> `MLP11 -> MLP16 -> MLP19` turns that into a stable delivery-format state; if
> that state favors external-file delivery, the late tool-call assembly module
> writes `<tool_call>`; if it favors direct inline answering, the plain-answer
> suppression module writes `no_tool` and pushes down the tool route.

---

## 2. Task and Minimal Intervention Interface

Each clean/corrupt pair differs only in one instruction-opening token or a very
small lead phrase.

- clean: the first generated token is on the `<tool_call>` side
- corrupt: the first generated token is on the `no_tool` side

This is not useful because "the first word matters."
It is useful because it provides a minimal intervention interface:

> changing a tiny opening cue flips the final decision.

So the real questions are:

1. Where is that opening cue first read?
2. Where does it become a stable delivery-format state?
3. How is that state turned into `<tool_call>`?
4. How does the no-tool route suppress the tool route?

---

## 3. Formal Circuit and Module Split

Figure 01 shows the final signed circuit.

![Figure 01 Final Signed Circuit](../figures/figure_01_final_signed_circuit.png)

**What Figure 01 establishes**

- the result is not a bag of nodes
- it is a sparse signed circuit
- it is the structural backbone for the module-level story below

The paper only needs two chains and four modules:

### Forward chain

`L2H14 -> MLP11 -> MLP16 -> MLP19 -> L20H5 -> L21H12 -> L24H6 -> MLP27`

### Suppressive chain

`L16H4 -> MLP17 -> L23H6`

| Module | Components | Main object operation | Final role |
|---|---|---|---|
| Opening-request reader | `L2H14` | reads the opening request phrase | distinguishes external-file-delivery framing from direct-answer framing |
| Delivery-format writer | `MLP11 -> MLP16 -> MLP19` | writes and maintains a stable delivery-format state | makes the delivery choice legible to later layers |
| Tool-call assembly | `L20H5 -> L21H12 -> L24H6 -> MLP27` | binds file target, function body, and tool protocol | writes `<tool_call>` |
| Plain-answer suppression | `L16H4 -> MLP17 -> L23H6` | writes a plain-answer / no-tool state and suppresses the tool route | pushes the first token toward `no_tool` |

---

## 4. Metrics and Formulae

These metrics are evidence measures. They are **not** the mechanism names.

### 4.1 Decision Score

`DecisionScore = Score_tool - Score_no_tool`

Interpretation:

- positive: more tool-like
- negative: more no-tool-like

### 4.2 Delivery Score

Historically the files use the field name `ObjectScore`, but in this document it
is best understood as a **delivery score**:

`ObjectScore = Score_file - Score_answer`

Interpretation:

- positive: more external-file delivery
- negative: more inline-answer delivery

### 4.3 Rescue Ratio

`RescueRatio = (Score_patched - Score_base) / (Score_anchor - Score_base)`

Interpretation:

- `1`: full recovery
- `0`: no recovery
- `< 0`: wrong-direction intervention

### 4.4 Mediation

`Mediation(A -> B) = Rescue(source-only) - Rescue(source-with-B-blocked)`

Interpretation:

- if patching `A` helps, but blocking `B` removes that help, then part of `A`'s
  effect is mediated through `B`

### 4.5 Projection Delta

`ProjectionDelta = <h_after - h_before, d_unit>`

Interpretation:

- positive: movement along the target direction
- negative: movement against it

In this document, projection metrics are only used to support module claims.
They are not the module story itself.

---

## 5. Module 1: Opening-Request Reader `L2H14`

This module answers:

> why is the minimal cue not ignored, but already read in the very early model?

The strongest current conclusion is:

- `L2H14` is the earliest retained head-level reader
- it reads an instruction-opening request bundle rather than an isolated token
- it is still frame-dominant and not yet a stable writer of the later
  delivery-format state

Figure 18 directly contrasts `L2H14` with `MLP11`.

![Figure 18 L2H14 vs MLP11](../figures/figure_18_earliest_reader_vs_mlp11.png)

**Main message of Figure 18**

- `L2H14` already distinguishes the opening request
- but it does not yet write a stable "external-file delivery vs direct answer"
  state
- `MLP11` is the first point where that state becomes stable

| Component | Reads | Writes | Strongest evidence |
|---|---|---|---|
| `L2H14` | instruction-opening request bundle; mostly how the request is framed | small opening-side difference into `MLP11` | same-object cross-frame `0.897` < same-frame cross-object `1.000`; write inject changes delivery score by only `+0.0022` |
| `MLP11` | upstream opening-side state | first stable delivery-format state | same-object cross-frame `0.992` > same-frame cross-object `0.974`; write-frame whole-node patch: file-rescue `0.332`, object-decision `0.141` |

So the paper sentence should be:

> `L2H14` is the opening-request reader, but not yet the stable writer of
> delivery format.

---

## 6. Module 2: Delivery-Format Writer `MLP11 -> MLP16 -> MLP19`

This module answers:

> where does the tiny opening cue become a persistent state that later layers
> can actually use?

The strongest current conclusion is:

- `MLP11` is the first stable writer of delivery format
- `MLP16` and `MLP19` maintain and amplify that written state
- by `MLP19`, the late tool-writing path can directly use it

Figure 19 shows the stagewise strengthening of this state.

![Figure 19 Stagewise Strengthening of Delivery Format](../figures/figure_19_stagewise_object_axis_accumulation.png)

**Main message of Figure 19**

- the opening difference is weak at `L2H14`
- it becomes stable at `MLP11`
- `MLP16` and `MLP19` keep and strengthen it

Figures 20 and 21 provide the strongest causal evidence.

![Figure 20 Downstream Trajectory after Editing MLP11](../figures/figure_20_mlp11_projection_trajectory_heatmap.png)

![Figure 21 Final Writer Effect of Editing MLP11](../figures/figure_21_mlp11_final_writer_effect.png)

**Main message of Figures 20 and 21**

- editing only `MLP11`'s delivery-format direction pushes downstream nodes
  toward the external-file-delivery side
- that movement reaches `MLP27` and changes endpoint logits

| Intervention | Delivery score delta | `tool logit` delta | `no_tool` / distractor delta | Key downstream movement |
|---|---:|---:|---:|---|
| `L2H14` write inject | `+0.0022` | `0.0` | `0.0` | `MLP27 +1.44` |
| `MLP11` write inject | `+0.678` | `+1.375` | `-1.625` | `MLP16 +9.26`, `MLP19 +20.26`, `L21H12 +8.26`, `L24H6 +27.38`, `MLP27 +94.68` |
| `MLP11` write erase | `-0.189` | `-0.500` | `+0.375` | `MLP16 -4.43`, `MLP19 -10.65`, `L21H12 -1.84`, `L24H6 -4.70`, `MLP27 -26.74` |

The cleanest interpretation is:

> `MLP11` writes "deliver the answer through an external file" versus "answer
> directly here" as a stable state, and `MLP16 -> MLP19` keep that state alive
> until later modules can act on it.

---

## 7. Module 3: Tool-Call Assembly `L20H5 -> L21H12 -> L24H6 -> MLP27`

This module answers:

> once the circuit favors external-file delivery, how does that become
> `<tool_call>`?

The strongest object-level split is:

| Node | Main object operation | Strongest current evidence |
|---|---|---|
| `L20H5` | reads the file target / function body side of the prompt | strongest causal-span evidence on `file_target` and `function_body_anchor`; rises under `MLP11` injection |
| `L21H12` | combines that state with tool protocol / instruction tail structure | `+8.26` under `MLP11` injection; most stable late router in the bridge |
| `L24H6` | relays the assembled tool-biased state toward the output-adjacent region | `+27.38` under `MLP11` injection; immediately before final writeout |
| `MLP27` | writes the final `<tool_call>` tendency | largest endpoint movement; `+94.68` under `MLP11` injection |

This module should therefore be described as:

> `L20H5` attaches the delivery-format state to the concrete file target and
> function body; `L21H12` combines that state with the tool protocol prefix;
> `L24H6` moves the assembled state next to the output; and `MLP27` writes the
> first token toward `<tool_call>`.

This is not a second abstract axis story. It is the late-stage assembly of a
tool-call prefix.

---

## 8. Module 4: Plain-Answer Suppression `L16H4 -> MLP17 -> L23H6`

This module answers:

> why is the no-tool route not merely parallel, but genuinely suppressive?

The strongest current conclusion is:

- `L16H4` reads ordinary-answer evidence from the task body / tail-suffix
- `MLP17` writes a `no_tool` state that has direct token-level consequences
- that same state both raises `no_tool` and lowers `<tool_call>`
- `MLP17` also pushes the late tool path toward the no-tool side
- `L23H6` relays the already-written suppressive state into the output-adjacent
  region

Figure 22 answers the first key question:

> does this module raise `no_tool`, lower `<tool_call>`, or both?

![Figure 22 Suppressive Residual Projection](../figures/figure_22_suppressive_residual_projection.png)

**Main message of Figure 22**

- the suppressive route is not single-sided
- especially at `MLP17`, both sides move:
  - `<tool_call>` goes down
  - `no_tool` goes up

| Node | Reads | Writes | Strongest evidence |
|---|---|---|---|
| `L16H4` | task-body / tail-suffix ordinary-answer evidence | suppressive head output into `MLP17` | task-body rescue `0.022`; `z` rescue `0.198`; inject on clean: tool `-0.25`, no-tool `+0.375` |
| `MLP17` | ordinary-answer state from `L16H4` | suppressive state that favors `no_tool` and lowers `<tool_call>` | projection delta: tool `-0.016`, no-tool `+0.219`; inject on clean: tool `-0.625`, no-tool `+1.125`, decision `-1.592` |
| `L23H6` | already-written suppressive state | late relay into the output-adjacent region | inject on clean: tool `-0.375`, no-tool `+0.625`; `z` rescue `0.280` |

The clean paper sentence is:

> `MLP17` is not just another token writer; it strengthens the plain-answer
> state while simultaneously weakening the tool-call side.

---

## 9. How the No-Tool Route Suppresses the Tool Route

Figure 23 asks whether `MLP17` only changes endpoint logits, or also changes the
late tool path itself.

![Figure 23 Tool Ingress Disturbance](../figures/figure_23_tool_ingress_disturbance.png)

**Main message of Figure 23**

- `MLP17` does not only write `no_tool` at the endpoint
- it also pushes `L20H5`, `L21H1`, `L21H12`, `L24H6`, and `MLP27` toward their
  local no-tool states

| Node | Projection change after `MLP17` inject |
|---|---:|
| `L20H5` | `+3.52` |
| `L21H1` | `+6.48` |
| `L21H12` | `+7.03` |
| `L24H6` | `+12.38` |
| `MLP27` | `+111.54` |

So the suppressive route is best described as:

> `MLP17` both writes the no-tool side directly and pushes the late tool-call
> assembly path away from `<tool_call>`.

That is why this route is genuinely suppressive rather than merely parallel.

---

## 10. Stagewise Accumulation of Suppression

Figures 24 and 25 complete the suppressive story.

![Figure 24 Downstream Suppression Heatmap](../figures/figure_24_downstream_suppression_heatmap.png)

![Figure 25 Suppression Stagewise Trajectory](../figures/figure_25_suppression_stagewise_trajectory.png)

**Main message of Figure 24**

- the effects of `L16H4`, `MLP17`, and `L23H6` are structured rather than
  random

**Main message of Figure 25**

- the suppressive state accumulates stage by stage
- it does not appear as a one-node endpoint artifact

| Stage | Nodes | `tool token` delta | `no_tool token` delta | `DecisionScoreDelta` | `no_tool_top1_rate` |
|---|---|---:|---:|---:|---:|
| 1 | `L16H4` | `-0.25` | `+0.375` | `-0.657` | `0.012` |
| 2 | `L16H4 | MLP17` | `-1.00` | `+1.625` | `-2.414` | `0.289` |
| 3 | `L16H4 | MLP17 | L23H6` | `-1.625` | `+2.750` | `-3.951` | `0.783` |

This supports the cleanest summary:

> `L16H4` reads ordinary-answer evidence, `MLP17` turns it into a token-effective
> no-tool state, and `L23H6` carries that state into the output-adjacent region.

---

## 11. End-to-End Mechanism: From Minimal Cue to First Token

The full story can now be written in ordinary object language.

When the instruction opening asks for the result to be delivered through an
external file, `L2H14` first reads that opening request. `MLP11` then writes a
stable delivery-format state from it, and `MLP16 -> MLP19` keep that state
active. In the late path, `L20H5` attaches that state to the concrete file
target and function body; `L21H12` combines it with the tool protocol prefix;
`L24H6` relays the assembled state next to the output; and `MLP27` writes the
first token toward `<tool_call>`.

When the instruction opening instead supports direct inline answering, the late
tool assembly path does not receive the same strong external-file-delivery
state. In parallel, `L16H4` reads ordinary-answer evidence from the task body
and tail-suffix region; `MLP17` writes that into a `no_tool` state, lowers the
`<tool_call>` side, and pushes the late tool path toward the no-tool side; then
`L23H6` relays that state into the output-adjacent region. The first token is
therefore pushed toward `no_tool`.

So the core mechanism is not "an abstract axis gets amplified." It is:

> the opening request is read as one of two delivery formats; one delivery
> format triggers tool-call assembly, while the other triggers plain-answer
> writing and competitive suppression of the tool path.

---

## 12. Claim Boundaries

The strongest current claims are:

1. `L2H14` is the earliest retained opening-request reader.
2. `MLP11` is the first stable writer of delivery format.
3. `MLP16 -> MLP19` maintain and amplify that delivery-format state.
4. `L20H5 -> L21H12 -> L24H6 -> MLP27` assemble and write the tool-call prefix.
5. `L16H4 -> MLP17 -> L23H6` write and relay a competing no-tool state.
6. `MLP17` both raises `no_tool`, lowers `<tool_call>`, and disturbs the late
   tool path.

These should **not** be the strongest claims:

- the exact microfeature name inside `L2H14`
- the exact microfeature name inside `L16H4`
- whether `L21H1` should be promoted to the same headline level as `L21H12`

---

## 13. Recommended Formal References

Use these files first:

- [Figure index](../figures/FIGURE_INDEX.csv)
- [Data index](../data/DATA_INDEX.csv)
- [Paper-facing focused evidence table](../data/paper_facing_focused_evidence_table.csv)
- [Paper-facing claim tiers](../data/paper_facing_claim_tiers.json)
- [Suppression focused evidence table](../data/suppression_focused_evidence_table.csv)
- [Suppression claim tiers](../data/suppression_claim_tiers.json)

Legacy markdown reports are archived in:

- `../archive/docs_legacy/`

---

## 14. One-Sentence Summary

The cleanest way to write the current mechanism is:

> the minimal cue is first read by `L2H14` as an opening request, then written by
> `MLP11 -> MLP16 -> MLP19` into a stable delivery-format state; if that state
> favors external-file delivery, `L20H5 -> L21H12 -> L24H6 -> MLP27` assemble a
> tool-call prefix and write `<tool_call>`; if it favors direct inline answering,
> `L16H4 -> MLP17 -> L23H6` write and relay a competing no-tool state that also
> suppresses the tool path, pushing the first token toward `no_tool`.
