#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List


def run_stage(
    stage_name: str,
    cmd: List[str],
    *,
    cwd: Path,
    log_path: Path,
    env: dict[str, str],
    done_path: Path,
) -> None:
    if done_path.exists():
        print(f"[skip] {stage_name}: {done_path}", flush=True)
        return
    log_path.parent.mkdir(parents=True, exist_ok=True)
    attempt = 0
    while not done_path.exists():
        attempt += 1
        start = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[launch] {stage_name} attempt={attempt}", flush=True)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"\n[{start}] launch: {' '.join(cmd)}\n")
            log.flush()
            proc = subprocess.run(
                cmd,
                cwd=str(cwd),
                stdout=log,
                stderr=subprocess.STDOUT,
                env=env,
                check=False,
            )
            end = time.strftime("%Y-%m-%d %H:%M:%S")
            log.write(f"[{end}] exit_code={proc.returncode}\n")
            log.flush()
        print(f"[exit] {stage_name} attempt={attempt} exit_code={proc.returncode}", flush=True)
        if done_path.exists():
            print(f"[done] {stage_name}: {done_path}", flush=True)
            return
        time.sleep(2.0)


def default_discovery_root(method: str) -> Path:
    mapping = {
        "relp": Path("/root/autodl-tmp/project-ReIP/project copy"),
        "eap_ig": Path("/root/autodl-tmp/project-EAP-IG/project copy"),
    }
    return mapping[method]


def build_discovery_env(local_root: Path, discovery_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    src_paths = [str(local_root / "src")]
    discovery_src = str(discovery_root / "src")
    if discovery_src not in src_paths:
        src_paths.append(discovery_src)
    existing = env.get("PYTHONPATH", "")
    if existing:
        src_paths.append(existing)
    env["PYTHONPATH"] = ":".join(src_paths)
    env["PYTORCH_CUDA_ALLOC_CONF"] = env.get("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    return env


def append_if_present(cmd: List[str], flag: str, value: int) -> None:
    if value > 0:
        cmd.extend([flag, str(value)])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RelP or EAP-IG discovery, then the local signed-circuit pipeline.")
    parser.add_argument("--method", choices=["relp", "eap_ig"], required=True)
    parser.add_argument("--run-root", type=str, required=True)
    parser.add_argument("--dataset-root", type=str, required=True)
    parser.add_argument("--model-path", type=str, required=True)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--discovery-project-root", type=str, default="")
    parser.add_argument("--skip-plots", action="store_true")
    parser.add_argument("--relp-head-score-mode", type=str, default="approx_proxy")
    parser.add_argument("--relp-ct-head-mode", dest="legacy_relp_head_score_mode", type=str, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--relp-mlp-mode", type=str, default="approx_proxy")
    parser.add_argument("--eap-ig-steps", type=int, default=6)
    parser.add_argument("--eap-edge-counts", type=str, default="12,20,28,40")
    parser.add_argument("--discovery-max-samples", type=int, default=0)
    parser.add_argument("--causal-eval-max-samples", type=int, default=0)
    parser.add_argument("--functional-validate-max-samples", type=int, default=0)
    parser.add_argument("--family-mediation-max-samples", type=int, default=0)
    parser.add_argument("--node-importance-max-samples", type=int, default=0)
    parser.add_argument("--edge-importance-max-samples", type=int, default=0)
    parser.add_argument("--edge-importance-max-edges", type=int, default=0)
    parser.add_argument("--trajectory-max-samples", type=int, default=0)
    args = parser.parse_args()

    local_root = Path(__file__).resolve().parents[1]
    discovery_root = (
        Path(args.discovery_project_root).resolve()
        if args.discovery_project_root
        else default_discovery_root(args.method)
    )
    run_root = Path(args.run_root).resolve()
    run_root.mkdir(parents=True, exist_ok=True)

    env = build_discovery_env(local_root, discovery_root)
    py = sys.executable
    dataset_root = str(Path(args.dataset_root).resolve())
    model_path = str(Path(args.model_path).resolve())
    device = args.device

    forward_batch = run_root / "forward_batch"
    forward_agg = run_root / "forward_aggregate"
    reverse_batch = run_root / "reverse_batch"
    reverse_agg = run_root / "reverse_aggregate"
    bidirectional = run_root / "bidirectional"
    causal_aligned = run_root / "causal_aligned"
    causal_full = run_root / "causal_full"
    head_reads = run_root / "head_reads"
    signed_circuit = run_root / "final_signed_circuit"
    signed_validate = run_root / "signed_validate"
    token_flip = run_root / "token_flip"
    signed_families = run_root / "final_signed_families"
    signed_family_mediation = run_root / "signed_family_mediation"
    signed_composition = run_root / "signed_composition"
    node_importance = run_root / "node_importance"
    edge_importance = run_root / "edge_importance"
    signed_trajectory = run_root / "signed_layer_trajectory"
    functional_groups = run_root / "functional_groups"
    functional_validate = run_root / "functional_validate"
    final_report = run_root / "FINAL_REPORT.md"

    if args.method == "relp":
        relp_head_score_mode = args.relp_head_score_mode if args.legacy_relp_head_score_mode is None else args.legacy_relp_head_score_mode
        forward_cmd = [
            py, str(discovery_root / "scripts" / "mine_toolcall_batch.py"),
            "--source", "dataset",
            "--dataset-root", dataset_root,
            "--model-path", model_path,
            "--out-root", str(forward_batch),
            "--device", device,
            "--resume",
            "--objective-kind", "kl",
            "--attribution-backend", "relp",
            "--ct-head-mode", relp_head_score_mode,
            "--mlp-mode", args.relp_mlp_mode,
        ]
        reverse_cmd = [
            py, str(discovery_root / "scripts" / "mine_toolcall_reverse_batch.py"),
            "--source", "dataset",
            "--dataset-root", dataset_root,
            "--model-path", model_path,
            "--out-root", str(reverse_batch),
            "--device", device,
            "--resume",
            "--objective-kind", "kl",
            "--attribution-backend", "relp",
            "--ct-head-mode", relp_head_score_mode,
            "--mlp-mode", args.relp_mlp_mode,
        ]
    else:
        forward_cmd = [
            py, str(discovery_root / "scripts" / "mine_toolcall_eap_ig_batch.py"),
            "--direction", "forward",
            "--source", "dataset",
            "--dataset-root", dataset_root,
            "--model-path", model_path,
            "--out-root", str(forward_batch),
            "--device", device,
            "--resume",
            "--ig-steps", str(args.eap_ig_steps),
            "--edge-counts", args.eap_edge_counts,
        ]
        reverse_cmd = [
            py, str(discovery_root / "scripts" / "mine_toolcall_eap_ig_batch.py"),
            "--direction", "reverse",
            "--source", "dataset",
            "--dataset-root", dataset_root,
            "--model-path", model_path,
            "--out-root", str(reverse_batch),
            "--device", device,
            "--resume",
            "--ig-steps", str(args.eap_ig_steps),
            "--edge-counts", args.eap_edge_counts,
        ]

    append_if_present(forward_cmd, "--max-samples", args.discovery_max_samples)
    append_if_present(reverse_cmd, "--max-samples", args.discovery_max_samples)
    if args.skip_plots:
        forward_cmd.append("--skip-plots")
        reverse_cmd.append("--skip-plots")

    stages = [
        (
            "forward_batch",
            forward_batch / "batch_summary.json",
            forward_cmd,
            run_root / "logs" / "01_forward_batch.log",
        ),
        (
            "forward_aggregate",
            forward_agg / "global_core_summary.json",
            [
                py, str(local_root / "scripts" / "aggregate_toolcall_behavior.py"),
                "--input-root", str(forward_batch),
                "--output-root", str(forward_agg),
                "--model-path", model_path,
                "--device", device,
                "--summary-label", f"{args.method}_forward_kl",
                "--skip-replay",
            ],
            run_root / "logs" / "02_forward_aggregate.log",
        ),
        (
            "reverse_batch",
            reverse_batch / "batch_summary.json",
            reverse_cmd,
            run_root / "logs" / "03_reverse_batch.log",
        ),
        (
            "reverse_aggregate",
            reverse_agg / "global_core_summary.json",
            [
                py, str(local_root / "scripts" / "aggregate_toolcall_behavior.py"),
                "--input-root", str(reverse_batch),
                "--output-root", str(reverse_agg),
                "--model-path", model_path,
                "--device", device,
                "--output-node-label", "Residual Output: no_tool",
                "--summary-label", f"{args.method}_reverse_kl",
                "--skip-replay",
            ],
            run_root / "logs" / "04_reverse_aggregate.log",
        ),
        (
            "bidirectional",
            bidirectional / "bidirectional_summary.json",
            [
                py, str(local_root / "scripts" / "analyze_toolcall_bidirectional.py"),
                "--forward-batch-root", str(forward_batch),
                "--forward-aggregate-summary", str(forward_agg / "global_core_summary.json"),
                "--reverse-batch-root", str(reverse_batch),
                "--reverse-aggregate-summary", str(reverse_agg / "global_core_summary.json"),
                "--output-root", str(bidirectional),
            ],
            run_root / "logs" / "05_bidirectional.log",
        ),
        (
            "causal_aligned",
            causal_aligned / "cross_eval_summary.json",
            [
                py, str(local_root / "scripts" / "evaluate_toolcall_bidirectional_causal.py"),
                "--forward-batch-root", str(forward_batch),
                "--forward-aggregate-summary", str(forward_agg / "global_core_summary.json"),
                "--reverse-aggregate-summary", str(reverse_agg / "global_core_summary.json"),
                "--bidirectional-summary", str(bidirectional / "bidirectional_summary.json"),
                "--model-path", model_path,
                "--device", device,
                "--max-samples", str(args.causal_eval_max_samples),
                "--matrix", "aligned",
                "--output-root", str(causal_aligned),
            ],
            run_root / "logs" / "06_causal_aligned.log",
        ),
        (
            "causal_full",
            causal_full / "cross_eval_summary.json",
            [
                py, str(local_root / "scripts" / "evaluate_toolcall_bidirectional_causal.py"),
                "--forward-batch-root", str(forward_batch),
                "--forward-aggregate-summary", str(forward_agg / "global_core_summary.json"),
                "--reverse-aggregate-summary", str(reverse_agg / "global_core_summary.json"),
                "--bidirectional-summary", str(bidirectional / "bidirectional_summary.json"),
                "--model-path", model_path,
                "--device", device,
                "--max-samples", str(args.causal_eval_max_samples),
                "--matrix", "full",
                "--output-root", str(causal_full),
            ],
            run_root / "logs" / "07_causal_full.log",
        ),
        (
            "head_reads",
            head_reads / "head_read_report.json",
            [
                py, str(local_root / "scripts" / "analyze_toolcall_bidirectional_head_reads.py"),
                "--dataset-root", dataset_root,
                "--reverse-batch-root", str(reverse_batch),
                "--forward-aggregate-summary", str(forward_agg / "global_core_summary.json"),
                "--reverse-aggregate-summary", str(reverse_agg / "global_core_summary.json"),
                "--bidirectional-summary", str(bidirectional / "bidirectional_summary.json"),
                "--model-path", model_path,
                "--device", device,
                "--output-root", str(head_reads),
            ],
            run_root / "logs" / "08_head_reads.log",
        ),
        (
            "signed_circuit",
            signed_circuit / "final_signed_circuit_summary.json",
            [
                py, str(local_root / "scripts" / "build_toolcall_signed_circuit.py"),
                "--bidirectional-summary", str(bidirectional / "bidirectional_summary.json"),
                "--node-support-csv", str(bidirectional / "node_bidirectional_support.csv"),
                "--edge-support-csv", str(bidirectional / "edge_bidirectional_support.csv"),
                "--head-read-csv", str(head_reads / "per_head_read_mass.csv"),
                "--output-root", str(signed_circuit),
            ],
            run_root / "logs" / "09_signed_circuit.log",
        ),
        (
            "signed_validate",
            signed_validate / "signed_group_report.json",
            [
                py, str(local_root / "scripts" / "validate_toolcall_signed_circuit.py"),
                "--forward-batch-root", str(forward_batch),
                "--forward-aggregate-summary", str(forward_agg / "global_core_summary.json"),
                "--reverse-aggregate-summary", str(reverse_agg / "global_core_summary.json"),
                "--bidirectional-summary", str(bidirectional / "bidirectional_summary.json"),
                "--model-path", model_path,
                "--device", device,
                "--output-root", str(signed_validate),
            ],
            run_root / "logs" / "10_signed_validate.log",
        ),
        (
            "token_flip",
            token_flip / "group_token_flip_summary.json",
            [
                py, str(local_root / "scripts" / "evaluate_toolcall_bidirectional_token_flip.py"),
                "--forward-batch-root", str(forward_batch),
                "--forward-aggregate-summary", str(forward_agg / "global_core_summary.json"),
                "--reverse-aggregate-summary", str(reverse_agg / "global_core_summary.json"),
                "--bidirectional-summary", str(bidirectional / "bidirectional_summary.json"),
                "--model-path", model_path,
                "--device", device,
                "--output-root", str(token_flip),
            ],
            run_root / "logs" / "11_token_flip.log",
        ),
        (
            "signed_families",
            signed_families / "signed_family_summary.json",
            [
                py, str(local_root / "scripts" / "analyze_toolcall_signed_families.py"),
                "--signed-edges-csv", str(signed_circuit / "final_signed_edges.csv"),
                "--output-root", str(signed_families),
            ],
            run_root / "logs" / "12_signed_families.log",
        ),
        (
            "signed_family_mediation",
            signed_family_mediation / "signed_family_mediation_report.json",
            [
                py, str(local_root / "scripts" / "evaluate_toolcall_signed_family_mediation.py"),
                "--forward-batch-root", str(forward_batch),
                "--bidirectional-summary", str(bidirectional / "bidirectional_summary.json"),
                "--signed-family-summary-csv", str(signed_families / "signed_family_summary.csv"),
                "--model-path", model_path,
                "--device", device,
                "--max-samples", str(args.family_mediation_max_samples),
                "--output-root", str(signed_family_mediation),
            ],
            run_root / "logs" / "13_family_mediation.log",
        ),
        (
            "signed_composition",
            signed_composition / "signed_composition_report.json",
            [
                py, str(local_root / "scripts" / "evaluate_toolcall_signed_composition.py"),
                "--forward-batch-root", str(forward_batch),
                "--bidirectional-summary", str(bidirectional / "bidirectional_summary.json"),
                "--model-path", model_path,
                "--device", device,
                "--output-root", str(signed_composition),
            ],
            run_root / "logs" / "14_signed_composition.log",
        ),
        (
            "node_importance",
            node_importance / "signed_node_importance_report.json",
            [
                py, str(local_root / "scripts" / "evaluate_toolcall_signed_node_importance.py"),
                "--forward-batch-root", str(forward_batch),
                "--bidirectional-summary", str(bidirectional / "bidirectional_summary.json"),
                "--signed-nodes-csv", str(signed_circuit / "final_signed_nodes.csv"),
                "--model-path", model_path,
                "--device", device,
                "--max-samples", str(args.node_importance_max_samples),
                "--output-root", str(node_importance),
            ],
            run_root / "logs" / "15_node_importance.log",
        ),
        (
            "edge_importance",
            edge_importance / "signed_edge_mediation_report.json",
            [
                py, str(local_root / "scripts" / "evaluate_toolcall_signed_edge_importance.py"),
                "--forward-batch-root", str(forward_batch),
                "--signed-edges-csv", str(signed_circuit / "final_signed_edges.csv"),
                "--model-path", model_path,
                "--device", device,
                "--max-samples", str(args.edge_importance_max_samples),
                "--max-edges", str(args.edge_importance_max_edges),
                "--output-root", str(edge_importance),
            ],
            run_root / "logs" / "16_edge_importance.log",
        ),
        (
            "signed_trajectory",
            signed_trajectory / "signed_layer_trajectory_report.json",
            [
                py, str(local_root / "scripts" / "analyze_toolcall_signed_layer_trajectory.py"),
                "--forward-batch-root", str(forward_batch),
                "--bidirectional-summary", str(bidirectional / "bidirectional_summary.json"),
                "--model-path", model_path,
                "--device", device,
                "--max-samples", str(args.trajectory_max_samples),
                "--output-root", str(signed_trajectory),
            ],
            run_root / "logs" / "17_signed_trajectory.log",
        ),
        (
            "functional_groups",
            functional_groups / "functional_group_summary.json",
            [
                py, str(local_root / "scripts" / "analyze_toolcall_functional_groups.py"),
                "--signed-nodes-csv", str(signed_circuit / "final_signed_nodes.csv"),
                "--signed-edges-csv", str(signed_circuit / "final_signed_edges.csv"),
                "--head-read-csv", str(head_reads / "per_head_read_mass.csv"),
                "--node-importance-csv", str(node_importance / "signed_node_importance_summary.csv"),
                "--output-root", str(functional_groups),
            ],
            run_root / "logs" / "18_functional_groups.log",
        ),
        (
            "functional_validate",
            functional_validate / "functional_group_report.json",
            [
                py, str(local_root / "scripts" / "evaluate_toolcall_functional_groups.py"),
                "--forward-batch-root", str(forward_batch),
                "--functional-group-json", str(functional_groups / "functional_group_summary.json"),
                "--model-path", model_path,
                "--device", device,
                "--max-samples", str(args.functional_validate_max_samples),
                "--output-root", str(functional_validate),
            ],
            run_root / "logs" / "19_functional_validate.log",
        ),
        (
            "final_report",
            final_report,
            [
                py, str(local_root / "scripts" / "build_toolcall_final_report.py"),
                "--run-root", str(run_root),
                "--output", str(final_report),
            ],
            run_root / "logs" / "20_final_report.log",
        ),
    ]

    for stage_name, done_path, cmd, log_path in stages:
        run_stage(stage_name, cmd, cwd=local_root, log_path=log_path, env=env, done_path=done_path)


if __name__ == "__main__":
    main()
