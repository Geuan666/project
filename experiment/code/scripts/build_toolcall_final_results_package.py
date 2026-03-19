#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import textwrap
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import matplotlib.pyplot as plt
import numpy as np


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def copy_file(src: Path, dst: Path) -> None:
    if src.resolve() == dst.resolve():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2))


def write_csv(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def find_summary_row(rows: Sequence[dict], key: str, value: str) -> dict:
    for row in rows:
        if str(row.get(key)) == str(value):
            return row
    raise KeyError(f"Could not find row where {key} == {value!r}")


def short_variant_label(name: str) -> str:
    mapping = {
        "clean_full": "clean",
        "corrupt_full": "corrupt",
        "clean_with_corrupt_instruction": "clean+corrupt instruction",
        "corrupt_with_clean_instruction": "corrupt+clean instruction",
        "clean_with_corrupt_lead": "clean+corrupt lead",
        "corrupt_with_clean_lead": "corrupt+clean lead",
        "clean_no_schema": "no schema",
        "clean_schema_mismatch": "schema mismatch",
        "clean_no_protocol": "no protocol",
    }
    return mapping.get(name, name)


def format_float(value: float, digits: int = 3) -> str:
    if value is None or not math.isfinite(float(value)):
        return "NA"
    return f"{float(value):.{digits}f}"


def build_instruction_flip_plot(summary_json: Path, out_path: Path, title: str) -> None:
    data = load_json(summary_json)
    rows = data["variant_summary_rows"]
    labels = [short_variant_label(row["variant"]) for row in rows]
    decision = [float(row["decision_score_median"]) for row in rows]
    tool = [float(row["tool_top1_rate"]) for row in rows]
    no_tool = [float(row["no_tool_top1_rate"]) for row in rows]

    xs = np.arange(len(labels))
    plt.style.use("default")
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.5), constrained_layout=True)
    axes[0].bar(xs, decision, color=["#b2182b" if x > 0 else "#2166ac" for x in decision])
    axes[0].axhline(0.0, color="#666666", linewidth=1.0)
    axes[0].set_title(f"{title}: Decision Score")
    axes[0].set_xticks(xs, labels, rotation=20, ha="right")
    axes[0].set_ylabel("median decision score")

    w = 0.36
    axes[1].bar(xs - w / 2, tool, width=w, label="<tool_call>", color="#b2182b")
    axes[1].bar(xs + w / 2, no_tool, width=w, label="no_tool", color="#2166ac")
    axes[1].set_title(f"{title}: Top-1 Rate")
    axes[1].set_xticks(xs, labels, rotation=20, ha="right")
    axes[1].set_ylim(0.0, 1.05)
    axes[1].legend(frameon=False)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_head_span_heatmap(span_csv: Path, out_path: Path) -> None:
    rows = load_csv(span_csv)
    heads = sorted({row["head"] for row in rows}, key=lambda x: (int(x[1:].split("H")[0]), x))
    spans = ["lead_phrase", "file_target", "function_body_anchor", "tail_suffix", "task_body"]
    matrix = np.zeros((len(heads), len(spans)))
    for i, head in enumerate(heads):
        for j, span in enumerate(spans):
            for row in rows:
                if row["head"] == head and row["span"] == span:
                    matrix[i, j] = float(row["attn_density_median"])
                    break
    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(8.5, 4.8), constrained_layout=True)
    im = ax.imshow(matrix, aspect="auto", cmap="YlOrRd")
    ax.set_title("Key Head Read Density by Span")
    ax.set_xticks(np.arange(len(spans)), spans, rotation=20, ha="right")
    ax.set_yticks(np.arange(len(heads)), heads)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("median attention density")
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_head_qkv_heatmap(qkv_csv: Path, out_path: Path) -> None:
    rows = load_csv(qkv_csv)
    heads = sorted({row["head"] for row in rows}, key=lambda x: (int(x[1:].split("H")[0]), x))
    comps = ["q", "k", "v", "z"]
    matrix = np.zeros((len(heads), len(comps)))
    for i, head in enumerate(heads):
        for j, comp in enumerate(comps):
            for row in rows:
                if row["head"] == head and row["component"] == comp:
                    matrix[i, j] = float(row["rescue_ratio_median"])
                    break
    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(6.8, 4.8), constrained_layout=True)
    im = ax.imshow(matrix, aspect="auto", cmap="RdPu")
    ax.set_title("Key Head Component Rescue by Q/K/V/Z")
    ax.set_xticks(np.arange(len(comps)), comps)
    ax.set_yticks(np.arange(len(heads)), heads)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("median rescue ratio")
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_reverse_overlap_plot(summary_json: Path, out_path: Path) -> None:
    data = load_json(summary_json)
    rows = data["rows"]
    edge_rows = data["edge_rows"]
    order = ["minimal_no_tool", "semantic_no_tool", "reverse_aligned_no_tool"]
    name_map = {
        "minimal_no_tool": "minimal no-tool",
        "semantic_no_tool": "semantic no-tool",
        "reverse_aligned_no_tool": "reverse-aligned no-tool",
    }
    node_recall = [next(float(r["reverse_selective_recall"]) for r in rows if r["name"] == k) for k in order]
    node_jaccard = [next(float(r["reverse_selective_jaccard"]) for r in rows if r["name"] == k) for k in order]
    edge_recall = [next(float(r["reverse_selective_recall"]) for r in edge_rows if r["name"] == k) for k in order]
    edge_jaccard = [next(float(r["reverse_selective_jaccard"]) for r in edge_rows if r["name"] == k) for k in order]

    xs = np.arange(len(order))
    labels = [name_map[k] for k in order]
    plt.style.use("default")
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.8), constrained_layout=True)
    w = 0.36
    axes[0].bar(xs - w / 2, node_recall, width=w, label="node recall", color="#d6604d")
    axes[0].bar(xs + w / 2, node_jaccard, width=w, label="node jaccard", color="#f4a582")
    axes[0].set_ylim(0.0, 1.05)
    axes[0].set_xticks(xs, labels, rotation=20, ha="right")
    axes[0].set_title("No-Tool Line vs Reverse-Selective Nodes")
    axes[0].legend(frameon=False)

    axes[1].bar(xs - w / 2, edge_recall, width=w, label="edge recall", color="#2166ac")
    axes[1].bar(xs + w / 2, edge_jaccard, width=w, label="edge jaccard", color="#67a9cf")
    axes[1].set_ylim(0.0, 1.05)
    axes[1].set_xticks(xs, labels, rotation=20, ha="right")
    axes[1].set_title("No-Tool Line vs Reverse-Selective Edges")
    axes[1].legend(frameon=False)

    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_metrics_overview(source_root: Path) -> dict:
    signed = load_json(source_root / "signed_validate" / "signed_group_report.json")
    functional = load_json(source_root / "functional_groups" / "functional_group_summary.json")
    mech = load_json(source_root / "final_mechanism_evidence" / "final_mechanism_evidence_summary.json")
    query = load_json(source_root / "query_decision_chain" / "query_decision_summary.json")
    instruction = load_json(source_root / "instruction_commitment" / "instruction_commitment_summary.json")
    lead = load_json(source_root / "instruction_lead" / "instruction_lead_summary.json")
    steering = load_json(source_root / "mlp27_steering" / "mlp27_steering_summary.json")
    reverse_overlap = load_json(source_root / "reverse_overlap" / "reverse_overlap_summary.json")
    circuit = load_json(source_root / "final_signed_circuit" / "final_signed_circuit_summary.json")

    full = find_summary_row(signed["summary_rows"], "group", "full_signed_circuit")
    tool_schema = find_summary_row(functional["summary_rows"], "functional_group", "tool_schema_readers")
    suppress = find_summary_row(functional["summary_rows"], "functional_group", "suppression_readers")
    integrators = find_summary_row(functional["summary_rows"], "functional_group", "arbitration_integrators")
    query_last = next(row for row in query["step_summary_rows"] if row["family"] == "query" and int(row["step_idx"]) == 6)
    suppress_last = next(row for row in query["step_summary_rows"] if row["family"] == "suppress" and int(row["step_idx"]) == 3)
    instr_clean_corrupt = find_summary_row(instruction["variant_summary_rows"], "variant", "clean_with_corrupt_instruction")
    lead_clean_corrupt = find_summary_row(lead["variant_summary_rows"], "variant", "clean_with_corrupt_lead")
    steering_corrupt = [row for row in steering["summary_rows"] if row["base_variant"] == "corrupt_full"]

    return {
        "dataset_n": int(full["n_samples"]),
        "circuit_nodes": int(circuit["n_nodes"]),
        "circuit_edges": int(circuit["n_edges"]),
        "full_promote_sufficiency": float(full["promote_suff_ratio_median"]),
        "full_suppress_sufficiency": float(full["suppress_suff_ratio_median"]),
        "full_promote_top1": float(full["promote_tool_top1_rate"]),
        "full_suppress_top1": float(full["suppress_no_tool_top1_rate"]),
        "tool_schema_promote": float(tool_schema["promote_strength_median"]),
        "suppression_promote": float(suppress["promote_strength_median"]),
        "integrator_promote": float(integrators["promote_strength_median"]),
        "query_chain_top1": float(query_last["top1_rate"]),
        "suppress_chain_top1": float(suppress_last["top1_rate"]),
        "instruction_flip_no_tool_top1": float(instr_clean_corrupt["no_tool_top1_rate"]),
        "lead_flip_no_tool_top1": float(lead_clean_corrupt["no_tool_top1_rate"]),
        "mlp27_corrupt_alpha_15_tool_top1": float(
            next(row["tool_top1_rate"] for row in steering_corrupt if float(row["alpha"]) == 1.5)
        ),
        "reverse_aligned_node_jaccard": float(
            next(row["reverse_selective_jaccard"] for row in reverse_overlap["rows"] if row["name"] == "reverse_aligned_no_tool")
        ),
        "reverse_aligned_edge_jaccard": float(
            next(row["reverse_selective_jaccard"] for row in reverse_overlap["edge_rows"] if row["name"] == "reverse_aligned_no_tool")
        ),
        "claim_level_A": len(mech["claim_tree"]["level_A"]),
        "claim_level_B": len(mech["claim_tree"]["level_B"]),
        "claim_level_C": len(mech["claim_tree"]["level_C"]),
    }


def build_package_document(
    final_root: Path,
    metrics: dict,
    mechanism_summary: dict,
    figure_specs: Sequence[dict],
    structural_rows: Sequence[dict],
    functional_rows: Sequence[dict],
    core_components: Sequence[dict],
    full_nodes: Sequence[dict],
) -> str:
    structural_table = "\n".join(
        [
            "| 结构组 | 节点数 | promote sufficiency | suppress sufficiency | 作用 |",
            "|---|---:|---:|---:|---|",
        ]
        + [
            f"| {row['group_label']} | {row['n_nodes']} | {format_float(float(row['promote_suff_ratio_median']))} | {format_float(float(row['suppress_suff_ratio_median']))} | {row['group_label']} 在结构层上的保真度与抑制能力。 |"
            for row in structural_rows
        ]
    )

    functional_table = "\n".join(
        [
            "| 功能组 | 节点 | promote median | suppress median | 解释 |",
            "|---|---|---:|---:|---|",
        ]
        + [
            f"| {row['functional_label']} | {row['nodes']} | {format_float(float(row['promote_strength_median']))} | {format_float(float(row['suppress_strength_median']))} | {row['description']} |"
            for row in functional_rows
        ]
    )

    core_table = "\n".join(
        [
            "| 节点 | 对象语言功能 | 读什么 | 写什么 | 关键证据 |",
            "|---|---|---|---|---|",
        ]
        + [
            f"| {row['component']} | {row['final_function']} | {row['reads'] or '-'} | {row['writes'] or '-'} | {row['direct_evidence']}; {row['path_evidence']}; {row['counterfactual_evidence']} |"
            for row in core_components
        ]
    )

    full_node_table = "\n".join(
        [
            "| 节点 | 层 | 结构组 | 功能组 | 当前语义提示 | 当前证据摘要 |",
            "|---|---:|---|---|---|---|",
        ]
        + [
            f"| {row['node']} | {row['layer']} | {row['structural_group']} | {row['functional_label']} | {row['semantic_hint']} | {row['evidence']} |"
            for row in full_nodes
        ]
    )

    figure_sections = []
    for spec in figure_specs:
        figure_sections.append(
            "\n".join(
                [
                    f"## 图{spec['index']:02d} {spec['title']}",
                    "",
                    f"![图{spec['index']:02d} {spec['title']}](figures/{spec['filename']})",
                    "",
                    f"**怎么看这张图**：{spec['how_to_read']}",
                    "",
                    f"**这张图支持的结论**：{spec['supports']}",
                    "",
                ]
            )
        )

    text = f"""# Tool-Call Circuit Final Package

## 1. 交付说明

这个目录是当前项目的最终整理版交付包。根目录只保留一个 `final` 目录，里面包含：

- `FINAL_PACKAGE.md`：最终总文档。
- `figures/`：顺序编号后的图像，命名为 `figure_01` 到最后一张。
- `data/`：关键汇总表、关键 JSON、节点与边的证据表。
- `archive/`：旧 run 和旧结果归档，避免 `results` 根目录继续混乱。

本文档优先回答四个问题：

1. 模型在首个生成位置如何决定输出 `<tool_call>` 还是 `no_tool`。
2. 这条机制链包含哪些节点，它们各自读什么、写什么、通过什么路径起作用。
3. 完整 24 节点电路如何和 8 节点核心决策链对应。
4. 所有图和指标各自是什么意思，应该如何解释。

## 2. 最终机制摘要

当前最强的机制结论是：

1. 模型首先从用户第一句 instruction 中读取一个 **instruction-level commitment cue**。这个 cue 区分的是“要求把结果交付到外部文件/环境里”还是“仅要求把函数体写出来”。
2. 这个 cue 通过晚层 user-conditioned ingress 路径 `L20H5 -> L21H1/L21H12 -> L24H6 -> MLP27` 进入 tool-call 写出链。
3. `MLP27` 是主要的晚层 writer，它把这条状态写成 `<tool_call>` 倾向。
4. 同时存在一条竞争性的 no-tool 链 `L16H4 -> MLP17 -> L23H6`，它会把相同工具环境下的请求压回 `no_tool`，并且会压制 tool ingress。

最核心的整体验证指标如下：

- 数据规模：`{metrics['dataset_n']}` 对 clean/corrupt 样本。
- 最终 signed circuit：`{metrics['circuit_nodes']}` 个节点，`{metrics['circuit_edges']}` 条边。
- full-circuit KL recovery：promote `{format_float(metrics['full_promote_sufficiency'])}`，suppress `{format_float(metrics['full_suppress_sufficiency'])}`。
- full-circuit top-1 保真：promote `{format_float(metrics['full_promote_top1'])}`，suppress `{format_float(metrics['full_suppress_top1'])}`。
- 固定 schema 下的完整 tool 主链 top-1：`{format_float(metrics['query_chain_top1'])}`。
- 完整 no-tool 竞争链 top-1：`{format_float(metrics['suppress_chain_top1'])}`。
- 只换整句 instruction 后的 no-tool top-1：`{format_float(metrics['instruction_flip_no_tool_top1'])}`。
- 只换首句 lead phrase 后的 no-tool top-1：`{format_float(metrics['lead_flip_no_tool_top1'])}`。

## 3. 先讲完整 24 节点电路，再讲 8 节点核心链

这次最终 signed circuit 不是一条单线，而是一个 `24` 节点 / `64` 边的有向电路。理解它时要分两层：

- **完整 24 节点电路**：负责提供上下文、维持 tool/no-tool 两条候选通路、并在晚层汇合。
- **8 节点核心链**：负责最终把决策写到首个生成位置。

当前最合理的全电路分层是：

- 早期 query 入口候选：`L2H14, MLP11`
- 共享整合骨架：`L12H6, L13H9, MLP16, MLP19`
- 工具侧辅助读取/路由：`L16H8, L17H2, L17H8, L23H5, MLP21`
- no-tool 侧辅助抑制链：`MLP12, L15H5, L16H13, L16H9, L18H14`
- 最终决策核心：`L16H4, MLP17, L20H5, L21H1, L21H12, L23H6, L24H6, MLP27`

其中真正可以进入主文核心算法的，是这条 8 节点最小主链：

- tool 决策主链：`L20H5 -> L21H1/L21H12 -> L24H6 -> MLP27`
- no-tool 竞争主链：`L16H4 -> MLP17 -> L23H6`

## 4. 结构组与功能组

### 4.1 结构组

{structural_table}

### 4.2 功能组

{functional_table}

结构组回答“节点在电路图上的拓扑位置”，功能组回答“节点在对象语言上更像在做什么”。两者不能混用：

- 结构组保留了全 24 节点电路的整体形状。
- 功能组帮助把 attention head 和 MLP 串成人类可理解的步骤。

## 5. 8 个核心节点的对象语言机制与证据

{core_table}

### 5.1 这 8 个节点怎样协作

- `L20H5` 把 instruction-level commitment cue 接入晚层 tool 路。
- `L21H1` 和 `L21H12` 负责把这条状态继续路由，其中 `L21H12 -> MLP27` 是更强主路。
- `L24H6` 位于 writer 之前，更像 pre-writer relay。
- `MLP27` 负责把这条状态写成 `<tool_call>` 倾向。
- `L16H4 -> MLP17 -> L23H6` 则构成 competing no-tool chain。
- `MLP17` 不只是写 `no_tool`，还会压 `L20H5 / L21H1 / L21H12` 这些 tool ingress 点。

## 6. 完整 24 节点清单

下表保留了全 24 个节点的当前语义和证据摘要。它回答的是“全电路里每个节点目前被解释成什么”，而不是“所有节点都已经达到相同强度的 mechanistic certainty”。

{full_node_table}

## 7. 公式、指标与符号解释

### 7.1 两个 endpoint 分布

我们在首个生成位置上定义两个 clean endpoint 分布：

- `p^clean_tool`：clean prompt 在 `<tool_call>` 端点附近的分布。
- `p^clean_no_tool`：clean no-tool endpoint 在 `no_tool` 端点附近的分布。

设某个变体、patch 或 intervention 后的首 token 分布为 `q`。

### 7.2 两个 KL 目标分数

工具目标分数定义为：

`S_tool(q) = - KL(p^clean_tool || q)`

no-tool 目标分数定义为：

`S_no_tool(q) = - KL(p^clean_no_tool || q)`

解释：

- `KL(· || ·)` 越小，表示当前分布 `q` 越接近目标 endpoint 分布。
- 前面加负号，是为了让“越接近目标”对应“分数越大”。
- 所以 `S_tool` 越大，说明当前状态越像 clean 的 `<tool_call>` endpoint。
- `S_no_tool` 越大，说明当前状态越像 clean 的 `no_tool` endpoint。

### 7.3 决策分数

最终我们用：

`DecisionScore(q) = S_tool(q) - S_no_tool(q)`

来刻画首 token 更偏向哪一边。

解释：

- `DecisionScore > 0`：更偏 `<tool_call>`。
- `DecisionScore < 0`：更偏 `no_tool`。
- 它比单看某一个 logit 更稳，因为它同时比较了两个 endpoint。

### 7.4 Rescue Ratio

当我们从 base 状态 patch 一组节点到 anchor 状态时，恢复比例定义为：

`RescueRatio = (Score_patched - Score_base) / (Score_anchor - Score_base)`

解释：

- `Score_base`：没有 patch 时的分数。
- `Score_anchor`：目标端点的分数。
- `Score_patched`：patch 后的分数。
- `RescueRatio = 1` 表示完全恢复到 anchor 水平。
- `RescueRatio = 0` 表示没有救回。
- `RescueRatio < 0` 表示 patch 方向错了，反而更远。

### 7.5 Mediation Ratio

对边 `A -> B`，我们用：

`Mediation(A -> B) = Rescue(source-only) - Rescue(source-with-B-blocked)`

来估计这条边真正承担了多少因果传递。

解释：

- 如果 source-only rescue 很高，而把 `B` 挡住后 rescue 明显下降，说明 `A` 很大一部分效应是经由 `B` 实现的。
- Mediation 值越大，说明这条边越像真正的因果通路。

### 7.6 Top-1 Rate 与 Boundary Flip Rate

- `tool_top1_rate`：patch 后首 token 直接变成 `<tool_call>` 的样本比例。
- `no_tool_top1_rate`：patch 后首 token 直接变成 `no_tool` 的样本比例。
- `boundary_flip_rate`：`DecisionScore` 是否跨过 0 的比例。

解释：

- `DecisionScore` 看的是分布级别的方向变化。
- `top1_rate` 看的是最终离散决策是否真的翻转。
- 两者结合起来，既能看软分数变化，也能看硬决策变化。

## 8. 反向发现和 no-tool 支路

这部分很关键。当前 `no_tool` 语义线并不是后验随便命名出来的，而是和双向发现中的 reverse 方向高度重合。

- 最小 no-tool 主链 `L16H4 -> MLP17 -> L23H6` 被 reverse core 完整包含。
- 扩展后的 reverse-aligned no-tool 语义线 `{mechanism_summary['reverse_aligned_nodes']}`：
  - 节点上命中全部 `8/8` 个 reverse-selective 节点，额外只多一个共享晚层节点 `L23H6`
  - 节点 Jaccard 为 `{format_float(metrics['reverse_aligned_node_jaccard'])}`
  - 边 Jaccard 为 `{format_float(metrics['reverse_aligned_edge_jaccard'])}`

这说明：

- forward 方向更容易暴露促进 `<tool_call>` 的节点。
- reverse 方向特别有利于暴露 suppressive / no-tool-biased 节点。
- 双向方法本身就在帮助我们同时看见“促进支路”和“抑制支路”。

## 9. 图像总览与逐图解释

下面的图全部已经复制到 `figures/`，并按 `figure_01` 到最后一张的顺序重命名。每一张图都给出“怎么看”和“它支持什么结论”。

{chr(10).join(figure_sections)}

## 10. 数据文件索引

- `data/summary_metrics.json`：关键总指标。
- `data/final_signed_circuit_summary.json`：24 节点 / 64 边的结构总表。
- `data/final_signed_nodes.csv`：节点清单。
- `data/final_signed_edges.csv`：边清单。
- `data/functional_group_summary.json`：功能组总表。
- `data/functional_node_table.csv`：24 节点功能归类。
- `data/signed_group_report.json`：结构保真验证。
- `data/functional_group_report.json`：功能组保真验证。
- `data/query_decision_summary.json`：固定 schema 下的主链/竞争链结果。
- `data/instruction_commitment_summary.json`：整句 instruction 交换结果。
- `data/instruction_lead_summary.json`：lead phrase 交换结果。
- `data/mlp27_steering_summary.json`：`MLP27` 局部写出干预结果。
- `data/late_writer_backup_summary.json`：`MLP27` backup/minimality 结果。
- `data/head_final_audit_summary.json`：attention head 终版审计。
- `data/head_span_attention_summary.csv`：head 的 span 读取密度。
- `data/head_qkv_patch_summary.csv`：head 的 Q/K/V/Z rescue。
- `data/final_component_evidence_table.csv`：核心节点证据表。
- `data/final_edge_evidence_table.csv`：核心边证据表。
- `data/final_claim_tree.json`：主张分级。
- `data/reverse_overlap_summary.json`：no-tool 线和 reverse discovery 的重合分析。

## 11. 写作边界

当前可以强写的，是：

- 在固定工具环境里，instruction-level commitment cue 足以驱动 `<tool_call>` / `no_tool` 的翻转。
- 这条 cue 通过 `L20H5 -> L21H1/L21H12 -> L24H6 -> MLP27` 进入 tool-call 写出链。
- `MLP27` 是主要晚层 writer。
- `L16H4 -> MLP17 -> L23H6` 是竞争性的 no-tool 链。
- reverse discovery 对 suppressive / no-tool 支路特别敏感。

当前必须弱写的，是：

- `L20H5` 是否已经是完全抽象的 action-demand reader。
- `L16H4` 是否已经是完全纯净的 ordinary-answer prior reader。
- `direct-answer sufficiency` 是否就是当前数据里唯一的潜变量。

当前不能再写的，是：

- “统一模式切换器”
- “抽象仲裁区”
- “所有 reverse 节点都等于抑制节点”
- “所有 24 个节点都已经达到同等强度的语义确定性”
"""
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a cleaned final package under results/final.")
    parser.add_argument("--results-root", type=str, default="/root/autodl-tmp/project/experiment/results/legacy")
    parser.add_argument("--source-run", type=str, default="13-01-39-final-kl")
    parser.add_argument("--source-root", type=str, default="")
    parser.add_argument("--cleanup", action="store_true", help="Remove smoke dirs and move legacy results under final/archive.")
    args = parser.parse_args()

    results_root = Path(args.results_root).resolve()
    if args.source_root:
        source_root = Path(args.source_root).resolve()
    else:
        nested_source = results_root / "final" / "archive" / "raw_runs" / args.source_run
        flat_source = results_root / args.source_run
        source_root = nested_source if nested_source.exists() else flat_source
    final_root = results_root / "final"
    if not source_root.exists():
        raise FileNotFoundError(f"Missing source run: {source_root}")

    ensure_clean_dir(final_root)
    figures_root = final_root / "figures"
    data_root = final_root / "data"
    archive_root = final_root / "archive"
    figures_root.mkdir(parents=True, exist_ok=True)
    data_root.mkdir(parents=True, exist_ok=True)
    archive_root.mkdir(parents=True, exist_ok=True)

    # Copy key data files.
    data_files = [
        ("final_signed_circuit/final_signed_circuit_summary.json", "final_signed_circuit_summary.json"),
        ("final_signed_circuit/final_signed_nodes.csv", "final_signed_nodes.csv"),
        ("final_signed_circuit/final_signed_edges.csv", "final_signed_edges.csv"),
        ("functional_groups/functional_group_summary.json", "functional_group_summary.json"),
        ("functional_groups/functional_node_table.csv", "functional_node_table.csv"),
        ("signed_validate/signed_group_report.json", "signed_group_report.json"),
        ("functional_validate/functional_group_report.json", "functional_group_report.json"),
        ("query_decision_chain/query_decision_summary.json", "query_decision_summary.json"),
        ("instruction_commitment/instruction_commitment_summary.json", "instruction_commitment_summary.json"),
        ("instruction_lead/instruction_lead_summary.json", "instruction_lead_summary.json"),
        ("mlp27_steering/mlp27_steering_summary.json", "mlp27_steering_summary.json"),
        ("late_writer_backup/late_writer_backup_summary.json", "late_writer_backup_summary.json"),
        ("final_head_attention_audit/head_final_audit_summary.json", "head_final_audit_summary.json"),
        ("final_head_attention_audit/head_span_attention_summary.csv", "head_span_attention_summary.csv"),
        ("final_head_attention_audit/head_qkv_patch_summary.csv", "head_qkv_patch_summary.csv"),
        ("final_mechanism_evidence/final_mechanism_evidence_summary.json", "final_mechanism_evidence_summary.json"),
        ("final_mechanism_evidence/final_component_evidence_table.csv", "final_component_evidence_table.csv"),
        ("final_mechanism_evidence/final_edge_evidence_table.csv", "final_edge_evidence_table.csv"),
        ("final_mechanism_evidence/final_claim_tree.json", "final_claim_tree.json"),
        ("reverse_overlap/reverse_overlap_summary.json", "reverse_overlap_summary.json"),
        ("FINAL_REPORT.md", "source_FINAL_REPORT.md"),
        ("FINAL_MECHANISTIC_RESULT.md", "source_FINAL_MECHANISTIC_RESULT.md"),
    ]
    for rel_src, rel_dst in data_files:
        copy_file(source_root / rel_src, data_root / rel_dst)

    # Generate and copy figures in final sequence.
    build_instruction_flip_plot(
        source_root / "instruction_lead" / "instruction_lead_summary.json",
        figures_root / "figure_09_lead_phrase_flip.png",
        "Lead Phrase Swap",
    )
    build_head_span_heatmap(
        source_root / "final_head_attention_audit" / "head_span_attention_summary.csv",
        figures_root / "figure_11_head_span_attention.png",
    )
    build_head_qkv_heatmap(
        source_root / "final_head_attention_audit" / "head_qkv_patch_summary.csv",
        figures_root / "figure_12_head_qkv_decomposition.png",
    )
    build_reverse_overlap_plot(
        source_root / "reverse_overlap" / "reverse_overlap_summary.json",
        figures_root / "figure_13_reverse_overlap.png",
    )

    figure_specs = [
        {
            "index": 1,
            "filename": "figure_01_final_signed_circuit.png",
            "src": source_root / "final_signed_circuit" / "final_signed_circuit.png",
            "title": "最终 Signed Circuit 总览",
            "how_to_read": "节点表示最终保留下来的 24 个电路节点，边表示最终保留下来的 64 条边。颜色表示结构层上的偏向或共享性。",
            "supports": "这张图证明最终交付不是零散节点，而是一张稀疏但完整的 signed circuit。",
        },
        {
            "index": 2,
            "filename": "figure_02_functional_group_graph.png",
            "src": source_root / "functional_groups" / "functional_group_graph.png",
            "title": "24 节点功能语义分组图",
            "how_to_read": "同一张电路按功能组重新上色，显示 tool-schema readers、suppression readers、writers、integrators 等组。",
            "supports": "这张图把 24 个节点从结构图变成可叙述的功能图，是后续机制故事的桥梁。",
        },
        {
            "index": 3,
            "filename": "figure_03_bidirectional_union_circuit.png",
            "src": source_root / "bidirectional" / "union_circuit.png",
            "title": "双向发现后的联合电路",
            "how_to_read": "这张图展示 forward 与 reverse 两个方向联合后的节点和边。",
            "supports": "它说明最终 signed circuit 来自双向发现，而不是单向启发式筛选。",
        },
        {
            "index": 4,
            "filename": "figure_04_reverse_selective_circuit.png",
            "src": source_root / "bidirectional" / "reverse_selective_circuit.png",
            "title": "Reverse-Selective 子电路",
            "how_to_read": "这张图只保留 reverse-selective 支路，主要是 no-tool / suppressive 方向。",
            "supports": "它直接支持“反向发现特别有利于暴露抑制节点和抑制支路”。",
        },
        {
            "index": 5,
            "filename": "figure_05_structural_validation_heatmap.png",
            "src": source_root / "signed_validate" / "signed_group_validation_heatmap.png",
            "title": "结构组保真验证热图",
            "how_to_read": "热图显示不同结构组在 promote/suppress 两个方向上的 sufficiency 与 necessity。",
            "supports": "它证明完整电路和主要结构组在行为层面是 faithful 的，不是纯相关图。",
        },
        {
            "index": 6,
            "filename": "figure_06_functional_validation_heatmap.png",
            "src": source_root / "functional_validate" / "functional_group_validation_heatmap.png",
            "title": "功能组保真验证热图",
            "how_to_read": "热图显示功能组在 tool/no-tool 两个方向上的 sufficiency 与 necessity。",
            "supports": "它说明语义分组不是只看 attention 命名，而是有行为恢复支撑。",
        },
        {
            "index": 7,
            "filename": "figure_07_query_decision_stepwise.png",
            "src": source_root / "query_decision_chain" / "query_decision_stepwise.png",
            "title": "固定 Schema 下的 Query 决策链逐步恢复",
            "how_to_read": "横轴是逐步加入的节点集合，纵轴分别看 decision score 和 top-1 恢复率。",
            "supports": "它证明在固定工具环境下，`L20H5 -> L21H1/L21H12 -> L24H6 -> MLP27` 会逐步把 corrupt 拉回 `<tool_call>`。",
        },
        {
            "index": 8,
            "filename": "figure_08_instruction_commitment_flip.png",
            "src": source_root / "instruction_commitment" / "instruction_variant_effects.png",
            "title": "整句 Instruction Swap 的行为翻转",
            "how_to_read": "左图是 decision score，右图是 `<tool_call>`/`no_tool` top-1 比例。",
            "supports": "它证明第一句 instruction 本身就是强决定变量。",
        },
        {
            "index": 9,
            "filename": "figure_09_lead_phrase_flip.png",
            "src": figures_root / "figure_09_lead_phrase_flip.png",
            "title": "最小 Lead Phrase Swap 的行为翻转",
            "how_to_read": "只换首句开头短语，不换后面主体内容，仍然看 decision score 和 top-1。",
            "supports": "它把关键变量继续缩小到 instruction 开头的 commitment cue，而不是整段文本。",
        },
        {
            "index": 10,
            "filename": "figure_10_mlp27_steering_curves.png",
            "src": source_root / "mlp27_steering" / "mlp27_steering_curves.png",
            "title": "MLP27 局部写出干预曲线",
            "how_to_read": "不同 alpha 表示对 MLP27 局部表示的不同强度 steering，纵轴看 decision score 与 top-1。",
            "supports": "这张图支持 `MLP27` 是主要晚层 writer，而不只是一个相关晚层节点。",
        },
        {
            "index": 11,
            "filename": "figure_11_head_span_attention.png",
            "src": figures_root / "figure_11_head_span_attention.png",
            "title": "关键 Attention Head 的 Span 读取密度",
            "how_to_read": "横轴是候选 span，纵轴是关键 head，颜色越深表示中位 attention density 越高。",
            "supports": "它帮助判断 head 更像在读 lead phrase、file target、function body scaffold 还是 task body。",
        },
        {
            "index": 12,
            "filename": "figure_12_head_qkv_decomposition.png",
            "src": figures_root / "figure_12_head_qkv_decomposition.png",
            "title": "关键 Attention Head 的 Q/K/V/Z 分解",
            "how_to_read": "颜色表示把某个组件单独 patch 回去后带来的 rescue ratio。",
            "supports": "它说明 tool 路上的关键 head 更像 late routing head，主要依赖 Q/Z，而不是纯 V-copy。",
        },
        {
            "index": 13,
            "filename": "figure_13_reverse_overlap.png",
            "src": figures_root / "figure_13_reverse_overlap.png",
            "title": "No-Tool 语义线与 Reverse Discovery 的重合",
            "how_to_read": "左图比较节点重合，右图比较边重合；越接近 1 表示越一致。",
            "supports": "它证明 no-tool 语义线与 reverse-selective 子电路高度重合。",
        },
        {
            "index": 14,
            "filename": "figure_14_edge_mediation_heatmap.png",
            "src": source_root / "edge_importance" / "signed_edge_mediation_heatmap.png",
            "title": "边级中介热图",
            "how_to_read": "热图颜色表示边的中介强度，越高表示越像真正的因果通路。",
            "supports": "它支持 `L21H12 -> MLP27` 和 `L16H4 -> MLP17 -> L23H6` 不是单纯共现边。",
        },
        {
            "index": 15,
            "filename": "figure_15_semantic_chain_progression.png",
            "src": source_root / "semantic_chain" / "semantic_chain_progression.png",
            "title": "早期语义链提取的渐进恢复",
            "how_to_read": "这张图展示最早一轮 semantic chain 提取时，逐步加入节点后的恢复曲线。",
            "supports": "它展示了从早期 chain 候选到后来 fixed-schema 主链的演进关系。",
        },
        {
            "index": 16,
            "filename": "figure_16_schema_stagewise_plot.png",
            "src": source_root / "schema_stagewise" / "schema_stagewise_plot.png",
            "title": "Schema / Protocol 两步恢复图",
            "how_to_read": "第一步看 `L21H12`，第二步看 `MLP27`，观察在 no-schema/no-protocol 等变体上的恢复。",
            "supports": "它说明 `L21H12` 与 `MLP27` 分别承担 late routing 和 late writing 的不同角色。",
        },
        {
            "index": 17,
            "filename": "figure_17_signed_layer_trajectory.png",
            "src": source_root / "signed_layer_trajectory" / "signed_layer_trajectory.png",
            "title": "跨层决策轨迹图",
            "how_to_read": "横轴是层号，纵轴是不同方向上累积的 signed effect。",
            "supports": "它说明最终决策是如何在中晚层逐渐成形，而不是单层瞬时出现。",
        },
    ]
    for spec in figure_specs:
        copy_file(spec["src"], figures_root / spec["filename"])

    # Summary metrics and auxiliary tables.
    metrics = build_metrics_overview(source_root)
    write_json(data_root / "summary_metrics.json", metrics)

    functional_summary = load_json(source_root / "functional_groups" / "functional_group_summary.json")
    signed_report = load_json(source_root / "signed_validate" / "signed_group_report.json")
    mechanism_summary = {
        "reverse_aligned_nodes": "MLP12, L15H5, L16H13, L16H4, L16H8, L16H9, MLP17, L17H2, L23H6"
    }

    full_nodes = []
    functional_rows = load_csv(source_root / "functional_groups" / "functional_node_table.csv")
    label_map = {row["functional_group"]: row["functional_label"] for row in functional_summary["summary_rows"]}
    for row in functional_rows:
        full_nodes.append(
            {
                "node": row["node"],
                "layer": row["layer"],
                "structural_group": row["structural_group"],
                "functional_label": label_map.get(row["functional_group"], row["functional_group"]),
                "semantic_hint": row["semantic_hint"],
                "evidence": row["evidence"],
            }
        )

    package_doc = build_package_document(
        final_root=final_root,
        metrics=metrics,
        mechanism_summary=mechanism_summary,
        figure_specs=figure_specs,
        structural_rows=signed_report["summary_rows"],
        functional_rows=functional_summary["summary_rows"],
        core_components=load_json(source_root / "final_mechanism_evidence" / "final_mechanism_evidence_summary.json")["component_rows"],
        full_nodes=full_nodes,
    )
    write_text(final_root / "FINAL_PACKAGE.md", package_doc)
    write_text(final_root / "README.md", "# Final Package\n\nSee [FINAL_PACKAGE.md](FINAL_PACKAGE.md).\n")

    write_csv(
        final_root / "figures" / "FIGURE_INDEX.csv",
        [
            {
                "figure": f"图{spec['index']:02d}",
                "filename": spec["filename"],
                "title": spec["title"],
                "supports": spec["supports"],
            }
            for spec in figure_specs
        ],
    )
    write_csv(
        final_root / "data" / "DATA_INDEX.csv",
        [{"filename": p.name, "type": p.suffix.lstrip(".")} for p in sorted(data_root.iterdir()) if p.is_file()],
    )

    if args.cleanup:
        raw_archive = archive_root / "raw_runs"
        raw_archive.mkdir(parents=True, exist_ok=True)
        for child in sorted(results_root.iterdir()):
            if child.name == "final":
                continue
            if child.is_dir() and (child.name.startswith("_smoke") or child.name.startswith("smoke_")):
                shutil.rmtree(child)
            else:
                shutil.move(str(child), raw_archive / child.name)


if __name__ == "__main__":
    main()
