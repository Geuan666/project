#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="为 split/train 的 Tool-Call Construction refine 生成 source-root 数据包。")
    parser.add_argument(
        "--run-root",
        type=Path,
        default=Path("/root/autodl-tmp/project/experiment/results/split/pipeline"),
    )
    parser.add_argument(
        "--legacy-data-root",
        type=Path,
        default=Path("/root/autodl-tmp/project/experiment/results/legacy/final/data"),
    )
    parser.add_argument(
        "--attention-root",
        type=Path,
        default=Path("/root/autodl-tmp/project/experiment/results/split/attentionhead"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/root/autodl-tmp/project/experiment/results/split/tool_call_construction/source_data"),
    )
    parser.add_argument("--model-path", type=str, default="/root/autodl-tmp/Qwen/Qwen3-1.7B")
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--max-samples", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    code_root = Path(__file__).resolve().parents[1]
    module_path = code_root / "src" / "toolcall_circuit" / "tool_call_construction_analysis.py"
    command = [
        sys.executable,
        str(module_path),
        "--run-root",
        str(args.run_root.resolve()),
        "--legacy-data-root",
        str(args.legacy_data_root.resolve()),
        "--attention-root",
        str(args.attention_root.resolve()),
        "--model-path",
        args.model_path,
        "--device",
        args.device,
        "--max-samples",
        str(args.max_samples),
        "--output-root",
        str(args.output_root.resolve()),
    ]
    subprocess.run(command, check=True, cwd=code_root)


if __name__ == "__main__":
    main()
