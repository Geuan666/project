#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import torch
from tqdm.auto import tqdm

from toolcall_circuit.dataset import load_dataset_samples
from toolcall_circuit.objective import build_bidirectional_endpoint_objectives
from toolcall_circuit.output_route_decision_refine import (
    ANCHOR_NODES,
    binary_auc,
    build_route_score,
    collect_cache,
    collect_names,
    extract_node,
    module_score,
    score_from_cache,
    spearman_corr,
    unit,
)
from toolcall_circuit.single_sample import load_hooked_qwen3, objective_from_logits


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="用 train 几何在 test 集上验证 route score 泛化。")
    parser.add_argument(
        "--train-dataset-root",
        type=Path,
        default=Path("/root/autodl-tmp/project/experiment/datasets/train"),
    )
    parser.add_argument(
        "--test-dataset-root",
        type=Path,
        default=Path("/root/autodl-tmp/project/experiment/datasets/test"),
    )
    parser.add_argument("--model-path", type=str, default="/root/autodl-tmp/Qwen/Qwen3-1.7B")
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("/root/autodl-tmp/project/experiment/results/split/test_validation/route_score_test_validation.csv"),
    )
    return parser.parse_args()


def finite(values: Iterable[float]) -> List[float]:
    out: List[float] = []
    for value in values:
        try:
            num = float(value)
        except Exception:
            continue
        if math.isfinite(num):
            out.append(num)
    return out


def median(values: Iterable[float]) -> float:
    vals = finite(values)
    if not vals:
        return float("nan")
    vals.sort()
    n = len(vals)
    mid = n // 2
    if n % 2 == 1:
        return vals[mid]
    return 0.5 * (vals[mid - 1] + vals[mid])


def safe_rate(values: Iterable[bool]) -> float:
    vals = [1.0 if bool(v) else 0.0 for v in values]
    return sum(vals) / len(vals) if vals else float("nan")


def write_csv(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_geometry(model, samples) -> Dict[str, Dict[str, torch.Tensor | float]]:
    hook_names = collect_names(ANCHOR_NODES)
    mean_clean: Dict[str, torch.Tensor] = {}
    mean_corrupt: Dict[str, torch.Tensor] = {}
    valid = 0

    for sample in tqdm(samples, desc="Train geometry", dynamic_ncols=True):
        clean_text = sample.clean_path.read_text(encoding="utf-8")
        corrupt_text = sample.corrupt_path.read_text(encoding="utf-8")
        clean_tokens = model.to_tokens(clean_text, prepend_bos=False)
        corrupt_tokens = model.to_tokens(corrupt_text, prepend_bos=False)
        clean_cache = collect_cache(model, clean_tokens, hook_names)
        corrupt_cache = collect_cache(model, corrupt_tokens, hook_names)
        for node in ANCHOR_NODES:
            clean_vec = extract_node(clean_cache, node)
            corrupt_vec = extract_node(corrupt_cache, node)
            if node not in mean_clean:
                mean_clean[node] = clean_vec.clone()
                mean_corrupt[node] = corrupt_vec.clone()
            else:
                mean_clean[node] += clean_vec
                mean_corrupt[node] += corrupt_vec
        valid += 1

    if valid == 0:
        raise ValueError("训练集上没有有效样本，无法构造 route 几何。")

    geometry: Dict[str, Dict[str, torch.Tensor | float]] = {}
    for node in ANCHOR_NODES:
        mu_clean = mean_clean[node] / float(valid)
        mu_corrupt = mean_corrupt[node] / float(valid)
        direction = unit(mu_clean - mu_corrupt)
        midpoint = 0.5 * (mu_clean + mu_corrupt)
        scale = float(torch.dot(mu_clean - midpoint, direction).item())
        geometry[node] = {
            "mu_clean": mu_clean,
            "mu_corrupt": mu_corrupt,
            "direction": direction,
            "midpoint": midpoint,
            "scale": scale,
        }
    return geometry


def evaluate_split(model, tokenizer, samples, geometry) -> List[Dict[str, object]]:
    hook_names = collect_names(ANCHOR_NODES)
    rows: List[Dict[str, object]] = []

    for sample in tqdm(samples, desc="Test route score", dynamic_ncols=True):
        clean_text = sample.clean_path.read_text(encoding="utf-8")
        corrupt_text = sample.corrupt_path.read_text(encoding="utf-8")
        clean_tokens = model.to_tokens(clean_text, prepend_bos=False)
        corrupt_tokens = model.to_tokens(corrupt_text, prepend_bos=False)

        with torch.no_grad():
            clean_logits = model(clean_tokens)
            corrupt_logits = model(corrupt_tokens)

        tool_objective, no_tool_objective = build_bidirectional_endpoint_objectives(
            clean_logits,
            corrupt_logits,
            tokenizer=tokenizer,
        )
        clean_route = build_route_score(clean_logits, tool_objective, no_tool_objective)
        corrupt_route = build_route_score(corrupt_logits, tool_objective, no_tool_objective)

        clean_cache = collect_cache(model, clean_tokens, hook_names)
        corrupt_cache = collect_cache(model, corrupt_tokens, hook_names)

        clean_scores = {node: score_from_cache(clean_cache, node, geometry) for node in ANCHOR_NODES}
        corrupt_scores = {node: score_from_cache(corrupt_cache, node, geometry) for node in ANCHOR_NODES}
        clean_module = module_score(clean_scores)
        corrupt_module = module_score(corrupt_scores)

        for node in ANCHOR_NODES:
            rows.append(
                {
                    "sample_id": sample.sample_id,
                    "node": node,
                    "condition": "clean",
                    "local_route_score": clean_scores[node],
                    "module_route_score": clean_module,
                    "route_margin": clean_route,
                }
            )
            rows.append(
                {
                    "sample_id": sample.sample_id,
                    "node": node,
                    "condition": "corrupt",
                    "local_route_score": corrupt_scores[node],
                    "module_route_score": corrupt_module,
                    "route_margin": corrupt_route,
                }
            )
    return rows


def summarize(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    summary_rows: List[Dict[str, object]] = []
    for node in ANCHOR_NODES:
        clean_vals = [float(r["local_route_score"]) for r in rows if r["node"] == node and r["condition"] == "clean"]
        corrupt_vals = [float(r["local_route_score"]) for r in rows if r["node"] == node and r["condition"] == "corrupt"]
        all_vals = [float(r["local_route_score"]) for r in rows if r["node"] == node]
        all_margins = [float(r["route_margin"]) for r in rows if r["node"] == node]
        summary_rows.append(
            {
                "node": node,
                "n_samples_per_condition": len(clean_vals),
                "clean_score_median": median(clean_vals),
                "corrupt_score_median": median(corrupt_vals),
                "clean_positive_rate": safe_rate(v > 0.0 for v in clean_vals),
                "corrupt_negative_rate": safe_rate(v < 0.0 for v in corrupt_vals),
                "auc_clean_vs_corrupt": binary_auc(clean_vals, corrupt_vals),
                "spearman_with_route_margin": spearman_corr(all_vals, all_margins),
            }
        )

    module_clean = [float(r["module_route_score"]) for r in rows if r["node"] == ANCHOR_NODES[0] and r["condition"] == "clean"]
    module_corrupt = [float(r["module_route_score"]) for r in rows if r["node"] == ANCHOR_NODES[0] and r["condition"] == "corrupt"]
    module_all = [float(r["module_route_score"]) for r in rows if r["node"] == ANCHOR_NODES[0]]
    module_margins = [float(r["route_margin"]) for r in rows if r["node"] == ANCHOR_NODES[0]]
    summary_rows.append(
        {
            "node": "module_anchor_mean",
            "n_samples_per_condition": len(module_clean),
            "clean_score_median": median(module_clean),
            "corrupt_score_median": median(module_corrupt),
            "clean_positive_rate": safe_rate(v > 0.0 for v in module_clean),
            "corrupt_negative_rate": safe_rate(v < 0.0 for v in module_corrupt),
            "auc_clean_vs_corrupt": binary_auc(module_clean, module_corrupt),
            "spearman_with_route_margin": spearman_corr(module_all, module_margins),
        }
    )
    return summary_rows


def main() -> None:
    args = parse_args()
    train_samples = load_dataset_samples(args.train_dataset_root.resolve())
    test_samples = load_dataset_samples(args.test_dataset_root.resolve())
    model, tokenizer = load_hooked_qwen3(args.model_path, device=args.device, dtype=torch.bfloat16)

    geometry = build_geometry(model, train_samples)
    per_sample_rows = evaluate_split(model, tokenizer, test_samples, geometry)
    summary_rows = summarize(per_sample_rows)
    write_csv(args.output_path.resolve(), summary_rows)

    geometry_summary = {
        node: {
            "scale": float(geometry[node]["scale"]),
            "direction_norm": float(torch.norm(geometry[node]["direction"]).item()),  # type: ignore[arg-type]
        }
        for node in ANCHOR_NODES
    }
    (args.output_path.resolve().with_suffix(".json")).write_text(
        json.dumps(
            {
                "train_dataset_root": str(args.train_dataset_root.resolve()),
                "test_dataset_root": str(args.test_dataset_root.resolve()),
                "n_train": len(train_samples),
                "n_test": len(test_samples),
                "geometry": geometry_summary,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
