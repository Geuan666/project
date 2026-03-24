#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="在 split/train 主流水线上运行 Instruction Integration refine。")
    parser.add_argument(
        "--run-root",
        type=Path,
        default=Path("/root/autodl-tmp/project/experiment/results/split/pipeline"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/root/autodl-tmp/project/experiment/results/split/instruction_integration"),
    )
    parser.add_argument("--model-path", type=str, default="/root/autodl-tmp/Qwen/Qwen3-1.7B")
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--save-every", type=int, default=25)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    code_root = Path(__file__).resolve().parents[1]
    script_path = code_root / "scripts" / "analyze_toolcall_instruction_integration_refine.py"
    command = [
        sys.executable,
        str(script_path),
        "--forward-batch-root",
        str(args.run_root.resolve() / "forward_batch"),
        "--reverse-batch-root",
        str(args.run_root.resolve() / "reverse_batch"),
        "--model-path",
        args.model_path,
        "--device",
        args.device,
        "--max-samples",
        str(args.max_samples),
        "--save-every",
        str(args.save_every),
        "--output-root",
        str(args.output_root.resolve()),
    ]
    subprocess.run(command, check=True, cwd=code_root)


if __name__ == "__main__":
    main()
