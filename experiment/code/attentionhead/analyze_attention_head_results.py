#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(rows: Sequence[Dict[str, object]], out_path: Path) -> None:
    if not rows:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def head_sort_key(head: str) -> Tuple[int, int]:
    layer_s, head_s = head[1:].split("H")
    return int(layer_s), int(head_s)


def format_top_pairs(items: Iterable[Tuple[str, float]], n: int = 5) -> str:
    top = sorted(items, key=lambda x: x[1], reverse=True)[:n]
    return ", ".join(f"{name}={value:.4f}" for name, value in top)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze aggregate attention-head span results.")
    parser.add_argument("--result-root", type=str, required=True)
    parser.add_argument("--output-root", type=str, default="")
    args = parser.parse_args()

    result_root = Path(args.result_root).resolve()
    summary_root = result_root / "summary"
    output_root = Path(args.output_root).resolve() if args.output_root else result_root / "analysis"
    output_root.mkdir(parents=True, exist_ok=True)

    run_summary = json.loads((summary_root / "run_summary.json").read_text(encoding="utf-8"))
    span_token_rows = read_csv(summary_root / "span_token_count_summary.csv")
    decision_rows = read_csv(summary_root / "head_decision_row_summary.csv")
    heatmap_rows = read_csv(summary_root / "head_heatmap_summary.csv")

    span_order = [row["span"] for row in span_token_rows if row["condition"] == "clean"]
    heads = sorted({row["head"] for row in decision_rows}, key=head_sort_key)
    layers = sorted({int(row["layer"]) for row in decision_rows})

    for row in decision_rows:
        row["layer"] = int(row["layer"])
        row["decision_mass_mean"] = float(row["decision_mass_mean"])
        row["decision_density_mean"] = float(row["decision_density_mean"])
    for row in heatmap_rows:
        row["mass_mean"] = float(row["mass_mean"])
        row["density_mean"] = float(row["density_mean"])

    decision_by = {(row["condition"], row["head"], row["key_span"]): row for row in decision_rows}
    heatmap_by = {(row["condition"], row["head"], row["query_span"], row["key_span"]): row for row in heatmap_rows}

    head_overview_rows: List[Dict[str, object]] = []
    for head in heads:
        layer = head_sort_key(head)[0]
        clean_mass = {span: decision_by[("clean", head, span)]["decision_mass_mean"] for span in span_order}
        corrupt_mass = {span: decision_by[("corrupt", head, span)]["decision_mass_mean"] for span in span_order}
        clean_density = {span: decision_by[("clean", head, span)]["decision_density_mean"] for span in span_order}
        corrupt_density = {span: decision_by[("corrupt", head, span)]["decision_density_mean"] for span in span_order}
        delta_mass = {span: corrupt_mass[span] - clean_mass[span] for span in span_order}
        delta_density = {span: corrupt_density[span] - clean_density[span] for span in span_order}

        clean_mass_top = max(clean_mass.items(), key=lambda x: x[1])
        corrupt_mass_top = max(corrupt_mass.items(), key=lambda x: x[1])
        clean_density_top = max(clean_density.items(), key=lambda x: x[1])
        corrupt_density_top = max(corrupt_density.items(), key=lambda x: x[1])
        delta_mass_pos = max(delta_mass.items(), key=lambda x: x[1])
        delta_mass_neg = min(delta_mass.items(), key=lambda x: x[1])
        delta_density_pos = max(delta_density.items(), key=lambda x: x[1])
        delta_density_neg = min(delta_density.items(), key=lambda x: x[1])

        head_overview_rows.append(
            {
                "head": head,
                "layer": layer,
                "clean_mass_top_span": clean_mass_top[0],
                "clean_mass_top_value": clean_mass_top[1],
                "corrupt_mass_top_span": corrupt_mass_top[0],
                "corrupt_mass_top_value": corrupt_mass_top[1],
                "clean_density_top_span": clean_density_top[0],
                "clean_density_top_value": clean_density_top[1],
                "corrupt_density_top_span": corrupt_density_top[0],
                "corrupt_density_top_value": corrupt_density_top[1],
                "decision_mass_l1_shift": sum(abs(v) for v in delta_mass.values()),
                "decision_density_l1_shift": sum(abs(v) for v in delta_density.values()),
                "decision_mass_delta_pos_span": delta_mass_pos[0],
                "decision_mass_delta_pos_value": delta_mass_pos[1],
                "decision_mass_delta_neg_span": delta_mass_neg[0],
                "decision_mass_delta_neg_value": delta_mass_neg[1],
                "decision_density_delta_pos_span": delta_density_pos[0],
                "decision_density_delta_pos_value": delta_density_pos[1],
                "decision_density_delta_neg_span": delta_density_neg[0],
                "decision_density_delta_neg_value": delta_density_neg[1],
                "clean_density_user_lead_phrase": clean_density["user_lead_phrase"],
                "corrupt_density_user_lead_phrase": corrupt_density["user_lead_phrase"],
                "clean_density_function_body_anchor": clean_density["function_body_anchor"],
                "corrupt_density_function_body_anchor": corrupt_density["function_body_anchor"],
                "clean_density_file_target": clean_density["file_target"],
                "corrupt_density_file_target": corrupt_density["file_target"],
                "clean_density_instruction_suffix": clean_density["instruction_suffix"],
                "corrupt_density_instruction_suffix": corrupt_density["instruction_suffix"],
                "clean_density_task_body": clean_density["task_body"],
                "corrupt_density_task_body": corrupt_density["task_body"],
                "clean_density_assistant_prefix": clean_density["assistant_prefix"],
                "corrupt_density_assistant_prefix": corrupt_density["assistant_prefix"],
            }
        )
    write_csv(head_overview_rows, output_root / "head_overview.csv")

    top_heads_rows: List[Dict[str, object]] = []
    for metric in ["decision_mass_mean", "decision_density_mean"]:
        for span in span_order:
            clean_rank = sorted(
                ((decision_by[("clean", head, span)][metric], head) for head in heads),
                reverse=True,
            )
            delta_rank = sorted(
                (
                    (
                        decision_by[("corrupt", head, span)][metric]
                        - decision_by[("clean", head, span)][metric],
                        head,
                    )
                    for head in heads
                ),
                reverse=True,
            )
            for rank, (value, head) in enumerate(clean_rank[:15], start=1):
                top_heads_rows.append(
                    {
                        "metric": metric,
                        "span": span,
                        "ranking_type": "clean_top",
                        "rank": rank,
                        "head": head,
                        "value": value,
                    }
                )
            for rank, (value, head) in enumerate(delta_rank[:15], start=1):
                top_heads_rows.append(
                    {
                        "metric": metric,
                        "span": span,
                        "ranking_type": "delta_positive_top",
                        "rank": rank,
                        "head": head,
                        "value": value,
                    }
                )
            for rank, (value, head) in enumerate(sorted(delta_rank)[:15], start=1):
                top_heads_rows.append(
                    {
                        "metric": metric,
                        "span": span,
                        "ranking_type": "delta_negative_top",
                        "rank": rank,
                        "head": head,
                        "value": value,
                    }
                )
    write_csv(top_heads_rows, output_root / "top_heads_by_span.csv")

    layer_profile_rows: List[Dict[str, object]] = []
    for metric in ["decision_mass_mean", "decision_density_mean"]:
        for condition in ["clean", "corrupt"]:
            for layer in layers:
                layer_heads = [head for head in heads if head_sort_key(head)[0] == layer]
                span_means = {
                    span: sum(decision_by[(condition, head, span)][metric] for head in layer_heads) / len(layer_heads)
                    for span in span_order
                }
                top1 = max(span_means.items(), key=lambda x: x[1])
                top2 = sorted(span_means.items(), key=lambda x: x[1], reverse=True)[1]
                row = {
                    "metric": metric,
                    "condition": condition,
                    "layer": layer,
                    "top1_span": top1[0],
                    "top1_value": top1[1],
                    "top2_span": top2[0],
                    "top2_value": top2[1],
                }
                for span, value in span_means.items():
                    row[span] = value
                layer_profile_rows.append(row)
    write_csv(layer_profile_rows, output_root / "layer_span_profiles.csv")

    offdiag_rows: List[Dict[str, object]] = []
    for head in heads:
        for query_span in span_order:
            for key_span in span_order:
                if query_span == key_span:
                    continue
                clean_density = heatmap_by[("clean", head, query_span, key_span)]["density_mean"]
                corrupt_density = heatmap_by[("corrupt", head, query_span, key_span)]["density_mean"]
                offdiag_rows.append(
                    {
                        "head": head,
                        "layer": head_sort_key(head)[0],
                        "query_span": query_span,
                        "key_span": key_span,
                        "clean_density": clean_density,
                        "corrupt_density": corrupt_density,
                        "delta_density": corrupt_density - clean_density,
                    }
                )
    write_csv(sorted(offdiag_rows, key=lambda r: r["clean_density"], reverse=True), output_root / "offdiag_density_ranked.csv")
    write_csv(sorted(offdiag_rows, key=lambda r: r["delta_density"], reverse=True), output_root / "offdiag_delta_density_ranked.csv")

    clean_mass_dom = Counter(row["clean_mass_top_span"] for row in head_overview_rows)
    corrupt_mass_dom = Counter(row["corrupt_mass_top_span"] for row in head_overview_rows)
    clean_density_dom = Counter(row["clean_density_top_span"] for row in head_overview_rows)
    corrupt_density_dom = Counter(row["corrupt_density_top_span"] for row in head_overview_rows)
    largest_mass_shift = sorted(head_overview_rows, key=lambda r: r["decision_mass_l1_shift"], reverse=True)[:20]
    largest_density_shift = sorted(head_overview_rows, key=lambda r: r["decision_density_l1_shift"], reverse=True)[:20]
    key_heads = ["L2H14", "L16H4", "L20H5", "L21H1", "L21H12", "L23H6", "L24H6", "L27H7"]
    key_head_rows = {row["head"]: row for row in head_overview_rows if row["head"] in key_heads}

    lines: List[str] = []
    lines.append("# Attention Head Aggregate Analysis")
    lines.append("")
    lines.append("## Run")
    lines.append("")
    lines.append(f"- Samples: `{run_summary['n_valid_samples']}` / `{run_summary['n_requested_samples']}`")
    lines.append(f"- Heads: `{run_summary['n_layers']} x {run_summary['n_heads']} = {run_summary['n_layers'] * run_summary['n_heads']}`")
    lines.append(f"- Spans: `{', '.join(span_order)}`")
    lines.append("")
    lines.append("## Dominant Decision-Row Spans")
    lines.append("")
    lines.append(f"- Clean mass dominant spans: `{clean_mass_dom}`")
    lines.append(f"- Corrupt mass dominant spans: `{corrupt_mass_dom}`")
    lines.append(f"- Clean density dominant spans: `{clean_density_dom}`")
    lines.append(f"- Corrupt density dominant spans: `{corrupt_density_dom}`")
    lines.append("")
    lines.append("## Largest Clean/Corrupt Shifts")
    lines.append("")
    for row in largest_mass_shift[:10]:
        lines.append(
            f"- Mass shift `{row['head']}`: L1 `{row['decision_mass_l1_shift']:.4f}`, "
            f"+`{row['decision_mass_delta_pos_span']}` `{row['decision_mass_delta_pos_value']:.4f}`, "
            f"`{row['decision_mass_delta_neg_span']}` `{row['decision_mass_delta_neg_value']:.4f}`."
        )
    lines.append("")
    for row in largest_density_shift[:10]:
        lines.append(
            f"- Density shift `{row['head']}`: L1 `{row['decision_density_l1_shift']:.4f}`, "
            f"+`{row['decision_density_delta_pos_span']}` `{row['decision_density_delta_pos_value']:.4f}`, "
            f"`{row['decision_density_delta_neg_span']}` `{row['decision_density_delta_neg_value']:.4f}`."
        )
    lines.append("")
    lines.append("## Key Heads")
    lines.append("")
    for head in key_heads:
        row = key_head_rows.get(head)
        if row is None:
            continue
        lines.append(
            f"- `{head}`: clean density top `{row['clean_density_top_span']}` `{row['clean_density_top_value']:.4f}`, "
            f"corrupt density top `{row['corrupt_density_top_span']}` `{row['corrupt_density_top_value']:.4f}`, "
            f"mass shift `{row['decision_mass_l1_shift']:.4f}`, density shift `{row['decision_density_l1_shift']:.4f}`."
        )
    lines.append("")
    lines.append("## Layer Trends")
    lines.append("")
    for metric in ["decision_mass_mean", "decision_density_mean"]:
        for condition in ["clean", "corrupt"]:
            subset = [row for row in layer_profile_rows if row["metric"] == metric and row["condition"] == condition]
            lines.append(
                f"- `{metric}` / `{condition}` early layers (0-7): "
                + format_top_pairs(
                    (
                        (
                            span,
                            sum(row[span] for row in subset if 0 <= row["layer"] <= 7) / 8.0,
                        )
                        for span in span_order
                    ),
                    n=4,
                )
            )
            lines.append(
                f"- `{metric}` / `{condition}` middle layers (8-17): "
                + format_top_pairs(
                    (
                        (
                            span,
                            sum(row[span] for row in subset if 8 <= row["layer"] <= 17) / 10.0,
                        )
                        for span in span_order
                    ),
                    n=4,
                )
            )
            lines.append(
                f"- `{metric}` / `{condition}` late layers (18-27): "
                + format_top_pairs(
                    (
                        (
                            span,
                            sum(row[span] for row in subset if 18 <= row["layer"] <= 27) / 10.0,
                        )
                        for span in span_order
                    ),
                    n=4,
                )
            )
    lines.append("")
    lines.append("## Off-Diagonal Patterns")
    lines.append("")
    top_offdiag = sorted(offdiag_rows, key=lambda r: r["clean_density"], reverse=True)[:20]
    top_delta_offdiag = sorted(offdiag_rows, key=lambda r: r["delta_density"], reverse=True)[:20]
    bottom_delta_offdiag = sorted(offdiag_rows, key=lambda r: r["delta_density"])[:20]
    lines.append("- Strongest clean off-diagonal density links:")
    for row in top_offdiag[:10]:
        lines.append(
            f"  - `{row['head']}` `{row['query_span']} -> {row['key_span']}` clean density `{row['clean_density']:.4f}`"
        )
    lines.append("- Largest positive corrupt-clean off-diagonal density shifts:")
    for row in top_delta_offdiag[:10]:
        lines.append(
            f"  - `{row['head']}` `{row['query_span']} -> {row['key_span']}` delta `{row['delta_density']:.4f}`"
        )
    lines.append("- Largest negative corrupt-clean off-diagonal density shifts:")
    for row in bottom_delta_offdiag[:10]:
        lines.append(
            f"  - `{row['head']}` `{row['query_span']} -> {row['key_span']}` delta `{row['delta_density']:.4f}`"
        )

    (output_root / "ATTENTION_HEAD_ANALYSIS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
