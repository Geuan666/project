# Tool-Call ACDC Migration Notes

This directory mirrors the role of the reference project's `final/README.md`: it documents the adapted workflow and the required output roots for the new 1189-pair dataset.

## Dataset Facts

- Dataset root: `/root/autodl-tmp/project/datasets`
- Clean count: `1189`
- Corrupt count: `1189`
- Pairing rule: match by identical filename
- Clean criterion: assistant first generated token is `<tool_call>`
- Corrupt criterion: assistant first generated token is not `<tool_call>`
- `<tool_call>` is still a single tokenizer token under `/root/autodl-tmp/Qwen/Qwen3-1.7B`

## Required Generalizations

- Sample identity is filename-based, not `q1..q164`
- Contrast handling is multi-position aware (`contrast_positions`, `contrast_spans`)
- `Input Embed` path patching now patches the full contrast position set
- `<tool_call>` / `</tool_call>` locations are found dynamically
- The old pair layout remains supported only as a compatibility mode

## Full Workflow

From `/root/autodl-tmp/project/Automatic-Circuit-Discovery`:

```bash
bash experiments/run_toolcall_project_pipeline.sh
```

Default output roots:

- `experiments/results/toolcall_project_1189`
- `experiments/results/toolcall_project_1189_aggregate`
- `experiments/results/toolcall_project_1189_semantic_roles`

## Smoke Validation Already Produced

The migration smoke run used:

- phrase sample: `codecontests_cpp_186`
- verb sample: `codecontests_cpp_284`

Generated roots:

- `experiments/results/smoke_batch`
- `experiments/results/smoke_batch_aggregate`
- `experiments/results/smoke_batch_semantic`
- `experiments/results/smoke_batch_refined`
- `experiments/results/smoke_batch_consistency_eval.json`

Smoke-specific checks that passed:

- batch mining
- cross-sample aggregation
- semantic role analysis
- role-group causal validation
- contrast tracing with span lengths `1` and `3`
- edge-level path patching
- refined-consistency auxiliary scripts
