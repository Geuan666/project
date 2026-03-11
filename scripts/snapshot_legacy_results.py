#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEGACY_ROOT = PROJECT_ROOT / "Automatic-Circuit-Discovery" / "experiments" / "results"


def copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    shutil.copytree(src, dst, dirs_exist_ok=True)


def collect_artifacts(run_root: Path) -> None:
    figs = run_root / "figs"
    tables = run_root / "tables"
    figs.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    for folder_name in ["aggregate", "semantic_roles", "refined_consistent"]:
        folder = run_root / folder_name
        if not folder.exists():
            continue
        for path in folder.rglob("*"):
            if not path.is_file():
                continue
            dest_name = f"{folder_name}__{path.name}"
            if path.suffix.lower() == ".png":
                shutil.copy2(path, figs / dest_name)
            elif path.suffix.lower() in {".csv", ".json"}:
                shutil.copy2(path, tables / dest_name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Snapshot the completed legacy results into the new timestamped results layout.")
    parser.add_argument("--legacy-root", type=str, default=str(DEFAULT_LEGACY_ROOT))
    parser.add_argument("--batch-name", type=str, default="toolcall_project_1189")
    parser.add_argument("--run-tag", type=str, required=True)
    parser.add_argument("--output-root", type=str, default=str(PROJECT_ROOT / "results"))
    args = parser.parse_args()

    legacy_root = Path(args.legacy_root).resolve()
    out_root = Path(args.output_root).resolve() / args.run_tag
    if out_root.exists():
        raise FileExistsError(f"Refusing to overwrite existing run root: {out_root}")
    out_root.mkdir(parents=True, exist_ok=False)

    batch_src = legacy_root / args.batch_name
    aggregate_src = legacy_root / f"{args.batch_name}_aggregate"
    semantic_src = legacy_root / f"{args.batch_name}_semantic_roles"
    refined_src = legacy_root / f"{args.batch_name}_refined_consistent"
    consistency_src = legacy_root / f"{args.batch_name}_consistency_eval.json"

    copy_tree(batch_src, out_root / "batch")
    copy_tree(aggregate_src, out_root / "aggregate")
    copy_tree(semantic_src, out_root / "semantic_roles")
    copy_tree(refined_src, out_root / "refined_consistent")
    if consistency_src.exists():
        shutil.copy2(consistency_src, out_root / "consistency_eval.json")

    collect_artifacts(out_root)

    manifest = {
        "source": {
            "legacy_root": str(legacy_root),
            "batch": str(batch_src),
            "aggregate": str(aggregate_src),
            "semantic_roles": str(semantic_src),
            "refined_consistent": str(refined_src),
            "consistency_eval": str(consistency_src),
        },
        "snapshot": {
            "run_root": str(out_root),
            "batch": str(out_root / "batch"),
            "aggregate": str(out_root / "aggregate"),
            "semantic_roles": str(out_root / "semantic_roles"),
            "refined_consistent": str(out_root / "refined_consistent"),
            "consistency_eval": str(out_root / "consistency_eval.json"),
            "figs": str(out_root / "figs"),
            "tables": str(out_root / "tables"),
        },
    }
    (out_root / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
