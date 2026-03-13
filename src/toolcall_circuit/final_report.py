#!/usr/bin/env python3
"""
Assemble a concise Markdown report for the final tool-call circuit deliverable.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def read_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fmt(value: object, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the final Markdown report for the tool-call circuit run.")
    parser.add_argument("--run-root", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    run_root = Path(args.run_root).resolve()
    out_path = Path(args.output).resolve()

    bidi = read_json(run_root / "bidirectional" / "bidirectional_summary.json")
    signed = read_json(run_root / "final_signed_circuit" / "final_signed_circuit_summary.json")
    signed_validate = read_json(run_root / "signed_validate" / "signed_group_report.json")
    token_flip = read_json(run_root / "token_flip" / "group_token_flip_summary.json")
    node_importance = read_json(run_root / "node_importance" / "signed_node_importance_report.json")
    functional = read_json(run_root / "functional_groups" / "functional_group_summary.json")
    functional_validate_path = run_root / "functional_validate" / "functional_group_report.json"
    functional_validate = read_json(functional_validate_path) if functional_validate_path.exists() else {"summary_rows": []}

    signed_rows = {str(r["group"]): r for r in signed_validate.get("summary_rows", [])}
    flip_rows = {str(r["group"]): r for r in token_flip.get("summary_rows", [])}
    node_rows = list(node_importance.get("summary_rows", []))
    func_rows = list(functional.get("summary_rows", []))
    func_validate_rows = {str(r["group"]): r for r in functional_validate.get("summary_rows", [])}

    lines: List[str] = []
    lines.append("# Tool-Call Signed Circuit Final Report")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(
        f"- Dataset: `{bidi['forward']['n_samples']}` discovery samples per direction in this run root."
    )
    lines.append(
        f"- Final structural signed circuit: `{signed['n_nodes']}` nodes / `{signed['n_edges']}` edges."
    )
    full_row = signed_rows.get("full_signed_circuit", {})
    lines.append(
        f"- Full-circuit KL recovery: promote `{fmt(full_row.get('promote_suff_ratio_median'))}`, suppress `{fmt(full_row.get('suppress_suff_ratio_median'))}`."
    )
    lines.append(
        f"- Full-circuit top-1 flips: promote `{fmt(full_row.get('promote_tool_top1_rate'))}`, suppress `{fmt(full_row.get('suppress_no_tool_top1_rate'))}`."
    )
    lines.append("")
    lines.append("## Structural Story")
    lines.append("")
    lines.append("- Structural groups remain internal analysis tags:")
    for key, nodes in signed.get("groups", {}).items():
        lines.append(f"  - `{key}`: `{len(nodes)}` nodes")
    lines.append("")
    lines.append("Core structural artifacts:")
    lines.append("- `final_signed_circuit/final_signed_circuit.png`")
    lines.append("- `bidirectional/bidirectional_summary.json`")
    lines.append("- `signed_validate/signed_group_report.json`")
    lines.append("")
    lines.append("## Functional Semantic Groups")
    lines.append("")
    for row in func_rows:
        lines.append(
            f"- `{row['functional_label']}`: `{row['n_nodes']}` nodes, "
            f"promote median `{fmt(row['promote_strength_median'])}`, "
            f"suppress median `{fmt(row['suppress_strength_median'])}`."
        )
    lines.append("")
    lines.append("Functional artifacts:")
    lines.append("- `functional_groups/functional_group_graph.png`")
    lines.append("- `functional_groups/functional_node_table.csv`")
    lines.append("- `functional_validate/functional_group_report.json`")
    lines.append("")
    lines.append("## Faithfulness Checks")
    lines.append("")
    lines.append("- Structural group validation:")
    for key in ["symmetric_backbone", "tool_bias_backbone", "no_tool_bias_backbone", "tool_tail", "no_tool_tail"]:
        if key not in signed_rows:
            continue
        row = signed_rows[key]
        lines.append(
            f"  - `{key}`: suff `{fmt(row['promote_suff_ratio_median'])}/{fmt(row['suppress_suff_ratio_median'])}`, "
            f"nec `{fmt(row['promote_nec_drop_median'])}/{fmt(row['suppress_nec_drop_median'])}`."
        )
    lines.append("- Functional group validation:")
    for key in functional.get("groups", {}).keys():
        row = func_validate_rows.get(key)
        if not row:
            continue
        lines.append(
            f"  - `{row['functional_label']}`: suff `{fmt(row['promote_suff_ratio_median'])}/{fmt(row['suppress_suff_ratio_median'])}`, "
            f"nec `{fmt(row['promote_nec_drop_median'])}/{fmt(row['suppress_nec_drop_median'])}`."
        )
    lines.append("")
    lines.append("## Behavioral Evidence")
    lines.append("")
    for key in ["shared_backbone", "shared_backbone_exclusive", "forward_selective", "reverse_selective"]:
        row = flip_rows.get(key)
        if not row:
            continue
        lines.append(
            f"- `{key}`: top-1 `{fmt(row['promote_tool_top1_rate'])}/{fmt(row['suppress_no_tool_top1_rate'])}`, "
            f"boundary `{fmt(row['promote_boundary_flip_rate'])}/{fmt(row['suppress_boundary_flip_rate'])}`."
        )
    lines.append("")
    lines.append("## Node / Edge Diagnostics")
    lines.append("")
    lines.append("- Top node diagnostics:")
    for row in node_rows[:10]:
        lines.append(
            f"  - `{row['node']}`: suff `{fmt(row['promote_suff_ratio_median'])}/{fmt(row['suppress_suff_ratio_median'])}`, "
            f"nec `{fmt(row['promote_nec_drop_median'])}/{fmt(row['suppress_nec_drop_median'])}`."
        )
    edge_report_path = run_root / "edge_importance" / "signed_edge_mediation_report.json"
    if edge_report_path.exists():
        edge_report = read_json(edge_report_path)
        edge_rows = list(edge_report.get("summary_rows", []))
        lines.append("- Top edge diagnostics:")
        for row in edge_rows[:10]:
            lines.append(
                f"  - `{row['edge']}`: mediated `{fmt(row['promote_mediated_ratio_median'])}/{fmt(row['suppress_mediated_ratio_median'])}`."
            )
    lines.append("")
    method_report_path = run_root / "method_benchmark" / "benchmark_summary.json"
    if method_report_path.exists():
        method_report = read_json(method_report_path)
        lines.append("## Method Comparison")
        lines.append("")
        for row in method_report.get("summary_rows", []):
            lines.append(
                f"- `{row['method']}`: faithfulness `{fmt(row.get('faithfulness_median'))}`, "
                f"sparsity `{fmt(row.get('n_nodes'))}`, semantic `{fmt(row.get('semantic_coherence'))}`, "
                f"runtime `{fmt(row.get('runtime_seconds'))}` sec."
            )
        lines.append("")
    lines.append("## Artifact Index")
    lines.append("")
    lines.append(f"- Run root: `{run_root}`")
    lines.append("- Main figure: `final_signed_circuit/final_signed_circuit.png`")
    lines.append("- Structural validation: `signed_validate/signed_group_validation_heatmap.png`")
    lines.append("- Functional graph: `functional_groups/functional_group_graph.png`")
    lines.append("- Functional validation: `functional_validate/functional_group_validation_heatmap.png`")
    lines.append("- Token flips: `token_flip/group_token_flip_summary.csv`")
    lines.append("- Node importance: `node_importance/signed_node_importance_heatmap.png`")
    lines.append("- Trajectory: `signed_layer_trajectory/signed_layer_trajectory.png`")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(str(out_path))


if __name__ == "__main__":
    main()
