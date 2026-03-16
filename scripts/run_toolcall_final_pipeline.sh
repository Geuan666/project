#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

if [[ -f /etc/network_turbo ]]; then
  # Optional proxy/bootstrap hook requested by the user for any later downloads.
  # This script does not require network by default, but sourcing is harmless.
  source /etc/network_turbo || true
fi

DATASET_ROOT="${DATASET_ROOT:-$PROJECT_ROOT/datasets}"
MODEL_PATH="${MODEL_PATH:-/root/autodl-tmp/Qwen/Qwen3-1.7B}"
DEVICE="${DEVICE:-cuda}"
RUN_TAG="${RUN_TAG:-$(date +%d-%H-%M)-final-kl}"
RUN_ROOT="${RUN_ROOT:-$PROJECT_ROOT/results/$RUN_TAG}"
SAMPLE_IDS="${SAMPLE_IDS:-}"
MAX_SAMPLES="${MAX_SAMPLES:-0}"
DISCOVERY_CT_HEAD_MODE="${DISCOVERY_CT_HEAD_MODE:-ap_proxy}"
SKIP_PLOTS="${SKIP_PLOTS:-1}"
RESUME_DISCOVERY="${RESUME_DISCOVERY:-1}"
FAMILY_MEDIATION_MAX_SAMPLES="${FAMILY_MEDIATION_MAX_SAMPLES:-0}"
NODE_IMPORTANCE_MAX_SAMPLES="${NODE_IMPORTANCE_MAX_SAMPLES:-0}"
EDGE_IMPORTANCE_MAX_SAMPLES="${EDGE_IMPORTANCE_MAX_SAMPLES:-0}"
EDGE_IMPORTANCE_MAX_EDGES="${EDGE_IMPORTANCE_MAX_EDGES:-0}"
TRAJECTORY_MAX_SAMPLES="${TRAJECTORY_MAX_SAMPLES:-0}"
CAUSAL_EVAL_MAX_SAMPLES="${CAUSAL_EVAL_MAX_SAMPLES:-0}"
FUNCTIONAL_VALIDATE_MAX_SAMPLES="${FUNCTIONAL_VALIDATE_MAX_SAMPLES:-0}"
SEMANTIC_CHAIN_MAX_SAMPLES="${SEMANTIC_CHAIN_MAX_SAMPLES:-0}"
SEMANTIC_FACTORIZED_MAX_SAMPLES="${SEMANTIC_FACTORIZED_MAX_SAMPLES:-0}"
SCHEMA_STAGEWISE_MAX_SAMPLES="${SCHEMA_STAGEWISE_MAX_SAMPLES:-0}"
MECHANISM_AUDIT_MAX_SAMPLES="${MECHANISM_AUDIT_MAX_SAMPLES:-0}"
MLP27_STEERING_MAX_SAMPLES="${MLP27_STEERING_MAX_SAMPLES:-0}"
LATE_WRITER_BACKUP_MAX_SAMPLES="${LATE_WRITER_BACKUP_MAX_SAMPLES:-0}"
QUERY_DECISION_MAX_SAMPLES="${QUERY_DECISION_MAX_SAMPLES:-0}"
INSTRUCTION_COMMITMENT_MAX_SAMPLES="${INSTRUCTION_COMMITMENT_MAX_SAMPLES:-0}"
INSTRUCTION_LEAD_MAX_SAMPLES="${INSTRUCTION_LEAD_MAX_SAMPLES:-0}"

mkdir -p "$RUN_ROOT"

FORWARD_BATCH="$RUN_ROOT/forward_batch"
FORWARD_AGG="$RUN_ROOT/forward_aggregate"
REVERSE_BATCH="$RUN_ROOT/reverse_batch"
REVERSE_AGG="$RUN_ROOT/reverse_aggregate"
BIDIRECTIONAL="$RUN_ROOT/bidirectional"
CAUSAL_ALIGNED="$RUN_ROOT/causal_aligned"
CAUSAL_FULL="$RUN_ROOT/causal_full"
HEAD_READS="$RUN_ROOT/head_reads"
SIGNED_CIRCUIT="$RUN_ROOT/final_signed_circuit"
SIGNED_VALIDATE="$RUN_ROOT/signed_validate"
TOKEN_FLIP="$RUN_ROOT/token_flip"
SIGNED_FAMILIES="$RUN_ROOT/final_signed_families"
SIGNED_FAMILY_MEDIATION="$RUN_ROOT/signed_family_mediation"
SIGNED_COMPOSITION="$RUN_ROOT/signed_composition"
NODE_IMPORTANCE="$RUN_ROOT/node_importance"
EDGE_IMPORTANCE="$RUN_ROOT/edge_importance"
SIGNED_TRAJECTORY="$RUN_ROOT/signed_layer_trajectory"
FUNCTIONAL_GROUPS="$RUN_ROOT/functional_groups"
FUNCTIONAL_VALIDATE="$RUN_ROOT/functional_validate"
SEMANTIC_CHAIN="$RUN_ROOT/semantic_chain"
SEMANTIC_FACTORIZED="$RUN_ROOT/semantic_factorized"
SCHEMA_STAGEWISE="$RUN_ROOT/schema_stagewise"
MECHANISM_AUDIT="$RUN_ROOT/mechanism_audit"
MLP27_STEERING="$RUN_ROOT/mlp27_steering"
LATE_WRITER_BACKUP="$RUN_ROOT/late_writer_backup"
QUERY_DECISION="$RUN_ROOT/query_decision_chain"
INSTRUCTION_COMMITMENT="$RUN_ROOT/instruction_commitment"
INSTRUCTION_LEAD="$RUN_ROOT/instruction_lead"
FINAL_HEAD_AUDIT="$RUN_ROOT/final_head_attention_audit"
METHOD_BENCHMARK="$RUN_ROOT/method_benchmark"
FINAL_MECHANISTIC="$RUN_ROOT/FINAL_MECHANISTIC_RESULT.md"
FINAL_REPORT="$RUN_ROOT/FINAL_REPORT.md"

RELP_ROOT="${RELP_ROOT:-}"
EAP_ROOT="${EAP_ROOT:-}"
FEATURE_ROOT="${FEATURE_ROOT:-}"

common_batch_args=(
  --source dataset
  --dataset-root "$DATASET_ROOT"
  --model-path "$MODEL_PATH"
  --device "$DEVICE"
)

if [[ "$MAX_SAMPLES" != "0" ]]; then
  common_batch_args+=(--max-samples "$MAX_SAMPLES")
fi

if [[ -n "$SAMPLE_IDS" ]]; then
  common_batch_args+=(--sample-ids "$SAMPLE_IDS")
fi

if [[ "$SKIP_PLOTS" != "0" ]]; then
  common_batch_args+=(--skip-plots)
fi

if [[ "$RESUME_DISCOVERY" != "0" ]]; then
  common_batch_args+=(--resume)
fi

python scripts/mine_toolcall_batch.py \
  "${common_batch_args[@]}" \
  --out-root "$FORWARD_BATCH" \
  --ct-head-mode "$DISCOVERY_CT_HEAD_MODE"

python scripts/aggregate_toolcall_behavior.py \
  --input-root "$FORWARD_BATCH" \
  --output-root "$FORWARD_AGG" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --summary-label "forward_kl" \
  --skip-replay

python scripts/mine_toolcall_reverse_batch.py \
  "${common_batch_args[@]}" \
  --out-root "$REVERSE_BATCH" \
  --ct-head-mode "$DISCOVERY_CT_HEAD_MODE"

python scripts/aggregate_toolcall_behavior.py \
  --input-root "$REVERSE_BATCH" \
  --output-root "$REVERSE_AGG" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --output-node-label "Residual Output: no_tool" \
  --summary-label "reverse_kl" \
  --skip-replay

python scripts/analyze_toolcall_bidirectional.py \
  --forward-batch-root "$FORWARD_BATCH" \
  --forward-aggregate-summary "$FORWARD_AGG/global_core_summary.json" \
  --reverse-batch-root "$REVERSE_BATCH" \
  --reverse-aggregate-summary "$REVERSE_AGG/global_core_summary.json" \
  --output-root "$BIDIRECTIONAL"

python scripts/evaluate_toolcall_bidirectional_causal.py \
  --forward-batch-root "$FORWARD_BATCH" \
  --forward-aggregate-summary "$FORWARD_AGG/global_core_summary.json" \
  --reverse-aggregate-summary "$REVERSE_AGG/global_core_summary.json" \
  --bidirectional-summary "$BIDIRECTIONAL/bidirectional_summary.json" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$CAUSAL_EVAL_MAX_SAMPLES" \
  --matrix aligned \
  --output-root "$CAUSAL_ALIGNED"

python scripts/evaluate_toolcall_bidirectional_causal.py \
  --forward-batch-root "$FORWARD_BATCH" \
  --forward-aggregate-summary "$FORWARD_AGG/global_core_summary.json" \
  --reverse-aggregate-summary "$REVERSE_AGG/global_core_summary.json" \
  --bidirectional-summary "$BIDIRECTIONAL/bidirectional_summary.json" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$CAUSAL_EVAL_MAX_SAMPLES" \
  --matrix full \
  --output-root "$CAUSAL_FULL"

python scripts/analyze_toolcall_bidirectional_head_reads.py \
  --dataset-root "$DATASET_ROOT" \
  --reverse-batch-root "$REVERSE_BATCH" \
  --forward-aggregate-summary "$FORWARD_AGG/global_core_summary.json" \
  --reverse-aggregate-summary "$REVERSE_AGG/global_core_summary.json" \
  --bidirectional-summary "$BIDIRECTIONAL/bidirectional_summary.json" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --output-root "$HEAD_READS"

python scripts/build_toolcall_signed_circuit.py \
  --bidirectional-summary "$BIDIRECTIONAL/bidirectional_summary.json" \
  --node-support-csv "$BIDIRECTIONAL/node_bidirectional_support.csv" \
  --edge-support-csv "$BIDIRECTIONAL/edge_bidirectional_support.csv" \
  --head-read-csv "$HEAD_READS/per_head_read_mass.csv" \
  --output-root "$SIGNED_CIRCUIT"

python scripts/validate_toolcall_signed_circuit.py \
  --forward-batch-root "$FORWARD_BATCH" \
  --forward-aggregate-summary "$FORWARD_AGG/global_core_summary.json" \
  --reverse-aggregate-summary "$REVERSE_AGG/global_core_summary.json" \
  --bidirectional-summary "$BIDIRECTIONAL/bidirectional_summary.json" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "${MAX_SAMPLES:-0}" \
  --output-root "$SIGNED_VALIDATE"

python scripts/evaluate_toolcall_bidirectional_token_flip.py \
  --forward-batch-root "$FORWARD_BATCH" \
  --forward-aggregate-summary "$FORWARD_AGG/global_core_summary.json" \
  --reverse-aggregate-summary "$REVERSE_AGG/global_core_summary.json" \
  --bidirectional-summary "$BIDIRECTIONAL/bidirectional_summary.json" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "${MAX_SAMPLES:-0}" \
  --output-root "$TOKEN_FLIP"

python scripts/analyze_toolcall_signed_families.py \
  --signed-edges-csv "$SIGNED_CIRCUIT/final_signed_edges.csv" \
  --output-root "$SIGNED_FAMILIES"

python scripts/evaluate_toolcall_signed_family_mediation.py \
  --forward-batch-root "$FORWARD_BATCH" \
  --bidirectional-summary "$BIDIRECTIONAL/bidirectional_summary.json" \
  --signed-family-summary-csv "$SIGNED_FAMILIES/signed_family_summary.csv" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$FAMILY_MEDIATION_MAX_SAMPLES" \
  --output-root "$SIGNED_FAMILY_MEDIATION"

python scripts/evaluate_toolcall_signed_composition.py \
  --forward-batch-root "$FORWARD_BATCH" \
  --bidirectional-summary "$BIDIRECTIONAL/bidirectional_summary.json" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "${MAX_SAMPLES:-0}" \
  --output-root "$SIGNED_COMPOSITION"

python scripts/evaluate_toolcall_signed_node_importance.py \
  --forward-batch-root "$FORWARD_BATCH" \
  --bidirectional-summary "$BIDIRECTIONAL/bidirectional_summary.json" \
  --signed-nodes-csv "$SIGNED_CIRCUIT/final_signed_nodes.csv" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$NODE_IMPORTANCE_MAX_SAMPLES" \
  --output-root "$NODE_IMPORTANCE"

python scripts/evaluate_toolcall_signed_edge_importance.py \
  --forward-batch-root "$FORWARD_BATCH" \
  --signed-edges-csv "$SIGNED_CIRCUIT/final_signed_edges.csv" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$EDGE_IMPORTANCE_MAX_SAMPLES" \
  --max-edges "$EDGE_IMPORTANCE_MAX_EDGES" \
  --output-root "$EDGE_IMPORTANCE"

python scripts/analyze_toolcall_signed_layer_trajectory.py \
  --forward-batch-root "$FORWARD_BATCH" \
  --bidirectional-summary "$BIDIRECTIONAL/bidirectional_summary.json" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$TRAJECTORY_MAX_SAMPLES" \
  --output-root "$SIGNED_TRAJECTORY"

python scripts/analyze_toolcall_functional_groups.py \
  --signed-nodes-csv "$SIGNED_CIRCUIT/final_signed_nodes.csv" \
  --signed-edges-csv "$SIGNED_CIRCUIT/final_signed_edges.csv" \
  --head-read-csv "$HEAD_READS/per_head_read_mass.csv" \
  --node-importance-csv "$NODE_IMPORTANCE/signed_node_importance_summary.csv" \
  --output-root "$FUNCTIONAL_GROUPS"

python scripts/evaluate_toolcall_functional_groups.py \
  --forward-batch-root "$FORWARD_BATCH" \
  --functional-group-json "$FUNCTIONAL_GROUPS/functional_group_summary.json" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$FUNCTIONAL_VALIDATE_MAX_SAMPLES" \
  --output-root "$FUNCTIONAL_VALIDATE"

python scripts/analyze_toolcall_semantic_causal_chain.py \
  --run-root "$RUN_ROOT" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$SEMANTIC_CHAIN_MAX_SAMPLES" \
  --output-root "$SEMANTIC_CHAIN"

python scripts/analyze_toolcall_semantic_factorized_counterfactual.py \
  --run-root "$RUN_ROOT" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$SEMANTIC_FACTORIZED_MAX_SAMPLES" \
  --output-root "$SEMANTIC_FACTORIZED"

python scripts/analyze_toolcall_semantic_schema_stagewise.py \
  --run-root "$RUN_ROOT" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$SCHEMA_STAGEWISE_MAX_SAMPLES" \
  --output-root "$SCHEMA_STAGEWISE"

python scripts/build_toolcall_mechanism_component_audit.py \
  --run-root "$RUN_ROOT" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$MECHANISM_AUDIT_MAX_SAMPLES" \
  --output-root "$MECHANISM_AUDIT"

python scripts/analyze_toolcall_mlp27_steering.py \
  --run-root "$RUN_ROOT" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$MLP27_STEERING_MAX_SAMPLES" \
  --output-root "$MLP27_STEERING"

python scripts/analyze_toolcall_late_writer_backup_search.py \
  --run-root "$RUN_ROOT" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$LATE_WRITER_BACKUP_MAX_SAMPLES" \
  --output-root "$LATE_WRITER_BACKUP"

python scripts/analyze_toolcall_query_decision_chain.py \
  --run-root "$RUN_ROOT" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$QUERY_DECISION_MAX_SAMPLES" \
  --output-root "$QUERY_DECISION"

python scripts/analyze_toolcall_query_instruction_commitment.py \
  --run-root "$RUN_ROOT" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$INSTRUCTION_COMMITMENT_MAX_SAMPLES" \
  --output-root "$INSTRUCTION_COMMITMENT"

python scripts/analyze_toolcall_instruction_verb_phrase_audit.py \
  --run-root "$RUN_ROOT" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples "$INSTRUCTION_LEAD_MAX_SAMPLES" \
  --output-root "$INSTRUCTION_LEAD"

python scripts/analyze_toolcall_final_head_attention_audit.py \
  --run-root "$RUN_ROOT" \
  --model-path "$MODEL_PATH" \
  --device "$DEVICE" \
  --max-samples 0 \
  --output-root "$FINAL_HEAD_AUDIT"

python scripts/build_toolcall_final_mechanistic_result.py \
  --run-root "$RUN_ROOT" \
  --output "$FINAL_MECHANISTIC"

if [[ -n "$RELP_ROOT" || -n "$EAP_ROOT" || -n "$FEATURE_ROOT" ]]; then
  benchmark_args=(
    --baseline-root "$RUN_ROOT"
    --output-root "$METHOD_BENCHMARK"
  )
  if [[ -n "$RELP_ROOT" ]]; then
    benchmark_args+=(--relp-root "$RELP_ROOT")
  fi
  if [[ -n "$EAP_ROOT" ]]; then
    benchmark_args+=(--eap-root "$EAP_ROOT")
  fi
  if [[ -n "$FEATURE_ROOT" ]]; then
    benchmark_args+=(--feature-root "$FEATURE_ROOT")
  fi
  python scripts/collect_toolcall_method_benchmark.py "${benchmark_args[@]}"
fi

python scripts/build_toolcall_final_report.py \
  --run-root "$RUN_ROOT" \
  --output "$FINAL_REPORT"

echo "[done] final pipeline outputs: $RUN_ROOT"
echo "[done] final report: $FINAL_REPORT"
