# Legacy 结果分层整理

`legacy` 只负责保存历史主结果和对应的整理视图；注意力头专项实验单独保存在 [experiment/results/attentionhead](/root/autodl-tmp/project/experiment/results/attentionhead)。

## 三层分类

| 层级 | 说明 | 入口 |
| --- | --- | --- |
| 正式保留 | 当前主叙事直接使用、应优先引用的正式结果包 | [official_keep](/root/autodl-tmp/project/experiment/results/legacy/official_keep) |
| 高价值参考 | 对当前 4 模块主线仍然很有帮助，但还带有旧叙事痕迹的材料 | [high_value_reference](/root/autodl-tmp/project/experiment/results/legacy/high_value_reference) |
| 可以降级归档 | 更早期、近似性更强、主要服务过程记录或排错的历史产物 | [downgraded_archive](/root/autodl-tmp/project/experiment/results/legacy/downgraded_archive) |

## 当前分类原则

- 正式保留：只保留当前 `final` 包中的主文档、主数据、主图和总索引。
- 高价值参考：保留最终结果对应的主 raw run，以及仍然能帮助理解旧实验链条的历史报告。
- 可以降级归档：保留更早期 raw runs 和明显偏过程性的结果，默认不进入主文叙事。

## 具体映射

| 原始位置 | 当前层级 | 原因 |
| --- | --- | --- |
| [final/FINAL_PACKAGE.md](/root/autodl-tmp/project/experiment/results/legacy/final/FINAL_PACKAGE.md) | 正式保留 | 当前总结果包入口 |
| [final/docs](/root/autodl-tmp/project/experiment/results/legacy/final/docs) | 正式保留 | 当前主文档出口 |
| [final/data](/root/autodl-tmp/project/experiment/results/legacy/final/data) | 正式保留 | 当前主数据出口 |
| [final/figures](/root/autodl-tmp/project/experiment/results/legacy/final/figures) | 正式保留 | 当前主图出口 |
| [final/archive/raw_runs/13-01-39-final-kl](/root/autodl-tmp/project/experiment/results/legacy/final/archive/raw_runs/13-01-39-final-kl) | 高价值参考 | 当前最终包背后的主 raw run |
| [final/archive/docs_legacy](/root/autodl-tmp/project/experiment/results/legacy/final/archive/docs_legacy) | 高价值参考 | 旧叙事文档很多，但仍有索引价值 |
| [final/archive/raw_runs/11-22-45-bidirectional_approxy](/root/autodl-tmp/project/experiment/results/legacy/final/archive/raw_runs/11-22-45-bidirectional_approxy) | 可以降级归档 | 旧版近似双向结果，非当前正式版本 |
| [final/archive/raw_runs/11-21-37](/root/autodl-tmp/project/experiment/results/legacy/final/archive/raw_runs/11-21-37) | 可以降级归档 | 更早期批处理结果 |
| [final/archive/raw_runs/11-21-30](/root/autodl-tmp/project/experiment/results/legacy/final/archive/raw_runs/11-21-30) | 可以降级归档 | 更早期过程性结果 |
| [final/archive/raw_runs/reverse_exact_check_cpp1](/root/autodl-tmp/project/experiment/results/legacy/final/archive/raw_runs/reverse_exact_check_cpp1) | 可以降级归档 | 过程性核查样例，不作为主叙事出口 |
