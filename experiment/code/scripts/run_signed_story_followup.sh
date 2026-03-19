#!/usr/bin/env bash
set -euo pipefail

CODE_ROOT="/root/autodl-tmp/project/experiment/code"
RESULTS_ROOT="/root/autodl-tmp/project/experiment/results/legacy/final/archive/raw_runs"
ROOT="$RESULTS_ROOT/11-22-45-bidirectional_approxy"
REPORT_JSON="$ROOT/signed_validate_full/signed_group_report.json"
FAMILY_JSON="$ROOT/signed_family_mediation_200/signed_family_mediation_report.json"
COMPOSITION_JSON="$ROOT/signed_composition_full/signed_composition_report.json"
NODE_JSON="$ROOT/signed_node_importance_200/signed_node_importance_report.json"
TRAJECTORY_JSON="$ROOT/signed_layer_trajectory_200/signed_layer_trajectory_report.json"

cd "$CODE_ROOT"

while [ ! -f "$REPORT_JSON" ]; do
  sleep 120
done

python scripts/build_toolcall_signed_story_report.py \
  --root "$ROOT" \
  --output "$ROOT/SIGNED_STORY_REPORT.md"

if [ ! -f "$FAMILY_JSON" ]; then
  python scripts/evaluate_toolcall_signed_family_mediation.py \
    --forward-batch-root "$RESULTS_ROOT/11-21-37/batch" \
    --bidirectional-summary "$ROOT/bidirectional_full/bidirectional_summary.json" \
    --signed-family-summary-csv "$ROOT/final_signed_families/signed_family_summary.csv" \
    --max-samples 200 \
    --output-root "$ROOT/signed_family_mediation_200"
fi

if [ ! -f "$COMPOSITION_JSON" ]; then
  python scripts/evaluate_toolcall_signed_composition.py \
    --forward-batch-root "$RESULTS_ROOT/11-21-37/batch" \
    --bidirectional-summary "$ROOT/bidirectional_full/bidirectional_summary.json" \
    --output-root "$ROOT/signed_composition_full"
fi

if [ ! -f "$NODE_JSON" ]; then
  python scripts/evaluate_toolcall_signed_node_importance.py \
    --forward-batch-root "$RESULTS_ROOT/11-21-37/batch" \
    --bidirectional-summary "$ROOT/bidirectional_full/bidirectional_summary.json" \
    --signed-nodes-csv "$ROOT/final_signed_circuit/final_signed_nodes.csv" \
    --max-samples 200 \
    --output-root "$ROOT/signed_node_importance_200"
fi

if [ ! -f "$TRAJECTORY_JSON" ]; then
  python scripts/analyze_toolcall_signed_layer_trajectory.py \
    --forward-batch-root "$RESULTS_ROOT/11-21-37/batch" \
    --bidirectional-summary "$ROOT/bidirectional_full/bidirectional_summary.json" \
    --max-samples 200 \
    --output-root "$ROOT/signed_layer_trajectory_200"
fi

python scripts/build_toolcall_signed_story_report.py \
  --root "$ROOT" \
  --output "$ROOT/SIGNED_STORY_REPORT.md"
