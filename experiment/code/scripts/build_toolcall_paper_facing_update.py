#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    if not rows:
        return
    fieldnames: List[str] = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: object, digits: int = 3) -> str:
    try:
        value = float(value)
    except Exception:
        return str(value)
    if not math.isfinite(value):
        return "nan"
    return f"{value:.{digits}f}"


def finite(values: Iterable[float]) -> List[float]:
    return [float(v) for v in values if isinstance(v, (int, float)) and math.isfinite(float(v))]


def plot_q1_reader_vs_writer(data_root: Path, out_path: Path) -> None:
    rep = pd.read_csv(data_root / "delivery_object_2x2_strict_representation_summary.csv")
    patch = pd.read_csv(data_root / "delivery_object_2x2_strict_patch_summary.csv")
    direction = pd.read_csv(data_root / "delivery_object_direction_intervention_summary.csv")

    rep = rep[rep["space"].isin(["l2h14_lead_k", "l2h14_z", "mlp11_out"])].copy()
    rep["label"] = rep["space"].map(
        {
            "l2h14_lead_k": "L2H14 lead-k",
            "l2h14_z": "L2H14 z",
            "mlp11_out": "MLP11 out",
        }
    )
    patch = patch[patch["frame"] == "write"].copy()
    patch["label"] = patch["node"]
    direction = direction[
        (direction["frame"] == "write") & (direction["mode"] == "inject_file_into_answer") & (direction["node"].isin(["L2H14", "MLP11"]))
    ].copy()
    direction["label"] = direction["node"]

    plt.style.use("default")
    fig, axes = plt.subplots(2, 2, figsize=(13.0, 9.0), constrained_layout=True)

    ax = axes[0, 0]
    xs = np.arange(len(rep))
    ax.bar(xs, rep["object_minus_frame_cosine_median"], color=["#c44e52", "#dd8452", "#4c72b0"])
    ax.axhline(0.0, color="#666666", linewidth=1.0)
    ax.set_xticks(xs, rep["label"], rotation=18, ha="right")
    ax.set_title("Object Dominance Over Frame")
    ax.set_ylabel("same-object minus same-frame cosine")

    ax = axes[0, 1]
    ax.bar(xs, rep["object_wins_rate"], color=["#c44e52", "#dd8452", "#4c72b0"])
    ax.set_xticks(xs, rep["label"], rotation=18, ha="right")
    ax.set_ylim(0.0, 1.05)
    ax.set_title("Object Wins Rate")
    ax.set_ylabel("rate")

    ax = axes[1, 0]
    metrics = ["file_rescue_ratio_median", "object_decision_score_median", "object_boundary_flip_rate", "tool_top1_rate"]
    metric_labels = ["whole-node rescue", "object decision", "boundary flip", "tool top-1"]
    x = np.arange(len(metrics))
    width = 0.38
    l2 = patch[patch["node"] == "L2H14"].iloc[0]
    m11 = patch[patch["node"] == "MLP11"].iloc[0]
    ax.bar(x - width / 2, [float(l2[m]) for m in metrics], width=width, label="L2H14", color="#dd8452")
    ax.bar(x + width / 2, [float(m11[m]) for m in metrics], width=width, label="MLP11", color="#4c72b0")
    ax.axhline(0.0, color="#666666", linewidth=1.0)
    ax.set_xticks(x, metric_labels, rotation=18, ha="right")
    ax.set_title("Whole-Node Causal Contrast")
    ax.legend(frameon=False)

    ax = axes[1, 1]
    metrics = ["object_score_delta_median", "tool_token_delta_median", "distractor_token_delta_median", "MLP27_projection_delta_median"]
    metric_labels = ["object score", "<tool_call> logit", "no_tool logit", "MLP27 proj"]
    x = np.arange(len(metrics))
    l2 = direction[direction["node"] == "L2H14"].iloc[0]
    m11 = direction[direction["node"] == "MLP11"].iloc[0]
    ax.bar(x - width / 2, [float(l2[m]) for m in metrics], width=width, label="L2H14", color="#dd8452")
    ax.bar(x + width / 2, [float(m11[m]) for m in metrics], width=width, label="MLP11", color="#4c72b0")
    ax.axhline(0.0, color="#666666", linewidth=1.0)
    ax.set_xticks(x, metric_labels, rotation=18, ha="right")
    ax.set_title("Direction-Only Causal Contrast")
    ax.legend(frameon=False)

    fig.suptitle("Earliest Reader vs First Stable Writer", fontsize=14)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_q1_stagewise_accumulation(data_root: Path, out_path: Path) -> None:
    direction = pd.read_csv(data_root / "delivery_object_direction_intervention_summary.csv")
    rows = direction[(direction["node"] == "MLP11") & (direction["mode"] == "inject_file_into_answer")].copy()
    node_cols = [
        "MLP11_projection_delta_median",
        "MLP16_projection_delta_median",
        "MLP19_projection_delta_median",
        "L20H5_projection_delta_median",
        "L21H12_projection_delta_median",
        "L24H6_projection_delta_median",
        "MLP27_projection_delta_median",
    ]
    labels = ["MLP11", "MLP16", "MLP19", "L20H5", "L21H12", "L24H6", "MLP27"]

    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(10.8, 5.6), constrained_layout=True)
    x = np.arange(len(labels))
    for frame, color in [("write", "#4c72b0"), ("develop", "#c44e52")]:
        row = rows[rows["frame"] == frame].iloc[0]
        ys = [max(float(row[col]), 1e-3) for col in node_cols]
        ax.plot(x, ys, marker="o", linewidth=2.3, color=color, label=frame)
        for xi, yi in zip(x, ys):
            ax.text(xi, yi * 1.08, fmt(yi, 1), ha="center", va="bottom", fontsize=8, color=color)
    ax.set_yscale("log")
    ax.set_xticks(x, labels)
    ax.set_ylabel("projection delta (log scale)")
    ax.set_title("Stagewise Amplification of the Shared File-vs-Answer Axis")
    ax.legend(frameon=False, title="frame")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_q1_projection_heatmap(data_root: Path, out_path: Path) -> None:
    direction = pd.read_csv(data_root / "delivery_object_direction_intervention_summary.csv")
    rows = direction[(direction["node"] == "MLP11")].copy()
    order = [
        ("write", "inject_file_into_answer", "write inject"),
        ("write", "erase_file_component", "write erase"),
        ("develop", "inject_file_into_answer", "develop inject"),
        ("develop", "erase_file_component", "develop erase"),
    ]
    cols = [
        "MLP11_projection_delta_median",
        "MLP16_projection_delta_median",
        "MLP19_projection_delta_median",
        "L20H5_projection_delta_median",
        "L21H1_projection_delta_median",
        "L21H12_projection_delta_median",
        "L24H6_projection_delta_median",
        "MLP27_projection_delta_median",
    ]
    labels = ["MLP11", "MLP16", "MLP19", "L20H5", "L21H1", "L21H12", "L24H6", "MLP27"]
    mat = np.zeros((len(order), len(cols)))
    row_labels = []
    for i, (frame, mode, label) in enumerate(order):
        row = rows[(rows["frame"] == frame) & (rows["mode"] == mode)].iloc[0]
        row_labels.append(label)
        for j, col in enumerate(cols):
            mat[i, j] = float(row[col])
    vmax = np.nanpercentile(np.abs(mat), 98)
    vmax = max(float(vmax), 1.0)

    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(11.0, 4.8), constrained_layout=True)
    im = ax.imshow(mat, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(np.arange(len(labels)), labels, rotation=18, ha="right")
    ax.set_yticks(np.arange(len(row_labels)), row_labels)
    ax.set_title("Downstream Projection Trajectory Under MLP11 Direction Edits")
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, fmt(mat[i, j], 1), ha="center", va="center", fontsize=8)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label("projection delta")
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_q1_final_writer_effect(data_root: Path, out_path: Path) -> None:
    direction = pd.read_csv(data_root / "delivery_object_direction_intervention_summary.csv")
    rows = direction[direction["node"] == "MLP11"].copy()
    metrics = [
        ("object_score_delta_median", "object score"),
        ("tool_token_delta_median", "<tool_call> logit"),
        ("distractor_token_delta_median", "no_tool logit"),
        ("MLP27_projection_delta_median", "MLP27 proj"),
    ]

    plt.style.use("default")
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.8), constrained_layout=True)
    for ax, frame, title in zip(axes, ["write", "develop"], ["write frame", "develop frame"]):
        inject = rows[(rows["frame"] == frame) & (rows["mode"] == "inject_file_into_answer")].iloc[0]
        erase = rows[(rows["frame"] == frame) & (rows["mode"] == "erase_file_component")].iloc[0]
        x = np.arange(len(metrics))
        width = 0.38
        ax.bar(x - width / 2, [float(inject[m]) for m, _ in metrics], width=width, label="inject file", color="#4c72b0")
        ax.bar(x + width / 2, [float(erase[m]) for m, _ in metrics], width=width, label="erase file", color="#c44e52")
        ax.axhline(0.0, color="#666666", linewidth=1.0)
        ax.set_xticks(x, [label for _, label in metrics], rotation=18, ha="right")
        ax.set_title(title)
        ax.legend(frameon=False)
    fig.suptitle("Final Writer Effect of the MLP11 Shared Direction", fontsize=14)
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_q2_residual_projection(data_root: Path, out_path: Path) -> None:
    proj = pd.read_csv(data_root / "suppression_projection_summary.csv")
    intervention = pd.read_csv(data_root / "suppression_intervention_summary.csv")
    order = ["L16H4", "MLP17", "L23H6"]
    proj = proj.set_index("node").loc[order].reset_index()
    intervention = intervention.set_index("node").loc[order].reset_index()

    plt.style.use("default")
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.8), constrained_layout=True)
    x = np.arange(len(order))
    width = 0.35

    axes[0].bar(x - width / 2, proj["tool_logit_delta_median"], width=width, label="delta <tool_call>", color="#c44e52")
    axes[0].bar(x + width / 2, proj["no_tool_logit_delta_median"], width=width, label="delta no_tool", color="#4c72b0")
    axes[0].axhline(0.0, color="#666666", linewidth=1.0)
    axes[0].set_xticks(x, order)
    axes[0].set_title("Clean->Corrupt Residual Projection Shift")
    axes[0].legend(frameon=False)

    axes[1].bar(x - width / 2, intervention["tool_token_delta_median"], width=width, label="inject: <tool_call>", color="#c44e52")
    axes[1].bar(x + width / 2, intervention["no_tool_token_delta_median"], width=width, label="inject: no_tool", color="#4c72b0")
    axes[1].axhline(0.0, color="#666666", linewidth=1.0)
    axes[1].set_xticks(x, order)
    axes[1].set_title("Direction Inject into Clean")
    axes[1].legend(frameon=False)

    fig.suptitle("How the No-Tool Chain Changes Output-Side Residual Evidence", fontsize=14)
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_q2_tool_ingress_disturbance(data_root: Path, out_path: Path) -> None:
    intervention = pd.read_csv(data_root / "suppression_intervention_summary.csv")
    row = intervention[intervention["node"] == "MLP17"].iloc[0]
    labels = ["L20H5", "L21H1", "L21H12", "L24H6", "MLP27"]
    values = [float(row[f"{label}_projection_delta_median"]) for label in labels]

    plt.style.use("default")
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.8), constrained_layout=True)
    x = np.arange(len(labels))
    axes[0].bar(x, values, color="#4c72b0")
    axes[0].axhline(0.0, color="#666666", linewidth=1.0)
    axes[0].set_xticks(x, labels, rotation=18, ha="right")
    axes[0].set_title("MLP17 Inject: Local No-Tool Axis Shift")
    axes[0].set_ylabel("projection delta")

    token_labels = ["<tool_call>", "no_tool", "decision"]
    token_values = [
        float(row["tool_token_delta_median"]),
        float(row["no_tool_token_delta_median"]),
        float(row["decision_score_delta_median"]),
    ]
    axes[1].bar(np.arange(3), token_values, color=["#c44e52", "#4c72b0", "#8172b2"])
    axes[1].axhline(0.0, color="#666666", linewidth=1.0)
    axes[1].set_xticks(np.arange(3), token_labels, rotation=18, ha="right")
    axes[1].set_title("Same Inject: Final Output Shift")

    fig.suptitle("MLP17 Directly Disturbs the Tool Ingress Route", fontsize=14)
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_q2_suppression_heatmap(data_root: Path, out_path: Path) -> None:
    intervention = pd.read_csv(data_root / "suppression_intervention_summary.csv")
    order = ["L16H4", "MLP17", "L23H6"]
    cols = [
        "tool_token_delta_median",
        "no_tool_token_delta_median",
        "decision_score_delta_median",
        "L20H5_projection_delta_median",
        "L21H1_projection_delta_median",
        "L21H12_projection_delta_median",
        "L24H6_projection_delta_median",
        "MLP27_projection_delta_median",
    ]
    labels = ["<tool_call>", "no_tool", "decision", "L20H5", "L21H1", "L21H12", "L24H6", "MLP27"]
    mat = np.zeros((len(order), len(cols)))
    raw = np.zeros_like(mat)
    for i, node in enumerate(order):
        row = intervention[intervention["node"] == node].iloc[0]
        for j, col in enumerate(cols):
            raw[i, j] = float(row[col])
    for j in range(raw.shape[1]):
        denom = max(np.max(np.abs(raw[:, j])), 1e-6)
        mat[:, j] = raw[:, j] / denom

    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(11.8, 4.5), constrained_layout=True)
    im = ax.imshow(mat, cmap="RdBu_r", vmin=-1.0, vmax=1.0, aspect="auto")
    ax.set_xticks(np.arange(len(labels)), labels, rotation=18, ha="right")
    ax.set_yticks(np.arange(len(order)), order)
    ax.set_title("Suppression Heatmap (column-normalized, raw values annotated)")
    for i in range(raw.shape[0]):
        for j in range(raw.shape[1]):
            ax.text(j, i, fmt(raw[i, j], 2), ha="center", va="center", fontsize=8)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label("normalized effect by column")
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_q2_stagewise(data_root: Path, out_path: Path) -> None:
    stage = pd.read_csv(data_root / "suppression_stagewise_summary.csv").sort_values("step_idx")
    x = np.arange(len(stage))
    labels = ["L16H4", "+MLP17", "+L23H6"]

    plt.style.use("default")
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.8), constrained_layout=True)

    axes[0].plot(x, stage["tool_token_delta_median"], marker="o", linewidth=2.2, color="#c44e52", label="<tool_call>")
    axes[0].plot(x, stage["no_tool_token_delta_median"], marker="o", linewidth=2.2, color="#4c72b0", label="no_tool")
    axes[0].plot(x, stage["decision_score_delta_median"], marker="o", linewidth=2.2, color="#8172b2", label="decision")
    axes[0].axhline(0.0, color="#666666", linewidth=1.0)
    axes[0].set_xticks(x, labels)
    axes[0].set_title("Stagewise Output Trajectory")
    axes[0].legend(frameon=False)

    for col, color in [
        ("L20H5_projection_delta_median", "#64b5cd"),
        ("L21H12_projection_delta_median", "#55a868"),
        ("L24H6_projection_delta_median", "#dd8452"),
        ("MLP27_projection_delta_median", "#4c72b0"),
    ]:
        axes[1].plot(x, stage[col], marker="o", linewidth=2.1, label=col.replace("_projection_delta_median", ""), color=color)
    axes[1].axhline(0.0, color="#666666", linewidth=1.0)
    axes[1].set_xticks(x, labels)
    axes[1].set_title("Stagewise Ingress / Writer Shift")
    axes[1].legend(frameon=False)

    fig.suptitle("How the Suppressive State Accumulates Across the No-Tool Chain", fontsize=14)
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_combined_outputs(final_root: Path, figure_specs: Sequence[Dict[str, str]]) -> None:
    data_root = final_root / "data"
    figures_root = final_root / "figures"

    q1_table = pd.read_csv(data_root / "earliest_reader_focused_evidence_table.csv")
    q2_table = pd.read_csv(data_root / "suppression_focused_evidence_table.csv")
    combined_table = pd.concat([q1_table, q2_table], ignore_index=True)
    combined_table.to_csv(data_root / "paper_facing_focused_evidence_table.csv", index=False)

    q1_claims = load_json(data_root / "earliest_reader_claim_tiers.json")
    q2_claims = load_json(data_root / "suppression_claim_tiers.json")
    combined_claims = {
        "question_1": q1_claims,
        "question_2": q2_claims,
        "final_verdict": {
            "question_1_paper_ready": bool(q1_claims.get("paper_grade_status", {}).get("overall")),
            "question_2_paper_ready": bool(q2_claims.get("paper_grade_status", {}).get("overall")),
            "remaining_gap_question_1": "exact microfeature inside L2H14" if not q1_claims.get("paper_grade_status", {}).get("l2h14_exact_microfeature_name") else "",
            "remaining_gap_question_2": "exact microfeature inside L16H4" if not q2_claims.get("paper_grade_status", {}).get("exact_l16h4_microfeature_name") else "",
        },
    }
    (data_root / "paper_facing_claim_tiers.json").write_text(json.dumps(combined_claims, ensure_ascii=False, indent=2), encoding="utf-8")

    still = [
        {
            "issue": "exact_microfeature_inside_l2h14",
            "current_best_answer": "`L2H14` reads an opening-side bundle with a weak shared file-vs-answer component",
            "blocker": "the reader-side component is real but not yet uniquely named at the microfeature level",
            "minimal_next_evidence": "within-opening matched counterfactual or edge-restricted DAS on `L2H14 -> MLP11`",
        },
        {
            "issue": "exact_microfeature_inside_l16h4",
            "current_best_answer": "`L16H4` reads a user-side ordinary-answer bundle concentrated in task-body / tail-suffix tokens",
            "blocker": "the suppressive reader is localized, but the exact subfeature name is still broader than ideal",
            "minimal_next_evidence": "within-task matched counterfactual or edge-restricted DAS on `L16H4 -> MLP17`",
        },
    ]
    write_csv(data_root / "paper_facing_still_unsolved.csv", still)

    figure_plan_lines = [
        "# Paper Figure Plan",
        "",
        "## Q1: Forward Mechanism",
        "",
        "- Figure 18: contrasts `L2H14` against `MLP11` to show weak shared object component vs first stable writer.",
        "- Figure 19: shows stagewise amplification of the shared file-vs-answer axis from `MLP11` to `MLP27`.",
        "- Figure 20: shows node-by-node downstream projection trajectories under `MLP11` direction edits.",
        "- Figure 21: shows the final writer effect on `<tool_call>`, `no_tool`, object score, and `MLP27`.",
        "",
        "## Q2: Suppression Mechanism",
        "",
        "- Figure 22: shows whether the suppressive chain raises `no_tool`, lowers `<tool_call>`, or both.",
        "- Figure 23: shows that `MLP17` directly pushes the tool ingress route toward the no-tool state.",
        "- Figure 24: shows the full suppressive heatmap across chain nodes and downstream targets.",
        "- Figure 25: shows stagewise accumulation across `L16H4 -> MLP17 -> L23H6`.",
        "",
    ]
    (figures_root / "PAPER_FIGURE_PLAN.md").write_text("\n".join(figure_plan_lines), encoding="utf-8")

    report_lines = [
        "# Paper-Facing Mechanism Update",
        "",
        "## 1. Scope",
        "",
        "这份更新不重开 circuit localization 或 correctness。它只回答两个剩余问题：",
        "",
        "1. 为什么最小 lead phrase cue 会沿前向链被读取、传播、放大，并最终把首 token 推到 `<tool_call>`。",
        "2. `L16H4 -> MLP17 -> L23H6` 如何实现真正的 suppressive no-tool mechanism。",
        "",
        "## 2. Question 1: Forward Mechanistic Story",
        "",
        "当前可以强写的主链是：`minimal cue -> L2H14 -> MLP11 -> MLP16 -> MLP19 -> L20H5 -> L21H12 -> L24H6 -> MLP27`。",
        "",
        "- `L2H14` 是最早的 head-level reader，但还不是 first stable delivery-object writer。",
        "- `MLP11` 是 first stable delivery-object writer。",
        "- 只改 `MLP11` 的 shared file-vs-answer direction，就会把同一条对象轴推入 `MLP16 -> MLP19 -> L20H5 -> L21H12 -> L24H6 -> MLP27`。",
        "- 最终后果不是只在中层表里好看，而是直接改变 `<tool_call>` / `no_tool` 与 `MLP27` 的终端写出。",
        "",
        "对应主图：`figure_18` 到 `figure_21`。",
        "",
        "## 3. Question 2: Suppression Mechanistic Story",
        "",
        "当前可以强写的主链是：`L16H4 -> MLP17 -> L23H6`。",
        "",
        "- `L16H4` 读的是 user-side ordinary-answer evidence，集中在 task-body / tail-suffix 一带，而不是 tool schema。",
        "- `MLP17` 是 suppressive writer：它既抬高 `no_tool`，也压低 `<tool_call>`。",
        "- `MLP17` 不只改末端 token；它还把 `L20H5 / L21H1 / L21H12 / L24H6 / MLP27` 推向各自的 local no-tool axis。",
        "- `L23H6` 是 late suppressive relay，把已经写好的 suppressive state 送进输出附近。",
        "",
        "对应主图：`figure_22` 到 `figure_25`。",
        "",
        "## 4. Final Verdict",
        "",
        f"- Question 1 paper-ready: `{combined_claims['final_verdict']['question_1_paper_ready']}`.",
        f"- Question 2 paper-ready: `{combined_claims['final_verdict']['question_2_paper_ready']}`.",
        f"- Remaining Q1 gap: `{combined_claims['final_verdict']['remaining_gap_question_1'] or 'none that blocks main-text writing'}`.",
        f"- Remaining Q2 gap: `{combined_claims['final_verdict']['remaining_gap_question_2'] or 'none that blocks main-text writing'}`.",
        "",
        "## 5. Deliverables",
        "",
        "- `paper_facing_focused_evidence_table.csv`",
        "- `paper_facing_claim_tiers.json`",
        "- `paper_facing_still_unsolved.csv`",
        "- `figures/PAPER_FIGURE_PLAN.md`",
        "- `figure_18` to `figure_25`",
        "",
    ]
    (data_root / "paper_facing_main_report.md").write_text("\n".join(report_lines), encoding="utf-8")

    data_index_rows = [{"filename": path.name, "type": path.suffix.lstrip(".")} for path in sorted(data_root.iterdir()) if path.is_file()]
    write_csv(data_root / "DATA_INDEX.csv", data_index_rows)

    figure_index_rows = load_csv(figures_root / "FIGURE_INDEX.csv")
    existing_files = {row["filename"] for row in figure_index_rows}
    for spec in figure_specs:
        if spec["filename"] in existing_files:
            continue
        figure_index_rows.append(
            {
                "figure": spec["figure"],
                "filename": spec["filename"],
                "title": spec["title"],
                "supports": spec["supports"],
            }
        )
    write_csv(figures_root / "FIGURE_INDEX.csv", figure_index_rows)


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    final_root = project_root / "results" / "final"
    data_root = final_root / "data"
    figures_root = final_root / "figures"
    figures_root.mkdir(parents=True, exist_ok=True)

    plot_q1_reader_vs_writer(data_root, figures_root / "figure_18_earliest_reader_vs_mlp11.png")
    plot_q1_stagewise_accumulation(data_root, figures_root / "figure_19_stagewise_object_axis_accumulation.png")
    plot_q1_projection_heatmap(data_root, figures_root / "figure_20_mlp11_projection_trajectory_heatmap.png")
    plot_q1_final_writer_effect(data_root, figures_root / "figure_21_mlp11_final_writer_effect.png")
    plot_q2_residual_projection(data_root, figures_root / "figure_22_suppressive_residual_projection.png")
    plot_q2_tool_ingress_disturbance(data_root, figures_root / "figure_23_tool_ingress_disturbance.png")
    plot_q2_suppression_heatmap(data_root, figures_root / "figure_24_downstream_suppression_heatmap.png")
    plot_q2_stagewise(data_root, figures_root / "figure_25_suppression_stagewise_trajectory.png")

    figure_specs = [
        {
            "figure": "图18",
            "filename": "figure_18_earliest_reader_vs_mlp11.png",
            "title": "L2H14 与 MLP11 对照图",
            "supports": "它把 earliest reader 的弱共享对象分量与 MLP11 作为 first stable writer 的强因果效应放在同一图里。",
        },
        {
            "figure": "图19",
            "filename": "figure_19_stagewise_object_axis_accumulation.png",
            "title": "Shared Object Axis 的逐层放大",
            "supports": "它展示 `MLP11 -> MLP16 -> MLP19 -> L20H5 -> L21H12 -> L24H6 -> MLP27` 如何逐层放大同一条 file-vs-answer 方向。",
        },
        {
            "figure": "图20",
            "filename": "figure_20_mlp11_projection_trajectory_heatmap.png",
            "title": "MLP11 编辑后的下游投影轨迹热图",
            "supports": "它把 `MLP11` direction edit 对各个下游节点的同轴投影变化做成论文主图，而不是停留在 CSV。",
        },
        {
            "figure": "图21",
            "filename": "figure_21_mlp11_final_writer_effect.png",
            "title": "MLP11 对最终 Writer 的影响",
            "supports": "它直接显示 `MLP11` shared direction 如何改变 `<tool_call>`、`no_tool`、object score 和 `MLP27` 的最终写出。",
        },
        {
            "figure": "图22",
            "filename": "figure_22_suppressive_residual_projection.png",
            "title": "Suppressive Residual Projection",
            "supports": "它回答 no-tool 链是在抬高 `no_tool`、压低 `<tool_call>`，还是两者同时发生。",
        },
        {
            "figure": "图23",
            "filename": "figure_23_tool_ingress_disturbance.png",
            "title": "Tool Ingress Disturbance",
            "supports": "它显示 `MLP17` 的 suppressive direction 会直接把 `L20H5/L21H1/L21H12/L24H6/MLP27` 推向 no-tool 侧。",
        },
        {
            "figure": "图24",
            "filename": "figure_24_downstream_suppression_heatmap.png",
            "title": "Downstream Suppression Heatmap",
            "supports": "它把 `L16H4 / MLP17 / L23H6` 三个 intervention 对输出和 tool ingress 的影响汇总成真正的 suppressive heatmap。",
        },
        {
            "figure": "图25",
            "filename": "figure_25_suppression_stagewise_trajectory.png",
            "title": "Suppression Stagewise Trajectory",
            "supports": "它展示 suppressive state 如何沿 `L16H4 -> MLP17 -> L23H6` 逐层积累并进入输出附近。",
        },
    ]
    build_combined_outputs(final_root, figure_specs)


if __name__ == "__main__":
    main()
