#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

DATASET_ROOT="${DATASET_ROOT:-$PROJECT_ROOT/datasets}"
MODEL_PATH="${MODEL_PATH:-/root/autodl-tmp/Qwen/Qwen3-1.7B}"
DEVICE="${DEVICE:-cuda}"

# Default to continuing the existing partial run root.
RUN_ROOT="${RUN_ROOT:-$PROJECT_ROOT/results/11-22-45-bidirectional_approxy}"

REVERSE_BATCH_ROOT="$RUN_ROOT/reverse_batch"
REVERSE_AGGREGATE_FULL="$RUN_ROOT/reverse_aggregate_full"
BIDIRECTIONAL_FULL="$RUN_ROOT/bidirectional_full"
CAUSAL_ALIGNED="$RUN_ROOT/causal_eval_full_aligned"
CAUSAL_FULLMATRIX="$RUN_ROOT/causal_eval_full_matrix"
HEAD_READS_FULL="$RUN_ROOT/head_reads_full"
STRATIFIED_FULL="$RUN_ROOT/stratified_full"
STABILITY_FULL="$RUN_ROOT/reverse_stability_full.json"

mkdir -p "$RUN_ROOT"

echo "[info] project_root=$PROJECT_ROOT"
echo "[info] run_root=$RUN_ROOT"
echo "[info] dataset_root=$DATASET_ROOT"
echo "[info] model_path=$MODEL_PATH"
echo "[info] device=$DEVICE"

python - <<'PY' "$DATASET_ROOT"
from pathlib import Path
import sys
root=Path(sys.argv[1])
clean=set(p.name for p in (root/"clean").glob("*.txt"))
corrupt=set(p.name for p in (root/"corrupt").glob("*.txt"))
shared=clean & corrupt
print("[info] clean_txt", len(clean))
print("[info] corrupt_txt", len(corrupt))
print("[info] shared_pairs", len(shared))
if clean-corrupt:
    print("[warn] missing_corrupt", len(clean-corrupt))
if corrupt-clean:
    print("[warn] missing_clean", len(corrupt-clean))
PY

echo "[stage] reverse batch (resume)"
mkdir -p "$REVERSE_BATCH_ROOT"
python scripts/mine_toolcall_reverse_batch.py \
  --source dataset \
  --dataset-root "$DATASET_ROOT" \
  --model-path "$MODEL_PATH" \
  --out-root "$REVERSE_BATCH_ROOT" \
  --device "$DEVICE" \
  --ct-head-mode ap_proxy \
  --resume \
  --skip-plots

echo "[stage] reverse aggregate (full)"
python scripts/aggregate_toolcall_behavior.py \
  --input-root "$REVERSE_BATCH_ROOT" \
  --output-root "$REVERSE_AGGREGATE_FULL" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --output-node-label "Residual Output: no_tool" \
  --summary-label "reverse_no_tool_full" \
  --skip-replay

echo "[stage] bidirectional analysis (full)"
python scripts/analyze_toolcall_bidirectional.py \
  --forward-batch-root "$PROJECT_ROOT/results/11-21-37/batch" \
  --forward-aggregate-summary "$PROJECT_ROOT/results/11-21-37/aggregate/global_core_summary.json" \
  --reverse-batch-root "$REVERSE_BATCH_ROOT" \
  --reverse-aggregate-summary "$REVERSE_AGGREGATE_FULL/global_core_summary.json" \
  --output-root "$BIDIRECTIONAL_FULL"

echo "[stage] causal eval (aligned, full)"
python scripts/evaluate_toolcall_bidirectional_causal.py \
  --forward-batch-root "$PROJECT_ROOT/results/11-21-37/batch" \
  --forward-aggregate-summary "$PROJECT_ROOT/results/11-21-37/aggregate/global_core_summary.json" \
  --reverse-aggregate-summary "$REVERSE_AGGREGATE_FULL/global_core_summary.json" \
  --bidirectional-summary "$BIDIRECTIONAL_FULL/bidirectional_summary.json" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --bootstrap 400 \
  --matrix aligned \
  --output-root "$CAUSAL_ALIGNED"

echo "[stage] causal eval (full matrix, full)"
python scripts/evaluate_toolcall_bidirectional_causal.py \
  --forward-batch-root "$PROJECT_ROOT/results/11-21-37/batch" \
  --forward-aggregate-summary "$PROJECT_ROOT/results/11-21-37/aggregate/global_core_summary.json" \
  --reverse-aggregate-summary "$REVERSE_AGGREGATE_FULL/global_core_summary.json" \
  --bidirectional-summary "$BIDIRECTIONAL_FULL/bidirectional_summary.json" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --bootstrap 300 \
  --matrix full \
  --output-root "$CAUSAL_FULLMATRIX"

echo "[stage] head reads (full)"
python scripts/analyze_toolcall_bidirectional_head_reads.py \
  --dataset-root "$DATASET_ROOT" \
  --reverse-batch-root "$REVERSE_BATCH_ROOT" \
  --forward-aggregate-summary "$PROJECT_ROOT/results/11-21-37/aggregate/global_core_summary.json" \
  --reverse-aggregate-summary "$REVERSE_AGGREGATE_FULL/global_core_summary.json" \
  --bidirectional-summary "$BIDIRECTIONAL_FULL/bidirectional_summary.json" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --output-root "$HEAD_READS_FULL"

echo "[stage] stratified robustness (full)"
python scripts/analyze_toolcall_bidirectional_stratify.py \
  --per-sample-cross-eval "$CAUSAL_ALIGNED/per_sample_cross_eval.json" \
  --per-sample-overlap-csv "$BIDIRECTIONAL_FULL/per_sample_overlap.csv" \
  --output-root "$STRATIFIED_FULL"

echo "[stage] reverse-core stability (full)"
python scripts/analyze_toolcall_bidirectional_stability.py \
  --forward-aggregate-summary "$PROJECT_ROOT/results/11-21-37/aggregate/global_core_summary.json" \
  --reverse-batch-root "$REVERSE_BATCH_ROOT" \
  --output "$STABILITY_FULL" \
  --checkpoints 25,50,100,200,400,800,1189

echo "[done] full bidirectional outputs under: $RUN_ROOT"
