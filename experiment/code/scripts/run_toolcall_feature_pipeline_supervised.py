#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the feature-level tool-call pipeline with simple supervision.")
    parser.add_argument("--run-root", type=str, required=True)
    parser.add_argument("--dataset-root", type=str, required=True)
    parser.add_argument("--model-path", type=str, required=True)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--feature-project-root", type=str, default="/root/autodl-tmp/project-feature-circuits/project copy")
    parser.add_argument("--trainer", type=int, default=1)
    parser.add_argument("--discovery-batch-size", type=int, default=1)
    parser.add_argument("--eval-batch-size", type=int, default=2)
    parser.add_argument("--discovery-max-samples", type=int, default=0)
    parser.add_argument("--eval-max-samples", type=int, default=0)
    parser.add_argument("--top-k-per-layer", type=int, default=24)
    parser.add_argument("--seed", type=int, default=123)
    args = parser.parse_args()

    local_root = Path(__file__).resolve().parents[1]
    feature_root = Path(args.feature_project_root).resolve()
    run_root = Path(args.run_root).resolve()
    run_root.mkdir(parents=True, exist_ok=True)

    done_paths = [
        run_root / "REPORT.md",
        run_root / "validation" / "feature_group_report.json",
    ]
    log_path = run_root / "feature_pipeline_supervisor.log"

    env = os.environ.copy()
    env["PYTHONPATH"] = ":".join(
        [
            str(feature_root / "src"),
            str(local_root / "src"),
            env.get("PYTHONPATH", ""),
        ]
    ).rstrip(":")
    env["PYTORCH_CUDA_ALLOC_CONF"] = env.get("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

    cmd = [
        sys.executable,
        str(feature_root / "src" / "toolcall_circuit" / "feature_level_pipeline.py"),
        "--dataset-root",
        str(Path(args.dataset_root).resolve()),
        "--model-path",
        str(Path(args.model_path).resolve()),
        "--output-root",
        str(run_root),
        "--device",
        args.device,
        "--trainer",
        str(args.trainer),
        "--discovery-batch-size",
        str(args.discovery_batch_size),
        "--eval-batch-size",
        str(args.eval_batch_size),
        "--discovery-max-samples",
        str(args.discovery_max_samples),
        "--eval-max-samples",
        str(args.eval_max_samples),
        "--top-k-per-layer",
        str(args.top_k_per_layer),
        "--seed",
        str(args.seed),
    ]

    attempt = 0
    while not all(path.exists() for path in done_paths):
        attempt += 1
        start = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[launch] feature_pipeline attempt={attempt}", flush=True)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"\n[{start}] launch: {' '.join(cmd)}\n")
            log.flush()
            proc = subprocess.run(
                cmd,
                cwd=str(feature_root),
                stdout=log,
                stderr=subprocess.STDOUT,
                env=env,
                check=False,
            )
            end = time.strftime("%Y-%m-%d %H:%M:%S")
            log.write(f"[{end}] exit_code={proc.returncode}\n")
            log.flush()
        print(f"[exit] feature_pipeline attempt={attempt} exit_code={proc.returncode}", flush=True)
        if all(path.exists() for path in done_paths):
            print(f"[done] feature_pipeline: {run_root}", flush=True)
            return
        time.sleep(2.0)


if __name__ == "__main__":
    main()
