# Tool-Call Signed Circuit Final Report

## Executive Summary

- Dataset: `2` discovery samples per direction in this run root.
- Final structural signed circuit: `31` nodes / `70` edges.
- Full-circuit KL recovery: promote `1.000`, suppress `0.999`.
- Full-circuit top-1 flips: promote `1.000`, suppress `1.000`.

## Structural Story

- Structural groups remain internal analysis tags:
  - `symmetric_backbone`: `12` nodes
  - `tool_bias_backbone`: `1` nodes
  - `no_tool_bias_backbone`: `3` nodes
  - `tool_tail`: `8` nodes
  - `no_tool_tail`: `7` nodes

Core structural artifacts:
- `final_signed_circuit/final_signed_circuit.png`
- `bidirectional/bidirectional_summary.json`
- `signed_validate/signed_group_report.json`

## Functional Semantic Groups

- `Tool-Schema Readers`: `5` nodes, promote median `0.431`, suppress median `0.173`.
- `User-Query Readers`: `3` nodes, promote median `0.152`, suppress median `0.000`.
- `Suppression Readers`: `5` nodes, promote median `0.232`, suppress median `0.123`.
- `Promotion Routers`: `3` nodes, promote median `0.119`, suppress median `0.000`.
- `Tool-Call Writers`: `7` nodes, promote median `0.224`, suppress median `0.049`.
- `No-Tool Writers`: `2` nodes, promote median `0.133`, suppress median `0.039`.
- `Arbitration Integrators`: `6` nodes, promote median `0.563`, suppress median `0.330`.

Functional artifacts:
- `functional_groups/functional_group_graph.png`
- `functional_groups/functional_node_table.csv`
- `functional_validate/functional_group_report.json`

## Faithfulness Checks

- Structural group validation:
  - `symmetric_backbone`: suff `0.998/0.997`, nec `0.001/-0.019`.
  - `tool_bias_backbone`: suff `0.652/0.173`, nec `-0.000/0.000`.
  - `no_tool_bias_backbone`: suff `0.908/0.647`, nec `0.000/0.000`.
  - `tool_tail`: suff `0.754/0.223`, nec `0.000/-0.000`.
  - `no_tool_tail`: suff `0.905/0.493`, nec `-0.000/-0.002`.
- Functional group validation:
  - `Tool-Schema Readers`: suff `0.982/0.891`, nec `0.000/0.001`.
  - `User-Query Readers`: suff `0.231/0.075`, nec `-0.000/-0.000`.
  - `Suppression Readers`: suff `0.909/0.569`, nec `0.000/0.001`.
  - `Promotion Routers`: suff `0.205/0.076`, nec `0.000/-0.000`.
  - `Tool-Call Writers`: suff `0.968/0.784`, nec `-0.000/0.004`.
  - `No-Tool Writers`: suff `0.086/-0.061`, nec `-0.000/0.000`.
  - `Arbitration Integrators`: suff `0.996/0.980`, nec `0.000/0.001`.

## Behavioral Evidence

- `shared_backbone`: top-1 `1.000/1.000`, boundary `1.000/1.000`.
- `shared_backbone_exclusive`: top-1 `1.000/1.000`, boundary `1.000/1.000`.
- `forward_selective`: top-1 `0.500/0.000`, boundary `0.500/0.000`.
- `reverse_selective`: top-1 `1.000/0.500`, boundary `1.000/0.500`.

## Node / Edge Diagnostics

- Top node diagnostics:
  - `MLP27`: suff `0.771/0.649`, nec `0.000/-0.002`.
  - `L16H4`: suff `0.232/0.112`, nec `-0.000/-0.002`.
  - `MLP19`: suff `0.682/0.302`, nec `0.000/-0.001`.
  - `L17H8`: suff `0.222/0.117`, nec `-0.000/-0.001`.
  - `MLP16`: suff `0.874/0.581`, nec `0.000/-0.001`.
  - `MLP13`: suff `0.108/0.017`, nec `0.000/-0.001`.
  - `L17H12`: suff `0.333/0.136`, nec `-0.000/-0.001`.
  - `L13H9`: suff `0.159/0.043`, nec `-0.000/-0.001`.
  - `L2H14`: suff `0.154/-0.010`, nec `-0.000/-0.001`.
  - `L23H6`: suff `0.667/0.264`, nec `-0.000/-0.001`.
- Top edge diagnostics:
  - `L24H6->MLP27`: mediated `0.306/0.216`.
  - `MLP16->MLP17`: mediated `0.233/0.218`.
  - `L21H1->MLP27`: mediated `0.344/0.105`.
  - `MLP16->L21H1`: mediated `0.116/0.118`.
  - `L21H1->L24H6`: mediated `0.200/0.020`.
  - `L21H12->L23H6`: mediated `0.135/0.077`.
  - `L21H1->L23H6`: mediated `0.119/0.093`.
  - `MLP16->L24H6`: mediated `0.142/0.045`.
  - `MLP16->L23H6`: mediated `0.086/0.094`.
  - `L16H8->MLP17`: mediated `0.089/0.029`.

## Artifact Index

- Run root: `/root/autodl-tmp/project/results/_smoke_kl_pipeline_v2`
- Main figure: `final_signed_circuit/final_signed_circuit.png`
- Structural validation: `signed_validate/signed_group_validation_heatmap.png`
- Functional graph: `functional_groups/functional_group_graph.png`
- Functional validation: `functional_validate/functional_group_validation_heatmap.png`
- Token flips: `token_flip/group_token_flip_summary.csv`
- Node importance: `node_importance/signed_node_importance_heatmap.png`
- Trajectory: `signed_layer_trajectory/signed_layer_trajectory.png`
