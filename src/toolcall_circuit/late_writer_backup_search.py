#!/usr/bin/env python3
"""
Late-writer backup search for the current tool-call mechanism.

The goal is not to prove uniqueness. The goal is narrower:

1. Measure how much each late candidate can rescue the tool-call endpoint.
2. Re-run that rescue while forcing MLP27 back to the base state.
3. Treat the residual rescue under MLP27 block as evidence for an independent
   backup writer path.

If a candidate's rescue collapses when MLP27 is blocked, that candidate is more
plausibly upstream of MLP27 than an alternative late writer.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import matplotlib.pyplot as plt
import numpy as np
import torch
from tqdm.auto import tqdm

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from toolcall_circuit.bidirectional_causal_eval import collect_cache_cpu_for_nodes, load_sample_paths
from toolcall_circuit.objective import build_bidirectional_endpoint_objectives
from toolcall_circuit.semantic_factorized_counterfactual import build_variants, safe_float
from toolcall_circuit.signed_edge_importance import run_logits_with_assignments
from toolcall_circuit.single_sample import load_hooked_qwen3, objective_from_logits


DEFAULT_CANDIDATES = [
    "MLP27",
    "L24H6",
    "L21H12",
    "L21H1",
    "MLP19",
    "MLP16",
    "L23H6",
    "L17H8",
]

BASE_VARIANTS = [
    "corrupt_full",
    "clean_no_schema",
    "clean_schema_mismatch",
    "clean_no_protocol",
]


def write_csv(rows: Sequence[Dict[str, object]], out_path: Path) -> None:
    if not rows:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def median(values: Iterable[float]) -> float:
    vals = [float(v) for v in values if isinstance(v, (int, float)) and math.isfinite(float(v))]
    return float(np.median(vals)) if vals else float("nan")


def safe_rate(values: Iterable[bool]) -> float:
    vals = [1.0 if bool(v) else 0.0 for v in values]
    return float(np.mean(vals)) if vals else float("nan")


def finite_ratio(num: float, den: float) -> float:
    if not math.isfinite(num) or not math.isfinite(den) or abs(den) < 1e-8:
        return float("nan")
    return float(num / den)


def plot_backup_strength(summary_rows: Sequence[Dict[str, object]], out_path: Path) -> None:
    by_base: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in summary_rows:
        by_base[str(row["base_variant"])].append(row)

    bases = list(sorted(by_base))
    fig, axes = plt.subplots(
        len(bases),
        1,
        figsize=(10.5, max(3.4 * len(bases), 4.0)),
        constrained_layout=True,
    )
    if len(bases) == 1:
        axes = [axes]
    plt.style.use("default")

    for ax, base_variant in zip(axes, bases):
        rows = sorted(by_base[base_variant], key=lambda r: float(r["source_rescue_median"]), reverse=True)
        labels = [str(r["candidate"]) for r in rows]
        xs = np.arange(len(labels))
        source = np.array([float(r["source_rescue_median"]) for r in rows], dtype=float)
        blocked = np.array([float(r["blocked_rescue_median"]) for r in rows], dtype=float)
        width = 0.38
        ax.bar(xs - width / 2.0, source, width=width, color="#d88c4a", label="source rescue")
        ax.bar(xs + width / 2.0, blocked, width=width, color="#4e87b5", label="rescue with MLP27 blocked")
        ax.axhline(0.0, color="#888888", linewidth=1.0)
        ax.set_title(base_variant)
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, rotation=30, ha="right")
        ax.set_ylabel("median rescue ratio")
        ax.legend(frameon=False)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Late-writer backup search for the stable tool-call circuit.")
    parser.add_argument("--run-root", type=str, required=True)
    parser.add_argument("--model-path", type=str, default="/root/autodl-tmp/Qwen/Qwen3-1.7B")
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--candidates", type=str, default=",".join(DEFAULT_CANDIDATES))
    parser.add_argument("--output-root", type=str, required=True)
    args = parser.parse_args()

    run_root = Path(args.run_root).resolve()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    candidates = [x.strip() for x in args.candidates.split(",") if x.strip()]
    if "MLP27" not in candidates:
        candidates = ["MLP27", *candidates]
    all_nodes = sorted(set(candidates + ["MLP27"]))

    samples = load_sample_paths(run_root / "forward_batch", run_root / "reverse_batch", max_samples=args.max_samples)
    model, tokenizer = load_hooked_qwen3(args.model_path, device=args.device, dtype=torch.bfloat16)
    _ = tokenizer

    per_sample_rows: List[Dict[str, object]] = []
    pbar = tqdm(samples, desc="Late-writer backup search", dynamic_ncols=True)
    for sp in pbar:
        try:
            clean_text = sp.tool_call_prompt.read_text(encoding="utf-8")
            corrupt_text = sp.no_tool_prompt.read_text(encoding="utf-8")
        except Exception:
            continue
        variants = build_variants(clean_text, corrupt_text)

        tokens_by_variant: Dict[str, torch.Tensor] = {}
        logits_by_variant: Dict[str, torch.Tensor] = {}
        for name in ["clean_full", *BASE_VARIANTS]:
            tokens = model.to_tokens(variants[name], prepend_bos=False)
            tokens_by_variant[name] = tokens
            with torch.no_grad():
                logits_by_variant[name] = model(tokens)

        tool_objective, no_tool_objective = build_bidirectional_endpoint_objectives(
            logits_by_variant["clean_full"],
            logits_by_variant["corrupt_full"],
            tokenizer=tokenizer,
        )
        tool_gap = float(objective_from_logits(logits_by_variant["clean_full"], tool_objective).item()) - float(
            objective_from_logits(logits_by_variant["corrupt_full"], tool_objective).item()
        )
        if not math.isfinite(tool_gap) or abs(tool_gap) < 1e-8:
            continue

        clean_cache = collect_cache_cpu_for_nodes(model, tokens_by_variant["clean_full"], all_nodes)
        variant_caches = {
            name: collect_cache_cpu_for_nodes(model, tokens_by_variant[name], all_nodes)
            for name in BASE_VARIANTS
        }

        for base_variant in BASE_VARIANTS:
            base_tokens = tokens_by_variant[base_variant]
            base_cache = variant_caches[base_variant]
            base_tool = float(objective_from_logits(logits_by_variant[base_variant], tool_objective).item())
            base_no_tool = float(objective_from_logits(logits_by_variant[base_variant], no_tool_objective).item())
            for candidate in candidates:
                source_logits = run_logits_with_assignments(
                    model,
                    base_tokens,
                    clean_cache,
                    base_cache,
                    [candidate],
                    [],
                )
                source_tool = float(objective_from_logits(source_logits, tool_objective).item())
                source_no_tool = float(objective_from_logits(source_logits, no_tool_objective).item())
                source_ratio = (source_tool - base_tool) / tool_gap
                source_top1 = int(source_logits[0, -1].argmax().item()) == sp.target_tool_call
                source_boundary = source_tool > source_no_tool

                if candidate == "MLP27":
                    blocked_ratio = 0.0
                    blocked_top1 = False
                    blocked_boundary = False
                else:
                    blocked_logits = run_logits_with_assignments(
                        model,
                        base_tokens,
                        clean_cache,
                        base_cache,
                        [candidate],
                        ["MLP27"],
                    )
                    blocked_tool = float(objective_from_logits(blocked_logits, tool_objective).item())
                    blocked_no_tool = float(objective_from_logits(blocked_logits, no_tool_objective).item())
                    blocked_ratio = (blocked_tool - base_tool) / tool_gap
                    blocked_top1 = int(blocked_logits[0, -1].argmax().item()) == sp.target_tool_call
                    blocked_boundary = blocked_tool > blocked_no_tool

                per_sample_rows.append(
                    {
                        "sample_id": sp.sample_id,
                        "base_variant": base_variant,
                        "candidate": candidate,
                        "source_rescue": source_ratio,
                        "blocked_rescue": blocked_ratio,
                        "mlp27_mediated_rescue": source_ratio - blocked_ratio,
                        "blocked_retained_fraction": finite_ratio(blocked_ratio, source_ratio),
                        "source_tool_top1": source_top1,
                        "blocked_tool_top1": blocked_top1,
                        "source_boundary_flip": source_boundary,
                        "blocked_boundary_flip": blocked_boundary,
                    }
                )
        pbar.set_postfix(sample=sp.sample_id)

    write_csv(per_sample_rows, output_root / "late_writer_backup_per_sample.csv")

    summary_rows: List[Dict[str, object]] = []
    grouped: Dict[tuple[str, str], List[Dict[str, object]]] = defaultdict(list)
    for row in per_sample_rows:
        grouped[(str(row["base_variant"]), str(row["candidate"]))].append(row)
    for (base_variant, candidate), rows in sorted(grouped.items()):
        summary_rows.append(
            {
                "base_variant": base_variant,
                "candidate": candidate,
                "n_samples": len(rows),
                "source_rescue_median": median(safe_float(r["source_rescue"]) for r in rows),
                "blocked_rescue_median": median(safe_float(r["blocked_rescue"]) for r in rows),
                "mlp27_mediated_rescue_median": median(safe_float(r["mlp27_mediated_rescue"]) for r in rows),
                "blocked_retained_fraction_median": median(safe_float(r["blocked_retained_fraction"]) for r in rows),
                "source_tool_top1_rate": safe_rate(bool(r["source_tool_top1"]) for r in rows),
                "blocked_tool_top1_rate": safe_rate(bool(r["blocked_tool_top1"]) for r in rows),
                "source_boundary_flip_rate": safe_rate(bool(r["source_boundary_flip"]) for r in rows),
                "blocked_boundary_flip_rate": safe_rate(bool(r["blocked_boundary_flip"]) for r in rows),
            }
        )

    write_csv(summary_rows, output_root / "late_writer_backup_summary.csv")
    plot_backup_strength(summary_rows, output_root / "late_writer_backup_strength.png")

    by_base: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in summary_rows:
        by_base[str(row["base_variant"])].append(row)

    base_summary_rows: List[Dict[str, object]] = []
    for base_variant, rows in sorted(by_base.items()):
        mlp27_row = next(r for r in rows if str(r["candidate"]) == "MLP27")
        non_mlp27 = [r for r in rows if str(r["candidate"]) != "MLP27"]
        best_alt_direct = max(non_mlp27, key=lambda r: float(r["source_rescue_median"]), default=None)
        best_alt_independent = max(non_mlp27, key=lambda r: float(r["blocked_rescue_median"]), default=None)
        base_summary_rows.append(
            {
                "base_variant": base_variant,
                "mlp27_direct_rescue_median": mlp27_row["source_rescue_median"],
                "mlp27_tool_top1_rate": mlp27_row["source_tool_top1_rate"],
                "best_alt_direct_candidate": best_alt_direct["candidate"] if best_alt_direct else "",
                "best_alt_direct_rescue_median": best_alt_direct["source_rescue_median"] if best_alt_direct else float("nan"),
                "best_alt_independent_candidate": best_alt_independent["candidate"] if best_alt_independent else "",
                "best_alt_independent_rescue_median": best_alt_independent["blocked_rescue_median"] if best_alt_independent else float("nan"),
                "best_alt_independent_top1_rate": best_alt_independent["blocked_tool_top1_rate"] if best_alt_independent else float("nan"),
                "mlp27_margin_over_best_independent": (
                    float(mlp27_row["source_rescue_median"]) - float(best_alt_independent["blocked_rescue_median"])
                    if best_alt_independent
                    else float("nan")
                ),
            }
        )

    conclusion_lines = []
    for row in base_summary_rows:
        conclusion_lines.append(
            {
                "base_variant": row["base_variant"],
                "conclusion": (
                    "MLP27 remains the strongest direct late writer candidate"
                    if safe_float(row["mlp27_margin_over_best_independent"], float("-inf")) > 0.15
                    else "independent late-writer alternatives remain competitive"
                ),
            }
        )

    summary = {
        "candidate_summary_rows": summary_rows,
        "base_summary_rows": base_summary_rows,
        "conclusion_rows": conclusion_lines,
        "artifacts": {
            "per_sample_csv": str(output_root / "late_writer_backup_per_sample.csv"),
            "summary_csv": str(output_root / "late_writer_backup_summary.csv"),
            "plot": str(output_root / "late_writer_backup_strength.png"),
        },
    }
    (output_root / "late_writer_backup_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = ["# Late Writer Backup Search", ""]
    for row in base_summary_rows:
        lines.append(
            f"- `{row['base_variant']}`: MLP27 direct `{float(row['mlp27_direct_rescue_median']):.3f}`, "
            f"best alternative direct `{row['best_alt_direct_candidate']}`=`{float(row['best_alt_direct_rescue_median']):.3f}`, "
            f"best alternative with MLP27 blocked `{row['best_alt_independent_candidate']}`=`{float(row['best_alt_independent_rescue_median']):.3f}`."
        )
    lines.append("")
    lines.append("Interpretation:")
    for row in conclusion_lines:
        lines.append(f"- `{row['base_variant']}`: {row['conclusion']}.")
    (output_root / "late_writer_backup_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
