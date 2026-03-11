#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DATASET_ROOT="${DATASET_ROOT:-/root/autodl-tmp/project/datasets}"
MODEL_PATH="${MODEL_PATH:-/root/autodl-tmp/Qwen/Qwen3-1.7B}"
DEVICE="${DEVICE:-cuda}"
OUT_BASE="${OUT_BASE:-experiments/results/toolcall_project_1189}"
MAX_SAMPLES="${MAX_SAMPLES:-0}"
SAMPLE_IDS="${SAMPLE_IDS:-}"
BOOTSTRAP="${BOOTSTRAP:-1000}"
RESUME="${RESUME:-1}"
ACDC_CT_AP_PER_LAYER="${ACDC_CT_AP_PER_LAYER:-2}"
ACDC_CT_AP_TOP_GLOBAL="${ACDC_CT_AP_TOP_GLOBAL:-24}"

export ACDC_CT_AP_PER_LAYER
export ACDC_CT_AP_TOP_GLOBAL

batch_args=(
  --source dataset
  --dataset-root "$DATASET_ROOT"
  --model-path "$MODEL_PATH"
  --out-root "$OUT_BASE"
  --device "$DEVICE"
)

if [[ "$MAX_SAMPLES" != "0" ]]; then
  batch_args+=(--max-samples "$MAX_SAMPLES")
fi

if [[ -n "$SAMPLE_IDS" ]]; then
  batch_args+=(--sample-ids "$SAMPLE_IDS")
fi

if [[ "$RESUME" != "0" ]]; then
  batch_args+=(--resume)
fi

python experiments/launch_toolcall_qwen3_batch.py "${batch_args[@]}"

python experiments/aggregate_toolcall_circuits.py \
  --input-root "$OUT_BASE" \
  --output-root "${OUT_BASE}_aggregate" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE"

python experiments/analyze_toolcall_semantic_roles.py \
  --input-root "$OUT_BASE" \
  --aggregate-summary "${OUT_BASE}_aggregate/global_core_summary.json" \
  --output-root "${OUT_BASE}_semantic_roles" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$MAX_SAMPLES"

python experiments/evaluate_toolcall_role_groups.py \
  --input-root "$OUT_BASE" \
  --aggregate-summary "${OUT_BASE}_aggregate/global_core_summary.json" \
  --semantic-report "${OUT_BASE}_semantic_roles/semantic_roles_report.json" \
  --output-root "${OUT_BASE}_semantic_roles" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$MAX_SAMPLES" \
  --bootstrap "$BOOTSTRAP"

python experiments/trace_toolcall_contrast_token.py \
  --input-root "$OUT_BASE" \
  --output-root "${OUT_BASE}_semantic_roles" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$MAX_SAMPLES"

python experiments/path_patch_toolcall_edges.py \
  --input-root "$OUT_BASE" \
  --aggregate-summary "${OUT_BASE}_aggregate/global_core_summary.json" \
  --output-root "${OUT_BASE}_semantic_roles" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$MAX_SAMPLES" \
  --bootstrap "$BOOTSTRAP" \
  --trim-frac 0.10
