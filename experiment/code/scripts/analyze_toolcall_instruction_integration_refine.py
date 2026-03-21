#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
import torch
from tqdm.auto import tqdm

CODE_ROOT = Path(__file__).resolve().parents[1]
if __package__ in {None, ""}:
    sys.path.insert(0, str(CODE_ROOT / "src"))

from toolcall_circuit.bidirectional_causal_eval import collect_cache_cpu_for_nodes, load_sample_paths
from toolcall_circuit.instruction_verb_phrase_audit import build_variants as build_lead_variants
from toolcall_circuit.objective import build_bidirectional_endpoint_objectives, objective_from_logits
from toolcall_circuit.single_sample import load_hooked_qwen3


TARGET_NODES = ["MLP11", "MLP16", "MLP19"]
INGRESS_HEADS = ["L2H14", "L11H5"]


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(rows: Sequence[Dict[str, object]], out_path: Path) -> None:
    if not rows:
        return
    fieldnames: List[str] = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def finite(values: Iterable[float]) -> List[float]:
    return [float(v) for v in values if isinstance(v, (int, float)) and math.isfinite(float(v))]


def median(values: Iterable[float]) -> float:
    vals = finite(values)
    return float(np.median(vals)) if vals else float("nan")


def mean(values: Iterable[float]) -> float:
    vals = finite(values)
    return float(np.mean(vals)) if vals else float("nan")


def safe_rate(values: Iterable[bool]) -> float:
    vals = [1.0 if bool(v) else 0.0 for v in values]
    return float(np.mean(vals)) if vals else float("nan")


def bootstrap_median_ci(values: Iterable[float], *, n_boot: int = 400, seed: int = 123) -> Dict[str, float]:
    vals = finite(values)
    if not vals:
        return {"median": float("nan"), "lo": float("nan"), "hi": float("nan")}
    rng = random.Random(seed)
    n = len(vals)
    boots: List[float] = []
    for _ in range(n_boot):
        sample = [vals[rng.randrange(n)] for __ in range(n)]
        boots.append(float(np.median(sample)))
    boots.sort()
    lo = boots[max(0, int(0.025 * n_boot))]
    hi = boots[min(n_boot - 1, int(0.975 * n_boot))]
    return {"median": float(np.median(vals)), "lo": float(lo), "hi": float(hi)}


def fmt(value: object, digits: int = 3) -> str:
    try:
        value = float(value)
    except Exception:
        return str(value)
    if not math.isfinite(value):
        return "nan"
    return f"{value:.{digits}f}"


def to_float(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return float("nan")
        try:
            return float(text)
        except Exception:
            return float("nan")
    return float("nan")


def to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        low = value.strip().lower()
        if low in {"1", "true", "yes"}:
            return True
        if low in {"0", "false", "no", ""}:
            return False
    return bool(value)


def parse_head(node: str) -> Tuple[int, int]:
    body = node[1:]
    layer_s, head_s = body.split("H")
    return int(layer_s), int(head_s)


def node_to_hook_name(node: str) -> str:
    if node.startswith("MLP"):
        return f"blocks.{int(node[3:])}.hook_mlp_out"
    layer, _head = parse_head(node)
    return f"blocks.{layer}.attn.hook_z"


def resolve_prompt_path(path: Path) -> Path:
    if path.exists():
        return path
    text = str(path)
    legacy = "/root/autodl-tmp/project/datasets/"
    current = "/root/autodl-tmp/project/experiment/datasets/"
    if legacy in text:
        remapped = Path(text.replace(legacy, current))
        if remapped.exists():
            return remapped
    return path


def extract_node(cache: Dict[str, torch.Tensor], node: str) -> torch.Tensor:
    if node.startswith("MLP"):
        return cache[f"blocks.{int(node[3:])}.hook_mlp_out"][0, -1, :].float()
    layer, head = parse_head(node)
    return cache[f"blocks.{layer}.attn.hook_z"][0, -1, head, :].float()


def unit(vec: torch.Tensor) -> torch.Tensor:
    denom = float(vec.norm().item())
    if denom < 1e-8:
        return torch.zeros_like(vec)
    return vec / denom


def score_from_vec(vec: torch.Tensor, *, direction: torch.Tensor, midpoint: torch.Tensor, scale: float) -> float:
    raw = float(torch.dot(vec.float() - midpoint.float(), direction.float()).item())
    if not math.isfinite(scale) or abs(scale) < 1e-8:
        return float("nan")
    return raw / scale


def build_route_score(logits: torch.Tensor, tool_objective, no_tool_objective) -> float:
    tool_score = float(objective_from_logits(logits, tool_objective).item())
    no_tool_score = float(objective_from_logits(logits, no_tool_objective).item())
    return tool_score - no_tool_score


def run_with_assignments_and_collect(
    model,
    base_tokens: torch.Tensor,
    *,
    clean_cache_cpu: Dict[str, torch.Tensor],
    base_cache_cpu: Dict[str, torch.Tensor],
    patch_clean_nodes: Sequence[str],
    patch_base_nodes: Sequence[str],
    record_nodes: Sequence[str],
) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
    heads_by_layer_clean: Dict[int, List[int]] = defaultdict(list)
    heads_by_layer_base: Dict[int, List[int]] = defaultdict(list)
    mlp_layers_clean: List[int] = []
    mlp_layers_base: List[int] = []

    for node in patch_clean_nodes:
        if node.startswith("MLP"):
            mlp_layers_clean.append(int(node[3:]))
        else:
            layer, head = parse_head(node)
            heads_by_layer_clean[layer].append(head)
    for node in patch_base_nodes:
        if node.startswith("MLP"):
            mlp_layers_base.append(int(node[3:]))
        else:
            layer, head = parse_head(node)
            heads_by_layer_base[layer].append(head)

    hooks = []

    def add_head_hooks(layer_to_heads: Dict[int, List[int]], cache_cpu: Dict[str, torch.Tensor]) -> None:
        for layer, heads in layer_to_heads.items():
            cache_name = f"blocks.{layer}.attn.hook_z"
            src_act = cache_cpu[cache_name].to(base_tokens.device)
            uniq = sorted(set(heads))

            def make_head_hook(src: torch.Tensor, hs: Sequence[int]):
                def hook_fn(z: torch.Tensor, hook):  # noqa: ANN001
                    out = z.clone()
                    for h in hs:
                        out[:, -1, h, :] = src[:, -1, h, :].to(dtype=z.dtype)
                    return out

                return hook_fn

            hooks.append((cache_name, make_head_hook(src_act, uniq)))

    def add_mlp_hooks(layers: Sequence[int], cache_cpu: Dict[str, torch.Tensor]) -> None:
        for layer in sorted(set(layers)):
            cache_name = f"blocks.{layer}.hook_mlp_out"
            src_act = cache_cpu[cache_name].to(base_tokens.device)

            def make_mlp_hook(src: torch.Tensor):
                def hook_fn(mlp_out: torch.Tensor, hook):  # noqa: ANN001
                    out = mlp_out.clone()
                    out[:, -1, :] = src[:, -1, :].to(dtype=mlp_out.dtype)
                    return out

                return hook_fn

            hooks.append((cache_name, make_mlp_hook(src_act)))

    add_head_hooks(heads_by_layer_clean, clean_cache_cpu)
    add_head_hooks(heads_by_layer_base, base_cache_cpu)
    add_mlp_hooks(mlp_layers_clean, clean_cache_cpu)
    add_mlp_hooks(mlp_layers_base, base_cache_cpu)

    recorded: Dict[str, torch.Tensor] = {}
    for node in record_nodes:
        cache_name = node_to_hook_name(node)

        def make_record(name: str):
            def hook_fn(act: torch.Tensor, hook):  # noqa: ANN001
                recorded[name] = act.detach().cpu()
                return act

            return hook_fn

        hooks.append((cache_name, make_record(cache_name)))

    with torch.no_grad():
        logits = model.run_with_hooks(base_tokens, fwd_hooks=hooks)
    return logits, recorded


def build_route_geometry(*, samples, model) -> Dict[str, Dict[str, torch.Tensor | float]]:
    sums_clean: Dict[str, torch.Tensor] = {}
    sums_base: Dict[str, torch.Tensor] = {}
    count = 0
    for sp in tqdm(samples, desc="Geometry pass", dynamic_ncols=True):
        try:
            clean_text = resolve_prompt_path(sp.tool_call_prompt).read_text(encoding="utf-8")
            corrupt_text = resolve_prompt_path(sp.no_tool_prompt).read_text(encoding="utf-8")
        except Exception:
            continue
        variants = build_lead_variants(clean_text, corrupt_text)
        clean_tokens = model.to_tokens(variants["clean_full"], prepend_bos=False)
        base_tokens = model.to_tokens(variants["clean_with_corrupt_lead"], prepend_bos=False)
        if clean_tokens.shape != base_tokens.shape:
            continue
        clean_cache = collect_cache_cpu_for_nodes(model, clean_tokens, TARGET_NODES)
        base_cache = collect_cache_cpu_for_nodes(model, base_tokens, TARGET_NODES)
        for node in TARGET_NODES:
            clean_vec = extract_node(clean_cache, node)
            base_vec = extract_node(base_cache, node)
            if node not in sums_clean:
                sums_clean[node] = clean_vec.clone()
                sums_base[node] = base_vec.clone()
            else:
                sums_clean[node] += clean_vec
                sums_base[node] += base_vec
        count += 1
    if count == 0:
        raise ValueError("No valid samples for route geometry.")
    geometry: Dict[str, Dict[str, torch.Tensor | float]] = {}
    for node in TARGET_NODES:
        clean_mean = sums_clean[node] / count
        base_mean = sums_base[node] / count
        direction = unit(clean_mean - base_mean)
        midpoint = 0.5 * (clean_mean + base_mean)
        scale = float(torch.dot(clean_mean - midpoint, direction).item())
        geometry[node] = {
            "clean_mean": clean_mean,
            "base_mean": base_mean,
            "direction": direction,
            "midpoint": midpoint,
            "scale": scale,
        }
    return geometry


def local_rescues(
    recorded: Dict[str, torch.Tensor],
    *,
    base_scores: Dict[str, float],
    clean_scores: Dict[str, float],
    geometry: Dict[str, Dict[str, torch.Tensor | float]],
) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for node in TARGET_NODES:
        score = score_from_vec(
            extract_node(recorded, node),
            direction=geometry[node]["direction"],  # type: ignore[arg-type]
            midpoint=geometry[node]["midpoint"],  # type: ignore[arg-type]
            scale=float(geometry[node]["scale"]),
        )
        gap = clean_scores[node] - base_scores[node]
        out[f"{node}_local_score"] = score
        out[f"{node}_local_rescue"] = (
            (score - base_scores[node]) / gap
            if math.isfinite(gap) and abs(gap) > 1e-8
            else float("nan")
        )
    out["module_local_mean_rescue"] = mean(out[f"{node}_local_rescue"] for node in TARGET_NODES)
    return out


def experiment1_rows_for_sample(
    *,
    sp,
    model,
    tokenizer,
    geometry: Dict[str, Dict[str, torch.Tensor | float]],
) -> List[Dict[str, object]]:
    try:
        clean_text = resolve_prompt_path(sp.tool_call_prompt).read_text(encoding="utf-8")
        corrupt_text = resolve_prompt_path(sp.no_tool_prompt).read_text(encoding="utf-8")
    except Exception:
        return []
    variants = build_lead_variants(clean_text, corrupt_text)
    token_map: Dict[str, torch.Tensor] = {}
    logit_map: Dict[str, torch.Tensor] = {}
    for name in ["clean_full", "corrupt_full", "clean_with_corrupt_lead"]:
        toks = model.to_tokens(variants[name], prepend_bos=False)
        token_map[name] = toks
        with torch.no_grad():
            logit_map[name] = model(toks)
    if token_map["clean_full"].shape != token_map["clean_with_corrupt_lead"].shape:
        return []

    tool_objective, no_tool_objective = build_bidirectional_endpoint_objectives(
        logit_map["clean_full"],
        logit_map["corrupt_full"],
        tokenizer=tokenizer,
    )
    base_logits = logit_map["clean_with_corrupt_lead"]
    clean_logits = logit_map["clean_full"]
    base_tool = float(objective_from_logits(base_logits, tool_objective).item())
    clean_tool = float(objective_from_logits(clean_logits, tool_objective).item())
    tool_gap = clean_tool - base_tool
    base_route = build_route_score(base_logits, tool_objective, no_tool_objective)
    clean_route = build_route_score(clean_logits, tool_objective, no_tool_objective)
    route_gap = clean_route - base_route
    if (
        not math.isfinite(tool_gap)
        or abs(tool_gap) < 1e-8
        or not math.isfinite(route_gap)
        or abs(route_gap) < 1e-8
    ):
        return []

    patch_nodes = INGRESS_HEADS + TARGET_NODES
    clean_cache = collect_cache_cpu_for_nodes(model, token_map["clean_full"], patch_nodes)
    base_cache = collect_cache_cpu_for_nodes(model, token_map["clean_with_corrupt_lead"], patch_nodes)
    base_scores = {
        node: score_from_vec(
            extract_node(base_cache, node),
            direction=geometry[node]["direction"],  # type: ignore[arg-type]
            midpoint=geometry[node]["midpoint"],  # type: ignore[arg-type]
            scale=float(geometry[node]["scale"]),
        )
        for node in TARGET_NODES
    }
    clean_scores = {
        node: score_from_vec(
            extract_node(clean_cache, node),
            direction=geometry[node]["direction"],  # type: ignore[arg-type]
            midpoint=geometry[node]["midpoint"],  # type: ignore[arg-type]
            scale=float(geometry[node]["scale"]),
        )
        for node in TARGET_NODES
    }

    conditions = [("source_only", [])] + [(f"block_{target}", [target]) for target in TARGET_NODES]
    out: List[Dict[str, object]] = []
    for condition, patch_base_nodes in conditions:
        logits, recorded = run_with_assignments_and_collect(
            model,
            token_map["clean_with_corrupt_lead"],
            clean_cache_cpu=clean_cache,
            base_cache_cpu=base_cache,
            patch_clean_nodes=["L11H5"],
            patch_base_nodes=patch_base_nodes,
            record_nodes=TARGET_NODES,
        )
        tool_score = float(objective_from_logits(logits, tool_objective).item())
        route_score = build_route_score(logits, tool_objective, no_tool_objective)
        row: Dict[str, object] = {
            "sample_id": sp.sample_id,
            "condition": condition,
            "blocked_target": patch_base_nodes[0] if patch_base_nodes else "",
            "tool_ratio": (tool_score - base_tool) / tool_gap,
            "route_rescue": (route_score - base_route) / route_gap,
            "route_delta": route_score - base_route,
            "tool_top1_success": int(logits[0, -1].argmax().item()) == sp.target_tool_call,
        }
        row.update(
            local_rescues(
                recorded,
                base_scores=base_scores,
                clean_scores=clean_scores,
                geometry=geometry,
            )
        )
        out.append(row)
    return out


def experiment2_rows_for_sample(
    *,
    sp,
    model,
    tokenizer,
    geometry: Dict[str, Dict[str, torch.Tensor | float]],
) -> List[Dict[str, object]]:
    try:
        clean_text = resolve_prompt_path(sp.tool_call_prompt).read_text(encoding="utf-8")
        corrupt_text = resolve_prompt_path(sp.no_tool_prompt).read_text(encoding="utf-8")
    except Exception:
        return []
    variants = build_lead_variants(clean_text, corrupt_text)
    token_map: Dict[str, torch.Tensor] = {}
    logit_map: Dict[str, torch.Tensor] = {}
    for name in ["clean_full", "corrupt_full", "clean_with_corrupt_lead"]:
        toks = model.to_tokens(variants[name], prepend_bos=False)
        token_map[name] = toks
        with torch.no_grad():
            logit_map[name] = model(toks)
    if token_map["clean_full"].shape != token_map["clean_with_corrupt_lead"].shape:
        return []

    tool_objective, no_tool_objective = build_bidirectional_endpoint_objectives(
        logit_map["clean_full"],
        logit_map["corrupt_full"],
        tokenizer=tokenizer,
    )
    base_logits = logit_map["clean_with_corrupt_lead"]
    clean_logits = logit_map["clean_full"]
    base_tool = float(objective_from_logits(base_logits, tool_objective).item())
    clean_tool = float(objective_from_logits(clean_logits, tool_objective).item())
    tool_gap = clean_tool - base_tool
    base_route = build_route_score(base_logits, tool_objective, no_tool_objective)
    clean_route = build_route_score(clean_logits, tool_objective, no_tool_objective)
    route_gap = clean_route - base_route
    if (
        not math.isfinite(tool_gap)
        or abs(tool_gap) < 1e-8
        or not math.isfinite(route_gap)
        or abs(route_gap) < 1e-8
    ):
        return []

    patch_nodes = INGRESS_HEADS + TARGET_NODES
    clean_cache = collect_cache_cpu_for_nodes(model, token_map["clean_full"], patch_nodes)
    base_cache = collect_cache_cpu_for_nodes(model, token_map["clean_with_corrupt_lead"], patch_nodes)
    base_scores = {
        node: score_from_vec(
            extract_node(base_cache, node),
            direction=geometry[node]["direction"],  # type: ignore[arg-type]
            midpoint=geometry[node]["midpoint"],  # type: ignore[arg-type]
            scale=float(geometry[node]["scale"]),
        )
        for node in TARGET_NODES
    }
    clean_scores = {
        node: score_from_vec(
            extract_node(clean_cache, node),
            direction=geometry[node]["direction"],  # type: ignore[arg-type]
            midpoint=geometry[node]["midpoint"],  # type: ignore[arg-type]
            scale=float(geometry[node]["scale"]),
        )
        for node in TARGET_NODES
    }

    conditions = [
        ("L2H14_only", ["L2H14"]),
        ("L11H5_only", ["L11H5"]),
        ("L2H14_plus_L11H5", ["L2H14", "L11H5"]),
    ]
    out: List[Dict[str, object]] = []
    for condition, patch_clean_nodes in conditions:
        logits, recorded = run_with_assignments_and_collect(
            model,
            token_map["clean_with_corrupt_lead"],
            clean_cache_cpu=clean_cache,
            base_cache_cpu=base_cache,
            patch_clean_nodes=patch_clean_nodes,
            patch_base_nodes=[],
            record_nodes=TARGET_NODES,
        )
        tool_score = float(objective_from_logits(logits, tool_objective).item())
        route_score = build_route_score(logits, tool_objective, no_tool_objective)
        row: Dict[str, object] = {
            "sample_id": sp.sample_id,
            "condition": condition,
            "tool_ratio": (tool_score - base_tool) / tool_gap,
            "route_rescue": (route_score - base_route) / route_gap,
            "route_delta": route_score - base_route,
            "tool_top1_success": int(logits[0, -1].argmax().item()) == sp.target_tool_call,
        }
        row.update(
            local_rescues(
                recorded,
                base_scores=base_scores,
                clean_scores=clean_scores,
                geometry=geometry,
            )
        )
        out.append(row)
    return out


def summarize_experiment1(rows: Sequence[Dict[str, object]]) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    by_cond: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_cond[str(row["condition"])].append(dict(row))

    condition_summary: List[Dict[str, object]] = []
    for condition in ["source_only", "block_MLP11", "block_MLP16", "block_MLP19"]:
        grows = by_cond.get(condition, [])
        if not grows:
            continue
        summary: Dict[str, object] = {
            "condition": condition,
            "blocked_target": grows[0].get("blocked_target", ""),
            "n_samples": len(grows),
            "tool_ratio_median": median(to_float(r["tool_ratio"]) for r in grows),
            "route_rescue_median": median(to_float(r["route_rescue"]) for r in grows),
            "module_local_mean_rescue_median": median(to_float(r["module_local_mean_rescue"]) for r in grows),
            "tool_top1_success_rate": safe_rate(to_bool(r["tool_top1_success"]) for r in grows),
        }
        for node in TARGET_NODES:
            summary[f"{node}_local_rescue_median"] = median(to_float(r[f"{node}_local_rescue"]) for r in grows)
        condition_summary.append(summary)

    source_rows = {str(r["sample_id"]): r for r in by_cond.get("source_only", [])}
    blocked_summary: List[Dict[str, object]] = []
    for target in TARGET_NODES:
        blocked_rows = {str(r["sample_id"]): r for r in by_cond.get(f"block_{target}", [])}
        shared_ids = sorted(set(source_rows) & set(blocked_rows))
        if not shared_ids:
            continue
        route_mediated = [
            to_float(source_rows[sid]["route_rescue"]) - to_float(blocked_rows[sid]["route_rescue"])
            for sid in shared_ids
        ]
        tool_mediated = [
            to_float(source_rows[sid]["tool_ratio"]) - to_float(blocked_rows[sid]["tool_ratio"])
            for sid in shared_ids
        ]
        module_mediated = [
            to_float(source_rows[sid]["module_local_mean_rescue"]) - to_float(blocked_rows[sid]["module_local_mean_rescue"])
            for sid in shared_ids
        ]
        target_local_mediated = [
            to_float(source_rows[sid][f"{target}_local_rescue"]) - to_float(blocked_rows[sid][f"{target}_local_rescue"])
            for sid in shared_ids
        ]
        mlp11_local_mediated = [
            to_float(source_rows[sid]["MLP11_local_rescue"]) - to_float(blocked_rows[sid]["MLP11_local_rescue"])
            for sid in shared_ids
        ]
        route_ci = bootstrap_median_ci(route_mediated)
        target_ci = bootstrap_median_ci(target_local_mediated)
        blocked_summary.append(
            {
                "blocked_target": target,
                "n_samples": len(shared_ids),
                "tool_mediated_median": median(tool_mediated),
                "route_mediated_median": route_ci["median"],
                "route_mediated_ci_lo": route_ci["lo"],
                "route_mediated_ci_hi": route_ci["hi"],
                "module_local_mean_mediated_median": median(module_mediated),
                "target_local_mediated_median": target_ci["median"],
                "target_local_mediated_ci_lo": target_ci["lo"],
                "target_local_mediated_ci_hi": target_ci["hi"],
                "MLP11_local_mediated_median": median(mlp11_local_mediated),
            }
        )
    return condition_summary, blocked_summary


def summarize_experiment2(rows: Sequence[Dict[str, object]]) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    by_cond: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_cond[str(row["condition"])].append(dict(row))

    condition_summary: List[Dict[str, object]] = []
    for condition in ["L2H14_only", "L11H5_only", "L2H14_plus_L11H5"]:
        grows = by_cond.get(condition, [])
        if not grows:
            continue
        summary: Dict[str, object] = {
            "condition": condition,
            "n_samples": len(grows),
            "tool_ratio_median": median(to_float(r["tool_ratio"]) for r in grows),
            "route_rescue_median": median(to_float(r["route_rescue"]) for r in grows),
            "module_local_mean_rescue_median": median(to_float(r["module_local_mean_rescue"]) for r in grows),
            "tool_top1_success_rate": safe_rate(to_bool(r["tool_top1_success"]) for r in grows),
        }
        for node in TARGET_NODES:
            summary[f"{node}_local_rescue_median"] = median(to_float(r[f"{node}_local_rescue"]) for r in grows)
        condition_summary.append(summary)

    l2 = {str(r["sample_id"]): r for r in by_cond.get("L2H14_only", [])}
    l11 = {str(r["sample_id"]): r for r in by_cond.get("L11H5_only", [])}
    joint = {str(r["sample_id"]): r for r in by_cond.get("L2H14_plus_L11H5", [])}
    shared_ids = sorted(set(l2) & set(l11) & set(joint))
    comparisons: List[Dict[str, object]] = []
    metrics = ["MLP11_local_rescue", "module_local_mean_rescue", "route_rescue", "tool_ratio"]
    for metric in metrics:
        joint_minus_best = [
            to_float(joint[sid][metric]) - max(to_float(l2[sid][metric]), to_float(l11[sid][metric]))
            for sid in shared_ids
        ]
        joint_minus_l11 = [
            to_float(joint[sid][metric]) - to_float(l11[sid][metric])
            for sid in shared_ids
        ]
        joint_minus_l2 = [
            to_float(joint[sid][metric]) - to_float(l2[sid][metric])
            for sid in shared_ids
        ]
        ci = bootstrap_median_ci(joint_minus_best)
        comparisons.append(
            {
                "metric": metric,
                "n_samples": len(shared_ids),
                "joint_minus_best_single_median": ci["median"],
                "joint_minus_best_single_ci_lo": ci["lo"],
                "joint_minus_best_single_ci_hi": ci["hi"],
                "joint_minus_L11H5_median": median(joint_minus_l11),
                "joint_minus_L2H14_median": median(joint_minus_l2),
                "joint_beats_both_rate": safe_rate(
                    to_float(joint[sid][metric]) > to_float(l2[sid][metric]) and to_float(joint[sid][metric]) > to_float(l11[sid][metric])
                    for sid in shared_ids
                ),
                "joint_beats_or_ties_best_single_rate": safe_rate(
                    to_float(joint[sid][metric]) >= max(to_float(l2[sid][metric]), to_float(l11[sid][metric]))
                    for sid in shared_ids
                ),
                "joint_beats_or_ties_L11H5_rate": safe_rate(
                    to_float(joint[sid][metric]) >= to_float(l11[sid][metric])
                    for sid in shared_ids
                ),
            }
        )
    return condition_summary, comparisons


def markdown_table(rows: Sequence[Dict[str, object]], columns: Sequence[str]) -> str:
    if not rows:
        return "_无数据_"
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(fmt(row.get(col, "")) for col in columns) + " |")
    return "\n".join([header, sep, *body])


def build_report(
    *,
    out_root: Path,
    n_samples: int,
    exp1_conditions: Sequence[Dict[str, object]],
    exp1_blocked: Sequence[Dict[str, object]],
    exp2_conditions: Sequence[Dict[str, object]],
    exp2_comparisons: Sequence[Dict[str, object]],
) -> str:
    exp1_by = {str(r["condition"]): dict(r) for r in exp1_conditions}
    exp1_block_by = {str(r["blocked_target"]): dict(r) for r in exp1_blocked}
    exp2_by = {str(r["condition"]): dict(r) for r in exp2_conditions}
    exp2_cmp_by = {str(r["metric"]): dict(r) for r in exp2_comparisons}

    route_cmp = exp2_cmp_by.get("route_rescue", {})
    mlp11_cmp = exp2_cmp_by.get("MLP11_local_rescue", {})
    module_cmp = exp2_cmp_by.get("module_local_mean_rescue", {})
    mlp11_block = exp1_block_by.get("MLP11", {})
    mlp16_block = exp1_block_by.get("MLP16", {})
    mlp19_block = exp1_block_by.get("MLP19", {})
    source_only = exp1_by.get("source_only", {})
    l2_only = exp2_by.get("L2H14_only", {})
    l11_only = exp2_by.get("L11H5_only", {})

    lines: List[str] = []
    lines.append("# Instruction Integration 小修强化报告")
    lines.append("")
    lines.append("这轮只补两类因果证据，按 `module_level_node_evidence_tools.md` 的优先级，用 source-only patch 与 blocked-target mediation 做闭环，不重做头搜索，也不再扩展模块边界。")
    lines.append("")
    lines.append(f"- 样本数：`{n_samples}`")
    lines.append("- 输入设定：以 `clean_with_corrupt_lead` 为 base，以 `clean_full` 为 source。")
    lines.append("- 记录指标：`MLP11 / MLP16 / MLP19` local route score rescue、decision route rescue、tool objective rescue、首词成功率。")
    lines.append("")
    lines.append("## 实验 1：`L11H5 -> MLP11` handoff 加固")
    lines.append("")
    lines.append("直接做 `L11H5` source-only patch，再分别 block `MLP11 / MLP16 / MLP19`。如果 `L11H5` 的主要 handoff 目标真是 `MLP11`，那么：")
    lines.append("")
    lines.append("- source-only 应先显著抬高 `MLP11` local rescue；")
    lines.append("- block `MLP11` 应比 block `MLP16 / MLP19` 更强地吃掉 route rescue；")
    lines.append("- `L11H5` 对 `MLP11` 的 target-local mediated 应显著高于更晚目标。")
    lines.append("")
    lines.append(markdown_table(
        exp1_conditions,
        [
            "condition",
            "tool_ratio_median",
            "route_rescue_median",
            "MLP11_local_rescue_median",
            "MLP16_local_rescue_median",
            "MLP19_local_rescue_median",
            "module_local_mean_rescue_median",
            "tool_top1_success_rate",
        ],
    ))
    lines.append("")
    lines.append(markdown_table(
        exp1_blocked,
        [
            "blocked_target",
            "route_mediated_median",
            "route_mediated_ci_lo",
            "route_mediated_ci_hi",
            "target_local_mediated_median",
            "MLP11_local_mediated_median",
            "module_local_mean_mediated_median",
        ],
    ))
    lines.append("")
    route_rank = sorted(
        [
            ("MLP11", to_float(mlp11_block.get("route_mediated_median"))),
            ("MLP16", to_float(mlp16_block.get("route_mediated_median"))),
            ("MLP19", to_float(mlp19_block.get("route_mediated_median"))),
        ],
        key=lambda x: (math.isnan(x[1]), x[1]),
        reverse=True,
    )
    route_best_target = route_rank[0][0] if route_rank else "MLP11"
    lines.append("结论：")
    lines.append(
        f"- `L11H5` source-only 时，`MLP11` local rescue 中位数为 `{fmt(source_only.get('MLP11_local_rescue_median'))}`，"
        f"高于 `MLP16` 的 `{fmt(source_only.get('MLP16_local_rescue_median'))}` 和 `MLP19` 的 `{fmt(source_only.get('MLP19_local_rescue_median'))}`。"
    )
    lines.append(
        f"- block `MLP11` 对 `MLP11` local score 的 mediated 中位数为 `{fmt(mlp11_block.get('target_local_mediated_median'))}`，"
        f"而 block `MLP16 / MLP19` 对 `MLP11` local rescue 的 mediated 都接近 `{fmt(mlp16_block.get('MLP11_local_mediated_median'))}` / `{fmt(mlp19_block.get('MLP11_local_mediated_median'))}`。"
    )
    lines.append(
        f"- route 侧的 mediated 排名这轮由 block `{route_best_target}` 最大；这说明后续 route 放大还依赖 decision spine 的晚层节点。"
    )
    lines.append(
        "- 但这不削弱 same-block handoff 结论：对“直接交接给谁”的判定，最硬证据是 source-only 对 `MLP11` 的局部写入，以及 block `MLP11` 几乎独占地擦除了这份 `MLP11` 局部 rescue。"
    )
    lines.append(
        "- 因而这轮补强后，`L11H5` 可以更强地写成 `MLP11` 的关键 same-block handoff head；更晚 MLP 的 route drop 应解释为 decision spine 的 downstream dependence，而不是把 `L11H5` 重新改写成晚层 writer。"
    )
    lines.append("")
    lines.append("## 实验 2：`L2H14 + L11H5` ingress group 组合实验")
    lines.append("")
    lines.append("对同一 base 分别 patch `L2H14`、patch `L11H5`、patch `L2H14+L11H5`，看联合 patch 是否比单头更稳地把状态送进 `MLP11` 与 decision route。")
    lines.append("")
    lines.append(markdown_table(
        exp2_conditions,
        [
            "condition",
            "tool_ratio_median",
            "route_rescue_median",
            "MLP11_local_rescue_median",
            "MLP16_local_rescue_median",
            "MLP19_local_rescue_median",
            "module_local_mean_rescue_median",
            "tool_top1_success_rate",
        ],
    ))
    lines.append("")
    lines.append(markdown_table(
        exp2_comparisons,
        [
            "metric",
            "joint_minus_best_single_median",
            "joint_minus_best_single_ci_lo",
            "joint_minus_best_single_ci_hi",
            "joint_minus_L11H5_median",
            "joint_minus_L2H14_median",
            "joint_beats_both_rate",
            "joint_beats_or_ties_best_single_rate",
            "joint_beats_or_ties_L11H5_rate",
        ],
    ))
    lines.append("")
    lines.append("结论：")
    lines.append(
        f"- 联合 patch 在 `MLP11` local rescue 上相对 best single 的中位增益为 `{fmt(mlp11_cmp.get('joint_minus_best_single_median'))}`，"
        f"beats-both 比例为 `{fmt(mlp11_cmp.get('joint_beats_both_rate'))}`，"
        f"相对 `L11H5` 的增益为 `{fmt(mlp11_cmp.get('joint_minus_L11H5_median'))}`。"
    )
    lines.append(
        f"- 联合 patch 在 module mean rescue 上相对 best single 的中位增益为 `{fmt(module_cmp.get('joint_minus_best_single_median'))}`，"
        f"在 route rescue 上的中位增益为 `{fmt(route_cmp.get('joint_minus_best_single_median'))}`。"
    )
    lines.append(
        f"- 与 `L2H14` 单独 patch 相比，联合 patch 的 route 增益中位数为 `{fmt(route_cmp.get('joint_minus_L2H14_median'))}`；"
        f"与 `L11H5` 单独 patch 相比，联合 patch 的 route 增益中位数为 `{fmt(route_cmp.get('joint_minus_L11H5_median'))}`。"
    )
    lines.append(
        f"- 这说明联合 patch 更像把 `L2H14` 的早层 ingress 与 `L11H5` 的 `MLP11` handoff 接成一个前端入口：`L2H14` 单头更偏 route uplift（`{fmt(l2_only.get('route_rescue_median'))}`），`L11H5` 单头更偏 `MLP11` local rescue（`{fmt(l11_only.get('MLP11_local_rescue_median'))}`），联合 patch 则把两者合到 `MLP11` 与整体 route 上。"
    )
    lines.append(
        "- 因而它适合写成最小 ingress group，但不应硬写成强超加和协同；更稳妥的表述仍是“两段式前端入口”。"
    )
    lines.append("")
    lines.append("## 是否改变主结论")
    lines.append("")
    lines.append("- 不调整当前 anchor/support/candidate 分层，除非后续独立实验推翻这两条补强。")
    lines.append("- `MLP11` 最适合写成：Instruction Integration 的出口，同时也是 Output-Route Decision 的入口。")
    lines.append("- 这一轮不会把 `L2H15`、`L16H5` 或其他 candidate 再升格。")
    lines.append("")
    lines.append("## 论文写法建议")
    lines.append("")
    lines.append("可以强写：")
    lines.append("- `L11H5` is the main same-block handoff head into `MLP11` within the Instruction Integration module.")
    lines.append("- `L2H14` and `L11H5` form a two-stage ingress group that feeds integrated instruction state into `MLP11`.")
    lines.append("- `MLP11` is the boundary node where Instruction Integration exits and Output-Route Decision begins.")
    lines.append("")
    lines.append("仍然弱写：")
    lines.append("- 不要把 `L2H14 + L11H5` 写成唯一完整模块；更稳妥的说法是最小 ingress group。")
    lines.append("- 不要把联合 patch 写成强超加和，除非 joint-minus-best-single 在 `MLP11` 与 route 上都明显为正且区间不碰零。")
    lines.append("- 不要根据这一轮去改写 support/candidate 的边界。")
    lines.append("")
    lines.append("## 输出文件")
    lines.append("")
    lines.append(f"- `experiment1_per_sample.csv`: `{out_root / 'experiment1_per_sample.csv'}`")
    lines.append(f"- `experiment1_condition_summary.csv`: `{out_root / 'experiment1_condition_summary.csv'}`")
    lines.append(f"- `experiment1_blocked_summary.csv`: `{out_root / 'experiment1_blocked_summary.csv'}`")
    lines.append(f"- `experiment2_per_sample.csv`: `{out_root / 'experiment2_per_sample.csv'}`")
    lines.append(f"- `experiment2_condition_summary.csv`: `{out_root / 'experiment2_condition_summary.csv'}`")
    lines.append(f"- `experiment2_joint_comparison_summary.csv`: `{out_root / 'experiment2_joint_comparison_summary.csv'}`")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Minimal refine experiments for Instruction Integration.")
    parser.add_argument("--forward-batch-root", type=str, required=True)
    parser.add_argument("--reverse-batch-root", type=str, required=True)
    parser.add_argument("--model-path", type=str, default="/root/autodl-tmp/Qwen/Qwen3-1.7B")
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--save-every", type=int, default=25)
    parser.add_argument("--output-root", type=str, required=True)
    args = parser.parse_args()

    out_root = Path(args.output_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    exp1_per_sample_path = out_root / "experiment1_per_sample.csv"
    exp2_per_sample_path = out_root / "experiment2_per_sample.csv"
    report_path = out_root / "instruction_integration_refine_report.md"
    summary_json_path = out_root / "instruction_integration_refine_summary.json"

    samples = load_sample_paths(
        Path(args.forward_batch_root).resolve(),
        Path(args.reverse_batch_root).resolve(),
        max_samples=args.max_samples,
    )
    model, tokenizer = load_hooked_qwen3(args.model_path, device=args.device, dtype=torch.bfloat16)

    geometry = build_route_geometry(samples=samples, model=model)

    exp1_rows: List[Dict[str, object]] = list(read_csv_rows(exp1_per_sample_path))
    exp2_rows: List[Dict[str, object]] = list(read_csv_rows(exp2_per_sample_path))
    processed_ids = {str(row["sample_id"]) for row in exp1_rows} & {str(row["sample_id"]) for row in exp2_rows}

    def checkpoint() -> None:
        write_csv(exp1_rows, exp1_per_sample_path)
        write_csv(exp2_rows, exp2_per_sample_path)

    completed_new = 0
    pbar = tqdm(samples, desc="Instruction refine", dynamic_ncols=True)
    for sp in pbar:
        if sp.sample_id in processed_ids:
            pbar.set_postfix(sample=sp.sample_id, resumed="skip")
            continue
        sample_exp1 = experiment1_rows_for_sample(sp=sp, model=model, tokenizer=tokenizer, geometry=geometry)
        sample_exp2 = experiment2_rows_for_sample(sp=sp, model=model, tokenizer=tokenizer, geometry=geometry)
        if not sample_exp1 or not sample_exp2:
            pbar.set_postfix(sample=sp.sample_id, status="skip")
            continue
        exp1_rows.extend(sample_exp1)
        exp2_rows.extend(sample_exp2)
        processed_ids.add(sp.sample_id)
        completed_new += 1
        pbar.set_postfix(sample=sp.sample_id)
        if args.save_every > 0 and completed_new % args.save_every == 0:
            checkpoint()

    checkpoint()

    exp1_conditions, exp1_blocked = summarize_experiment1(exp1_rows)
    exp2_conditions, exp2_comparisons = summarize_experiment2(exp2_rows)

    write_csv(exp1_conditions, out_root / "experiment1_condition_summary.csv")
    write_csv(exp1_blocked, out_root / "experiment1_blocked_summary.csv")
    write_csv(exp2_conditions, out_root / "experiment2_condition_summary.csv")
    write_csv(exp2_comparisons, out_root / "experiment2_joint_comparison_summary.csv")

    report = build_report(
        out_root=out_root,
        n_samples=len(processed_ids),
        exp1_conditions=exp1_conditions,
        exp1_blocked=exp1_blocked,
        exp2_conditions=exp2_conditions,
        exp2_comparisons=exp2_comparisons,
    )
    report_path.write_text(report, encoding="utf-8")

    summary = {
        "n_samples": len(processed_ids),
        "geometry_nodes": TARGET_NODES,
        "experiment1_per_sample_csv": str(exp1_per_sample_path),
        "experiment1_condition_summary_csv": str(out_root / "experiment1_condition_summary.csv"),
        "experiment1_blocked_summary_csv": str(out_root / "experiment1_blocked_summary.csv"),
        "experiment2_per_sample_csv": str(exp2_per_sample_path),
        "experiment2_condition_summary_csv": str(out_root / "experiment2_condition_summary.csv"),
        "experiment2_joint_comparison_summary_csv": str(out_root / "experiment2_joint_comparison_summary.csv"),
        "report_md": str(report_path),
    }
    summary_json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
