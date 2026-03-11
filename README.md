# Tool-Call Circuit Project

This project reproduces the full tool-call circuit workflow on the 1,189-pair dataset under [datasets/](/root/autodl-tmp/project/datasets), without depending on the old `Automatic-Circuit-Discovery/experiments` layout for execution.

## Layout

- Code package: [src/toolcall_circuit](/root/autodl-tmp/project/src/toolcall_circuit)
- Runnable entrypoints: [scripts/](/root/autodl-tmp/project/scripts)
- Timestamped outputs: [results/](/root/autodl-tmp/project/results)
- Archived legacy code/results reference: [Automatic-Circuit-Discovery/](/root/autodl-tmp/project/Automatic-Circuit-Discovery)

## Main Modules

- Dataset and manifest utilities: [dataset.py](/root/autodl-tmp/project/src/toolcall_circuit/dataset.py)
- Single-sample circuit mining: [single_sample.py](/root/autodl-tmp/project/src/toolcall_circuit/single_sample.py)
- Batch mining: [batch.py](/root/autodl-tmp/project/src/toolcall_circuit/batch.py)
- Cross-sample aggregation: [aggregate.py](/root/autodl-tmp/project/src/toolcall_circuit/aggregate.py)
- Semantic roles: [semantic_roles.py](/root/autodl-tmp/project/src/toolcall_circuit/semantic_roles.py)
- Role-group causal validation: [role_groups.py](/root/autodl-tmp/project/src/toolcall_circuit/role_groups.py)
- Contrast tracing: [contrast_trace.py](/root/autodl-tmp/project/src/toolcall_circuit/contrast_trace.py)
- Edge path patching: [path_patch.py](/root/autodl-tmp/project/src/toolcall_circuit/path_patch.py)
- Backbone refinement: [refine.py](/root/autodl-tmp/project/src/toolcall_circuit/refine.py)
- Consistency evaluation: [consistency.py](/root/autodl-tmp/project/src/toolcall_circuit/consistency.py)

## Full Pipeline

Run from the project root:

```bash
bash scripts/run_toolcall_pipeline.sh
```

Default behavior:

- reads data from `/root/autodl-tmp/project/datasets`
- uses `/root/autodl-tmp/Qwen/Qwen3-1.7B`
- creates a new run under `results/<dd-hh-mm>/`
- refuses to overwrite an existing timestamp directory

Useful overrides:

```bash
RUN_TAG=11-23-10 \
MAX_SAMPLES=2 \
SAMPLE_IDS=codecontests_cpp_186,codecontests_cpp_284 \
BOOTSTRAP=100 \
bash scripts/run_toolcall_pipeline.sh
```

AP-pruned exact CT controls:

```bash
TOOLCALL_CT_AP_PER_LAYER=2
TOOLCALL_CT_AP_TOP_GLOBAL=24
```

## Script Entrypoints

- [mine_toolcall_single.py](/root/autodl-tmp/project/scripts/mine_toolcall_single.py)
- [mine_toolcall_batch.py](/root/autodl-tmp/project/scripts/mine_toolcall_batch.py)
- [aggregate_toolcall_circuits.py](/root/autodl-tmp/project/scripts/aggregate_toolcall_circuits.py)
- [analyze_toolcall_semantic_roles.py](/root/autodl-tmp/project/scripts/analyze_toolcall_semantic_roles.py)
- [evaluate_toolcall_role_groups.py](/root/autodl-tmp/project/scripts/evaluate_toolcall_role_groups.py)
- [trace_toolcall_contrast_token.py](/root/autodl-tmp/project/scripts/trace_toolcall_contrast_token.py)
- [path_patch_toolcall_edges.py](/root/autodl-tmp/project/scripts/path_patch_toolcall_edges.py)
- [refine_consistent_toolcall_circuits.py](/root/autodl-tmp/project/scripts/refine_consistent_toolcall_circuits.py)
- [evaluate_toolcall_consistency.py](/root/autodl-tmp/project/scripts/evaluate_toolcall_consistency.py)

## Current Archived Full Run

The completed full run has been snapshotted to:

- [results/11-21-37](/root/autodl-tmp/project/results/11-21-37)

Inside that run root:

- `batch/`
- `aggregate/`
- `semantic_roles/`
- `refined_consistent/`
- `consistency_eval.json`
- `figs/`
- `tables/`
- `run_manifest.json`

## Notes

- Clean means the assistant's first generated token is `<tool_call>`.
- Corrupt means the first generated token is not `<tool_call>`.
- `<tool_call>` is still a single tokenizer token on the current Qwen3-1.7B tokenizer.
- Contrast spans are dynamic and can be 1 to 3 tokens long; no fixed position assumptions remain.
