# Split Experiments README

## 目录结构

- `pipeline/`: train 集主流水线结果，包括双向电路发现、signed circuit、最终 mechanistic report。
- `attentionhead/`: train 集 448 个注意力头的全量实验、汇总数组、分析报告和图。
- `instruction_integration/`: 模块 1 结果。
- `output_route_decision/`: 模块 2 结果。
- `tool_call_construction/`: 模块 3 结果。
- `tool_call_suppression/`: 模块 4 结果。
- `test_validation/`: test 集上的 route score 与 stagewise 泛化验证。
- `split_comparison_summary.md`: full / train / test 对比总表。

## 数据切分

- 随机种子：`42`
- 划分比例：目标 `70/30`，在每个分层组内对 test 侧向下取整，因此最终为 `1223 / 499`。
- 分层维度：`lang × clean_candidate`。
- train/test 均保留 `clean/`、`corrupt/`、`merge_summary.json`，并在总目录生成 `split_summary.json`。

## 运行命令

```bash
cd /root/autodl-tmp/project/experiment/code
export PYTHONPATH="$(pwd)/src${PYTHONPATH:+:$PYTHONPATH}"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

# 1. 数据切分
python scripts/split_create_stratified_dataset.py

# 2. 主流水线
DATASET_ROOT=/root/autodl-tmp/project/experiment/datasets/train \
MODEL_PATH=/root/autodl-tmp/Qwen/Qwen3-1.7B \
DEVICE=cuda \
RUN_ROOT=/root/autodl-tmp/project/experiment/results/split/pipeline \
RUN_TAG=split-train \
SKIP_PLOTS=1 \
RESUME_DISCOVERY=1 \
bash scripts/run_toolcall_final_pipeline.sh

# 3. 注意力头
RUN_TAG=split-attention \
OUT_ROOT=/root/autodl-tmp/project/experiment/results/split/attentionhead \
DATASET_ROOT=/root/autodl-tmp/project/experiment/datasets/train \
MODEL_PATH=/root/autodl-tmp/Qwen/Qwen3-1.7B \
DEVICE=cuda \
DTYPE=bfloat16 \
MAX_SAMPLES=0 \
bash attentionhead/run_full_attention_head_experiment.sh
python attentionhead/analyze_attention_head_results.py \
  --result-root /root/autodl-tmp/project/experiment/results/split/attentionhead \
  --output-root /root/autodl-tmp/project/experiment/results/split/attentionhead/analysis

# 4. 四个模块
python scripts/split_run_instruction_integration.py \
  --run-root /root/autodl-tmp/project/experiment/results/split/pipeline \
  --output-root /root/autodl-tmp/project/experiment/results/split/instruction_integration \
  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B --device cuda --max-samples 0

python scripts/analyze_toolcall_output_route_decision_refine.py \
  --dataset-root /root/autodl-tmp/project/experiment/datasets/train \
  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B --device cuda --max-samples 0 \
  --output-root /root/autodl-tmp/project/experiment/results/split/output_route_decision

python scripts/split_prepare_construction_source.py \
  --run-root /root/autodl-tmp/project/experiment/results/split/pipeline \
  --legacy-data-root /root/autodl-tmp/project/experiment/results/legacy/final/data \
  --attention-root /root/autodl-tmp/project/experiment/results/split/attentionhead \
  --output-root /root/autodl-tmp/project/experiment/results/split/tool_call_construction/source_data \
  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B --device cuda --max-samples 0

python scripts/analyze_tool_call_construction_refine.py \
  --source-root /root/autodl-tmp/project/experiment/results/split/tool_call_construction/source_data \
  --run-root /root/autodl-tmp/project/experiment/results/split/pipeline \
  --attention-root /root/autodl-tmp/project/experiment/results/split/attentionhead \
  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B --device cuda --max-samples 0 \
  --output-root /root/autodl-tmp/project/experiment/results/split/tool_call_construction

python scripts/analyze_toolcall_minimal_cue_mechanism.py \
  --run-root /root/autodl-tmp/project/experiment/results/split/pipeline \
  --signed-nodes-csv /root/autodl-tmp/project/experiment/results/split/pipeline/final_signed_circuit/final_signed_nodes.csv \
  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B --device cuda --max-samples 0 \
  --output-root /root/autodl-tmp/project/experiment/results/split/pipeline/minimal_cue_mechanism

python scripts/analyze_toolcall_suppression_direction.py \
  --run-root /root/autodl-tmp/project/experiment/results/split/pipeline \
  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B --device cuda --max-samples 0 \
  --output-root /root/autodl-tmp/project/experiment/results/split/pipeline/suppression_direction

python scripts/split_prepare_suppression_legacy_root.py \
  --route-root /root/autodl-tmp/project/experiment/results/split/output_route_decision \
  --minimal-cue-root /root/autodl-tmp/project/experiment/results/split/pipeline/minimal_cue_mechanism \
  --suppression-root /root/autodl-tmp/project/experiment/results/split/pipeline/suppression_direction \
  --output-root /root/autodl-tmp/project/experiment/results/split/test_validation/suppression_legacy_root

python scripts/analyze_tool_call_suppression.py \
  --legacy-data-root /root/autodl-tmp/project/experiment/results/split/test_validation/suppression_legacy_root \
  --attention-root /root/autodl-tmp/project/experiment/results/split/attentionhead \
  --output-root /root/autodl-tmp/project/experiment/results/split/tool_call_suppression

# 5. test 泛化验证
python scripts/split_validate_route_score_on_test.py \
  --train-dataset-root /root/autodl-tmp/project/experiment/datasets/train \
  --test-dataset-root /root/autodl-tmp/project/experiment/datasets/test \
  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B --device cuda \
  --output-path /root/autodl-tmp/project/experiment/results/split/test_validation/route_score_test_validation.csv

python scripts/split_validate_stagewise_on_test.py \
  --train-dataset-root /root/autodl-tmp/project/experiment/datasets/train \
  --test-dataset-root /root/autodl-tmp/project/experiment/datasets/test \
  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B --device cuda \
  --construction-output /root/autodl-tmp/project/experiment/results/split/test_validation/construction_stagewise_test.csv \
  --suppression-output /root/autodl-tmp/project/experiment/results/split/test_validation/suppression_stagewise_test.csv

# 6. 汇总
python scripts/split_generate_comparison_docs.py
```

## 关键结论

- Route score 的 train/test 泛化稳定：`R_module` AUC 从 `0.9946` 到 `0.9943`。
- Construction 最终阶段 `+MLP27` 的 `<tool_call>` top1 从 train `0.9787` 到 test `0.9719`，变化很小。
- Suppression 最终阶段 `+L23H6` 的 no-tool top1 从 train `0.7899` 到 test `0.7816`，说明 suppressive chain 也能跨集保持。
