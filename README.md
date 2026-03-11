# Tool-Call ACDC Migration Project

This project ports the full `/root/autodl-tmp/XAI-1.7B-ACDC` workflow onto the new 1189-pair dataset under `/root/autodl-tmp/project/datasets`.

## What Changed

- Sample identity is now filename-based (`sample_id = <txt stem>`), not `q1..q164`.
- Clean/corrupt pairing comes from `datasets/clean` and `datasets/corrupt` by matching filenames.
- The pipeline validates `<tool_call>` tokenization before running. On the current Qwen3-1.7B tokenizer it is still a single token.
- Contrast handling is now multi-position aware:
  - summaries store `contrast_positions` and `contrast_spans`;
  - contrast tracing patches the full contrast token set;
  - edge path patching patches all contrast positions for `Input Embed`.
- `<tool_call>` / `</tool_call>` positions are located dynamically from tokens; no fixed `tool_call_pos` remains.
- The legacy pair-style reference layout is still supported for comparison runs.

## Main Paths

- Code root: `/root/autodl-tmp/project/Automatic-Circuit-Discovery`
- Dataset root: `/root/autodl-tmp/project/datasets`
- Full default outputs:
  - batch: `experiments/results/toolcall_project_1189`
  - aggregate: `experiments/results/toolcall_project_1189_aggregate`
  - semantic / role-group / trace / path-patch: `experiments/results/toolcall_project_1189_semantic_roles`
- Smoke outputs produced during migration:
  - batch: `experiments/results/smoke_batch`
  - aggregate: `experiments/results/smoke_batch_aggregate`
  - downstream analysis: `experiments/results/smoke_batch_semantic`

## Full Run

From `/root/autodl-tmp/project/Automatic-Circuit-Discovery`:

```bash
bash experiments/run_toolcall_project_pipeline.sh
```

Equivalent explicit commands:

```bash
python experiments/launch_toolcall_qwen3_batch.py \
  --source dataset \
  --dataset-root /root/autodl-tmp/project/datasets \
  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B \
  --out-root experiments/results/toolcall_project_1189 \
  --device cuda

python experiments/aggregate_toolcall_circuits.py \
  --input-root experiments/results/toolcall_project_1189 \
  --output-root experiments/results/toolcall_project_1189_aggregate \
  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B \
  --device cuda

python experiments/analyze_toolcall_semantic_roles.py \
  --input-root experiments/results/toolcall_project_1189 \
  --aggregate-summary experiments/results/toolcall_project_1189_aggregate/global_core_summary.json \
  --output-root experiments/results/toolcall_project_1189_semantic_roles \
  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B \
  --device cuda

python experiments/evaluate_toolcall_role_groups.py \
  --input-root experiments/results/toolcall_project_1189 \
  --aggregate-summary experiments/results/toolcall_project_1189_aggregate/global_core_summary.json \
  --semantic-report experiments/results/toolcall_project_1189_semantic_roles/semantic_roles_report.json \
  --output-root experiments/results/toolcall_project_1189_semantic_roles \
  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B \
  --device cuda

python experiments/trace_toolcall_contrast_token.py \
  --input-root experiments/results/toolcall_project_1189 \
  --output-root experiments/results/toolcall_project_1189_semantic_roles \
  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B \
  --device cuda

python experiments/path_patch_toolcall_edges.py \
  --input-root experiments/results/toolcall_project_1189 \
  --aggregate-summary experiments/results/toolcall_project_1189_aggregate/global_core_summary.json \
  --output-root experiments/results/toolcall_project_1189_semantic_roles \
  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B \
  --device cuda \
  --trim-frac 0.10
```

## Smoke Run

The migration smoke test used one phrase sample and one verb sample:

```bash
SAMPLE_IDS=codecontests_cpp_186,codecontests_cpp_284 \
OUT_BASE=experiments/results/smoke_batch \
MAX_SAMPLES=2 \
BOOTSTRAP=100 \
bash experiments/run_toolcall_project_pipeline.sh
```

Manual smoke commands can use the same output roots already generated under `experiments/results/smoke_*`.

## Acceptance Notes

- `datasets/clean` and `datasets/corrupt` each contain 1189 `.txt` files, and the filename sets match exactly.
- `contrast_token_trace_report.json` from the smoke run confirms mixed contrast span lengths (`1` and `3`), validating the multi-token path.
- The smoke batch summaries include dynamic `tool_call_tag_positions`, manifest-backed `sample_catalog_record`, and multi-position `contrast_spans`.
