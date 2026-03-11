from __future__ import annotations

from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASETS_ROOT = PROJECT_ROOT / "datasets"
RESULTS_ROOT = PROJECT_ROOT / "results"
MODEL_PATH_DEFAULT = Path("/root/autodl-tmp/Qwen/Qwen3-1.7B")


def timestamp_tag(now: datetime | None = None) -> str:
    return (now or datetime.now()).strftime("%d-%H-%M")


def manual_run_root(name: str = "manual_run") -> Path:
    return RESULTS_ROOT / name
