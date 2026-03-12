#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/autodl-tmp/project/results/11-22-45-bidirectional_approxy"
REPORT_JSON="$ROOT/signed_validate_full/signed_group_report.json"
FAMILY_JSON="$ROOT/signed_family_mediation_200/signed_family_mediation_report.json"
COMPOSITION_JSON="$ROOT/signed_composition_full/signed_composition_report.json"
NODE_JSON="$ROOT/signed_node_importance_200/signed_node_importance_report.json"
TRAJECTORY_JSON="$ROOT/signed_layer_trajectory_200/signed_layer_trajectory_report.json"

cd /root/autodl-tmp/project

while [ ! -f "$REPORT_JSON" ]; do
  sleep 120
done

python scripts/build_toolcall_signed_story_report.py \
  --root "$ROOT" \
  --output "$ROOT/SIGNED_STORY_REPORT.md"

if [ ! -f "$FAMILY_JSON" ]; then
  python scripts/evaluate_toolcall_signed_family_mediation.py \
    --forward-batch-root results/11-21-37/batch \
    --bidirectional-summary results/11-22-45-bidirectional_approxy/bidirectional_full/bidirectional_summary.json \
    --signed-family-summary-csv results/11-22-45-bidirectional_approxy/final_signed_families/signed_family_summary.csv \
    --max-samples 200 \
    --output-root results/11-22-45-bidirectional_approxy/signed_family_mediation_200
fi

if [ ! -f "$COMPOSITION_JSON" ]; then
  python scripts/evaluate_toolcall_signed_composition.py \
    --forward-batch-root results/11-21-37/batch \
    --bidirectional-summary results/11-22-45-bidirectional_approxy/bidirectional_full/bidirectional_summary.json \
    --output-root results/11-22-45-bidirectional_approxy/signed_composition_full
fi

if [ ! -f "$NODE_JSON" ]; then
  python scripts/evaluate_toolcall_signed_node_importance.py \
    --forward-batch-root results/11-21-37/batch \
    --bidirectional-summary results/11-22-45-bidirectional_approxy/bidirectional_full/bidirectional_summary.json \
    --signed-nodes-csv results/11-22-45-bidirectional_approxy/final_signed_circuit/final_signed_nodes.csv \
    --max-samples 200 \
    --output-root results/11-22-45-bidirectional_approxy/signed_node_importance_200
fi

if [ ! -f "$TRAJECTORY_JSON" ]; then
  python scripts/analyze_toolcall_signed_layer_trajectory.py \
    --forward-batch-root results/11-21-37/batch \
    --bidirectional-summary results/11-22-45-bidirectional_approxy/bidirectional_full/bidirectional_summary.json \
    --max-samples 200 \
    --output-root results/11-22-45-bidirectional_approxy/signed_layer_trajectory_200
fi

python scripts/build_toolcall_signed_story_report.py \
  --root "$ROOT" \
  --output "$ROOT/SIGNED_STORY_REPORT.md"
