# Focused Mechanism Report

This report only addresses one question:

How the minimal cue is read, transmitted, amplified, and finally written into
`<tool_call>` / `no_tool` inside the existing 24-node circuit.

It does **not** re-argue circuit correctness.

## 1. Updated Mechanistic Chain

Only the steps below have enough evidence to keep in the main chain.

1. The earliest *head* candidate inside the 24-node circuit is `L2H14`, but
   this is still a weak claim.
   What it appears to read:
   user-side instruction content near the request body.
   What is still missing:
   a clean token-level differential that isolates the minimal cue itself.
   Why this stays weak:
   on the full 1722-sample summary, `L2H14` has only weak direct cue recovery
   (`tool rescue = 0.042`), and the in-circuit ingress edge
   `L2H14 -> MLP11` is small at the dataset median
   (`promote mediated = 0.009`).

2. The earliest **stable in-circuit carrier** of the cue-conditioned difference
   is `MLP11`, not a head.
   Interpretation:
   by layer 11, the minimal cue is no longer a bare lead token. It has already
   been folded into an early residual feature that distinguishes:
   - external-file / environment delivery scaffold
   - text-only function-body answer scaffold
   Evidence:
   `MLP11` is the earliest node with substantial cue recovery on both sides
   (`tool rescue = 0.331`, `no_tool rescue = 0.153`).

3. The earliest strong transmission edge is `MLP11 -> MLP16`.
   Interpretation:
   `MLP11` writes the earliest scaffold feature, and `MLP16` receives it as a
   shared amplified delivery-state carrier.
   Evidence:
   `MLP11 -> MLP16` is far stronger than `MLP11 -> L12H6` on the full summary
   (`promote mediated = 0.242` vs `0.020`; suppress `0.133` vs `0.006`).
   This is the first place where the cue-conditioned state is clearly routed
   into the shared backbone.

4. The shared scaffold is centered on `MLP16 -> MLP19`.
   Interpretation:
   `MLP16` and `MLP19` do not yet look like pure `<tool_call>` writers or pure
   `no_tool` writers. They look like carriers of a polarity-not-yet-finalized
   delivery configuration:
   - file target / function-body anchor / instruction suffix on the tool side
   - task-body / newline / textual-answer continuation on the no-tool side
   Evidence:
   `MLP16` has strong direct effects in both directions
   (`tool rescue = 0.524`, `no_tool rescue = 0.431`);
   `MLP19` also has strong direct effects in both directions
   (`tool rescue = 0.538`, `no_tool rescue = 0.376`);
   and `MLP16 -> MLP19` is strong in both directions
   (`promote mediated = 0.133`, `suppress mediated = 0.132`).
   This is why the most defensible object-language reading is:
   the scaffold is carrying a cue-conditioned **answer-delivery state** before
   token identity splits cleanly.

5. `MLP16` fans the scaffold into both late routes.
   Tool-facing fan-out:
   `MLP16 -> L20H5`, `MLP16 -> L21H1`, `MLP16 -> L21H12`.
   No-tool-facing fan-out:
   `MLP16 -> MLP17`.
   Evidence:
   `MLP16 -> MLP17` is one of the strongest early edges on either side
   (`promote mediated = 0.220`, `suppress mediated = 0.210`);
   `MLP16 -> L21H12` also remains substantial
   (`0.104` / `0.082`);
   `MLP16 -> L21H1` remains substantial
   (`0.084` / `0.090`).
   So `MLP16` is the point where the shared scaffold begins to fork toward
   tool writing and no-tool competition.

6. `MLP19` is the late shared fan-out hub.
   Interpretation:
   `MLP19` hands the shared scaffold into both the tool ingress route and the
   no-tool relay route.
   Evidence:
   `MLP19 -> L20H5` mediated `0.064`,
   `MLP19 -> L21H1` `0.094`,
   `MLP19 -> L21H12` `0.085`,
   `MLP19 -> L23H6` `0.074`,
   `MLP19 -> L24H6` `0.180`.
   The strongest outgoing effect is actually toward `L24H6`, which supports a
   reading where `MLP19` has already amplified the scaffold into a late output-
   proximal configuration.

7. The late tool route is object-bound, not lead-token-bound.
   `L20H5`:
   reads file-target and function-body anchors, especially file suffixes such
   as `.py`, `.cpp`, `.java` and the token `body`.
   It barely attends to the bare lead phrase.
   Evidence:
   span density `file_target = 0.0515`,
   `function_body_anchor = 0.0424`,
   `lead_phrase = 0.00015`;
   top tokens include `.py`, `.cpp`, `.java`, ` body`.
   Mechanism:
   `q` already carries part of the cue-conditioned state (`0.156`), but the
   strongest effect is in `z` (`0.308`), so by `L20H5` the cue is already a
   written head-output feature.

8. `L21H1` and `L21H12` route two different object bundles into the tool writer.
   `L21H1`:
   reads instruction-boundary / code-preamble objects
   (`<|im_start|>`, `static`, newline-like boundaries).
   `L21H12`:
   reads instruction-tail / tool-protocol objects
   (newline, `<|im_start|>`, `tools`, `{"`).
   Evidence:
   `L21H1` top tokens are dominated by `<|im_start|>` and code-preamble tokens;
   `L21H12` top tokens are dominated by newline, `<|im_start|>`, `tools`, and
   JSON openers.
   Transmission:
   both heads act mainly through `q` and `z`, not `v`:
   `L21H1 q = 0.546, z = 0.573`;
   `L21H12 q = 0.692, z = 0.707`.
   So these are routing heads, not plain value-copy heads.

9. `L24H6` is a pre-writer relay into the `<tool_call>` token scaffold.
   What it reads:
   `<tool_call>` itself and message-boundary markers.
   Evidence:
   top tokens are dominated by `<tool_call>` and `<|im_start|>`.
   Interpretation:
   by layer 24 the cue-conditioned delivery state has already been converted
   into an output-format scaffold that directly neighbors the tool-call tag.

10. `MLP27` writes the final `<tool_call>`-favoring residual direction.
    Evidence:
    direct rescue `0.809`;
    steering on `corrupt_full` raises `tool_top1_rate` from `0.000` to `0.833`
    at `alpha = 1.5`;
    the best independent alternative under `MLP27` block is only `0.371`
    (`L21H12`), far below `MLP27`.
    Strong reading:
    `MLP27` is the primary late writer, not just a correlated late node.

11. The no-tool route is also object-bound.
    `L16H4` does not primarily read the file target.
    It reads textual-answer-side anchors:
    newline-heavy task body, `input`, and the instruction tail.
    Evidence:
    span density is largest on `tail_suffix = 0.00966` and task-body-like
    content; top tokens are newline, `input`, and `<|im_start|>`.
    Transmission:
    `z = 0.198` dominates, while `v = 0.034` and `q/k` are near zero.
    So `L16H4` is not recomputing the cue from scratch; it receives a
    previously written suppressive state and forwards it as a head output.

12. `MLP17` is the main no-tool writer and suppressor.
    What it writes:
    a `no_tool`-favoring residual state.
    How it transmits:
    it pushes that state to `L23H6`, but also back into the tool path.
    Evidence:
    direct rescue `0.474`;
    `MLP17 -> L23H6 = 0.066`;
    `MLP17 -> L21H12 = 0.066`;
    `MLP17 -> L21H1 = 0.058`;
    `MLP17 -> L20H5 = 0.049`;
    `MLP17 -> L24H6 = 0.048`.
    Strong reading:
    suppression is double-sided:
    - it writes a no-tool output-side state
    - it weakens the late tool ingress route

13. `L23H6` is a late suppressive relay, not the earliest semantic reader.
    What it reads:
    mostly newline / boundary scaffold, not lexical task content.
    Evidence:
    top tokens are dominated by `<|im_start|>` and `\n\n`.
    Transmission:
    `z = 0.280` dominates.
    Interpretation:
    `L23H6` is the late carrier that brings the already-written no-tool state
    into the output-adjacent region.

## 2. Mechanism Evidence Table

See `focused_mechanism_table.csv`.

Read the table as:

- `reads`: what object the node or edge is best supported to carry
- `writes`: what downstream state it contributes
- `transmission`: how the state moves onward
- `evidence`: strongest existing reader / writer / transmission / amplification
  evidence from the final package

## 3. Claim Tiers

See `focused_mechanism_claim_tiers.json`.

The short version is:

- Strong-write:
  `MLP11 -> MLP16 -> MLP19` is the earliest strong shared scaffold already
  inside the circuit.
  `L20H5/L21H1/L21H12/L24H6/MLP27` is the late tool writing route.
  `L16H4/MLP17/L23H6` is the no-tool competing route.
- Weak-write:
  `L2H14` is the earliest in-circuit head candidate, but it is not yet a solved
  earliest reader.
  `MLP12` looks like an early no-tool seed, but its exact semantics remain
  weaker than `MLP11/MLP16/MLP17`.
- Not yet solved:
  the exact lexical/semantic feature that first enters `MLP11`.

## 4. What Is Now Explained, and What Still Is Not

### Explained Well Enough

- The minimal cue is not being carried through the late tool route as a bare
  lead token.
- By the time the strong in-circuit evidence appears, the cue is already bound
  to answer-delivery objects:
  file suffixes, file target, function-body anchors, instruction tail,
  protocol markers, and textual-answer scaffolds.
- The shared scaffold is best localized as `MLP11 -> MLP16 -> MLP19`.
- The late tool route writes `<tool_call>` through an object-bound scaffold:
  `L20H5` reads file-target/body anchors,
  `L21H1/L21H12` route boundary/protocol structure,
  `L24H6` relays into the `<tool_call>` token scaffold,
  `MLP27` writes the final direction.
- The no-tool route competes in two ways:
  `MLP17` writes no-tool state toward `L23H6`,
  and `MLP17` suppresses the late tool ingress nodes at the same time.

### Only Partly Explained

- The earliest in-circuit head reader is not yet solved to the same standard as
  the late tool route.
- `L2H14` is the best existing candidate, but the full-dataset evidence is too
  weak to strong-write it as *the* earliest cue reader.
- Because `MLP11` is the earliest stable carrier, the most honest statement is:
  the cue is already inside the residual stream by layer 11, but the first
  in-circuit head that reads it cleanly is still underdetermined.

### What Still Needs New Evidence

- A clean token-level clean-vs-corrupt differential for the earliest upstream
  reader feeding `MLP11`.
- Direct residual-direction or logit-lens measurements for `MLP11`, `MLP16`,
  `MLP19`, and `MLP17`, not just rescue-style writer evidence.
- A more isolated object-composition counterfactual that separates:
  - file-target / function-body delivery
  - protocol / tool JSON formatting
  - textual-answer continuation

## Bottom Line

The earliest part of the mechanism is now only partly solved:

- **Solved strongly**:
  the earliest strong in-circuit scaffold is `MLP11 -> MLP16 -> MLP19`.
  It carries a cue-conditioned answer-delivery state and fans it into both the
  late tool writer route and the no-tool competitor route.
- **Solved weakly**:
  `L2H14` is the best existing earliest-head candidate, but not yet strong
  enough for a firm main-text claim.
- **Still missing**:
  the exact first head-level reader that turns the minimal cue into the
  `MLP11` scaffold feature.
