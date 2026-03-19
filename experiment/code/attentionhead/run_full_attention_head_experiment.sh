#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$CODE_ROOT/../.." && pwd)"
cd "$CODE_ROOT"

RUN_TAG="${RUN_TAG:-$(date +%Y%m%d-%H%M%S)-attention-head-full}"
OUT_ROOT="${OUT_ROOT:-$PROJECT_ROOT/experiment/results/attentionhead/$RUN_TAG}"
DATASET_ROOT="${DATASET_ROOT:-$PROJECT_ROOT/experiment/datasets}"
MODEL_PATH="${MODEL_PATH:-/root/autodl-tmp/Qwen/Qwen3-1.7B}"
DEVICE="${DEVICE:-cuda}"
DTYPE="${DTYPE:-bfloat16}"
MAX_SAMPLES="${MAX_SAMPLES:-0}"

mkdir -p "$OUT_ROOT"

python "$CODE_ROOT/attentionhead/run_attention_head_span_experiment.py" \
  --dataset-root "$DATASET_ROOT" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --dtype "$DTYPE" \
  --max-samples "$MAX_SAMPLES" \
  --output-root "$OUT_ROOT" \
  "$@"
