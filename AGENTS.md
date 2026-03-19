# AGENTS

## 目录结构

```text
project/
├── AGENTS.md                         # Codex 协作规则与项目总览
├── task.md                           # 当前主任务顺序
├── history.md                        # 数据、方法、结果、机制假说历史
├── survey/
│   ├── references/                   # 外部论文与参考仓库入口
│   └── notes/                        # 文献笔记
├── experiment/
│   ├── code/
│   │   ├── src/                      # 核心源码
│   │   ├── scripts/                  # 主实验脚本
│   │   └── attentionhead/            # 注意力头专项实验代码
│   ├── datasets/                     # clean/corrupt 成对数据
│   └── results/
│       ├── legacy/                   # 历史主结果与分层整理
│       └── attentionhead/            # 注意力头实验结果
├── paper/                            # 论文主文、图表、草稿
├── .venvs/                           # 本地环境
└── tmp/                              # 临时文件与探针输出
```

## 行为规则

- 没有完成目标，不要自行停下；先把当前回合内能做完的事情做完。
- 除绘图、论文写作、代码标识外，默认全部用中文，不用难懂缩写和空洞说法。
- 科研不是作秀；表达要简洁、清楚、有力，不写做作的话。
- 任何判断都要有依据；不确定就先查代码、数据、结果，不要硬猜。
- 不要编造实验结论，不要替数据说话。
- 非必要不写新文档；必须写文档时，优先图、表、短段落结合，保证 Markdown 预览可直接阅读。
- 需要翻墙时先执行 `source /etc/network_turbo`。
- 默认使用 `base` 环境，优先本地 `4090D` GPU。
- 不要中断、覆盖或抢占别人的进程；先检查，再行动。

## 核心想法与现有结果

- 本项目研究的是：为什么只改用户提示开头的一个动词或短词组，就会让模型在首个输出词上从 `<tool_call>` 翻到非 `<tool_call>`。
- 当前统一使用的模型是 `/root/autodl-tmp/Qwen/Qwen3-1.7B`。
- 当前数据集是 `1700+` 对 clean/corrupt 样本，关闭 thinking，采用 Qwen 原生工具调用格式；每对样本除首个用户要求词外尽量保持一致。
- 项目的核心方法是模块级电路定位，并加入双向反转：既把 `<tool_call>` 一侧当 clean，也把它当 corrupt，从而同时找到促进、抑制和共享部分，让电路更 faithful。
- 当前已经得到一张通过充分性和必要性验证的最终 signed circuit：`24` 个节点、`64` 条边；主结果集中在 `experiment/results/legacy/final` 对应的结果包中。
- 当前新的总机制假说分为 4 个模块：`Instruction Integration`、`Output-Route Decision`、`Tool-Call Construction`、`Tool-Call Suppression`。
- 注意力头全量聚合实验已经完成：覆盖 `1722` 个样本、`448` 个注意力头，结果保存在 `experiment/results/attentionhead/20260319-121000-attention-head-full/`，后续可直接为模块分析服务。
- 本轮重构的目标不是推翻旧结果，而是把有价值的代码、数据和结果重新整理进一个更适合人和 Codex 协同推进的项目结构。

## 当前机制猜想（英文）

> Before generating the first output token, the model first performs Instruction Integration, combining the opening request with the function-body phrase, the filename, and the remaining task description into a unified representation of what kind of answer is being asked for. It then enters an Output-Route Decision stage, where this integrated instruction state is converted into a stable internal choice between a tool-mediated output route and a direct-response route. If the decision favors the tool route, a Tool-Call Construction mechanism organizes filename cues, function-body content, and call-format structure to push the first token toward `<tool_call>`. If the decision favors the direct-response route, a competing Tool-Call Suppression mechanism strengthens the no-tool state while actively inhibiting the tool-calling pathway. In this view, tool use is not treated as an isolated yes-or-no switch, but as the outcome of a broader decision about how the answer should be produced and delivered.
