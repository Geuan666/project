# Spotlight-Style Paper Narrative Outline

## 0. Goal

This outline restructures the current `results/final` package into a
single-line, paper-facing narrative closer to a NeurIPS spotlight paper.

The key constraint is:

- do **not** tell a broad "we found many interesting things" story
- do tell one sharp causal story with a memorable mechanism

The current strongest paper story is:

> A minimal instruction-opening cue selects between two competing answer-delivery
> routes inside a sparse signed circuit.  
> A weak early reader state is stabilized by `MLP11`, amplified by
> `MLP16 -> MLP19`, written to `<tool_call>` via a late tool route, and opposed
> by a suppressive no-tool route centered on `MLP17`.

## 1. Recommended Paper Positioning

### One-Sentence Pitch

We identify a sparse, human-readable decision circuit showing how a single
instruction-opening cue flips a model's first generated token between
`<tool_call>` and `no_tool`.

### Why This Is Spotlight-Friendly

- The intervention is minimal and memorable: one tiny lead phrase.
- The behavior flip is stark and causal.
- The mechanism is not just localized; it is decomposed into reader, writer,
  amplification, and suppression roles.
- There are two competing routes, which makes the story more interesting than a
  single positive chain.

### What To Avoid Claiming

Do **not** center the paper on:

- "we fully solved the earliest microfeature"
- "we found the one true earliest semantic atom"
- "we explain all 24 nodes equally well"

Those claims are not needed for the strongest paper.

## 2. Main Claim Hierarchy

### Main Claim

A minimal instruction-opening cue is converted into a first-token decision by a
signed circuit with:

- one forward tool-writing route
- one competing suppressive no-tool route

### Strongest Subclaims

1. A sparse signed circuit is sufficient and necessary for the first-token
   decision.
2. The earliest retained head-level reader is `L2H14`, but the first stable
   delivery-object writer is `MLP11`.
3. `MLP11 -> MLP16 -> MLP19` amplifies a shared file-vs-answer axis.
4. That axis reaches the final tool writer through
   `L20H5 -> L21H12 -> L24H6 -> MLP27`.
5. The competing no-tool route is
   `L16H4 -> MLP17 -> L23H6`.
6. `MLP17` both raises `no_tool` and lowers `<tool_call>`, while also pushing
   late tool-ingress nodes toward their local no-tool directions.

### Non-Central Open Questions

1. The exact microfeature inside `L2H14`.
2. The exact microfeature inside `L16H4`.
3. The exact role split between `L21H1` and `L21H12` for all late features.

These belong in limitations / future work, not the central claim.

## 3. Recommended Title Angles

Use titles that foreground:

- the minimal cue
- the signed competing routes
- the first-token decision

### Strong Candidates

1. `How a Minimal Instruction Cue Flips Tool Use: A Signed Circuit for First-Token Decisions in LLMs`
2. `From Lead Phrase to Tool Call: Reverse-Engineering a Signed Decision Circuit in LLMs`
3. `A Sparse Competing-Routes Circuit for Tool-Use Decisions from Minimal Instruction Cues`

### Weaker Angles To Avoid

- generic "mechanistic analysis of tool use"
- generic "understanding reasoning in LLMs"
- generic "circuit discovery in tool-calling models"

They dilute the novelty.

## 4. Abstract Template

The abstract should follow this order:

1. One-sentence behavior phenomenon:
   a minimal lead-phrase change flips the first generated token from
   `<tool_call>` to `no_tool`.
2. One-sentence technical challenge:
   explaining how such a tiny input perturbation is read, amplified, and written
   inside a large model.
3. Method:
   signed circuit localization plus targeted mechanism analysis.
4. Main findings:
   earliest reader `L2H14`, first stable writer `MLP11`, shared amplifier
   `MLP16 -> MLP19`, late tool writer route, suppressive no-tool route.
5. Strongest causal result:
   editing only `MLP11`'s shared file-vs-answer direction strongly moves
   downstream nodes and final token logits.
6. Suppression result:
   `MLP17` both raises `no_tool` and lowers `<tool_call>`, while disturbing
   tool ingress.
7. Final takeaway:
   the first-token decision is implemented by a human-readable competing-routes
   mechanism.

## 5. Main-Text Section Structure

Recommended spotlight-style structure:

### 1. Introduction

Keep it short and sharp.

Use one memorable setup:

- change one tiny lead phrase
- first token flips between `<tool_call>` and `no_tool`
- ask how that tiny cue becomes a full decision

End intro with explicit contributions:

1. sparse signed circuit
2. forward writer chain
3. suppressive competing chain
4. causal object-axis interventions

### 2. Setup

Only include what is needed:

- clean/corrupt pair construction
- first-token endpoint
- why this is a minimal intervention interface

Do **not** dump the entire dataset and pipeline here.

### 3. Discovering the Signed Decision Circuit

Goal:
show localization/faithfulness quickly, then move on.

Use:

- final circuit figure
- one compact validation heatmap or table

This section should be short.
Treat localization as enabling machinery, not the main result.

### 4. Forward Mechanism: From Minimal Cue to `<tool_call>`

This is one of the two core sections.

Subsections:

1. `L2H14` is the earliest retained reader, but not the first stable writer
2. `MLP11` writes the first stable delivery-object axis
3. `MLP11 -> MLP16 -> MLP19` amplifies the axis
4. `L20H5 -> L21H12 -> L24H6 -> MLP27` writes the final tool-call state

### 5. Suppression Mechanism: How the No-Tool Route Wins

This is the second core section.

Subsections:

1. `L16H4` reads ordinary-answer evidence
2. `MLP17` writes a suppressive direction
3. `MLP17` both raises `no_tool` and lowers `<tool_call>`
4. `MLP17` perturbs late tool ingress
5. `L23H6` relays the suppressive state into the output-adjacent region

### 6. Discussion

Only discuss:

- what is solved mechanistically
- what is still not fully microfeature-resolved
- why this still counts as a human-readable decision circuit

### Appendix

Move bulk tables, scans, older intermediate analyses, and alternative stories.

## 6. Main Figure Order

The main text should not use all figures equally.
Use a very small number of figures as anchors.

### Figure 1: Teaser / Main Mechanism Summary

This figure likely still needs to be made or reworked from existing pieces.

It should show, in one page:

- the minimal cue contrast
- the signed circuit backbone
- the forward route
- the suppressive route
- the first-token decision endpoint

This is the single biggest missing "spotlight-style" figure.

### Figure 2: Final Signed Circuit

Use the existing final circuit figure.

Purpose:

- show that the circuit is sparse, structured, and signed
- define the components the rest of the paper will discuss

### Figure 3: Forward Chain Main Evidence

Prefer to combine:

- earliest-reader vs `MLP11`
- stagewise object-axis accumulation

If too crowded, split into two figures.

Must communicate:

- `L2H14` is weak/early
- `MLP11` is the first stable writer
- the axis grows through `MLP16 -> MLP19`

### Figure 4: `MLP11` Direction-Level Causal Effect

Use the new `MLP11` projection/final-writer figures.

Must communicate:

- editing only `MLP11` shared direction moves downstream nodes
- final token logits move accordingly

This is probably the strongest single forward mechanism figure.

### Figure 5: Suppression Mechanism

Prefer to combine:

- residual projection plot
- ingress disturbance
- stagewise suppression

Must communicate:

- `MLP17` is a real suppressive writer
- suppression is double-sided
- it directly disturbs the tool route

### Figure 6: Optional Validation Figure

One compact validation figure, not many.

Could be:

- structural/functional validation heatmap
- or sufficiency/necessity summary

Keep this minimal.

## 7. What To Move To Appendix

Put these in appendix / supplement:

- exhaustive node tables
- older intermediate reports
- raw per-sample CSVs
- earlier "focused_mechanism" versions
- every alternate chain hypothesis
- broader circuit family summaries not needed for the main argument

Main text should not feel like a package dump.

## 8. Strongest Evidence Chain For Q1

The Q1 section should be written almost exactly as:

1. A minimal cue changes the first token.
2. `L2H14` is the earliest retained head-level reader.
3. `L2H14` already contains a weak shared file-vs-answer component.
4. That component is too weak to drive the endpoint by itself.
5. `MLP11` is the first stable writer of that axis.
6. `MLP11 -> MLP16 -> MLP19` amplifies it.
7. The amplified axis enters the late tool writer route.
8. `MLP27` writes the final `<tool_call>`-favoring residual.

This gives a clean causal ladder.

## 9. Strongest Evidence Chain For Q2

The Q2 section should be written almost exactly as:

1. `L16H4` reads ordinary-answer evidence from the user-side task body /
   tail-suffix region.
2. `MLP17` converts that state into a suppressive residual feature.
3. That suppressive feature both:
   - raises `no_tool`
   - lowers `<tool_call>`
4. The same suppressive direction perturbs
   `L20H5`, `L21H1`, `L21H12`, `L24H6`, and `MLP27`.
5. `L23H6` relays the already-written suppressive state into the
   output-adjacent region.

This is the cleanest paper version of the no-tool story.

## 10. Comparison To The Logic-Circuit Paper

Relative to the propositional-logic spotlight paper, our main strengths are:

- a more behaviorally realistic setting
- a signed competing-routes story
- a stronger suppression story
- direct first-token decision framing

Relative to that paper, our main weaknesses are:

- less modular family naming
- more complicated package/history
- no cross-model story
- still missing a single iconic teaser figure

Therefore, to approach spotlight quality without cross-model experiments, the
most important remaining improvement is:

`make one unforgettable main mechanism figure and simplify the main-text story around it`

## 11. Minimal Additional Experiments Worth Doing

Only do more experiments if they improve the main-text narrative directly.

### High ROI

1. A single integrated teaser figure built from existing evidence.
2. One compact summary plot comparing the magnitude of
   `L2H14` vs `MLP11` direction edits on:
   - object score
   - tool logit
   - `MLP27`
3. One compact suppressive comparison plot comparing
   `L16H4`, `MLP17`, `L23H6` on:
   - `<tool_call>` delta
   - `no_tool` delta
   - decision score delta

### Low ROI Right Now

1. More localization
2. More raw patch rescue scans
3. More earliest-microfeature naming attempts
4. More circuit-wide exploratory searches

## 12. Final Recommendation

Yes, the current project can support a spotlight-style mechanism paper,
**provided the paper is rewritten around a single causal story**:

- minimal cue
- first stable writer
- shared amplification
- final writer
- competing suppressive route

The paper should be framed as:

`a signed, human-readable decision mechanism for a minimal cue-driven tool-use flip`

not as:

`a large package of many interesting mechanistic observations`
