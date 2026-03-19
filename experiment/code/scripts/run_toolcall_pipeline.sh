#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

DATASET_ROOT="${DATASET_ROOT:-$PROJECT_ROOT/datasets}"
MODEL_PATH="${MODEL_PATH:-/root/autodl-tmp/Qwen/Qwen3-1.7B}"
DEVICE="${DEVICE:-cuda}"
RUN_TAG="${RUN_TAG:-$(date +%d-%H-%M)}"
RUN_ROOT="${RUN_ROOT:-$PROJECT_ROOT/results/$RUN_TAG}"
MAX_SAMPLES="${MAX_SAMPLES:-0}"
SAMPLE_IDS="${SAMPLE_IDS:-}"
BOOTSTRAP="${BOOTSTRAP:-1000}"
RESUME="${RESUME:-1}"
TOOLCALL_CT_AP_PER_LAYER="${TOOLCALL_CT_AP_PER_LAYER:-2}"
TOOLCALL_CT_AP_TOP_GLOBAL="${TOOLCALL_CT_AP_TOP_GLOBAL:-24}"

if [[ -e "$RUN_ROOT" ]]; then
  echo "[error] run root already exists: $RUN_ROOT" >&2
  echo "[error] set RUN_TAG or RUN_ROOT explicitly to avoid overwriting prior results" >&2
  exit 1
fi

export TOOLCALL_CT_AP_PER_LAYER
export TOOLCALL_CT_AP_TOP_GLOBAL

BATCH_ROOT="$RUN_ROOT/batch"
AGGREGATE_ROOT="$RUN_ROOT/aggregate"
SEMANTIC_ROOT="$RUN_ROOT/semantic_roles"
REFINED_ROOT="$RUN_ROOT/refined_consistent"
CONSISTENCY_JSON="$RUN_ROOT/consistency_eval.json"

mkdir -p "$RUN_ROOT"

batch_args=(
  --source dataset
  --dataset-root "$DATASET_ROOT"
  --model-path "$MODEL_PATH"
  --out-root "$BATCH_ROOT"
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

python scripts/mine_toolcall_batch.py "${batch_args[@]}"

python scripts/aggregate_toolcall_circuits.py \
  --input-root "$BATCH_ROOT" \
  --output-root "$AGGREGATE_ROOT" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE"

python scripts/analyze_toolcall_semantic_roles.py \
  --input-root "$BATCH_ROOT" \
  --aggregate-summary "$AGGREGATE_ROOT/global_core_summary.json" \
  --output-root "$SEMANTIC_ROOT" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$MAX_SAMPLES"

python scripts/evaluate_toolcall_role_groups.py \
  --input-root "$BATCH_ROOT" \
  --aggregate-summary "$AGGREGATE_ROOT/global_core_summary.json" \
  --semantic-report "$SEMANTIC_ROOT/semantic_roles_report.json" \
  --output-root "$SEMANTIC_ROOT" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$MAX_SAMPLES" \
  --bootstrap "$BOOTSTRAP"

python scripts/trace_toolcall_contrast_token.py \
  --input-root "$BATCH_ROOT" \
  --output-root "$SEMANTIC_ROOT" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$MAX_SAMPLES"

python scripts/path_patch_toolcall_edges.py \
  --input-root "$BATCH_ROOT" \
  --aggregate-summary "$AGGREGATE_ROOT/global_core_summary.json" \
  --output-root "$SEMANTIC_ROOT" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$MAX_SAMPLES" \
  --bootstrap "$BOOTSTRAP" \
  --trim-frac 0.10

python scripts/refine_consistent_toolcall_circuits.py \
  --input-root "$BATCH_ROOT" \
  --aggregate-summary "$AGGREGATE_ROOT/global_core_summary.json" \
  --output-root "$REFINED_ROOT" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE"

python scripts/evaluate_toolcall_consistency.py \
  --base-root "$BATCH_ROOT" \
  --variant "refined=$REFINED_ROOT" \
  --output "$CONSISTENCY_JSON"

python - <<'PY' "$RUN_ROOT" "$DATASET_ROOT" "$MODEL_PATH" "$DEVICE" "$RUN_TAG" "$MAX_SAMPLES" "$SAMPLE_IDS" "$BOOTSTRAP"
import json
import sys
from pathlib import Path

run_root = Path(sys.argv[1])
manifest = {
    "run_root": str(run_root),
    "dataset_root": sys.argv[2],
    "model_path": sys.argv[3],
    "device": sys.argv[4],
    "run_tag": sys.argv[5],
    "max_samples": int(sys.argv[6]),
    "sample_ids": sys.argv[7],
    "bootstrap": int(sys.argv[8]),
    "stages": {
        "batch": str(run_root / "batch"),
        "aggregate": str(run_root / "aggregate"),
        "semantic_roles": str(run_root / "semantic_roles"),
        "refined_consistent": str(run_root / "refined_consistent"),
        "consistency_eval": str(run_root / "consistency_eval.json"),
    },
}
(run_root / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False, indent=2))
PY

echo "[done] full pipeline outputs: $RUN_ROOT"
