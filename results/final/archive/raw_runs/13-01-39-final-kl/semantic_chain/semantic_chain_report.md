# Semantic Causal Chain Report

- Run root: `/root/autodl-tmp/project/results/13-01-39-final-kl`

## Extracted Candidate Paths

### Query-Conditioned Tool Branch

- Direction: `tool`
- Nodes: `L2H14 -> MLP11 -> MLP16 -> L24H6 -> Residual Output: decision`
- Path score: `-7.931`
- Node semantics:
  - `L2H14`: User-Query Readers / tool_tail / tool-tail router / reads user content on tool endpoint (user=0.31)
  - `MLP11`: Tool-Call Writers / tool_bias_backbone / tool-biased writer MLP / tool-skewed writer (+0.18)
  - `MLP16`: Arbitration Integrators / symmetric_backbone / shared writer MLP / shared late writer with balanced causal role (+0.09)
  - `L24H6`: Arbitration Integrators / symmetric_backbone / format/prefix router / late shared head with balanced causal profile (+0.16)
- Edge evidence:
  - `L2H14 -> MLP11`: promote-mediated `0.009`, suppress-mediated `0.000`, support `0.187`
  - `MLP11 -> MLP16`: promote-mediated `0.242`, suppress-mediated `0.133`, support `0.242`
  - `MLP16 -> L24H6`: promote-mediated `0.166`, suppress-mediated `0.038`, support `0.237`
  - `L24H6 -> Residual Output: decision`: promote-mediated `nan`, suppress-mediated `nan`, support `0.994`
- Stagewise cumulative patching:
  - step 1 / `L2H14`: cum `0.042`, inc `0.042`, top1 `0.000`, boundary `0.000`
  - step 2 / `MLP11`: cum `0.350`, inc `0.309`, top1 `0.037`, boundary `0.036`
  - step 3 / `MLP16`: cum `0.577`, inc `0.220`, top1 `0.131`, boundary `0.127`
  - step 4 / `L24H6`: cum `0.812`, inc `0.220`, top1 `0.322`, boundary `0.311`

### Schema-Conditioned Tool Branch

- Direction: `tool`
- Nodes: `L21H12 -> MLP27 -> Residual Output: decision`
- Path score: `-1.114`
- Node semantics:
  - `L21H12`: Tool-Schema Readers / tool_bias_backbone / format/prefix router / reads tools/tags (tools=0.25, tags=0.015)
  - `MLP27`: Arbitration Integrators / symmetric_backbone / shared writer MLP / shared late writer with balanced causal role (+0.00)
- Edge evidence:
  - `L21H12 -> MLP27`: promote-mediated `0.328`, suppress-mediated `0.166`, support `0.714`
  - `MLP27 -> Residual Output: decision`: promote-mediated `nan`, suppress-mediated `nan`, support `0.999`
- Stagewise cumulative patching:
  - step 1 / `L21H12`: cum `0.707`, inc `0.707`, top1 `0.159`, boundary `0.143`
  - step 2 / `MLP27`: cum `0.948`, inc `0.228`, top1 `0.733`, boundary `0.805`

### No-Tool Suppression Branch

- Direction: `no_tool`
- Nodes: `L16H4 -> MLP17 -> L23H6 -> Residual Output: decision`
- Path score: `-5.302`
- Node semantics:
  - `L16H4`: Suppression Readers / no_tool_bias_backbone / no-tool-biased router / reads user/prefix more in no-tool mode (d_user=+0.06, d_prefix=-0.00)
  - `MLP17`: No-Tool Writers / no_tool_bias_backbone / no-tool-biased writer MLP / no-tool-skewed writer (+0.08)
  - `L23H6`: Suppression Readers / tool_bias_backbone / tool-biased router / reads user/prefix more in no-tool mode (d_user=+0.02, d_prefix=+0.06)
- Edge evidence:
  - `L16H4 -> MLP17`: promote-mediated `0.081`, suppress-mediated `0.076`, support `0.419`
  - `MLP17 -> L23H6`: promote-mediated `0.050`, suppress-mediated `0.066`, support `0.553`
  - `L23H6 -> Residual Output: decision`: promote-mediated `nan`, suppress-mediated `nan`, support `0.994`
- Stagewise cumulative patching:
  - step 1 / `L16H4`: cum `0.198`, inc `0.198`, top1 `0.012`, boundary `0.001`
  - step 2 / `MLP17`: cum `0.605`, inc `0.389`, top1 `0.246`, boundary `0.179`
  - step 3 / `L23H6`: cum `0.795`, inc `0.174`, top1 `0.516`, boundary `0.474`

## Candidate Algorithm

- Query-conditioned branch: a small early reader (`L2H14`) reads actionable user wording, an early tool-biased writer (`MLP11`) amplifies it, then late shared integrators (`MLP16`, `L24H6`) carry it to the decision output.
- Schema-conditioned branch: late schema/tag readers (`L21H12` in the extracted path) inject tool-availability evidence directly into the final writer bottleneck (`MLP27`).
- No-tool branch: suppression readers (`L16H4` in the extracted path) feed a no-tool-biased writer (`MLP17`), which then routes through a late suppressive node (`L23H6`) to keep generation in ordinary-answer mode.
- The final decision is therefore not a single switch; it is a late competition between a query/tool-use branch and a no-tool suppression branch.

## Artifacts

- `semantic_chain_summary.json`
- `semantic_chain_summary.csv`
- `semantic_chain_per_sample.csv`
- `semantic_chain_progression.png`

