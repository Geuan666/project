#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

DATASET_ROOT="${DATASET_ROOT:-$PROJECT_ROOT/datasets}"
MODEL_PATH="${MODEL_PATH:-/root/autodl-tmp/Qwen/Qwen3-1.7B}"
DEVICE="${DEVICE:-cuda}"
FORWARD_RUN_ROOT="${FORWARD_RUN_ROOT:-$PROJECT_ROOT/results/11-21-37}"
RUN_TAG="${RUN_TAG:-$(date +%d-%H-%M)-bidirectional}"
RUN_ROOT="${RUN_ROOT:-$PROJECT_ROOT/results/$RUN_TAG}"
MAX_SAMPLES="${MAX_SAMPLES:-0}"
SAMPLE_IDS="${SAMPLE_IDS:-}"
RESUME="${RESUME:-1}"
REVERSE_SKIP_REPLAY="${REVERSE_SKIP_REPLAY:-0}"
REVERSE_REPLAY_RANDOM="${REVERSE_REPLAY_RANDOM:-1}"
REVERSE_CT_HEAD_MODE="${REVERSE_CT_HEAD_MODE:-ap_proxy}"
REVERSE_SKIP_PLOTS="${REVERSE_SKIP_PLOTS:-1}"

if [[ -e "$RUN_ROOT" && "$RESUME" == "0" ]]; then
  echo "[error] run root already exists: $RUN_ROOT" >&2
  exit 1
fi

mkdir -p "$RUN_ROOT"

REVERSE_BATCH_ROOT="$RUN_ROOT/reverse_batch"
REVERSE_AGGREGATE_ROOT="$RUN_ROOT/reverse_aggregate"
BIDIRECTIONAL_ROOT="$RUN_ROOT/bidirectional"

batch_args=(
  --source dataset
  --dataset-root "$DATASET_ROOT"
  --model-path "$MODEL_PATH"
  --out-root "$REVERSE_BATCH_ROOT"
  --device "$DEVICE"
  --ct-head-mode "$REVERSE_CT_HEAD_MODE"
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

if [[ "$REVERSE_SKIP_PLOTS" != "0" ]]; then
  batch_args+=(--skip-plots)
fi

python scripts/mine_toolcall_reverse_batch.py "${batch_args[@]}"

aggregate_args=(
  --input-root "$REVERSE_BATCH_ROOT"
  --output-root "$REVERSE_AGGREGATE_ROOT"
  --model-path "$MODEL_PATH"
  --device "$DEVICE"
  --output-node-label "Residual Output: no_tool"
  --summary-label "reverse_no_tool"
  --replay-random "$REVERSE_REPLAY_RANDOM"
)

if [[ "$REVERSE_SKIP_REPLAY" != "0" ]]; then
  aggregate_args+=(--skip-replay)
fi

python scripts/aggregate_toolcall_behavior.py "${aggregate_args[@]}"

python scripts/analyze_toolcall_bidirectional.py \
  --forward-batch-root "$FORWARD_RUN_ROOT/batch" \
  --forward-aggregate-summary "$FORWARD_RUN_ROOT/aggregate/global_core_summary.json" \
  --reverse-batch-root "$REVERSE_BATCH_ROOT" \
  --reverse-aggregate-summary "$REVERSE_AGGREGATE_ROOT/global_core_summary.json" \
  --output-root "$BIDIRECTIONAL_ROOT"

python - <<'PY' "$RUN_ROOT" "$FORWARD_RUN_ROOT" "$REVERSE_BATCH_ROOT" "$REVERSE_AGGREGATE_ROOT" "$BIDIRECTIONAL_ROOT"
import json
import sys
from pathlib import Path

run_root = Path(sys.argv[1])
manifest = {
    "run_root": str(run_root),
    "forward_run_root": sys.argv[2],
    "reverse_batch_root": sys.argv[3],
    "reverse_aggregate_root": sys.argv[4],
    "bidirectional_root": sys.argv[5],
}
(run_root / "bidirectional_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False, indent=2))
PY

echo "[done] bidirectional outputs: $RUN_ROOT"
