#!/usr/bin/env python3
"""
Reverse-direction circuit mining for the no-tool decision.

This leaves the canonical dataset unchanged:
- canonical clean prompt: tool-call prompt
- canonical corrupt prompt: no-tool prompt

For the reverse experiment we swap roles at runtime:
- reverse clean prompt: canonical no-tool prompt
- reverse corrupt prompt: canonical tool-call prompt

The reverse target token is the top non-`<tool_call>` token on the no-tool prompt.
This now uses the same distributional objective as the forward run:
  reverse objective = -KL(p_no_tool_endpoint || q_current)
"""

from __future__ import annotations

import argparse
import gc
import inspect
import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import torch

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from toolcall_circuit.dataset import (
    ToolCallSample,
    build_position_sets,
    decode_token_at,
    get_tool_call_target_spec,
    load_toolcall_samples,
    resolve_distractor_token,
    select_samples,
)
from toolcall_circuit.graph_utils import (
    DEFAULT_OUTPUT_NODE,
    INPUT_NODE,
    apply_plot_style,
    draw_circuit_with_output,
    remap_output_node,
)
from toolcall_circuit.objective import build_distribution_objective, summarize_endpoint_pair
from toolcall_circuit.paths import DATASETS_ROOT, MODEL_PATH_DEFAULT, RESULTS_ROOT
from toolcall_circuit.single_sample import (
    assert_no_dead_ends,
    build_edges,
    collect_clean_cache_cpu,
    compute_ap_head_gain,
    compute_ap_head_gain_lowmem,
    compute_ct_head_gain,
    compute_mlp_gain,
    evaluate_on_base_with_source,
    load_hooked_qwen3,
    objective_from_logits,
    pick_nodes,
    select_ct_candidate_heads,
)

REVERSE_OUTPUT_NODE = "Residual Output: no_tool"


def single_token_spec(tokenizer, token_id: int) -> Dict[str, object]:
    token_id = int(token_id)
    token_text = tokenizer.decode([token_id])
    return {
        "text": token_text,
        "token_ids": [token_id],
        "tokens": tokenizer.convert_ids_to_tokens([token_id]),
        "length": 1,
        "is_single_token": True,
    }


def plot_head_heatmap_generic(
    data: np.ndarray,
    title: str,
    out_path: Path,
    *,
    cbar_label: str,
) -> None:
    apply_plot_style()
    clip = float(np.percentile(np.abs(data), 98))
    clip = max(clip, 1e-6)
    fig, ax = plt.subplots(figsize=(10.5, 6.2), constrained_layout=True)
    im = ax.imshow(data, cmap="RdBu_r", vmin=-clip, vmax=clip, aspect="auto", origin="lower")
    ax.set_title(f"{title}\nSymmetric clipping at +/-{clip:.3f}")
    ax.set_xlabel("Head")
    ax.set_ylabel("Layer")
    ax.set_xticks(np.arange(data.shape[1]))
    ax.set_yticks(np.arange(data.shape[0]))
    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label(cbar_label)
    fig.savefig(out_path, dpi=260, bbox_inches="tight")
    plt.close(fig)


def plot_probe_generic(
    out_path: Path,
    component_name: str,
    corrupt_obj: float,
    corrupt_with_component: float,
    clean_obj: float,
    clean_with_component_corrupt: float,
    *,
    title: str,
    ylabel: str,
) -> None:
    labels = [
        "Reverse corrupt baseline",
        f"Reverse corrupt + {component_name}(clean)",
        "Reverse clean baseline",
        f"Reverse clean + {component_name}(corrupt)",
    ]
    vals = [corrupt_obj, corrupt_with_component, clean_obj, clean_with_component_corrupt]
    colors = ["#b35d5d", "#4f81bd", "#5a9f6f", "#c08a4f"]

    apply_plot_style()
    plt.rcParams.update({"axes.titlesize": 15})
    fig, ax = plt.subplots(figsize=(9.6, 5.4), constrained_layout=True)
    bars = ax.bar(np.arange(len(vals)), vals, color=colors, edgecolor="black", linewidth=1.1)
    ax.axhline(0.0, color="black", linewidth=1.0)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xticks(np.arange(len(vals)))
    ax.set_xticklabels(labels, rotation=14, ha="right")
    for bar, val in zip(bars, vals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + (0.08 if val >= 0 else -0.08),
            f"{val:.2f}",
            ha="center",
            va="bottom" if val >= 0 else "top",
        )
    fig.savefig(out_path, dpi=260, bbox_inches="tight")
    plt.close(fig)


def resolve_reverse_sample(
    *,
    dataset_root: str,
    pair_dir: str,
    sample_id: str,
    sample_rank: int,
    q_index: int,
) -> ToolCallSample:
    use_pair = q_index > 0 and not sample_id and sample_rank <= 0
    if use_pair:
        samples = load_toolcall_samples(pair_dir=Path(pair_dir))
        chosen = select_samples(samples, legacy_indices=[q_index])
        if not chosen:
            raise ValueError(f"Could not resolve q_index={q_index} under {pair_dir}")
        return chosen[0]

    samples = load_toolcall_samples(dataset_root=Path(dataset_root))
    chosen = select_samples(
        samples,
        sample_ids=[sample_id] if sample_id else (),
        sample_rank_min=sample_rank if sample_rank > 0 else 1,
        sample_rank_max=sample_rank if sample_rank > 0 else 1,
    )
    if not chosen:
        sample_ref = sample_id or f"sample_rank={sample_rank if sample_rank > 0 else 1}"
        raise ValueError(f"Could not resolve {sample_ref} under {dataset_root}")
    return chosen[0]


def run_one_sample_reverse(
    *,
    sample: ToolCallSample,
    out_dir: Path,
    model,
    tokenizer,
    model_path: str,
    ct_head_mode: str = "exact",
    skip_plots: bool = False,
) -> Dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)

    tool_text = sample.clean_path.read_text(encoding="utf-8")
    no_tool_text = sample.corrupt_path.read_text(encoding="utf-8")

    clean_text = no_tool_text
    corrupt_text = tool_text
    clean_prompt_path = sample.corrupt_path
    corrupt_prompt_path = sample.clean_path

    clean_tokens = model.to_tokens(clean_text, prepend_bos=False)
    corrupt_tokens = model.to_tokens(corrupt_text, prepend_bos=False)
    if clean_tokens.shape != corrupt_tokens.shape:
        raise ValueError(f"Reverse clean/corrupt token shapes differ: {clean_tokens.shape} vs {corrupt_tokens.shape}")

    ids_clean = [int(x) for x in clean_tokens[0].tolist()]
    ids_corrupt = [int(x) for x in corrupt_tokens[0].tolist()]
    pos_sets = build_position_sets(ids_clean, ids_corrupt, tokenizer, clean_text=clean_text)

    with torch.no_grad():
        clean_logits = model(clean_tokens)
        corrupt_logits = model(corrupt_tokens)

    tool_spec = get_tool_call_target_spec(tokenizer, target_text="<tool_call>")
    if not tool_spec.is_single_token:
        raise NotImplementedError(
            f"<tool_call> tokenization is no longer single-token ({tool_spec.token_ids}); "
            "upgrade the reverse objective before running this workflow."
        )
    tool_token = tool_spec.primary_token_id
    reverse_target_token = resolve_distractor_token(clean_logits[0, -1, :], tool_token)

    endpoint_temperature = 1.0
    endpoint_masked_token_ids: tuple[int, ...] = ()
    endpoint_objective = build_distribution_objective(
        clean_logits,
        endpoint_label="no_tool",
        tokenizer=tokenizer,
        temperature=endpoint_temperature,
        masked_token_ids=endpoint_masked_token_ids,
    )
    endpoint_summary = summarize_endpoint_pair(
        tool_logits=corrupt_logits,
        no_tool_logits=clean_logits,
        tokenizer=tokenizer,
        temperature=endpoint_temperature,
        masked_token_ids=endpoint_masked_token_ids,
        topk=12,
    )

    clean_obj = float(objective_from_logits(clean_logits, endpoint_objective).item())
    corrupt_obj = float(objective_from_logits(corrupt_logits, endpoint_objective).item())
    gap = clean_obj - corrupt_obj
    if not math.isfinite(gap) or abs(gap) <= 1e-8:
        raise ValueError(f"Reverse gap is degenerate for {sample.sample_id}: {gap}")

    clean_cache_cpu = collect_clean_cache_cpu(model, clean_tokens)

    ap_mode = "full"
    try:
        ap_head = compute_ap_head_gain(
            model=model,
            corrupt_tokens=corrupt_tokens,
            clean_cache_cpu=clean_cache_cpu,
            target_token=endpoint_objective,
            distractor_token=None,
        )
    except torch.OutOfMemoryError:
        gc.collect()
        torch.cuda.empty_cache()
        ap_mode = "lowmem"
        try:
            ap_head = compute_ap_head_gain_lowmem(
                model=model,
                corrupt_tokens=corrupt_tokens,
                clean_cache_cpu=clean_cache_cpu,
                target_token=endpoint_objective,
                distractor_token=None,
            )
        except torch.OutOfMemoryError:
            gc.collect()
            torch.cuda.empty_cache()
            ap_mode = "zero_fallback"
            ap_head = torch.zeros(model.cfg.n_layers, model.cfg.n_heads, dtype=torch.float32)
    model.reset_hooks()

    ct_ap_top_per_layer = max(
        0,
        int(os.environ.get("TOOLCALL_CT_AP_PER_LAYER", os.environ.get("ACDC_CT_AP_PER_LAYER", "0"))),
    )
    ct_ap_top_global = max(
        0,
        int(os.environ.get("TOOLCALL_CT_AP_TOP_GLOBAL", os.environ.get("ACDC_CT_AP_TOP_GLOBAL", "0"))),
    )
    ct_candidate_heads = None
    ct_mode = "exact"
    if ap_mode != "zero_fallback":
        ct_candidate_heads = select_ct_candidate_heads(
            ap_head,
            ap_top_per_layer=ct_ap_top_per_layer,
            ap_top_global=ct_ap_top_global,
        )
        if ct_candidate_heads:
            ct_mode = "ap_pruned_exact_ct"
    if ct_head_mode == "ap_proxy":
        ct_head = ap_head.detach().float().cpu().clone()
        ct_mode = "ap_proxy"
    else:
        ct_head = compute_ct_head_gain(
            model=model,
            corrupt_tokens=corrupt_tokens,
            clean_cache_cpu=clean_cache_cpu,
            target_token=endpoint_objective,
            distractor_token=None,
            corrupt_obj=corrupt_obj,
            candidate_heads_by_layer=ct_candidate_heads,
            fallback_scores=ap_head if ct_candidate_heads else None,
        )

    mlp_gain = compute_mlp_gain(
        model=model,
        corrupt_tokens=corrupt_tokens,
        clean_cache_cpu=clean_cache_cpu,
        target_token=endpoint_objective,
        distractor_token=None,
        corrupt_obj=corrupt_obj,
    )

    detailed_nodes, rough_nodes, score_table = pick_nodes(ct_head, ap_head, mlp_gain)
    score_lookup = {s.name: s.score for s in score_table}
    detailed_edges_raw = build_edges(detailed_nodes, score_lookup=score_lookup, max_parents=2)
    rough_edges_raw = build_edges(rough_nodes, score_lookup=score_lookup, max_parents=2)
    assert_no_dead_ends(detailed_nodes, detailed_edges_raw)
    assert_no_dead_ends(rough_nodes, rough_edges_raw)

    detailed_obj = evaluate_on_base_with_source(
        model=model,
        base_tokens=corrupt_tokens,
        source_cache_cpu=clean_cache_cpu,
        patch_nodes=detailed_nodes,
        target_token=endpoint_objective,
        distractor_token=None,
    )
    detailed_ratio = (detailed_obj - corrupt_obj) / gap

    rough_obj = evaluate_on_base_with_source(
        model=model,
        base_tokens=corrupt_tokens,
        source_cache_cpu=clean_cache_cpu,
        patch_nodes=rough_nodes,
        target_token=endpoint_objective,
        distractor_token=None,
    )
    rough_ratio = (rough_obj - corrupt_obj) / gap

    corrupt_cache_cpu = collect_clean_cache_cpu(model, corrupt_tokens)
    clean_with_detailed_corrupted = evaluate_on_base_with_source(
        model=model,
        base_tokens=clean_tokens,
        source_cache_cpu=corrupt_cache_cpu,
        patch_nodes=detailed_nodes,
        target_token=endpoint_objective,
        distractor_token=None,
    )
    necessity_drop = clean_obj - clean_with_detailed_corrupted
    necessity_ratio = necessity_drop / gap

    clean_with_rough_corrupted = evaluate_on_base_with_source(
        model=model,
        base_tokens=clean_tokens,
        source_cache_cpu=corrupt_cache_cpu,
        patch_nodes=rough_nodes,
        target_token=endpoint_objective,
        distractor_token=None,
    )
    rough_necessity_drop = clean_obj - clean_with_rough_corrupted
    rough_necessity_ratio = rough_necessity_drop / gap

    head_scores = [s for s in score_table if s.name.startswith("L")]
    probe_head = head_scores[0].name if head_scores else "L0H0"
    if skip_plots:
        corrupt_with_probe = float("nan")
        clean_with_probe_corrupt = float("nan")
    else:
        corrupt_with_probe = evaluate_on_base_with_source(
            model=model,
            base_tokens=corrupt_tokens,
            source_cache_cpu=clean_cache_cpu,
            patch_nodes=[probe_head],
            target_token=endpoint_objective,
            distractor_token=None,
        )
        clean_with_probe_corrupt = evaluate_on_base_with_source(
            model=model,
            base_tokens=clean_tokens,
            source_cache_cpu=corrupt_cache_cpu,
            patch_nodes=[probe_head],
            target_token=endpoint_objective,
            distractor_token=None,
        )

    detailed_edges = remap_output_node(detailed_edges_raw, target_output=REVERSE_OUTPUT_NODE)
    rough_edges = remap_output_node(rough_edges_raw, target_output=REVERSE_OUTPUT_NODE)

    if not skip_plots:
        plot_head_heatmap_generic(
            ap_head.numpy(),
            "Reverse Attribution Patching Head Heatmap (No-tool Endpoint)",
            out_dir / "ap_head_heatmap.png",
            cbar_label="Contribution (positive = supports the no-tool endpoint)",
        )
        plot_head_heatmap_generic(
            ct_head.numpy(),
            "Reverse Causal Tracing Head Heatmap (No-tool Endpoint)",
            out_dir / "ct_head_heatmap.png",
            cbar_label="Contribution (positive = supports the no-tool endpoint)",
        )
        plot_probe_generic(
            out_path=out_dir / f"{probe_head}_probe.png",
            component_name=probe_head,
            corrupt_obj=corrupt_obj,
            corrupt_with_component=corrupt_with_probe,
            clean_obj=clean_obj,
            clean_with_component_corrupt=clean_with_probe_corrupt,
            title=f"Reverse Component Probe: {probe_head}",
            ylabel="Endpoint score",
        )
        draw_circuit_with_output(
            nodes=detailed_nodes,
            edges=detailed_edges,
            out_path=out_dir / "final_circuit_detailed.png",
            title="Detailed Circuit (No-tool Decision)",
            input_node=INPUT_NODE,
            output_node=REVERSE_OUTPUT_NODE,
        )
        draw_circuit_with_output(
            nodes=rough_nodes,
            edges=rough_edges,
            out_path=out_dir / "final_circuit.png",
            title="Simplified Circuit (No-tool Decision)",
            input_node=INPUT_NODE,
            output_node=REVERSE_OUTPUT_NODE,
        )

    contrast_token_details = [
        {
            "position": int(pos),
            "clean_token": decode_token_at(tokenizer, ids_clean, int(pos)),
            "corrupt_token": decode_token_at(tokenizer, ids_corrupt, int(pos)),
        }
        for pos in pos_sets["contrast"]
    ]

    summary: Dict[str, object] = {
        "sample_id": sample.sample_id,
        "sample_rank": sample.sample_rank,
        "filename": sample.filename,
        "source_kind": sample.source_kind,
        "q_index": sample.legacy_index,
        "direction": "reverse_no_tool",
        "decision_label": "no_tool_vs_tool_call",
        "output_node_label": REVERSE_OUTPUT_NODE,
        "clean_role": "no_tool",
        "corrupt_role": "tool_call",
        "canonical_tool_prompt": str(sample.clean_path),
        "canonical_no_tool_prompt": str(sample.corrupt_path),
        "clean_prompt": str(clean_prompt_path),
        "corrupt_prompt": str(corrupt_prompt_path),
        "model_path": model_path,
        "clean_prompt_token_length": int(clean_tokens.shape[1]),
        "corrupt_prompt_token_length": int(corrupt_tokens.shape[1]),
        "token_lengths_aligned": bool(clean_tokens.shape == corrupt_tokens.shape),
        "target_tokenization": single_token_spec(tokenizer, reverse_target_token),
        "target_token_id": int(reverse_target_token),
        "target_token_str": tokenizer.decode([int(reverse_target_token)]),
        "distractor_token_id": int(tool_token),
        "distractor_token_str": tokenizer.decode([int(tool_token)]),
        "tool_call_tokenization": tool_spec.to_dict(tokenizer),
        "ap_mode": ap_mode,
        "ct_mode": ct_mode,
        "ct_head_mode_requested": ct_head_mode,
        "skip_plots": skip_plots,
        "objective_mode": "negative_kl_to_clean_endpoint",
        "objective_endpoint": "no_tool",
        "objective_temperature": endpoint_temperature,
        "objective_masked_token_ids": list(endpoint_masked_token_ids),
        "ct_candidate_ap_top_per_layer": ct_ap_top_per_layer,
        "ct_candidate_ap_top_global": ct_ap_top_global,
        "ct_candidate_head_count": sum(len(v) for v in ct_candidate_heads.values()) if ct_candidate_heads else 0,
        "clean_obj": clean_obj,
        "corrupt_obj": corrupt_obj,
        "gap": gap,
        "clean_kl_to_endpoint": -clean_obj,
        "corrupt_kl_to_endpoint": -corrupt_obj,
        "endpoint_js_divergence": endpoint_summary["endpoint_js_divergence"],
        "detailed_obj": detailed_obj,
        "detailed_ratio_vs_gap": detailed_ratio,
        "detailed_kl_recovery_ratio": detailed_ratio,
        "rough_obj": rough_obj,
        "rough_ratio_vs_gap": rough_ratio,
        "rough_kl_recovery_ratio": rough_ratio,
        "clean_with_detailed_corrupted": clean_with_detailed_corrupted,
        "necessity_drop": necessity_drop,
        "necessity_ratio_vs_gap": necessity_ratio,
        "necessity_kl_drop_ratio": necessity_ratio,
        "clean_with_rough_corrupted": clean_with_rough_corrupted,
        "rough_necessity_drop": rough_necessity_drop,
        "rough_necessity_ratio_vs_gap": rough_necessity_ratio,
        "rough_necessity_kl_drop_ratio": rough_necessity_ratio,
        "probe_head": probe_head,
        "probe_corrupt_with_head": corrupt_with_probe,
        "probe_clean_with_head_corrupt": clean_with_probe_corrupt,
        "detailed_nodes": detailed_nodes,
        "detailed_edges": detailed_edges,
        "rough_nodes": rough_nodes,
        "rough_edges": rough_edges,
        "contrast_positions": list(pos_sets["contrast"]),
        "contrast_spans": list(pos_sets["contrast_spans"]),
        "contrast_token_details": contrast_token_details,
        "tool_call_open_positions": list(pos_sets["tool_call_open"]),
        "tool_call_close_positions": list(pos_sets["tool_call_close"]),
        "tool_call_tag_positions": list(pos_sets["tool_call_tags"]),
        "tools_block_positions": list(pos_sets["tools_block"]),
        "user_block_positions": list(pos_sets["user_block"]),
        "sample_catalog_record": sample.catalog_record(),
        "endpoint_distribution_summary": endpoint_summary,
        "top_node_scores": [
            {"name": s.name, "score": s.score, "ct": s.ct, "ap": s.ap}
            for s in score_table
        ],
        "artifacts": {
            "ap_head_heatmap": str(out_dir / "ap_head_heatmap.png") if not skip_plots else "",
            "ct_head_heatmap": str(out_dir / "ct_head_heatmap.png") if not skip_plots else "",
            "probe": str(out_dir / f"{probe_head}_probe.png") if not skip_plots else "",
            "final_circuit_detailed": str(out_dir / "final_circuit_detailed.png") if not skip_plots else "",
            "final_circuit": str(out_dir / "final_circuit.png") if not skip_plots else "",
        },
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine a reverse no-tool circuit on Qwen3.")
    parser.add_argument("--dataset-root", type=str, default=str(DATASETS_ROOT))
    parser.add_argument("--sample-id", type=str, default="")
    parser.add_argument("--sample-rank", type=int, default=0)
    parser.add_argument("--q-index", type=int, default=0, help="Legacy pair-style sample index.")
    parser.add_argument("--pair-dir", type=str, default="/root/autodl-tmp/XAI-1.7B-ACDC/pair")
    parser.add_argument("--model-path", type=str, default=str(MODEL_PATH_DEFAULT))
    parser.add_argument("--out-dir", type=str, default=str(RESULTS_ROOT / "manual_run" / "reverse_single_sample"))
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--ct-head-mode", choices=["exact", "ap_proxy"], default="exact")
    parser.add_argument("--skip-plots", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    sample = resolve_reverse_sample(
        dataset_root=args.dataset_root,
        pair_dir=args.pair_dir,
        sample_id=args.sample_id,
        sample_rank=args.sample_rank,
        q_index=args.q_index,
    )
    model, tokenizer = load_hooked_qwen3(args.model_path, device=args.device, dtype=torch.bfloat16)
    summary = run_one_sample_reverse(
        sample=sample,
        out_dir=out_dir,
        model=model,
        tokenizer=tokenizer,
        model_path=args.model_path,
        ct_head_mode=args.ct_head_mode,
        skip_plots=args.skip_plots,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
