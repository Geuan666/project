#!/usr/bin/env python3
"""
Batch circuit mining for tool-call behavior.

This keeps the reference workflow structure but generalizes sample discovery to:
- dataset-root mode (`datasets/clean` + `datasets/corrupt`);
- legacy pair-dir mode.
"""

from __future__ import annotations

import os
import argparse
import csv
import gc
import json
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Sequence

import torch
from tqdm.auto import tqdm

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from experiments.launch_toolcall_qwen3_q85 import load_hooked_qwen3, run_one_sample
from experiments.toolcall_dataset import (
    load_toolcall_samples,
    parse_legacy_index_list,
    parse_sample_id_list,
    save_sample_catalog,
    select_samples,
)


def save_summary_csv(rows: Sequence[Dict[str, object]], out_path: Path) -> None:
    if not rows:
        return
    fieldnames = [
        "sample_id",
        "sample_rank",
        "q_index",
        "filename",
        "status",
        "clean_obj",
        "corrupt_obj",
        "gap",
        "detailed_ratio_vs_gap",
        "necessity_ratio_vs_gap",
        "rough_ratio_vs_gap",
        "rough_necessity_ratio_vs_gap",
        "probe_head",
        "target_token_str",
        "distractor_token_str",
        "ap_mode",
        "error",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def make_row_from_summary(summary: Dict[str, object], status: str, error: str = "") -> Dict[str, object]:
    return {
        "sample_id": summary.get("sample_id"),
        "sample_rank": summary.get("sample_rank"),
        "q_index": summary.get("q_index"),
        "filename": summary.get("filename"),
        "status": status,
        "clean_obj": summary.get("clean_obj"),
        "corrupt_obj": summary.get("corrupt_obj"),
        "gap": summary.get("gap"),
        "detailed_ratio_vs_gap": summary.get("detailed_ratio_vs_gap"),
        "necessity_ratio_vs_gap": summary.get("necessity_ratio_vs_gap"),
        "rough_ratio_vs_gap": summary.get("rough_ratio_vs_gap"),
        "rough_necessity_ratio_vs_gap": summary.get("rough_necessity_ratio_vs_gap"),
        "probe_head": summary.get("probe_head"),
        "target_token_str": summary.get("target_token_str"),
        "distractor_token_str": summary.get("distractor_token_str"),
        "ap_mode": summary.get("ap_mode"),
        "error": error,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch mine tool-call circuits on Qwen3.")
    parser.add_argument("--source", choices=["dataset", "pair"], default="dataset")
    parser.add_argument("--dataset-root", type=str, default="/root/autodl-tmp/project/datasets")
    parser.add_argument("--pair-dir", type=str, default="/root/autodl-tmp/XAI-1.7B-ACDC/pair")
    parser.add_argument("--model-path", type=str, default="/root/autodl-tmp/Qwen/Qwen3-1.7B")
    parser.add_argument("--out-root", type=str, default="experiments/results/toolcall_project_1189")
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--sample-ids", type=str, default="")
    parser.add_argument("--sample-rank-min", type=int, default=0)
    parser.add_argument("--sample-rank-max", type=int, default=0)
    parser.add_argument("--q-list", type=str, default="")
    parser.add_argument("--q-min", type=int, default=0)
    parser.add_argument("--q-max", type=int, default=0)
    parser.add_argument("--max-samples", type=int, default=0, help="0 means run all selected samples.")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--stop-on-error", action="store_true")
    args = parser.parse_args()

    out_root = Path(args.out_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    if args.source == "dataset":
        samples = load_toolcall_samples(dataset_root=Path(args.dataset_root))
        targets = select_samples(
            samples,
            sample_ids=parse_sample_id_list(args.sample_ids),
            sample_rank_min=args.sample_rank_min if args.sample_rank_min > 0 else 1,
            sample_rank_max=args.sample_rank_max,
            max_samples=args.max_samples,
        )
    else:
        samples = load_toolcall_samples(pair_dir=Path(args.pair_dir))
        if args.q_list.strip():
            legacy_indices = parse_legacy_index_list(args.q_list)
        elif args.q_min > 0 or args.q_max > 0:
            lo = args.q_min if args.q_min > 0 else 1
            hi = args.q_max if args.q_max > 0 else 10**9
            legacy_indices = [s.legacy_index for s in samples if s.legacy_index is not None and lo <= s.legacy_index <= hi]
        else:
            legacy_indices = [s.legacy_index for s in samples if s.legacy_index is not None]
        targets = select_samples(
            samples,
            legacy_indices=[int(x) for x in legacy_indices if x is not None],
            max_samples=args.max_samples,
        )
    if not targets:
        raise ValueError("No valid samples selected.")

    save_sample_catalog(targets, out_root / "sample_catalog.jsonl")

    model, tokenizer = load_hooked_qwen3(args.model_path, device=args.device, dtype=torch.bfloat16)

    rows: List[Dict[str, object]] = []
    log_path = out_root / "batch_progress.jsonl"
    progress_label = "Batch samples" if args.source == "dataset" else "Batch q"
    pbar = tqdm(targets, desc=progress_label, dynamic_ncols=True)
    for sample in pbar:
        out_dir = out_root / sample.sample_id
        summary_path = out_dir / "summary.json"
        if args.resume and summary_path.exists():
            try:
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                row = make_row_from_summary(summary, status="skipped_resume")
            except Exception as ex:  # noqa: BLE001
                row = {
                    "sample_id": sample.sample_id,
                    "sample_rank": sample.sample_rank,
                    "q_index": sample.legacy_index,
                    "filename": sample.filename,
                    "status": "resume_read_failed",
                    "error": repr(ex),
                }
            rows.append(row)
            with log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            continue

        try:
            summary = run_one_sample(
                sample=sample,
                out_dir=out_dir,
                model=model,
                tokenizer=tokenizer,
                model_path=args.model_path,
            )
            row = make_row_from_summary(summary, status="ok")
            rows.append(row)
            with log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            pbar.set_postfix(
                sample=sample.sample_id,
                det=f"{summary['detailed_ratio_vs_gap']:.3f}",
                nec=f"{summary['necessity_ratio_vs_gap']:.3f}",
            )
        except Exception as ex:  # noqa: BLE001
            err = traceback.format_exc()
            row = {
                "sample_id": sample.sample_id,
                "sample_rank": sample.sample_rank,
                "q_index": sample.legacy_index,
                "filename": sample.filename,
                "status": "error",
                "clean_obj": "",
                "corrupt_obj": "",
                "gap": "",
                "detailed_ratio_vs_gap": "",
                "necessity_ratio_vs_gap": "",
                "rough_ratio_vs_gap": "",
                "rough_necessity_ratio_vs_gap": "",
                "probe_head": "",
                "target_token_str": "",
                "distractor_token_str": "",
                "ap_mode": "",
                "error": repr(ex),
            }
            rows.append(row)
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "error.txt").write_text(err, encoding="utf-8")
            with log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            if args.stop_on_error:
                raise
        finally:
            gc.collect()
            torch.cuda.empty_cache()
            model.reset_hooks()

    save_summary_csv(rows, out_root / "batch_summary.csv")
    (out_root / "batch_summary.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for row in rows if row.get("status") in {"ok", "skipped_resume"})
    bad = sum(1 for row in rows if row.get("status") not in {"ok", "skipped_resume"})
    print(f"[done] total={len(rows)} ok_or_skipped={ok} error={bad}")
    print(f"[done] outputs root: {out_root}")


if __name__ == "__main__":
    main()
