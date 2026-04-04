# M3 分支策略优化实验

## 目标

在固定 MNIST 样本集与固定扰动半径下，对比 `branching.method`、`branching.candidates`、`branching.reduceop` 的影响，验证开题报告中主改进 A 的结论。

## 实验步骤

1. 固定数据集、模型、样本区间、epsilon 和 timeout。
2. 运行 baseline、auto、kfsb、kfsb-reduceop-max、kfsb-candidates5 五组配置。
3. 汇总 `verified_acc`、`timeout`、`mean_time_s`、`max_time_s`。
4. 生成条形图和对比表，写入阶段报告。

## 结果目录

- 日志: `项目书/results/m3/logs/`
- 图表: `项目书/results/m3/figures/`
- 汇总: `项目书/results/m3/m3_branching_ablation.csv`
