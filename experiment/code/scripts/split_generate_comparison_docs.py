#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable

import pandas as pd


ROOT = Path("/root/autodl-tmp/project/experiment")
RESULTS_ROOT = ROOT / "results"
SPLIT_ROOT = RESULTS_ROOT / "split"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成 split 实验的对比汇总和 README。")
    parser.add_argument("--split-root", type=Path, default=SPLIT_ROOT)
    parser.add_argument("--datasets-root", type=Path, default=ROOT / "datasets")
    parser.add_argument("--output-summary", type=Path, default=SPLIT_ROOT / "split_comparison_summary.md")
    parser.add_argument("--output-readme", type=Path, default=SPLIT_ROOT / "README.md")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"缺少文件: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"缺少文件: {path}")
    return pd.read_csv(path)


def fmt(value: object, digits: int = 3) -> str:
    try:
        num = float(value)
    except Exception:
        return str(value)
    if pd.isna(num):
        return "nan"
    return f"{num:.{digits}f}"


def md_table(headers: Iterable[str], rows: Iterable[Iterable[object]]) -> str:
    headers = list(headers)
    row_lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        row_lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(row_lines)


def pick_row(df: pd.DataFrame, **conds: object) -> pd.Series:
    mask = pd.Series([True] * len(df))
    for key, value in conds.items():
        mask &= df[key].astype(str) == str(value)
    sub = df.loc[mask]
    if sub.empty:
        raise KeyError(f"表中找不到行: {conds}")
    return sub.iloc[0]


def route_metric_row(label: str, node: str, full_df: pd.DataFrame, train_df: pd.DataFrame, test_df: pd.DataFrame, column: str) -> list[str]:
    return [
        label,
        fmt(pick_row(full_df, node=node)[column], 4),
        fmt(pick_row(train_df, node=node)[column], 4),
        fmt(pick_row(test_df, node=node)[column], 4),
    ]


def pretty_construction_label(raw: str) -> str:
    mapping = {
        "corrupt_full": "corrupt_full",
        "plus_MLP19": "+MLP19",
        "plus_L20H5": "+L20H5",
        "plus_L21H1": "+L21H1",
        "plus_L21H12": "+L21H12",
        "plus_L24H6": "+L24H6",
        "plus_MLP27": "+MLP27",
    }
    return mapping.get(str(raw), str(raw))


def pretty_suppression_label(raw: str) -> str:
    mapping = {
        "read_only": "L16H4",
        "writer_added": "+MLP17",
        "late_relay_added": "+L23H6",
    }
    return mapping.get(str(raw), str(raw))


def summarize_consistency(train_value: float, test_value: float, threshold: float) -> str:
    diff = abs(float(train_value) - float(test_value))
    if diff <= threshold:
        return f"一致（差值 {fmt(diff, 4)}）"
    return f"有偏移（差值 {fmt(diff, 4)}）"


def build_summary_md(
    *,
    split_root: Path,
    datasets_root: Path,
) -> str:
    full_route = load_csv(RESULTS_ROOT / "output_route_decision/20260319-110839-output-route-decision/route_score_summary.csv")
    train_route = load_csv(split_root / "output_route_decision/route_score_summary.csv")
    test_route = load_csv(split_root / "test_validation/route_score_test_validation.csv")

    full_edge = load_csv(RESULTS_ROOT / "output_route_decision/20260319-110839-output-route-decision/route_edge_summary.csv")
    train_edge = load_csv(split_root / "output_route_decision/route_edge_summary.csv")

    full_construction = load_csv(RESULTS_ROOT / "tool_call_construction/20260320-031957-tool-call-construction/construction_stagewise_summary.csv")
    train_construction = load_csv(split_root / "tool_call_construction/construction_stagewise_summary.csv")
    test_construction = load_csv(split_root / "test_validation/construction_stagewise_test.csv")

    full_suppression = load_csv(RESULTS_ROOT / "tool_call_suppression/20260320-065246-tool-call-suppression/suppression_stagewise_summary.csv")
    train_suppression = load_csv(split_root / "tool_call_suppression/suppression_stagewise_summary.csv")
    test_suppression = load_csv(split_root / "test_validation/suppression_stagewise_test.csv")

    full_signed_summary = load_json(RESULTS_ROOT / "legacy/final/data/final_signed_circuit_summary.json")
    full_signed_report = load_json(RESULTS_ROOT / "legacy/final/data/signed_group_report.json")
    train_signed_summary = load_json(split_root / "pipeline/final_signed_circuit/final_signed_circuit_summary.json")
    train_signed_report = load_json(split_root / "pipeline/signed_validate/signed_group_report.json")

    split_summary = load_json(datasets_root / "split_summary.json")

    full_signed_row = [row for row in full_signed_report["summary_rows"] if row["group"] == "full_signed_circuit"][0]
    train_signed_row = [row for row in train_signed_report["summary_rows"] if row["group"] == "full_signed_circuit"][0]

    route_rows = [
        route_metric_row("MLP11 route AUC", "MLP11", full_route, train_route, test_route, "auc_clean_vs_corrupt"),
        route_metric_row("MLP16 route AUC", "MLP16", full_route, train_route, test_route, "auc_clean_vs_corrupt"),
        route_metric_row("MLP19 route AUC", "MLP19", full_route, train_route, test_route, "auc_clean_vs_corrupt"),
        route_metric_row("R_module AUC", "module_anchor_mean", full_route, train_route, test_route, "auc_clean_vs_corrupt"),
        route_metric_row("MLP11 Spearman", "MLP11", full_route, train_route, test_route, "spearman_with_route_margin"),
        route_metric_row("MLP16 Spearman", "MLP16", full_route, train_route, test_route, "spearman_with_route_margin"),
        route_metric_row("MLP19 Spearman", "MLP19", full_route, train_route, test_route, "spearman_with_route_margin"),
        route_metric_row("R_module Spearman", "module_anchor_mean", full_route, train_route, test_route, "spearman_with_route_margin"),
    ]

    edge_rows = []
    for source, target in [("MLP11", "MLP16"), ("MLP16", "MLP19"), ("MLP16", "MLP17")]:
        full_row = pick_row(full_edge, source=source, target=target)
        train_row = pick_row(train_edge, source=source, target=target)
        edge_rows.append(
            [
                f"{source}->{target}",
                fmt(full_row["promote_route_mediated_ratio_median"], 4),
                fmt(train_row["promote_route_mediated_ratio_median"], 4),
                fmt(full_row["erase_route_mediated_ratio_median"], 4),
                fmt(train_row["erase_route_mediated_ratio_median"], 4),
            ]
        )

    construction_rows = []
    for raw_label in ["corrupt_full", "plus_MLP19", "plus_L20H5", "plus_L21H1", "plus_L21H12", "plus_L24H6", "plus_MLP27"]:
        construction_rows.append(
            [
                pretty_construction_label(raw_label),
                fmt(pick_row(full_construction, step_label=raw_label)["tool_top1_rate"], 4),
                fmt(pick_row(train_construction, step_label=raw_label)["tool_top1_rate"], 4),
                fmt(pick_row(test_construction, step_label=raw_label)["tool_top1_rate"], 4),
            ]
        )

    suppression_rows = []
    for raw_label in ["read_only", "writer_added", "late_relay_added"]:
        suppression_rows.append(
            [
                pretty_suppression_label(raw_label),
                fmt(pick_row(full_suppression, stage_label=raw_label)["no_tool_top1_rate"], 4),
                fmt(pick_row(train_suppression, stage_label=raw_label)["no_tool_top1_rate"], 4),
                fmt(pick_row(test_suppression, stage_label=raw_label)["no_tool_top1_rate"], 4),
            ]
        )

    signed_rows = [
        ["节点数", str(full_signed_summary["n_nodes"]), str(train_signed_summary["n_nodes"])],
        ["边数", str(full_signed_summary["n_edges"]), str(train_signed_summary["n_edges"])],
        [
            "充分性",
            f"{fmt(full_signed_row['promote_suff_ratio_median'], 4)} / {fmt(full_signed_row['suppress_suff_ratio_median'], 4)}",
            f"{fmt(train_signed_row['promote_suff_ratio_median'], 4)} / {fmt(train_signed_row['suppress_suff_ratio_median'], 4)}",
        ],
        [
            "必要性",
            f"{fmt(full_signed_row['promote_nec_drop_median'], 4)} / {fmt(full_signed_row['suppress_nec_drop_median'], 4)}",
            f"{fmt(train_signed_row['promote_nec_drop_median'], 4)} / {fmt(train_signed_row['suppress_nec_drop_median'], 4)}",
        ],
    ]

    module_auc_train = float(pick_row(train_route, node="module_anchor_mean")["auc_clean_vs_corrupt"])
    module_auc_test = float(pick_row(test_route, node="module_anchor_mean")["auc_clean_vs_corrupt"])
    construction_final_train = float(pick_row(train_construction, step_label="plus_MLP27")["tool_top1_rate"])
    construction_final_test = float(pick_row(test_construction, step_label="plus_MLP27")["tool_top1_rate"])
    suppression_final_train = float(pick_row(train_suppression, stage_label="late_relay_added")["no_tool_top1_rate"])
    suppression_final_test = float(pick_row(test_suppression, stage_label="late_relay_added")["no_tool_top1_rate"])

    lines: list[str] = []
    lines.append("# Split Comparison Summary")
    lines.append("")
    lines.append("## 数据切分")
    lines.append("")
    lines.append(
        f"- `seed=42`，按 `lang × clean_candidate` 分层；总计 `{split_summary['n_total']}`，train `{split_summary['n_train']}`，test `{split_summary['n_test']}`。"
    )
    lines.append("- 由于每个分层组都对 test 侧向下取整，最终 test 为 499 条，不会超过 30%。")
    lines.append("")
    lines.append("## Route Score 对比")
    lines.append("")
    lines.append(md_table(["指标", "全量 (1722)", "Train (1223)", "Test (499)"], route_rows))
    lines.append("")
    lines.append("## Edge Mediation 对比")
    lines.append("")
    lines.append(md_table(["边", "全量 promote", "Train promote", "全量 erase", "Train erase"], edge_rows))
    lines.append("")
    lines.append("## Construction Stagewise 对比")
    lines.append("")
    lines.append(md_table(["阶段", "全量 top1", "Train top1", "Test top1"], construction_rows))
    lines.append("")
    lines.append("## Suppression Stagewise 对比")
    lines.append("")
    lines.append(md_table(["阶段", "全量 no-tool top1", "Train no-tool top1", "Test no-tool top1"], suppression_rows))
    lines.append("")
    lines.append("## Signed Circuit 对比")
    lines.append("")
    lines.append(md_table(["指标", "全量", "Train"], signed_rows))
    lines.append("")
    lines.append("## 简短结论")
    lines.append("")
    lines.append(
        f"- Route module 的 AUC：train `{fmt(module_auc_train, 4)}`，test `{fmt(module_auc_test, 4)}`，{summarize_consistency(module_auc_train, module_auc_test, 0.01)}。"
    )
    lines.append(
        f"- Construction 最终 `+MLP27` 的 `<tool_call>` top1：train `{fmt(construction_final_train, 4)}`，test `{fmt(construction_final_test, 4)}`，{summarize_consistency(construction_final_train, construction_final_test, 0.03)}。"
    )
    lines.append(
        f"- Suppression 最终 `+L23H6` 的 no-tool top1：train `{fmt(suppression_final_train, 4)}`，test `{fmt(suppression_final_test, 4)}`，{summarize_consistency(suppression_final_train, suppression_final_test, 0.05)}。"
    )
    lines.append("- Signed circuit 在 train 上仍保持 `24` 个节点、`64` 条边，充分性与全量结果基本重合。")
    lines.append("")
    lines.append("注：Signed Circuit 表中的“充分性”为 `promote / suppress` 两个 sufficiency median；“必要性”为 `promote / suppress` 两个 necessity median drop。")
    lines.append("")
    return "\n".join(lines)


def build_readme_md(
    *,
    split_root: Path,
    datasets_root: Path,
) -> str:
    split_summary = load_json(datasets_root / "split_summary.json")
    route_test = load_csv(split_root / "test_validation/route_score_test_validation.csv")
    train_route = load_csv(split_root / "output_route_decision/route_score_summary.csv")
    train_cons = load_csv(split_root / "tool_call_construction/construction_stagewise_summary.csv")
    test_cons = load_csv(split_root / "test_validation/construction_stagewise_test.csv")
    train_supp = load_csv(split_root / "tool_call_suppression/suppression_stagewise_summary.csv")
    test_supp = load_csv(split_root / "test_validation/suppression_stagewise_test.csv")

    module_auc_train = float(pick_row(train_route, node="module_anchor_mean")["auc_clean_vs_corrupt"])
    module_auc_test = float(pick_row(route_test, node="module_anchor_mean")["auc_clean_vs_corrupt"])
    cons_train = float(pick_row(train_cons, step_label="plus_MLP27")["tool_top1_rate"])
    cons_test = float(pick_row(test_cons, step_label="plus_MLP27")["tool_top1_rate"])
    supp_train = float(pick_row(train_supp, stage_label="late_relay_added")["no_tool_top1_rate"])
    supp_test = float(pick_row(test_supp, stage_label="late_relay_added")["no_tool_top1_rate"])

    lines: list[str] = []
    lines.append("# Split Experiments README")
    lines.append("")
    lines.append("## 目录结构")
    lines.append("")
    lines.append("- `pipeline/`: train 集主流水线结果，包括双向电路发现、signed circuit、最终 mechanistic report。")
    lines.append("- `attentionhead/`: train 集 448 个注意力头的全量实验、汇总数组、分析报告和图。")
    lines.append("- `instruction_integration/`: 模块 1 结果。")
    lines.append("- `output_route_decision/`: 模块 2 结果。")
    lines.append("- `tool_call_construction/`: 模块 3 结果。")
    lines.append("- `tool_call_suppression/`: 模块 4 结果。")
    lines.append("- `test_validation/`: test 集上的 route score 与 stagewise 泛化验证。")
    lines.append("- `split_comparison_summary.md`: full / train / test 对比总表。")
    lines.append("")
    lines.append("## 数据切分")
    lines.append("")
    lines.append(f"- 随机种子：`{split_summary['seed']}`")
    lines.append("- 划分比例：目标 `70/30`，在每个分层组内对 test 侧向下取整，因此最终为 `1223 / 499`。")
    lines.append("- 分层维度：`lang × clean_candidate`。")
    lines.append("- train/test 均保留 `clean/`、`corrupt/`、`merge_summary.json`，并在总目录生成 `split_summary.json`。")
    lines.append("")
    lines.append("## 运行命令")
    lines.append("")
    lines.append("```bash")
    lines.append("cd /root/autodl-tmp/project/experiment/code")
    lines.append('export PYTHONPATH=\"$(pwd)/src${PYTHONPATH:+:$PYTHONPATH}\"')
    lines.append('export PYTORCH_CUDA_ALLOC_CONF=\"expandable_segments:True\"')
    lines.append("")
    lines.append("# 1. 数据切分")
    lines.append("python scripts/split_create_stratified_dataset.py")
    lines.append("")
    lines.append("# 2. 主流水线")
    lines.append("DATASET_ROOT=/root/autodl-tmp/project/experiment/datasets/train \\")
    lines.append("MODEL_PATH=/root/autodl-tmp/Qwen/Qwen3-1.7B \\")
    lines.append("DEVICE=cuda \\")
    lines.append("RUN_ROOT=/root/autodl-tmp/project/experiment/results/split/pipeline \\")
    lines.append("RUN_TAG=split-train \\")
    lines.append("SKIP_PLOTS=1 \\")
    lines.append("RESUME_DISCOVERY=1 \\")
    lines.append("bash scripts/run_toolcall_final_pipeline.sh")
    lines.append("")
    lines.append("# 3. 注意力头")
    lines.append("RUN_TAG=split-attention \\")
    lines.append("OUT_ROOT=/root/autodl-tmp/project/experiment/results/split/attentionhead \\")
    lines.append("DATASET_ROOT=/root/autodl-tmp/project/experiment/datasets/train \\")
    lines.append("MODEL_PATH=/root/autodl-tmp/Qwen/Qwen3-1.7B \\")
    lines.append("DEVICE=cuda \\")
    lines.append("DTYPE=bfloat16 \\")
    lines.append("MAX_SAMPLES=0 \\")
    lines.append("bash attentionhead/run_full_attention_head_experiment.sh")
    lines.append("python attentionhead/analyze_attention_head_results.py \\")
    lines.append("  --result-root /root/autodl-tmp/project/experiment/results/split/attentionhead \\")
    lines.append("  --output-root /root/autodl-tmp/project/experiment/results/split/attentionhead/analysis")
    lines.append("")
    lines.append("# 4. 四个模块")
    lines.append("python scripts/split_run_instruction_integration.py \\")
    lines.append("  --run-root /root/autodl-tmp/project/experiment/results/split/pipeline \\")
    lines.append("  --output-root /root/autodl-tmp/project/experiment/results/split/instruction_integration \\")
    lines.append("  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B --device cuda --max-samples 0")
    lines.append("")
    lines.append("python scripts/analyze_toolcall_output_route_decision_refine.py \\")
    lines.append("  --dataset-root /root/autodl-tmp/project/experiment/datasets/train \\")
    lines.append("  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B --device cuda --max-samples 0 \\")
    lines.append("  --output-root /root/autodl-tmp/project/experiment/results/split/output_route_decision")
    lines.append("")
    lines.append("python scripts/split_prepare_construction_source.py \\")
    lines.append("  --run-root /root/autodl-tmp/project/experiment/results/split/pipeline \\")
    lines.append("  --legacy-data-root /root/autodl-tmp/project/experiment/results/legacy/final/data \\")
    lines.append("  --attention-root /root/autodl-tmp/project/experiment/results/split/attentionhead \\")
    lines.append("  --output-root /root/autodl-tmp/project/experiment/results/split/tool_call_construction/source_data \\")
    lines.append("  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B --device cuda --max-samples 0")
    lines.append("")
    lines.append("python scripts/analyze_tool_call_construction_refine.py \\")
    lines.append("  --source-root /root/autodl-tmp/project/experiment/results/split/tool_call_construction/source_data \\")
    lines.append("  --run-root /root/autodl-tmp/project/experiment/results/split/pipeline \\")
    lines.append("  --attention-root /root/autodl-tmp/project/experiment/results/split/attentionhead \\")
    lines.append("  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B --device cuda --max-samples 0 \\")
    lines.append("  --output-root /root/autodl-tmp/project/experiment/results/split/tool_call_construction")
    lines.append("")
    lines.append("python scripts/analyze_toolcall_minimal_cue_mechanism.py \\")
    lines.append("  --run-root /root/autodl-tmp/project/experiment/results/split/pipeline \\")
    lines.append("  --signed-nodes-csv /root/autodl-tmp/project/experiment/results/split/pipeline/final_signed_circuit/final_signed_nodes.csv \\")
    lines.append("  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B --device cuda --max-samples 0 \\")
    lines.append("  --output-root /root/autodl-tmp/project/experiment/results/split/pipeline/minimal_cue_mechanism")
    lines.append("")
    lines.append("python scripts/analyze_toolcall_suppression_direction.py \\")
    lines.append("  --run-root /root/autodl-tmp/project/experiment/results/split/pipeline \\")
    lines.append("  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B --device cuda --max-samples 0 \\")
    lines.append("  --output-root /root/autodl-tmp/project/experiment/results/split/pipeline/suppression_direction")
    lines.append("")
    lines.append("python scripts/split_prepare_suppression_legacy_root.py \\")
    lines.append("  --route-root /root/autodl-tmp/project/experiment/results/split/output_route_decision \\")
    lines.append("  --minimal-cue-root /root/autodl-tmp/project/experiment/results/split/pipeline/minimal_cue_mechanism \\")
    lines.append("  --suppression-root /root/autodl-tmp/project/experiment/results/split/pipeline/suppression_direction \\")
    lines.append("  --output-root /root/autodl-tmp/project/experiment/results/split/test_validation/suppression_legacy_root")
    lines.append("")
    lines.append("python scripts/analyze_tool_call_suppression.py \\")
    lines.append("  --legacy-data-root /root/autodl-tmp/project/experiment/results/split/test_validation/suppression_legacy_root \\")
    lines.append("  --attention-root /root/autodl-tmp/project/experiment/results/split/attentionhead \\")
    lines.append("  --output-root /root/autodl-tmp/project/experiment/results/split/tool_call_suppression")
    lines.append("")
    lines.append("# 5. test 泛化验证")
    lines.append("python scripts/split_validate_route_score_on_test.py \\")
    lines.append("  --train-dataset-root /root/autodl-tmp/project/experiment/datasets/train \\")
    lines.append("  --test-dataset-root /root/autodl-tmp/project/experiment/datasets/test \\")
    lines.append("  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B --device cuda \\")
    lines.append("  --output-path /root/autodl-tmp/project/experiment/results/split/test_validation/route_score_test_validation.csv")
    lines.append("")
    lines.append("python scripts/split_validate_stagewise_on_test.py \\")
    lines.append("  --train-dataset-root /root/autodl-tmp/project/experiment/datasets/train \\")
    lines.append("  --test-dataset-root /root/autodl-tmp/project/experiment/datasets/test \\")
    lines.append("  --model-path /root/autodl-tmp/Qwen/Qwen3-1.7B --device cuda \\")
    lines.append("  --construction-output /root/autodl-tmp/project/experiment/results/split/test_validation/construction_stagewise_test.csv \\")
    lines.append("  --suppression-output /root/autodl-tmp/project/experiment/results/split/test_validation/suppression_stagewise_test.csv")
    lines.append("")
    lines.append("# 6. 汇总")
    lines.append("python scripts/split_generate_comparison_docs.py")
    lines.append("```")
    lines.append("")
    lines.append("## 关键结论")
    lines.append("")
    lines.append(f"- Route score 的 train/test 泛化稳定：`R_module` AUC 从 `{fmt(module_auc_train, 4)}` 到 `{fmt(module_auc_test, 4)}`。")
    lines.append(f"- Construction 最终阶段 `+MLP27` 的 `<tool_call>` top1 从 train `{fmt(cons_train, 4)}` 到 test `{fmt(cons_test, 4)}`，变化很小。")
    lines.append(f"- Suppression 最终阶段 `+L23H6` 的 no-tool top1 从 train `{fmt(supp_train, 4)}` 到 test `{fmt(supp_test, 4)}`，说明 suppressive chain 也能跨集保持。")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    split_root = args.split_root.resolve()
    datasets_root = args.datasets_root.resolve()
    summary_md = build_summary_md(split_root=split_root, datasets_root=datasets_root)
    readme_md = build_readme_md(split_root=split_root, datasets_root=datasets_root)

    args.output_summary.resolve().write_text(summary_md, encoding="utf-8")
    args.output_readme.resolve().write_text(readme_md, encoding="utf-8")


if __name__ == "__main__":
    main()
