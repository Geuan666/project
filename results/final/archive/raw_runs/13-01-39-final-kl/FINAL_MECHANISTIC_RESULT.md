# Final Mechanistic Result

## Core Claim

In this fixed tool environment, the decisive variable is not schema availability itself. The decisive variable is an instruction-level commitment cue in the user request: whether the model is being asked to commit to an external file-writing / execution-style delivery, or merely to author the function body in text.

The resulting signed circuit remains highly faithful: full-circuit KL recovery `1.000` / `0.998`, top-1 `0.999` / `0.997`.

## Final 4-Step Mechanistic Chain

1. The model reads an instruction-level commitment cue from the first user instruction line. Swapping only that line is enough to flip the first-token decision across the whole dataset.
   Evidence: `clean_full` decision `3.203` and tool-top1 `1.000`, but `clean_with_corrupt_instruction` drops to decision `-4.562` and tool-top1 `0.000`; `corrupt_with_clean_instruction` flips back to tool-top1 `1.000`.
   Stronger evidence: swapping only the minimal lead phrase has the same effect: `clean_with_corrupt_lead` tool-top1 `0.000`, `corrupt_with_clean_lead` tool-top1 `1.000`.

2. That commitment cue enters the tool-writing route through a user-conditioned late ingress path.
   The best-supported path is `L20H5 -> L21H1/L21H12 -> L24H6 -> MLP27`.
   Evidence: `L20H5` rescue `0.308`, `L21H1` `0.573`, `L21H12` `0.707`, `L21H12->MLP27` mediation `0.328`.
   Stepwise buildup: by `L20H5|L21H1|L21H12` the decision is already `0.714` with tool-top1 `0.700`; the full route reaches tool-top1 `0.937`.

3. `MLP27` writes this state into a `<tool_call>`-favoring output direction.
   Evidence: at steering alpha `1.5`, `corrupt_full` reaches tool-top1 `0.833`, `clean_schema_mismatch` reaches `0.957`, `clean_no_protocol` still reaches `0.593`.
   Backup search: on `corrupt_full`, MLP27 direct rescue is `0.809` while the best independent alternative under MLP27 block is only `0.371` from `L21H12`.
   Caveat: on `clean_no_schema`, alternatives remain more competitive; MLP27 is therefore best described as a primary late writer, not a proven unique bottleneck.

4. A competing no-tool chain pushes the same fixed tool environment back toward `no_tool`.
   The best-supported path is `L16H4 -> MLP17 -> L23H6`.
   Evidence: `MLP17` rescue `0.474`, `MLP17->L20H5` mediation `0.049`, full suppressive route no-tool top1 `0.516`.

## Human-Level Interpretation

The strongest interpretation is that the circuit is tracking a performative distinction: is the user asking for a committed file/environment action, or merely for authored content? In this dataset, that distinction is carried overwhelmingly by the opening instruction phrase.

This supports three human-readable latent variables, with different confidence levels:
- Strongest: `performative demand` or `instruction-level commitment cue`.
- Strong: `execution commitment threshold`, written by the late writer path around `MLP27`.
- Plausible but weaker: `direct-answer sufficiency`; it likely underlies the commitment cue, but the current dataset isolates instruction phrasing more directly than abstract answer sufficiency.

## What We Can Write Strongly

- Claim tiers from the mechanism audit: A=`6`, B=`8`, C=`1`.
- Strongest main-text statement: under fixed schema/protocol, swapping only the instruction-level commitment cue is sufficient to flip the model between `<tool_call>` and `no_tool`.
- Strong main-text statement: the user-conditioned route enters through `L20H5`, is routed by `L21H1/L21H12`, and is written out by `MLP27`.
- Strong main-text statement: `L16H4 -> MLP17 -> L23H6` is a competing no-tool route that can suppress the tool-writing path.

## What Must Stay Weak

- `L20H5` should be described as a user-conditioned late ingress point, not yet as a pure action-demand reader.
- `L16H4` should be described as a no-tool-biased user-side reader, not yet as a pure ordinary-answer prior.
- `MLP27` should be described as a primary late writer, not a proven unique bottleneck.

## What Should Not Be Claimed

- Do not claim a unified mode switcher.
- Do not claim a generic arbitration zone.
- Do not center the final story on the early `L2H14` branch.

## Artifact Index

- `query_decision_chain/query_decision_report.md`
- `instruction_commitment/instruction_commitment_report.md`
- `instruction_lead/instruction_lead_report.md`
- `late_writer_backup/late_writer_backup_report.md`
- `mechanism_audit/component_evidence_table.csv`
- `mechanism_audit/writing_boundary.md`
- `final_head_attention_audit/head_final_audit_report.md`
- `final_head_attention_audit/head_final_audit_summary.json`
- `final_mechanism_evidence/final_component_evidence_table.csv`
- `final_mechanism_evidence/final_edge_evidence_table.csv`
- `final_mechanism_evidence/final_claim_tree.json`
