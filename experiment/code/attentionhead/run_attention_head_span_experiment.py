#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import torch
from tqdm.auto import tqdm

CODE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = PROJECT_ROOT / "experiment"
if str(CODE_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(CODE_ROOT / "src"))

from toolcall_circuit.single_sample import load_hooked_qwen3


SPAN_NAMES = [
    "system_preamble",
    "tools_block",
    "tool_instruction",
    "tool_call_example",
    "user_lead_phrase",
    "function_body_anchor",
    "file_target",
    "instruction_suffix",
    "task_body",
    "assistant_prefix",
]

CONDITION_NAMES = ["clean", "corrupt"]

SYSTEM_TOOLS_OPEN = "<tools>"
SYSTEM_TOOLS_CLOSE = "</tools>"
SYSTEM_TOOL_CALL_OPEN = "<tool_call>"
SYSTEM_TOOL_CALL_CLOSE = "</tool_call>"
USER_MARKER = "<|im_start|>user\n"
ASSISTANT_MARKER = "<|im_end|>\n<|im_start|>assistant\n"
FILE_TARGET_RE = re.compile(r"solve\.(?:py|cpp|java)")


@dataclass(frozen=True)
class SamplePair:
    sample_id: str
    clean_path: Path
    corrupt_path: Path


def write_csv(rows: Sequence[Dict[str, object]], out_path: Path) -> None:
    if not rows:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def load_sample_pairs(dataset_root: Path, max_samples: int) -> List[SamplePair]:
    clean_dir = dataset_root / "clean"
    corrupt_dir = dataset_root / "corrupt"
    clean_files = {p.name: p for p in clean_dir.glob("*.txt")}
    corrupt_files = {p.name: p for p in corrupt_dir.glob("*.txt")}
    shared = sorted(set(clean_files) & set(corrupt_files))
    pairs = [
        SamplePair(sample_id=Path(name).stem, clean_path=clean_files[name], corrupt_path=corrupt_files[name])
        for name in shared
    ]
    if max_samples > 0:
        pairs = pairs[:max_samples]
    return pairs


def span_short_label(name: str) -> str:
    return {
        "system_preamble": "system",
        "tools_block": "tools",
        "tool_instruction": "tool_instr",
        "tool_call_example": "tool_example",
        "user_lead_phrase": "lead",
        "function_body_anchor": "body_anchor",
        "file_target": "file_target",
        "instruction_suffix": "instr_suffix",
        "task_body": "task_body",
        "assistant_prefix": "assistant",
    }[name]


def format_head_name(layer: int, head: int) -> str:
    return f"L{layer}H{head}"


def find_required_substring(text: str, needle: str, start: int = 0, *, use_last: bool = False) -> int:
    idx = text.rfind(needle, start) if use_last else text.find(needle, start)
    if idx < 0:
        raise ValueError(f"Failed to find required substring {needle!r}")
    return idx


def build_char_spans(text: str) -> Dict[str, Tuple[int, int]]:
    user_marker_idx = text.find(USER_MARKER)
    if user_marker_idx < 0:
        raise ValueError("Failed to find user marker")
    user_content_start = user_marker_idx + len(USER_MARKER)
    assistant_marker_idx = text.find(ASSISTANT_MARKER, user_content_start)
    if assistant_marker_idx < 0:
        raise ValueError("Failed to find assistant marker")

    tools_open_idx = find_required_substring(text[:user_content_start], SYSTEM_TOOLS_OPEN, use_last=True)
    tools_close_idx = find_required_substring(text[:user_content_start], SYSTEM_TOOLS_CLOSE, tools_open_idx)
    tools_close_end = tools_close_idx + len(SYSTEM_TOOLS_CLOSE)

    tool_example_open_idx = find_required_substring(text[:user_content_start], SYSTEM_TOOL_CALL_OPEN, use_last=True)

    user_content = text[user_content_start:assistant_marker_idx]
    first_line_end_rel = user_content.find("\n")
    if first_line_end_rel < 0:
        first_line_end_rel = len(user_content)
    first_line = user_content[:first_line_end_rel]
    line_start_abs = user_content_start
    line_end_abs = user_content_start + first_line_end_rel

    file_match = FILE_TARGET_RE.search(first_line)
    if file_match is None:
        raise ValueError("Failed to find file target in user instruction line")
    file_start_abs = line_start_abs + file_match.start()
    file_end_abs = line_start_abs + file_match.end()

    anchor_rel = first_line.find("the function body")
    if anchor_rel < 0:
        anchor_rel = first_line.find("function body")
    if anchor_rel < 0:
        raise ValueError("Failed to find function body anchor in user instruction line")
    anchor_start_abs = line_start_abs + anchor_rel

    spans = {
        "system_preamble": (0, tools_open_idx),
        "tools_block": (tools_open_idx, tools_close_end),
        "tool_instruction": (tools_close_end, tool_example_open_idx),
        "tool_call_example": (tool_example_open_idx, user_content_start),
        "user_lead_phrase": (user_content_start, anchor_start_abs),
        "function_body_anchor": (anchor_start_abs, file_start_abs),
        "file_target": (file_start_abs, file_end_abs),
        "instruction_suffix": (file_end_abs, line_end_abs),
        "task_body": (line_end_abs, assistant_marker_idx),
        "assistant_prefix": (assistant_marker_idx, len(text)),
    }
    validate_char_spans(spans, len(text))
    return spans


def validate_char_spans(spans: Dict[str, Tuple[int, int]], text_len: int) -> None:
    start = 0
    for name in SPAN_NAMES:
        lo, hi = spans[name]
        if lo != start:
            raise ValueError(f"Span {name} starts at {lo}, expected {start}")
        if hi <= lo:
            raise ValueError(f"Span {name} is empty or negative: {(lo, hi)}")
        start = hi
    if start != text_len:
        raise ValueError(f"Char spans end at {start}, expected {text_len}")


def token_span_positions(text: str, tokenizer) -> Dict[str, List[int]]:
    spans = build_char_spans(text)
    encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
    offsets = [(int(start), int(end)) for start, end in encoded["offset_mapping"]]
    positions = {name: [] for name in SPAN_NAMES}

    for tok_idx, (tok_start, tok_end) in enumerate(offsets):
        if tok_end <= tok_start:
            probe = float(tok_start)
        else:
            probe = tok_start + 0.5 * float(tok_end - tok_start)
        assigned = None
        for name in SPAN_NAMES:
            lo, hi = spans[name]
            if lo <= probe < hi:
                assigned = name
                break
        if assigned is None and tok_end == len(text):
            assigned = SPAN_NAMES[-1]
        if assigned is None:
            raise ValueError(f"Failed to assign token {tok_idx} offset={(tok_start, tok_end)}")
        positions[assigned].append(tok_idx)

    total_positions = sum(len(pos) for pos in positions.values())
    if total_positions != len(offsets):
        raise ValueError(f"Assigned {total_positions} tokens, expected {len(offsets)}")
    for name in SPAN_NAMES:
        if not positions[name]:
            raise ValueError(f"Span {name} has zero tokens after token assignment")
    return positions


def build_span_masks(span_positions: Dict[str, List[int]], seq_len: int, device: torch.device) -> Tuple[torch.Tensor, torch.Tensor]:
    mask = torch.zeros((len(SPAN_NAMES), seq_len), dtype=torch.float32, device=device)
    counts = torch.zeros((len(SPAN_NAMES),), dtype=torch.float32, device=device)
    for span_idx, name in enumerate(SPAN_NAMES):
        pos = span_positions[name]
        mask[span_idx, pos] = 1.0
        counts[span_idx] = float(len(pos))
    return mask, counts


def aggregate_layer_attention(
    pattern: torch.Tensor,
    span_mask: torch.Tensor,
    span_counts: torch.Tensor,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    # pattern: [heads, query_pos, key_pos]
    key_mass = torch.einsum("hqk,sk->hqs", pattern, span_mask)
    query_span_mass = torch.einsum("sq,hqk->hsk", span_mask, key_mass)
    mass = query_span_mass / span_counts.view(1, -1, 1)
    density = mass / span_counts.view(1, 1, -1)
    decision_mass = key_mass[:, -1, :]
    decision_density = decision_mass / span_counts.view(1, -1)
    return (
        mass.detach().cpu().numpy(),
        density.detach().cpu().numpy(),
        decision_mass.detach().cpu().numpy(),
        decision_density.detach().cpu().numpy(),
    )


def configure_matplotlib() -> None:
    plt.style.use("default")
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
        }
    )


def plot_heatmap_triptych(
    *,
    metric_name: str,
    clean: np.ndarray,
    corrupt: np.ndarray,
    labels: Sequence[str],
    title: str,
    out_path: Path,
) -> None:
    configure_matplotlib()
    delta = corrupt - clean
    vmax_main = float(max(np.max(clean), np.max(corrupt), 1e-8))
    vmax_delta = float(max(np.max(np.abs(delta)), 1e-8))

    fig, axes = plt.subplots(1, 3, figsize=(16.5, 4.8), constrained_layout=True)
    main_cmap = "YlOrRd"
    delta_cmap = "RdBu_r"

    im0 = axes[0].imshow(clean, cmap=main_cmap, vmin=0.0, vmax=vmax_main, aspect="auto")
    axes[0].set_title("Clean")
    im1 = axes[1].imshow(corrupt, cmap=main_cmap, vmin=0.0, vmax=vmax_main, aspect="auto")
    axes[1].set_title("Corrupt")
    im2 = axes[2].imshow(delta, cmap=delta_cmap, vmin=-vmax_delta, vmax=vmax_delta, aspect="auto")
    axes[2].set_title("Corrupt - Clean")

    for ax in axes:
        ax.set_xticks(np.arange(len(labels)))
        ax.set_xticklabels(labels, rotation=35, ha="right")
        ax.set_yticks(np.arange(len(labels)))
        ax.set_yticklabels(labels)
        ax.set_xlabel("Key Span")
        ax.set_ylabel("Query Span")

    cbar0 = fig.colorbar(im1, ax=axes[:2], fraction=0.040, pad=0.02)
    cbar0.set_label(metric_name)
    cbar1 = fig.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04)
    cbar1.set_label(f"{metric_name} delta")
    fig.suptitle(title)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_decision_row(
    *,
    clean_mass: np.ndarray,
    corrupt_mass: np.ndarray,
    clean_density: np.ndarray,
    corrupt_density: np.ndarray,
    labels: Sequence[str],
    title: str,
    out_path: Path,
) -> None:
    configure_matplotlib()
    xs = np.arange(len(labels))
    fig, axes = plt.subplots(1, 2, figsize=(15.5, 4.5), constrained_layout=True)
    line_specs = [
        (axes[0], clean_mass, corrupt_mass, "Mass"),
        (axes[1], clean_density, corrupt_density, "Density"),
    ]
    for ax, clean_vals, corrupt_vals, label in line_specs:
        ax.plot(xs, clean_vals, marker="o", linewidth=2.0, color="#b2182b", label="clean")
        ax.plot(xs, corrupt_vals, marker="s", linewidth=2.0, color="#2166ac", label="corrupt")
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, rotation=35, ha="right")
        ax.set_title(f"Decision Row {label}")
        ax.set_xlabel("Key Span")
        ax.set_ylabel(label)
        ax.grid(alpha=0.25, linewidth=0.6)
        ax.legend(frameon=False)
    fig.suptitle(title)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_longform_csvs(
    *,
    mass_mean: np.ndarray,
    density_mean: np.ndarray,
    decision_mass_mean: np.ndarray,
    decision_density_mean: np.ndarray,
    out_root: Path,
) -> None:
    heatmap_rows: List[Dict[str, object]] = []
    decision_rows: List[Dict[str, object]] = []
    n_conditions, n_layers, n_heads, n_spans, _ = mass_mean.shape

    for condition_idx in range(n_conditions):
        condition = CONDITION_NAMES[condition_idx]
        for layer in range(n_layers):
            for head in range(n_heads):
                head_name = format_head_name(layer, head)
                for q_idx, q_name in enumerate(SPAN_NAMES):
                    for k_idx, k_name in enumerate(SPAN_NAMES):
                        heatmap_rows.append(
                            {
                                "condition": condition,
                                "layer": layer,
                                "head": head_name,
                                "query_span": q_name,
                                "key_span": k_name,
                                "mass_mean": float(mass_mean[condition_idx, layer, head, q_idx, k_idx]),
                                "density_mean": float(density_mean[condition_idx, layer, head, q_idx, k_idx]),
                            }
                        )
                for k_idx, k_name in enumerate(SPAN_NAMES):
                    decision_rows.append(
                        {
                            "condition": condition,
                            "layer": layer,
                            "head": head_name,
                            "key_span": k_name,
                            "decision_mass_mean": float(decision_mass_mean[condition_idx, layer, head, k_idx]),
                            "decision_density_mean": float(decision_density_mean[condition_idx, layer, head, k_idx]),
                        }
                    )

    write_csv(heatmap_rows, out_root / "summary" / "head_heatmap_summary.csv")
    write_csv(decision_rows, out_root / "summary" / "head_decision_row_summary.csv")


def save_head_metadata(out_root: Path, n_layers: int, n_heads: int) -> None:
    rows: List[Dict[str, object]] = []
    for layer in range(n_layers):
        for head in range(n_heads):
            head_name = format_head_name(layer, head)
            base_dir = out_root / "plots" / f"layer_{layer:02d}" / head_name
            rows.append(
                {
                    "layer": layer,
                    "head_index": head,
                    "head": head_name,
                    "mass_heatmap_png": str(base_dir / "mass_heatmap.png"),
                    "density_heatmap_png": str(base_dir / "density_heatmap.png"),
                    "decision_row_png": str(base_dir / "decision_row.png"),
                }
            )
    write_csv(rows, out_root / "summary" / "head_plot_index.csv")


def make_plots(
    *,
    mass_mean: np.ndarray,
    density_mean: np.ndarray,
    decision_mass_mean: np.ndarray,
    decision_density_mean: np.ndarray,
    out_root: Path,
) -> None:
    labels = [span_short_label(name) for name in SPAN_NAMES]
    _, n_layers, n_heads, _, _ = mass_mean.shape
    pbar = tqdm(total=n_layers * n_heads, desc="Render plots", dynamic_ncols=True)
    for layer in range(n_layers):
        for head in range(n_heads):
            head_name = format_head_name(layer, head)
            base_dir = out_root / "plots" / f"layer_{layer:02d}" / head_name
            base_dir.mkdir(parents=True, exist_ok=True)

            plot_heatmap_triptych(
                metric_name="Mean Mass",
                clean=mass_mean[0, layer, head],
                corrupt=mass_mean[1, layer, head],
                labels=labels,
                title=f"{head_name} Span-to-Span Mean Mass",
                out_path=base_dir / "mass_heatmap.png",
            )
            plot_heatmap_triptych(
                metric_name="Mean Density",
                clean=density_mean[0, layer, head],
                corrupt=density_mean[1, layer, head],
                labels=labels,
                title=f"{head_name} Span-to-Span Mean Density",
                out_path=base_dir / "density_heatmap.png",
            )
            plot_decision_row(
                clean_mass=decision_mass_mean[0, layer, head],
                corrupt_mass=decision_mass_mean[1, layer, head],
                clean_density=decision_density_mean[0, layer, head],
                corrupt_density=decision_density_mean[1, layer, head],
                labels=labels,
                title=f"{head_name} Decision Row",
                out_path=base_dir / "decision_row.png",
            )
            pbar.update(1)
    pbar.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate full attention-head span statistics over the tool-call dataset.")
    parser.add_argument("--dataset-root", type=str, default=str(EXPERIMENT_ROOT / "datasets"))
    parser.add_argument("--model-path", type=str, default="/root/autodl-tmp/Qwen/Qwen3-1.7B")
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--dtype", type=str, default="bfloat16", choices=["bfloat16", "float16", "float32"])
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--output-root", type=str, required=True)
    parser.add_argument("--skip-plots", action="store_true")
    args = parser.parse_args()

    out_root = Path(args.output_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "summary").mkdir(parents=True, exist_ok=True)

    dtype = {
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32,
    }[args.dtype]

    sample_pairs = load_sample_pairs(Path(args.dataset_root).resolve(), args.max_samples)
    if not sample_pairs:
        raise ValueError("No clean/corrupt sample pairs found")

    model, tokenizer = load_hooked_qwen3(args.model_path, device=args.device, dtype=dtype)
    n_layers = int(model.cfg.n_layers)
    n_heads = int(model.cfg.n_heads)
    n_spans = len(SPAN_NAMES)
    hook_names = {f"blocks.{layer}.attn.hook_pattern" for layer in range(n_layers)}

    mass_sum = np.zeros((2, n_layers, n_heads, n_spans, n_spans), dtype=np.float64)
    density_sum = np.zeros((2, n_layers, n_heads, n_spans, n_spans), dtype=np.float64)
    decision_mass_sum = np.zeros((2, n_layers, n_heads, n_spans), dtype=np.float64)
    decision_density_sum = np.zeros((2, n_layers, n_heads, n_spans), dtype=np.float64)
    span_token_count_sum = np.zeros((2, n_spans), dtype=np.float64)

    skipped_rows: List[Dict[str, object]] = []
    n_valid = 0
    start_time = time.time()

    pbar = tqdm(sample_pairs, desc="Aggregate attention", dynamic_ncols=True)
    for pair in pbar:
        try:
            clean_text = pair.clean_path.read_text(encoding="utf-8")
            corrupt_text = pair.corrupt_path.read_text(encoding="utf-8")

            clean_span_positions = token_span_positions(clean_text, tokenizer)
            corrupt_span_positions = token_span_positions(corrupt_text, tokenizer)

            clean_tokens = model.to_tokens(clean_text, prepend_bos=False)
            corrupt_tokens = model.to_tokens(corrupt_text, prepend_bos=False)
            if clean_tokens.shape != corrupt_tokens.shape:
                raise ValueError(f"Token shapes differ: {tuple(clean_tokens.shape)} vs {tuple(corrupt_tokens.shape)}")

            pair_tokens = torch.cat([clean_tokens, corrupt_tokens], dim=0)
            with torch.no_grad():
                _, cache = model.run_with_cache(pair_tokens, names_filter=lambda name: name in hook_names)

            seq_len = int(clean_tokens.shape[-1])
            clean_mask, clean_counts = build_span_masks(clean_span_positions, seq_len, device=pair_tokens.device)
            corrupt_mask, corrupt_counts = build_span_masks(corrupt_span_positions, seq_len, device=pair_tokens.device)

            for condition_idx, (span_mask, span_counts) in enumerate(
                [(clean_mask, clean_counts), (corrupt_mask, corrupt_counts)]
            ):
                span_token_count_sum[condition_idx] += span_counts.detach().cpu().numpy()
                for layer in range(n_layers):
                    pattern = cache[f"blocks.{layer}.attn.hook_pattern"][condition_idx].float()
                    mass, density, decision_mass, decision_density = aggregate_layer_attention(
                        pattern=pattern,
                        span_mask=span_mask,
                        span_counts=span_counts,
                    )
                    mass_sum[condition_idx, layer] += mass
                    density_sum[condition_idx, layer] += density
                    decision_mass_sum[condition_idx, layer] += decision_mass
                    decision_density_sum[condition_idx, layer] += decision_density

            n_valid += 1
            pbar.set_postfix(valid=n_valid, sample=pair.sample_id)
            del cache
            model.reset_hooks()
        except Exception as exc:
            skipped_rows.append({"sample_id": pair.sample_id, "error": str(exc)})
            pbar.set_postfix(valid=n_valid, skipped=len(skipped_rows))
            continue

    pbar.close()

    if n_valid == 0:
        raise RuntimeError("All samples failed during aggregation")

    mass_mean = mass_sum / float(n_valid)
    density_mean = density_sum / float(n_valid)
    decision_mass_mean = decision_mass_sum / float(n_valid)
    decision_density_mean = decision_density_sum / float(n_valid)
    span_token_count_mean = span_token_count_sum / float(n_valid)

    np.savez_compressed(
        out_root / "summary" / "aggregate_arrays.npz",
        mass_mean=mass_mean,
        density_mean=density_mean,
        decision_mass_mean=decision_mass_mean,
        decision_density_mean=decision_density_mean,
        span_token_count_mean=span_token_count_mean,
    )

    save_longform_csvs(
        mass_mean=mass_mean,
        density_mean=density_mean,
        decision_mass_mean=decision_mass_mean,
        decision_density_mean=decision_density_mean,
        out_root=out_root,
    )
    save_head_metadata(out_root, n_layers, n_heads)

    span_rows: List[Dict[str, object]] = []
    for condition_idx, condition in enumerate(CONDITION_NAMES):
        for span_idx, span_name in enumerate(SPAN_NAMES):
            span_rows.append(
                {
                    "condition": condition,
                    "span": span_name,
                    "mean_token_count": float(span_token_count_mean[condition_idx, span_idx]),
                }
            )
    write_csv(span_rows, out_root / "summary" / "span_token_count_summary.csv")

    if skipped_rows:
        write_csv(skipped_rows, out_root / "summary" / "skipped_samples.csv")

    if not args.skip_plots:
        make_plots(
            mass_mean=mass_mean,
            density_mean=density_mean,
            decision_mass_mean=decision_mass_mean,
            decision_density_mean=decision_density_mean,
            out_root=out_root,
        )

    summary = {
        "project_root": str(PROJECT_ROOT),
        "dataset_root": str(Path(args.dataset_root).resolve()),
        "model_path": str(Path(args.model_path).resolve()),
        "device": args.device,
        "dtype": args.dtype,
        "n_layers": n_layers,
        "n_heads": n_heads,
        "n_spans": n_spans,
        "span_names": SPAN_NAMES,
        "condition_names": CONDITION_NAMES,
        "n_requested_samples": len(sample_pairs),
        "n_valid_samples": n_valid,
        "n_skipped_samples": len(skipped_rows),
        "elapsed_sec": time.time() - start_time,
        "artifacts": {
            "aggregate_arrays": str(out_root / "summary" / "aggregate_arrays.npz"),
            "heatmap_csv": str(out_root / "summary" / "head_heatmap_summary.csv"),
            "decision_row_csv": str(out_root / "summary" / "head_decision_row_summary.csv"),
            "span_token_count_csv": str(out_root / "summary" / "span_token_count_summary.csv"),
            "head_plot_index_csv": str(out_root / "summary" / "head_plot_index.csv"),
            "plot_root": str(out_root / "plots"),
        },
    }
    (out_root / "summary" / "run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
