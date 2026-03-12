#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/autodl-tmp/project/results/11-22-45-bidirectional_approxy"
TRAJECTORY_JSON="$ROOT/signed_layer_trajectory_200/signed_layer_trajectory_report.json"
LOG="$ROOT/trajectory_when_idle.log"

cd /root/autodl-tmp/project

if [ -f "$TRAJECTORY_JSON" ]; then
  python scripts/build_toolcall_signed_story_report.py \
    --root "$ROOT" \
    --output "$ROOT/SIGNED_STORY_REPORT.md"
  exit 0
fi

while true; do
  query="$(nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits 2>/dev/null | head -n 1 || true)"
  if [ -n "$query" ]; then
    read -r util mem < <(printf '%s\n' "$query" | awk -F', ' '{print $1, $2}')
    util="${util:-100}"
    mem="${mem:-99999}"
    if [[ "$util" =~ ^[0-9]+$ ]] && [[ "$mem" =~ ^[0-9]+$ ]]; then
      printf '[wait] gpu util=%s mem=%sMiB\n' "$util" "$mem" >> "$LOG"
      if [ "$util" -lt 20 ] && [ "$mem" -lt 1500 ]; then
        break
      fi
    else
      printf '[wait] invalid nvidia-smi query: %s\n' "$query" >> "$LOG"
      if pgrep -f '/root/autodl-tmp/qwen3_verb_probe/build_project_datasets_copy_extra600.py' >/dev/null; then
        printf '[wait] fallback process still running\n' >> "$LOG"
      else
        printf '[wait] fallback sees no conflicting process\n' >> "$LOG"
        break
      fi
    fi
  elif pgrep -f '/root/autodl-tmp/qwen3_verb_probe/build_project_datasets_copy_extra600.py' >/dev/null; then
    printf '[wait] fallback process still running\n' >> "$LOG"
  else
    printf '[wait] fallback sees no conflicting process\n' >> "$LOG"
    break
  fi
  sleep 120
done

python scripts/analyze_toolcall_signed_layer_trajectory.py \
  --forward-batch-root results/11-21-37/batch \
  --bidirectional-summary results/11-22-45-bidirectional_approxy/bidirectional_full/bidirectional_summary.json \
  --max-samples 200 \
  --output-root results/11-22-45-bidirectional_approxy/signed_layer_trajectory_200 >> "$LOG" 2>&1

python scripts/build_toolcall_signed_story_report.py \
  --root "$ROOT" \
  --output "$ROOT/SIGNED_STORY_REPORT.md" >> "$LOG" 2>&1
