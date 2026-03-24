#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="按 (language, clean_candidate) 分层，将数据集拆成 train/test 子集。"
    )
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--train-root", type=Path, required=True)
    parser.add_argument("--test-root", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-ratio", type=float, default=0.3)
    parser.add_argument("--link-mode", choices=("hardlink", "copy"), default="hardlink")
    return parser.parse_args()


def load_manifest_rows(path: Path) -> Dict[str, Dict[str, object]]:
    rows: Dict[str, Dict[str, object]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            filename = str(row.get("output_filename") or row.get("source_filename") or "")
            if not filename:
                raise ValueError(f"Manifest {path} 存在缺失文件名的行")
            if filename in rows:
                raise ValueError(f"Manifest {path} 中 {filename} 重复")
            rows[filename] = row
    return rows


def safe_rmtree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def ensure_clean_dir(path: Path) -> None:
    safe_rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def pair_sort_key(filename: str) -> Tuple[int, str]:
    stem = Path(filename).stem
    suffix_digits = ""
    for ch in reversed(stem):
        if ch.isdigit():
            suffix_digits = ch + suffix_digits
        else:
            break
    numeric = int(suffix_digits) if suffix_digits else 10**9
    return numeric, stem


def emit_json(path: Path, payload: object) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def emit_manifest(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")


def link_or_copy(src: Path, dst: Path, mode: str) -> None:
    if dst.exists():
        dst.unlink()
    if mode == "hardlink":
        os.link(src, dst)
    else:
        shutil.copy2(src, dst)


def build_subset_summary(
    model_path: str,
    output_root: Path,
    clean_rows: List[Dict[str, object]],
    corrupt_rows: List[Dict[str, object]],
) -> Dict[str, object]:
    return {
        "model_path": model_path,
        "output_root": str(output_root),
        "strict_pruned": True,
        "dropped_rows": 0,
        "corrupt_rows": len(corrupt_rows),
        "clean_rows": len(clean_rows),
        "language_counts": dict(sorted(Counter(str(row["language"]) for row in clean_rows).items())),
        "corrupt_candidate_counts": dict(
            sorted(Counter(str(row["assigned_candidate"]) for row in corrupt_rows).items())
        ),
        "clean_candidate_counts": dict(
            sorted(Counter(str(row["clean_candidate"]) for row in clean_rows).items())
        ),
    }


def main() -> None:
    args = parse_args()
    dataset_root = args.dataset_root.resolve()
    clean_dir = dataset_root / "clean"
    corrupt_dir = dataset_root / "corrupt"
    if not clean_dir.exists() or not corrupt_dir.exists():
        raise FileNotFoundError(f"缺少 clean/corrupt 目录: {dataset_root}")

    original_summary_path = dataset_root / "merge_summary.json"
    with original_summary_path.open("r", encoding="utf-8") as handle:
        original_summary = json.load(handle)

    clean_manifest = load_manifest_rows(clean_dir / "manifest.jsonl")
    corrupt_manifest = load_manifest_rows(corrupt_dir / "manifest.jsonl")
    clean_files = {path.name for path in clean_dir.glob("*.txt")}
    corrupt_files = {path.name for path in corrupt_dir.glob("*.txt")}
    shared_files = sorted(clean_files & corrupt_files, key=pair_sort_key)

    if clean_files != corrupt_files:
        missing_clean = sorted(corrupt_files - clean_files)
        missing_corrupt = sorted(clean_files - corrupt_files)
        raise ValueError(
            f"clean/corrupt 文件不对齐: missing_clean={len(missing_clean)} missing_corrupt={len(missing_corrupt)}"
        )
    missing_manifest = [name for name in shared_files if name not in clean_manifest or name not in corrupt_manifest]
    if missing_manifest:
        raise ValueError(f"有文件缺失 manifest 元数据，数量={len(missing_manifest)}")

    records: List[Dict[str, object]] = []
    for filename in shared_files:
        clean_row = clean_manifest[filename]
        corrupt_row = corrupt_manifest[filename]
        language = str(clean_row.get("language") or corrupt_row.get("language") or "").lower()
        clean_candidate = str(clean_row.get("clean_candidate") or "").strip()
        corrupt_candidate = str(
            clean_row.get("corrupt_candidate") or corrupt_row.get("assigned_candidate") or ""
        ).strip()
        if not language or not clean_candidate or not corrupt_candidate:
            raise ValueError(f"{filename} 缺失分层元数据")
        records.append(
            {
                "filename": filename,
                "lang": language,
                "clean_candidate": clean_candidate,
                "corrupt_candidate": corrupt_candidate,
                "clean_manifest": clean_row,
                "corrupt_manifest": corrupt_row,
            }
        )

    groups: Dict[Tuple[str, str], List[Dict[str, object]]] = defaultdict(list)
    for record in records:
        groups[(record["lang"], record["clean_candidate"])].append(record)

    rng = random.Random(args.seed)
    train_records: List[Dict[str, object]] = []
    test_records: List[Dict[str, object]] = []
    for key in sorted(groups):
        group = list(groups[key])
        rng.shuffle(group)
        n_test = math.floor(len(group) * args.test_ratio)
        test_slice = group[:n_test]
        train_slice = group[n_test:]
        train_records.extend(sorted(train_slice, key=lambda row: pair_sort_key(row["filename"])))
        test_records.extend(sorted(test_slice, key=lambda row: pair_sort_key(row["filename"])))

    train_records = sorted(train_records, key=lambda row: pair_sort_key(row["filename"]))
    test_records = sorted(test_records, key=lambda row: pair_sort_key(row["filename"]))

    if len(train_records) + len(test_records) != len(records):
        raise AssertionError("拆分后样本总数不守恒")
    if {row["filename"] for row in train_records} & {row["filename"] for row in test_records}:
        raise AssertionError("train/test 出现重复文件")

    for root in [args.train_root.resolve(), args.test_root.resolve()]:
        ensure_clean_dir(root / "clean")
        ensure_clean_dir(root / "corrupt")

    subset_map = {
        "train": (args.train_root.resolve(), train_records),
        "test": (args.test_root.resolve(), test_records),
    }
    for split_name, (split_root, split_records) in subset_map.items():
        split_clean_rows = []
        split_corrupt_rows = []
        for record in split_records:
            filename = record["filename"]
            link_or_copy(clean_dir / filename, split_root / "clean" / filename, args.link_mode)
            link_or_copy(corrupt_dir / filename, split_root / "corrupt" / filename, args.link_mode)
            split_clean_rows.append(record["clean_manifest"])
            split_corrupt_rows.append(record["corrupt_manifest"])
        emit_manifest(split_root / "clean" / "manifest.jsonl", split_clean_rows)
        emit_manifest(split_root / "corrupt" / "manifest.jsonl", split_corrupt_rows)
        split_summary = build_subset_summary(
            model_path=str(original_summary.get("model_path", "")),
            output_root=split_root,
            clean_rows=split_clean_rows,
            corrupt_rows=split_corrupt_rows,
        )
        emit_json(split_root / "merge_summary.json", split_summary)

    per_lang: Dict[str, Dict[str, int]] = {}
    per_clean_candidate: Dict[str, Dict[str, int]] = {}
    train_by_lang = Counter(str(row["lang"]) for row in train_records)
    test_by_lang = Counter(str(row["lang"]) for row in test_records)
    for lang in sorted({*train_by_lang.keys(), *test_by_lang.keys()}):
        per_lang[lang] = {"train": train_by_lang.get(lang, 0), "test": test_by_lang.get(lang, 0)}

    train_by_clean = Counter(str(row["clean_candidate"]) for row in train_records)
    test_by_clean = Counter(str(row["clean_candidate"]) for row in test_records)
    for candidate in sorted({*train_by_clean.keys(), *test_by_clean.keys()}):
        per_clean_candidate[candidate] = {
            "train": train_by_clean.get(candidate, 0),
            "test": test_by_clean.get(candidate, 0),
        }

    split_summary = {
        "seed": args.seed,
        "test_ratio": args.test_ratio,
        "n_total": len(records),
        "n_train": len(train_records),
        "n_test": len(test_records),
        "per_lang": per_lang,
        "per_clean_candidate": per_clean_candidate,
    }
    emit_json(dataset_root / "split_summary.json", split_summary)

    print(f"总样本: {len(records)}")
    print(f"train: {len(train_records)}")
    print(f"test: {len(test_records)}")
    print("\n按语言统计:")
    for lang, counts in per_lang.items():
        print(f"  {lang}: train={counts['train']} test={counts['test']}")
    print("\n按 clean_candidate 统计:")
    for candidate, counts in per_clean_candidate.items():
        print(f"  {candidate}: train={counts['train']} test={counts['test']}")


if __name__ == "__main__":
    main()
