# CLAUDE

## 当前唯一工作目录

- 当前唯一主目录：`/root/autodl-tmp/project`
- `/root/autodl-tmp/project_module1`、`/root/autodl-tmp/project_module2`、`/root/autodl-tmp/project_module3`、`/root/autodl-tmp/project_module4` 的四模块结果，已经同步进 `project`；这些目录现在只作为迁移来源和历史快照，不再作为正式结果入口。
- 如果只保留一个文件夹，只保留 `project` 即可。
- 当前最高优先级总览文档：
  - `final/PROJECT_MECHANISM_GUIDE_ZH.md`
  - `final/PROJECT_MACHINANISM_GUIDE_ZH.md`（兼容别名）

## 当前目录结构

```text
project/
├── CLAUDE.md
├── AGENTS.md
├── history.md
├── task.md
├── experiment/
│   ├── code/
│   ├── datasets/
│   │   ├── clean/
│   │   ├── corrupt/
│   │   ├── train/
│   │   └── test/
│   └── results/
│       └── split/
│           ├── pipeline/                    # train 集上重新发现的总电路与验证
│           ├── attentionhead/               # train 集注意力头聚合结果
│           ├── instruction_integration/     # 模块 1 正式结果
│           ├── output_route_decision/       # 模块 2 正式结果
│           ├── tool_call_construction/      # 模块 3 正式结果
│           ├── tool_call_suppression/       # 模块 4 正式结果
│           ├── test_validation/             # test 集验证结果
│           └── split_comparison_summary.md  # 全量 / train / test 对比
├── paper/
│   └── PAPER_OUTLINE.md
└── final/
    ├── PROJECT_MECHANISM_GUIDE_ZH.md
    ├── PROJECT_MACHINANISM_GUIDE_ZH.md
    ├── FIGURE_INDEX.csv
    └── figures/
```

## 只认这几处正式入口

- 总大纲：`paper/PAPER_OUTLINE.md`
- 总历史：`history.md`
- 总结总览：`final/PROJECT_MECHANISM_GUIDE_ZH.md`
- 四模块结果：
  - `experiment/results/split/instruction_integration/instruction_integration_module1_report.md`
  - `experiment/results/split/output_route_decision/output_route_decision_paper_assets.md`
  - `experiment/results/split/tool_call_construction/tool_call_construction_paper_report.md`
  - `experiment/results/split/tool_call_suppression/tool_call_suppression_report.md`
- 总体对比：`experiment/results/split/split_comparison_summary.md`

## 当前冻结结论

- 模型：`/root/autodl-tmp/Qwen/Qwen3-1.7B`
- 数据：`1722` 对 clean/corrupt 样本，Python `555` / Java `584` / C++ `583`
- 划分：按 `lang × clean_candidate` 分层，`seed=42`，train `1223` / test `499`
- 总电路：train 集上重新发现后仍为 `24` 个节点、`64` 条边
- 全局泛化：
  - `R_module` AUC：train `0.9946`，test `0.9943`
  - Construction 完整链 `+MLP27` `<tool_call>` top-1：train `97.9%`，test `97.2%`
  - Suppression 完整链 `+L23H6` no-tool top-1：train `79.0%`，test `78.2%`
- 当前四模块最稳主链：
  - `Instruction Integration`: `L2H14 + L11H5 -> MLP11`
  - `Output-Route Decision`: `MLP11 -> MLP16 -> MLP19`
  - `Tool-Call Construction`: `MLP19 -> L20H5 -> (L21H1 / L21H12) -> L24H6 -> MLP27`
  - `Tool-Call Suppression`: `MLP16 -> MLP17` 分叉进入 `L16H4 -> MLP17 -> L23H6`

## 协作规则

- 新代码、新结果、新文档，只写到 `project` 这棵树里，不再写 `project_module*`。
- 正式结果只认 `experiment/results/split/`；不要再往 `experiment/results/` 下新建未分离的顶层结果目录。
- 任何论文级结论，默认都要同时给出 train 和 test 数字。
- 如果更新了四模块结论，至少同步更新这三处：
  - `history.md`
  - `final/PROJECT_MECHANISM_GUIDE_ZH.md`
  - `final/FIGURE_INDEX.csv`
- 不要再引用旧 `legacy` 目录作为主入口；旧分散仓库和旧路径只可做历史核对，不可继续当正式口径。
- 需要临时文件时，放在 `/root/autodl-tmp/tmp`，不要放到 `/tmp`。
- 默认使用 `base` 环境，优先本地 `4090D` GPU。
- 不要中断、覆盖或抢占别人的进程；先检查，再行动。

## 建议阅读顺序

1. `final/PROJECT_MECHANISM_GUIDE_ZH.md`
2. `experiment/results/split/split_comparison_summary.md`
3. 四个模块正式报告
4. `paper/PAPER_OUTLINE.md`
5. `history.md`
