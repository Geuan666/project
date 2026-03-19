from __future__ import annotations

from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT_ROOT = PROJECT_ROOT / "experiment"
DATASETS_ROOT = EXPERIMENT_ROOT / "datasets"
RESULTS_ROOT = EXPERIMENT_ROOT / "results"
MODEL_PATH_DEFAULT = Path("/root/autodl-tmp/Qwen/Qwen3-1.7B")


def timestamp_tag(now: datetime | None = None) -> str:
    return (now or datetime.now()).strftime("%d-%H-%M")


def manual_run_root(name: str = "manual_run") -> Path:
    return RESULTS_ROOT / name
