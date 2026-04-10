# CLAUDE.md

## Project Context

This repository is a research and engineering workspace for robustness verification of ReLU feed-forward neural networks with alpha-beta-CROWN.

Primary project goals:

1. Reproduce the verification pipeline on MNIST with the fixed model `saved_models/mnist_fcnn.onnx`.
2. Compare verification strategies under fixed perturbation budgets, especially `baseline`, `auto`, and `kfsb`.
3. Evaluate branching-strategy improvements through controlled ablations.
4. Produce reproducible evidence chains: configs, logs, CSV summaries, figures, and report text.

## What Claude Code Should Optimize For

1. Be evidence-driven.
2. Prefer reproducible analysis over speculative claims.
3. Keep conclusions tied to logs, CSV outputs, and figures.
4. Distinguish between verified results, trend evidence, and tentative interpretation.
5. Treat configuration files, run scripts, and summary scripts as the authoritative source of truth.

## Current Research Framing

The project currently centers on two lines:

1. Main line A: branching-strategy optimization.
2. Auxiliary line B: epsilon-grid trend analysis.

For writeups and analysis, treat M3 as the main improvement experiment and M4 as the trend-validation experiment.

## Analysis Criteria

When evaluating project completion or feasibility, check these dimensions:

1. Runability: whether the environment, entry points, and configs execute successfully.
2. Reproducibility: whether each conclusion can be traced to config, command, log, and summary CSV.
3. Coverage: whether the required experiment matrix is complete.
4. Stability: whether results remain interpretable across perturbation settings.
5. Scalability: whether runtime and timeout behavior remain acceptable as epsilon grows.

## Recommended Evidence Sources

1. `项目书/results/阶段实验结果总汇_2026-04-03.md`
2. `项目书/results/结果汇总报告_2026-04-04.md`
3. `项目书/results/开题预期成效对照清单_2026-04-04.md`
4. `项目书/results/m2/m2_strategy_compare_0_100.csv`
5. `项目书/results/m3/m3_branching_ablation.csv`
6. `项目书/results/m3/m3_nodes_summary.csv`
7. `项目书/results/m4/m4_epsilon_grid.csv`
8. `项目书/results/m3/figures/`
9. `项目书/results/m4/figures/`

## Reporting Style

1. Use concise Chinese.
2. Prefer direct conclusions over long explanations.
3. If a claim is based on a specific file, cite the file path explicitly.
4. Separate completed results from planned work.
5. Avoid overstating feasibility when high-epsilon cases are dominated by timeout.

## Notes for Future Tasks

1. If a task asks for completion or feasibility analysis, start by checking the evidence chain in the results directory.
2. If a task asks for a paper draft, use the current research framing and data-backed conclusions.
3. If a task asks for prompt files or workspace instructions, keep them scoped to this project and aligned with the existing experiment hierarchy.
