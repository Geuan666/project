#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import torch
from tqdm.auto import tqdm

from toolcall_circuit.bidirectional_causal_eval import collect_cache_cpu_for_nodes
from toolcall_circuit.dataset import load_dataset_samples
from toolcall_circuit.objective import build_bidirectional_endpoint_objectives
from toolcall_circuit.single_sample import load_hooked_qwen3, objective_from_logits
from toolcall_circuit.signed_edge_importance import run_logits_with_assignments
from toolcall_circuit.suppression_direction_analysis import (
    ALL_TRACKED_NODES,
    STAGEWISE_CHAIN,
    TOOL_INGRESS_NODES,
    collect_cache,
    collect_names,
    extract_node,
    projection_delta,
    run_with_multi_edits_and_collect,
    unit,
)
from toolcall_circuit.tool_call_construction_analysis import STAGE_STEPS, collect_cache_with_scale


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="在 test 集上复用 train 决定的 construction/suppression stagewise 轨迹。")
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
        "--construction-output",
        type=Path,
        default=Path("/root/autodl-tmp/project/experiment/results/split/test_validation/construction_stagewise_test.csv"),
    )
    parser.add_argument(
        "--suppression-output",
        type=Path,
        default=Path("/root/autodl-tmp/project/experiment/results/split/test_validation/suppression_stagewise_test.csv"),
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


def summarize_by_step(rows: Sequence[Dict[str, object]], step_key: str, extra_projection_nodes: Sequence[str]) -> List[Dict[str, object]]:
    grouped: Dict[int, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["step_idx"])].append(dict(row))
    summary: List[Dict[str, object]] = []
    for step_idx, members in sorted(grouped.items()):
        base = members[0]
        row: Dict[str, object] = {
            "step_idx": step_idx,
            step_key: base[step_key],
            "nodes": base["nodes"],
            "n_samples": len(members),
            "route_margin_median": median(float(r["route_margin"]) for r in members) if "route_margin" in base else float("nan"),
            "tool_logit_median": median(float(r["tool_logit"]) for r in members) if "tool_logit" in base else float("nan"),
            "competitor_logit_median": median(float(r["competitor_logit"]) for r in members) if "competitor_logit" in base else float("nan"),
            "margin_logit_median": median(float(r["margin_logit"]) for r in members) if "margin_logit" in base else float("nan"),
            "tool_score_delta_median": median(float(r["tool_score_delta"]) for r in members) if "tool_score_delta" in base else float("nan"),
            "no_tool_score_delta_median": median(float(r["no_tool_score_delta"]) for r in members) if "no_tool_score_delta" in base else float("nan"),
            "decision_score_delta_median": median(float(r["decision_score_delta"]) for r in members) if "decision_score_delta" in base else float("nan"),
            "tool_token_delta_median": median(float(r["tool_token_delta"]) for r in members) if "tool_token_delta" in base else float("nan"),
            "no_tool_token_delta_median": median(float(r["no_tool_token_delta"]) for r in members) if "no_tool_token_delta" in base else float("nan"),
            "tool_top1_rate": safe_rate(bool(r["tool_top1"]) for r in members),
            "no_tool_top1_rate": safe_rate(bool(r["no_tool_top1"]) for r in members) if "no_tool_top1" in base else float("nan"),
            "boundary_flip_rate": safe_rate(bool(r["boundary_flip"]) for r in members) if "boundary_flip" in base else float("nan"),
        }
        for node in extra_projection_nodes:
            key = f"{node}_projection_delta"
            if key in base:
                row[f"{key}_median"] = median(float(r[key]) for r in members)
        summary.append(row)
    return summary


def build_train_suppression_dirs(model, train_samples) -> Dict[str, torch.Tensor]:
    hook_names = collect_names()
    direction_sums: Dict[str, torch.Tensor | None] = {node: None for node in ALL_TRACKED_NODES}

    for sample in tqdm(train_samples, desc="Train suppression dirs", dynamic_ncols=True):
        clean_text = sample.clean_path.read_text(encoding="utf-8")
        corrupt_text = sample.corrupt_path.read_text(encoding="utf-8")
        clean_tokens = model.to_tokens(clean_text, prepend_bos=False)
        corrupt_tokens = model.to_tokens(corrupt_text, prepend_bos=False)
        clean_cache = collect_cache(model, clean_tokens, hook_names)
        corrupt_cache = collect_cache(model, corrupt_tokens, hook_names)
        for node in ALL_TRACKED_NODES:
            diff = extract_node(corrupt_cache, node) - extract_node(clean_cache, node)
            direction_sums[node] = diff if direction_sums[node] is None else direction_sums[node] + diff

    return {node: unit(vec) for node, vec in direction_sums.items() if vec is not None}


def evaluate_construction(model, tokenizer, test_samples) -> List[Dict[str, object]]:
    tracked_nodes = sorted({node for _label, nodes in STAGE_STEPS for node in nodes})
    rows: List[Dict[str, object]] = []
    for sample in tqdm(test_samples, desc="Test construction stagewise", dynamic_ncols=True):
        clean_text = sample.clean_path.read_text(encoding="utf-8")
        corrupt_text = sample.corrupt_path.read_text(encoding="utf-8")
        clean_tokens = model.to_tokens(clean_text, prepend_bos=False)
        corrupt_tokens = model.to_tokens(corrupt_text, prepend_bos=False)
        if clean_tokens.shape != corrupt_tokens.shape:
            continue

        clean_cache = collect_cache_with_scale(model, clean_tokens, tracked_nodes)
        corrupt_cache = collect_cache_with_scale(model, corrupt_tokens, tracked_nodes)
        with torch.no_grad():
            clean_logits = model(clean_tokens)
            corrupt_logits = model(corrupt_tokens)
        tool_objective, no_tool_objective = build_bidirectional_endpoint_objectives(
            clean_logits,
            corrupt_logits,
            tokenizer=tokenizer,
        )
        tool_token_id = int(tool_objective.top_token_id or int(clean_logits[0, -1].argmax().item()))
        competitor_token_id = int(no_tool_objective.top_token_id or int(corrupt_logits[0, -1].argmax().item()))

        for step_idx, (step_label, nodes) in enumerate(STAGE_STEPS):
            if nodes:
                logits = run_logits_with_assignments(model, corrupt_tokens, clean_cache, corrupt_cache, nodes, [])
            else:
                logits = corrupt_logits
            tool_score = float(objective_from_logits(logits, tool_objective).item())
            no_tool_score = float(objective_from_logits(logits, no_tool_objective).item())
            rows.append(
                {
                    "sample_id": sample.sample_id,
                    "step_idx": step_idx,
                    "step_label": step_label,
                    "nodes": "|".join(nodes),
                    "route_margin": tool_score - no_tool_score,
                    "tool_logit": float(logits[0, -1, tool_token_id].item()),
                    "competitor_logit": float(logits[0, -1, competitor_token_id].item()),
                    "margin_logit": float(logits[0, -1, tool_token_id].item() - logits[0, -1, competitor_token_id].item()),
                    "tool_top1": int(logits[0, -1].argmax().item()) == tool_token_id,
                    "no_tool_top1": int(logits[0, -1].argmax().item()) == competitor_token_id,
                    "boundary_flip": tool_score > no_tool_score,
                }
            )
    return rows


def evaluate_suppression(model, tokenizer, test_samples, train_dirs: Dict[str, torch.Tensor]) -> List[Dict[str, object]]:
    hook_names = collect_names()
    rows: List[Dict[str, object]] = []
    for sample in tqdm(test_samples, desc="Test suppression stagewise", dynamic_ncols=True):
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
        tool_token_id = int(tool_objective.top_token_id or int(clean_logits[0, -1].argmax().item()))
        no_tool_token_id = int(no_tool_objective.top_token_id or int(corrupt_logits[0, -1].argmax().item()))

        clean_tool = float(objective_from_logits(clean_logits, tool_objective).item())
        clean_no_tool = float(objective_from_logits(clean_logits, no_tool_objective).item())
        clean_decision = clean_tool - clean_no_tool

        clean_cache = collect_cache(model, clean_tokens, hook_names)
        corrupt_cache = collect_cache(model, corrupt_tokens, hook_names)
        clean_vecs = {node: extract_node(clean_cache, node) for node in ALL_TRACKED_NODES}
        corrupt_vecs = {node: extract_node(corrupt_cache, node) for node in ALL_TRACKED_NODES}

        for step_idx, (stage_label, nodes) in enumerate(STAGEWISE_CHAIN, start=1):
            edits = {
                node: projection_delta(clean_vecs[node], corrupt_vecs[node], train_dirs[node])
                for node in nodes
            }
            edited_logits, recorded = run_with_multi_edits_and_collect(
                model,
                clean_tokens,
                edits=edits,
                record_names=hook_names,
            )
            edited_tool = float(objective_from_logits(edited_logits, tool_objective).item())
            edited_no_tool = float(objective_from_logits(edited_logits, no_tool_objective).item())
            row: Dict[str, object] = {
                "sample_id": sample.sample_id,
                "step_idx": step_idx,
                "stage_label": stage_label,
                "nodes": "|".join(nodes),
                "tool_token_delta": float(edited_logits[0, -1, tool_token_id].item() - clean_logits[0, -1, tool_token_id].item()),
                "no_tool_token_delta": float(edited_logits[0, -1, no_tool_token_id].item() - clean_logits[0, -1, no_tool_token_id].item()),
                "tool_score_delta": edited_tool - clean_tool,
                "no_tool_score_delta": edited_no_tool - clean_no_tool,
                "decision_score_delta": (edited_tool - edited_no_tool) - clean_decision,
                "tool_top1": int(edited_logits[0, -1].argmax().item()) == tool_token_id,
                "no_tool_top1": int(edited_logits[0, -1].argmax().item()) == no_tool_token_id,
            }
            for tracked in TOOL_INGRESS_NODES + ("MLP27",):
                edited_vec = extract_node(recorded, tracked)
                clean_vec = clean_vecs[tracked]
                direction = train_dirs[tracked]
                row[f"{tracked}_projection_delta"] = (
                    float(torch.dot(edited_vec - clean_vec, direction).item())
                    if float(direction.norm().item()) > 0.0
                    else float("nan")
                )
            rows.append(row)
    return rows


def main() -> None:
    args = parse_args()
    train_samples = load_dataset_samples(args.train_dataset_root.resolve())
    test_samples = load_dataset_samples(args.test_dataset_root.resolve())
    model, tokenizer = load_hooked_qwen3(args.model_path, device=args.device, dtype=torch.bfloat16)

    construction_rows = evaluate_construction(model, tokenizer, test_samples)
    construction_summary = summarize_by_step(construction_rows, "step_label", [])
    write_csv(args.construction_output.resolve(), construction_summary)

    train_dirs = build_train_suppression_dirs(model, train_samples)
    suppression_rows = evaluate_suppression(model, tokenizer, test_samples, train_dirs)
    suppression_summary = summarize_by_step(suppression_rows, "stage_label", list(TOOL_INGRESS_NODES) + ["MLP27"])
    write_csv(args.suppression_output.resolve(), suppression_summary)

    (args.suppression_output.resolve().with_suffix(".json")).write_text(
        json.dumps(
            {
                "train_dataset_root": str(args.train_dataset_root.resolve()),
                "test_dataset_root": str(args.test_dataset_root.resolve()),
                "n_train": len(train_samples),
                "n_test": len(test_samples),
                "construction_steps": [label for label, _nodes in STAGE_STEPS],
                "suppression_steps": [label for label, _nodes in STAGEWISE_CHAIN],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
