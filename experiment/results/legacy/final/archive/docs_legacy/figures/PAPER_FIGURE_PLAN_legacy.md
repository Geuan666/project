# Paper Figure Plan

## Q1: Forward Mechanism

- Figure 18: contrasts `L2H14` against `MLP11` to show weak shared object component vs first stable writer.
- Figure 19: shows stagewise amplification of the shared file-vs-answer axis from `MLP11` to `MLP27`.
- Figure 20: shows node-by-node downstream projection trajectories under `MLP11` direction edits.
- Figure 21: shows the final writer effect on `<tool_call>`, `no_tool`, object score, and `MLP27`.

## Q2: Suppression Mechanism

- Figure 22: shows whether the suppressive chain raises `no_tool`, lowers `<tool_call>`, or both.
- Figure 23: shows that `MLP17` directly pushes the tool ingress route toward the no-tool state.
- Figure 24: shows the full suppressive heatmap across chain nodes and downstream targets.
- Figure 25: shows stagewise accumulation across `L16H4 -> MLP17 -> L23H6`.
