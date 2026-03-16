# Tool-Call Signed Circuit Final Report

## Executive Summary

- Dataset: `1722` discovery samples per direction in this run root.
- Final structural signed circuit: `24` nodes / `64` edges.
- Full-circuit KL recovery: promote `1.000`, suppress `0.998`.
- Full-circuit top-1 flips: promote `0.999`, suppress `0.997`.

## Structural Story

- Structural groups remain internal analysis tags:
  - `symmetric_backbone`: `8` nodes
  - `tool_bias_backbone`: `4` nodes
  - `no_tool_bias_backbone`: `4` nodes
  - `tool_tail`: `4` nodes
  - `no_tool_tail`: `4` nodes

Core structural artifacts:
- `final_signed_circuit/final_signed_circuit.png`
- `bidirectional/bidirectional_summary.json`
- `signed_validate/signed_group_report.json`

## Functional Semantic Groups

- `Tool-Schema Readers`: `6` nodes, promote median `0.318`, suppress median `0.214`.
- `User-Query Readers`: `1` nodes, promote median `0.042`, suppress median `0.006`.
- `Suppression Readers`: `6` nodes, promote median `0.259`, suppress median `0.117`.
- `Tool-Call Writers`: `2` nodes, promote median `0.405`, suppress median `0.153`.
- `No-Tool Writers`: `2` nodes, promote median `0.554`, suppress median `0.474`.
- `Arbitration Integrators`: `7` nodes, promote median `0.524`, suppress median `0.376`.

Functional artifacts:
- `functional_groups/functional_group_graph.png`
- `functional_groups/functional_node_table.csv`
- `functional_validate/functional_group_report.json`

## Faithfulness Checks

- Structural group validation:
  - `symmetric_backbone`: suff `0.994/0.986`, nec `0.001/-0.003`.
  - `tool_bias_backbone`: suff `0.965/0.865`, nec `0.001/-0.001`.
  - `no_tool_bias_backbone`: suff `0.892/0.799`, nec `0.000/-0.002`.
  - `tool_tail`: suff `0.690/0.407`, nec `0.000/-0.002`.
  - `no_tool_tail`: suff `0.479/0.353`, nec `0.000/-0.000`.
- Functional group validation:
  - `Tool-Schema Readers`: suff `0.965/0.908`, nec `0.000/0.001`.
  - `User-Query Readers`: suff `0.042/0.006`, nec `0.000/0.000`.
  - `Suppression Readers`: suff `0.878/0.739`, nec `0.000/0.001`.
  - `Tool-Call Writers`: suff `0.598/0.280`, nec `0.000/0.001`.
  - `No-Tool Writers`: suff `0.590/0.541`, nec `0.000/0.001`.
  - `Arbitration Integrators`: suff `0.991/0.981`, nec `0.001/0.003`.

## Behavioral Evidence

- `shared_backbone`: top-1 `0.997/0.995`, boundary `1.000/1.000`.
- `shared_backbone_exclusive`: top-1 `0.973/0.987`, boundary `0.998/0.997`.
- `forward_selective`: top-1 `0.913/0.918`, boundary `0.972/0.930`.
- `reverse_selective`: top-1 `0.740/0.706`, boundary `0.787/0.727`.

## Initial Extracted Chain Candidates

- These are discovery-time chain candidates. The refined fixed-schema and instruction-level analyses below supersede the early `L2H14`-anchored query interpretation.
- `Query-Conditioned Tool Branch`: `L2H14 -> MLP11 -> MLP16 -> L24H6 -> Residual Output: decision`, final cumulative `0.812`, top1 `0.322`.
- `Schema-Conditioned Tool Branch`: `L21H12 -> MLP27 -> Residual Output: decision`, final cumulative `0.948`, top1 `0.733`.
- `No-Tool Suppression Branch`: `L16H4 -> MLP17 -> L23H6 -> Residual Output: decision`, final cumulative `0.795`, top1 `0.516`.
- Detailed chain report: `semantic_chain/semantic_chain_report.md`
- Progression plot: `semantic_chain/semantic_chain_progression.png`

## Factorized Counterfactuals

- `clean_full`: tool `0.000`, no-tool `-3.203`, tool-top1 `1.000`.
- `corrupt_full`: tool `-4.562`, no-tool `0.000`, tool-top1 `0.000`.
- `clean_no_schema`: tool `-3.102`, no-tool `-0.196`, tool-top1 `0.100`.
- `clean_schema_mismatch`: tool `-4.969`, no-tool `-0.174`, tool-top1 `0.053`.
- `clean_no_protocol`: tool `-13.000`, no-tool `-0.432`, tool-top1 `0.000`.
- rescue `no_tool_path` on `clean_full`: `0.795` with top1 `0.516`.
- rescue `query_tool_path` on `corrupt_full`: `0.812` with top1 `0.322`.
- rescue `schema_tool_path` on `clean_no_protocol`: `2.556` with top1 `0.469`.
- rescue `schema_tool_path` on `clean_no_schema`: `0.594` with top1 `0.740`.
- rescue `schema_tool_path` on `clean_schema_mismatch`: `1.008` with top1 `0.927`.
- schema step `1` / `L21H12` on `clean_no_protocol`: rescue `1.745`, top1 `0.015`.
- schema step `2` / `MLP27` on `clean_no_protocol`: rescue `2.556`, top1 `0.469`.
- schema step `1` / `L21H12` on `clean_no_schema`: rescue `0.532`, top1 `0.544`.
- schema step `2` / `MLP27` on `clean_no_schema`: rescue `0.594`, top1 `0.740`.
- schema step `1` / `L21H12` on `clean_schema_mismatch`: rescue `0.835`, top1 `0.471`.
- schema step `2` / `MLP27` on `clean_schema_mismatch`: rescue `1.008`, top1 `0.927`.
- Detailed schema-stagewise report: `schema_stagewise/schema_stagewise_report.md`
- Detailed factorized report: `semantic_factorized/semantic_factorized_report.md`

## Mechanism Audit

- Claim tiers: A=`6`, B=`8`, C=`1`.
- Main component findings:
  - `MLP11` [B]: candidate early tool-favoring writer downstream of the query-side reader (direct `0.331`, path `1.039`).
  - `MLP16` [B]: shared late relay/writer that transports upstream tool-biased state toward the output-adjacent region (direct `0.524`, path `1.039`).
  - `L21H12` [B]: reads schema/protocol availability cues and sends them to the late tool writer (direct `1.745`, path `3.739`).
  - `MLP27` [B]: late writer that converts schema-conditioned state into a tool-call-favoring output direction (direct `1.964`, path `3.739`).
  - `L16H4` [B]: reads no-tool / ordinary-answer evidence from the user-side prompt and feeds the no-tool chain (direct `0.198`, path `0.422`).
  - `MLP17` [B]: writes a no-tool-favoring residual state inside the suppression chain (direct `0.474`, path `0.422`).
  - `L23H6` [B]: late suppressive relay that carries no-tool-biased state toward the output (direct `0.280`, path `0.192`).
  - `L24H6` [B]: late relay/writer that helps carry tool-biased state into the final output region (direct `1.792`, path `0.335`).
- Main edge findings:
  - `L2H14->MLP11`: candidate ingress edge from query-side reader into the early tool writer (mediated `0.500` on `corrupt_full`).
  - `MLP11->MLP16`: candidate relay edge from early tool write into the shared late relay (mediated `1.039` on `corrupt_full`).
  - `MLP16->L24H6`: candidate late relay edge inside the query-conditioned branch (mediated `0.335` on `corrupt_full`).
  - `L21H12->MLP27`: carries schema/protocol-conditioned signal into the final late writer (mediated `3.739` on `clean_no_protocol`).
  - `L16H4->MLP17`: passes no-tool-biased user-side evidence into the no-tool writer (mediated `0.422` on `clean_full`).
  - `MLP17->L23H6`: passes no-tool-biased written state into the late suppressive relay (mediated `0.192` on `clean_full`).
- MLP27 steering at alpha `1.5`:
  - `corrupt_full`: decision `1.201`, tool-top1 `0.833`, boundary `0.900`.
  - `clean_no_schema`: decision `0.945`, tool-top1 `0.681`, boundary `0.761`.
  - `clean_schema_mismatch`: decision `2.038`, tool-top1 `0.957`, boundary `0.981`.
  - `clean_no_protocol`: decision `0.752`, tool-top1 `0.593`, boundary `0.661`.
- Late writer backup search:
  - `clean_no_protocol`: MLP27 direct `1.964`, best alt direct `L21H1`=`1.817`, best alt with MLP27 blocked `L21H12`=`0.993`.
  - `clean_no_schema`: MLP27 direct `0.468`, best alt direct `MLP19`=`0.561`, best alt with MLP27 blocked `MLP19`=`0.353`.
  - `clean_schema_mismatch`: MLP27 direct `0.872`, best alt direct `L21H12`=`0.835`, best alt with MLP27 blocked `L21H12`=`0.468`.
  - `corrupt_full`: MLP27 direct `0.809`, best alt direct `L21H12`=`0.707`, best alt with MLP27 blocked `L21H12`=`0.371`.
- Mechanism audit table: `mechanism_audit/component_evidence_table.csv`
- Writing boundary: `mechanism_audit/writing_boundary.md`
- MLP27 steering: `mlp27_steering/mlp27_steering_report.md`
- Late writer backup search: `late_writer_backup/late_writer_backup_report.md`

## Fixed-Schema Query Decision

- `L20H5` clean->corrupt rescue `0.308`; `L21H1` `0.573`; `L21H12` `0.707`; `MLP27` `0.809`.
- Cumulative fixed-schema query chain tool-top1 `0.937`.
- Competing suppressive chain no-tool top1 `0.516`.
- Key edge mediation: `L20H5->L21H12` `0.094`, `L21H12->MLP27` `0.328`, `MLP17->L20H5` `0.049`.
- Detailed report: `query_decision_chain/query_decision_report.md`
- Stepwise plot: `query_decision_chain/query_decision_stepwise.png`

## Instruction-Level Commitment

- `clean_full`: decision `3.203`, tool-top1 `1.000`, no-tool-top1 `0.000`.
- `clean_with_corrupt_instruction`: decision `-4.562`, tool-top1 `0.000`, no-tool-top1 `0.999`.
- `corrupt_with_clean_instruction`: decision `3.203`, tool-top1 `1.000`, no-tool-top1 `0.000`.
- `corrupt_full`: decision `-4.562`, tool-top1 `0.000`, no-tool-top1 `0.999`.
- Query chain on corrupt instruction swap: `L20H5|L21H1|L21H12|L24H6|MLP27` -> rescue `0.991`, tool-top1 `0.937`.
- No-tool chain on clean instruction swap: `L16H4|MLP17|L23H6` -> rescue `0.795`, no-tool-top1 `0.516`.
- Most common clean instruction lines:
  - `113`x `Directly build the function body in solve.py based on the function definition and docstring below:`
  - `87`x `Create the function body in solve.cpp based on the function definition and docstring below:`
  - `77`x `Edit the function body in solve.java based on the function definition and docstring below:`
- Most common corrupt instruction lines:
  - `99`x `Develop the function body in solve.cpp based on the function definition and docstring below:`
  - `89`x `Independently develop the function body in solve.py based on the function definition and docstring below:`
  - `82`x `Implement the function body in solve.cpp based on the function definition and docstring below:`
- Detailed report: `instruction_commitment/instruction_commitment_report.md`
- Variant effect plot: `instruction_commitment/instruction_variant_effects.png`

## Minimal Lead Cue

- `clean_full`: decision `3.203`, tool-top1 `1.000`, no-tool-top1 `0.000`.
- `clean_with_corrupt_lead`: decision `-4.562`, tool-top1 `0.000`, no-tool-top1 `0.999`.
- `corrupt_with_clean_lead`: decision `3.203`, tool-top1 `1.000`, no-tool-top1 `0.000`.
- `corrupt_full`: decision `-4.562`, tool-top1 `0.000`, no-tool-top1 `0.999`.
- Query chain on corrupt lead swap: `L20H5|L21H1|L21H12|L24H6|MLP27` -> rescue `0.991`, tool-top1 `0.937`.
- Detailed report: `instruction_lead/instruction_lead_report.md`

## Node / Edge Diagnostics

- Top node diagnostics:
  - `MLP19`: suff `0.538/0.376`, nec `0.000/-0.001`.
  - `MLP17`: suff `0.554/0.474`, nec `0.000/-0.001`.
  - `MLP21`: suff `0.405/0.143`, nec `0.000/-0.001`.
  - `MLP27`: suff `0.809/0.807`, nec `0.000/-0.001`.
  - `L23H6`: suff `0.525/0.280`, nec `0.000/-0.000`.
  - `L18H14`: suff `0.262/0.117`, nec `0.000/-0.000`.
  - `MLP16`: suff `0.524/0.431`, nec `0.000/-0.000`.
  - `L20H5`: suff `0.308/0.194`, nec `0.000/-0.000`.
  - `L21H12`: suff `0.707/0.368`, nec `0.000/-0.000`.
  - `L17H2`: suff `0.251/0.167`, nec `0.000/-0.000`.
- Top edge diagnostics:
  - `L24H6->MLP27`: mediated `0.305/0.256`.
  - `L21H12->MLP27`: mediated `0.328/0.166`.
  - `MLP16->MLP17`: mediated `0.220/0.210`.
  - `L21H1->MLP27`: mediated `0.292/0.130`.
  - `L23H6->MLP27`: mediated `0.264/0.133`.
  - `MLP11->MLP16`: mediated `0.242/0.133`.
  - `MLP17->MLP19`: mediated `0.149/0.169`.
  - `MLP12->MLP16`: mediated `0.170/0.123`.
  - `L23H6->L24H6`: mediated `0.235/0.053`.
  - `MLP16->MLP19`: mediated `0.133/0.132`.

## Artifact Index

- Run root: `/root/autodl-tmp/project/results/13-01-39-final-kl`
- Final mechanistic result: `FINAL_MECHANISTIC_RESULT.md`
- Main figure: `final_signed_circuit/final_signed_circuit.png`
- Structural validation: `signed_validate/signed_group_validation_heatmap.png`
- Functional graph: `functional_groups/functional_group_graph.png`
- Functional validation: `functional_validate/functional_group_validation_heatmap.png`
- Semantic chain: `semantic_chain/semantic_chain_report.md`
- Factorized counterfactuals: `semantic_factorized/semantic_factorized_report.md`
- Schema stagewise: `schema_stagewise/schema_stagewise_report.md`
- Mechanism audit: `mechanism_audit/mechanism_audit_summary.json`
- MLP27 steering: `mlp27_steering/mlp27_steering_report.md`
- Late writer backup: `late_writer_backup/late_writer_backup_report.md`
- Fixed-schema query decision: `query_decision_chain/query_decision_report.md`
- Instruction commitment: `instruction_commitment/instruction_commitment_report.md`
- Instruction lead cue: `instruction_lead/instruction_lead_report.md`
- Final head attention audit: `final_head_attention_audit/head_final_audit_report.md`
- Final mechanism evidence: `final_mechanism_evidence/final_mechanism_evidence_summary.json`
- Token flips: `token_flip/group_token_flip_summary.csv`
- Node importance: `node_importance/signed_node_importance_heatmap.png`
- Trajectory: `signed_layer_trajectory/signed_layer_trajectory.png`
