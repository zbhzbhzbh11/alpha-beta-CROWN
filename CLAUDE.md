# CLAUDE.md

## Project Identity

This is a **course project** (课程作业) built atop the upstream α,β-CROWN verifier. The goal is to compare verification strategies on a ReLU FCNN trained on MNIST, with branching-strategy optimization as the main research line and epsilon-grid scanning as the auxiliary line.

- **Upstream tool**: [Verified-Intelligence/alpha-beta-CROWN](https://github.com/Verified-Intelligence/alpha-beta-CROWN)
- **Course topic**: "对比不同验证策略在 MNIST/CIFAR-10 上的鲁棒性验证"
- **Scope**: Configuration-level experiments — not algorithm-level innovation.

## Project Boundaries (what is IN scope vs NOT)

### IN scope (existing work)
- MNIST FCNN (3-layer, 784→256→128→10, pure ReLU) robustness verification
- Complete BaB verification with α,β-CROWN
- Branching heuristic comparison: babsr (baseline) vs auto vs fsb vs kfsb
- Branching parameter ablation: method × candidates × reduceop
- Epsilon sweep: 0.01 / 0.02 / 0.03 / 0.05 under L∞ norm
- Reproducible pipeline: YAML config → shell script → log → CSV → plot → report

### NOT YET done (explicitly needed by course requirements)
- **CIFAR-10 experiments**: data loaders and model definitions exist in the codebase but no training/verification experiments have been run
- **Marabou cross-tool comparison**: mentioned in the proposal as a reference but never executed
- **Incomplete verification standalone evaluation**: CROWN-only / α-CROWN-only runs exist as intermediate steps in BaB but were never independently reported
- **PGD attack evaluation**: `attack.pgd_order` is set to `skip` in all course experiment configs

### Explicitly OUT of scope
- Algorithm-level innovation in CROWN/BaB/MIP solvers
- Global robustness certification
- Non-ReLU activation functions
- VNN-COMP competitive benchmarking

## Architecture Map

```
alpha-beta-CROWN/
├── complete_verifier/              # ← All experiments run from this directory
│   ├── abcrown.py                  # [ENTRY POINT] Main CLI: python abcrown.py --config <yaml>
│   ├── bab.py                      # BaB main loop: general_bab() at line 382
│   ├── beta_CROWN_solver.py        # LiRPANet: wraps PyTorch model into auto_LiRPA BoundedModule
│   ├── incomplete_verifier_func.py # Incomplete verification (CROWN/α-CROWN only, no BaB)
│   ├── complete_verifier_func.py   # Complete verification orchestrator (calls general_bab)
│   ├── alpha.py / beta.py          # α-CROWN and β-CROWN parameter management
│   ├── specifications.py           # VNNLIB specification generation (ε → formal constraints)
│   ├── model_defs.py               # ~50 model architectures (MNIST FCNN, CIFAR CNN, ResNet, etc.)
│   ├── data_utils.py               # MNIST/CIFAR data loading with normalization
│   ├── arguments.py                # Full CLI argument & YAML config system
│   ├── heuristics/                 # Branching heuristics (core of the research)
│   │   ├── babsr.py                # BaBSR scoring → baseline strategy
│   │   ├── kfsb.py                 # KFSB scoring → best strategy in current experiments
│   │   ├── fsb.py                  # FSB scoring (intermediate between babsr and kfsb)
│   │   └── base.py                 # NeuronBranchingHeuristic base class, RandomNeuronBranching
│   ├── attack/                     # Adversarial attack implementations
│   │   ├── attack_pgd.py           # PGD attack (hinge loss, L∞ norm)
│   │   ├── attack_interface.py     # Attack dispatch: attack() function
│   │   └── bab_attack.py           # BaB-based attack (stronger than PGD)
│   ├── lp_mip_solver/              # Gurobi LP/MIP solver integration (needs license)
│   ├── cuts/                       # CPLEX cut generation, BICCOS
│   ├── input_split/                # Input-space splitting (alternative to activation split)
│   └── exp_configs/course/         # ← Course experiment YAML configs
│       ├── mnist_baseline_auto.yaml
│       ├── mnist_baseline_kfsb.yaml
│       ├── m3/                     # M3 branching ablation (5 configs)
│       └── m4/                     # M4 epsilon grid (12 configs)
├── saved_models/                   # Pre-trained models (ONNX + PyTorch)
│   ├── mnist_fcnn.onnx             # ← Target model for ALL current experiments
│   └── mnist_fcnn.pth
├── 项目书/                         # Course project documents (Chinese)
│   ├── scripts/                    # Experiment run scripts & result processing
│   │   ├── run_m2_strategy_compare.sh     # M2: 3-strategy comparison
│   │   ├── run_m3_branching_ablation.sh   # M3: 5-config ablation
│   │   ├── run_m4_epsilon_grid.sh         # M4: 12-config epsilon sweep
│   │   ├── summarize_m2_results.py        # Log → CSV parser
│   │   ├── summarize_m3_results.py
│   │   ├── summarize_m4_results.py
│   │   ├── plot_m2_results.py             # CSV → PNG charts
│   │   ├── plot_m3_results.py
│   │   └── plot_m4_results.py
│   ├── results/                    # Experiment outputs (CSV, PNG, logs)
│   │   ├── m2/                     # M2 baseline comparison results
│   │   ├── m3/                     # M3 ablation results
│   │   ├── m4/                     # M4 epsilon grid results
│   │   ├── 结果汇总报告_2026-04-04.md
│   │   └── 开题预期成效对照清单_2026-04-04.md
│   ├── 开题报告.md
│   ├── 软件学报风格论文初稿.md
│   └── 实验日志/
├── train_mnist_fcnn.py            # [TRAINING] Only training script — creates saved_models/mnist_fcnn.*
└── auto_LiRPA/                    # Git submodule (UNINITIALIZED — must install manually)
```

## Key Commands

### Verify the verifier works
```bash
cd complete_verifier
python abcrown.py --help
```

### Run a single verification experiment
```bash
cd complete_verifier
python abcrown.py --config exp_configs/course/m3/mnist_m3_kfsb_candidates5.yaml
```

### Reproduce existing milestones
```bash
cd 项目书/scripts
bash run_m2_strategy_compare.sh   # ~30 min
bash run_m3_branching_ablation.sh # ~40 min
bash run_m4_epsilon_grid.sh       # ~2 hours
```

### Post-process results
```bash
cd 项目书/scripts
python summarize_m2_results.py && python plot_m2_results.py
python summarize_m3_results.py && python plot_m3_results.py
python summarize_m4_results.py && python plot_m4_results.py
```

### Train the MNIST FCNN model (if model needs regeneration)
```bash
python train_mnist_fcnn.py
# Outputs: saved_models/mnist_fcnn.pth, saved_models/mnist_fcnn.onnx
```

## Configuration System

All experiments are driven by YAML configs under `complete_verifier/exp_configs/`. CLI `--key value` overrides take precedence over YAML values.

**Critical config keys for course experiments:**

| YAML path | Meaning | Used in |
|-----------|---------|---------|
| `model.onnx_path` | Path to ONNX model | All configs |
| `data.dataset` | `MNIST` or `CIFAR` | All configs |
| `data.start` / `data.end` | Sample index range | All configs |
| `specification.norm` | Perturbation norm (`.inf`) | All configs |
| `specification.epsilon` | Perturbation radius | M4 varies this |
| `attack.pgd_order` | `skip` / `before` / `after` | Currently all `skip` |
| `solver.batch_size` | BaB batch size per round | 1024 (MNIST) |
| `bab.timeout` | Per-sample timeout in seconds | 30 (M2/M3), varies (M4) |
| `bab.branching.method` | `babsr` / `kfsb` / `fsb` | Core research variable |
| `bab.branching.candidates` | Top-K candidates for split | 3 (default), 5 (optimal) |
| `bab.branching.reduceop` | `min` or `max` for candidate scoring | `min` (default) |
| `general.complete_verifier` | `bab` for complete, `false` for incomplete-only | All M2/M3/M4 set to `bab` |

## Verification Flow (what abcrown.py actually does)

```
abcrown.py main():
  1. Load model: ONNX → onnx2pytorch → LiRPANet (auto_LiRPA BoundedModule)
  2. Load data: MNIST test set, specified sample range
  3. Generate specs: ε → VNNLIB (C matrix: true_label=+1, others=-1, rhs=0)
  4. [IF attack.pgd_order=before] Run PGD attack → mark violated samples
  5. Incomplete verification: CROWN/α-CROWN bound propagation → initial bounds
  6. Complete verification: general_bab() loop
     ├─ Branch: heuristic picks ReLU neuron to split
     ├─ Propagate: β-CROWN with split constraints + α-CROWN optimization
     ├─ Prune: remove domains where lb > rhs (safe) or ub ≤ rhs (unsafe)
     └─ Terminate: all domains resolved, or timeout, or max_domains reached
  7. Output: Final verified acc, problem counts, timing stats
```

## Key Facts About Results

### M2 (Strategy comparison, ε=0.02, 100 samples)
- baseline (babsr): 91.0% VRA, 9 timeout, 3.82s mean
- auto (babsr+auto): 91.0% VRA, 9 timeout, 5.77s mean
- kfsb: 92.0% VRA, 8 timeout, 3.17s mean

### M3 (Branching ablation, ε=0.02, 100 samples)
- **Best config: kfsb_candidates5** → 93.0% VRA, 7 timeout, 3.24s mean
- Improvement over baseline: +2.0% VRA, -2 timeout, -0.81s mean time
- Cost: more node visits (72224 vs 13014) but better total time

### M4 (Epsilon grid, 3 strategies × 4 epsilons)
- ε=0.01: all strategies 100% VRA, sub-second
- ε=0.02-0.03: kfsb advantage emerges (68% vs 65% vs 62% at 0.03)
- ε=0.05: timeout-dominated (88-95/100), results for trend only, NOT for precision comparison
- ⚠️ ε=0.05 used chunked execution with reduced parameters (different budget from 0.01-0.03)

## Relationship to Course Requirements

| Course requirement | Status | Evidence |
|-------------------|--------|----------|
| ReLU classification network | ✅ Done | `train_mnist_fcnn.py`, `saved_models/mnist_fcnn.onnx` |
| Compare verification strategies | ✅ Done | M2 (3 strategies) + M3 (5 configs) |
| Different perturbation radii | ✅ Done | M4 (4 epsilons) |
| Propose improved verification | ✅ Done | kfsb_candidates5 (+2.0% VRA) |
| MNIST experiments | ✅ Done | Full M2/M3/M4 pipeline |
| **CIFAR-10 experiments** | ❌ Missing | Infrastructure exists, no experiments run |
| **Cross-tool comparison (Marabou)** | ❌ Missing | Only literature references |
| **PGD attack evaluation** | ❌ Skipped | `attack.pgd_order: skip` in all configs |

## How to Add Missing Experiments (DO NOT do this without user request)

### PGD attack evaluation
- Change `attack.pgd_order: skip` → `attack.pgd_order: before` in any YAML config
- Expected: 5-8% of samples marked `unsafe-pgd` at ε=0.02

### CROWN-only / α-CROWN-only
- Set `general.complete_verifier: false` and keep `enable_incomplete_verification: true`
- For pure CROWN (no α optimization): add `alpha-crown.disable_optimization: true`

### CIFAR-10
- Train a `cifar_marabou_small` or `cifar_conv_small` model (defined in `model_defs.py`)
- Export to ONNX
- Create YAML with `data.dataset: CIFAR`, CIFAR-normalized mean/std, ε=2/255

## Known Issues & Pitfalls

1. **auto_LiRPA submodule is NOT initialized**: `auto_LiRPA/` is empty after clone. Must install manually via `cd auto_LiRPA && pip install -e .` or `git submodule update --init`.

2. **Hardcoded paths in scripts**: All shell scripts and Python summarizers under `项目书/scripts/` use `ROOT_DIR="/home/han/alpha-beta-CROWN"`. Must symlink or edit before running on a different machine.

3. **Gurobi license needed for LP/MIP**: The `lp_mip_solver/` module requires a Gurobi academic license. Current course experiments do not use MIP refinement, so this is not blocking.

4. **ε=0.05 results use different budget**: They were run with chunked execution and reduced MIP parameters. Do not compare 0.05 mean times directly with 0.01-0.03.

5. **All experiments run from `complete_verifier/`**: Running `abcrown.py` from the repo root will fail due to path resolution. Always `cd complete_verifier` first.

6. **Config file paths are relative to `complete_verifier/`**: `onnx_path: ../saved_models/mnist_fcnn.onnx` (note the `../`).

## Analysis Do's and Don'ts

### DO
- Cite specific file paths when making claims
- Reference CSV result files as authoritative evidence
- Distinguish "同预算口径" (ε=0.01-0.03) from "稳态口径" (ε=0.05)
- Use the experiment hierarchy: M3 = main improvement, M4 = trend validation
- Check the evidence chain: config → log → CSV → plot → report
- Look at `项目书/results/` for completed work before suggesting new experiments

### DON'T
- Create new Python source files in `complete_verifier/` (this is upstream code)
- Modify `model_defs.py`, `bab.py`, `abcrown.py` — these are upstream verifier code
- Suggest algorithm-level changes to CROWN/BaB — out of scope for this course project
- Claim ε=0.05 results are directly comparable with ε≤0.03 results
- Overstate kfsb's advantage at high epsilon — timeout dominates at ε=0.05
- Propose CIFAR-10 experiments without noting the training + verification time cost

## Writing Style for This Project

- Use concise Chinese for course-facing documents
- Prefer direct, evidence-backed conclusions
- When a claim depends on a specific file, cite it inline: `[path](relative/path)#L42`
- Separate "已完成" (completed) from "待补充" (planned but not done)
- Every quantitative claim should trace back to a log file or CSV
- For the course report: explicitly map each experiment to which course requirement it fulfills
