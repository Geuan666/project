#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Supervise a resumable command until a done file exists.")
    parser.add_argument("--done-path", type=str, required=True)
    parser.add_argument("--log-path", type=str, required=True)
    parser.add_argument("--workdir", type=str, default="")
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument("cmd", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if not args.cmd:
        raise ValueError("Command is required after the supervisor arguments.")
    cmd = list(args.cmd)
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        raise ValueError("Command is empty after removing the '--' separator.")

    done_path = Path(args.done_path).resolve()
    log_path = Path(args.log_path).resolve()
    workdir = Path(args.workdir).resolve() if args.workdir else None
    log_path.parent.mkdir(parents=True, exist_ok=True)

    while not done_path.exists():
        start = time.strftime("%Y-%m-%d %H:%M:%S")
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"\n[{start}] launching: {' '.join(cmd)}\n")
            log.flush()
            proc = subprocess.run(
                cmd,
                cwd=str(workdir) if workdir else None,
                stdout=log,
                stderr=subprocess.STDOUT,
                env=os.environ.copy(),
                check=False,
            )
            end = time.strftime("%Y-%m-%d %H:%M:%S")
            log.write(f"[{end}] exit_code={proc.returncode}\n")
            log.flush()
        if done_path.exists():
            break
        time.sleep(max(0.5, args.sleep_seconds))


if __name__ == "__main__":
    main()
