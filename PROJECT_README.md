# ReLU 全连接神经网络鲁棒性验证实验项目

[English](#english-version) | [中文](#中文版本)

---

## 中文版本

### 项目概述

本项目基于 **α,β-CROWN** 工具，针对 ReLU 激活函数的全连接神经网络（FCNN）进行鲁棒性验证实验研究。通过对比不同验证策略（baseline、auto、kfsb）在 MNIST 数据集上的表现，系统性评估了分支策略优化对验证效率的影响，并在多个扰动半径（ε=0.01–0.05）下验证了策略的稳定性。

**核心成果**：
- ✅ 完成 M1–M4 四个里程碑实验
- ✅ 提出改进配置 `kfsb + candidates=5`，在 ε=0.02 下达到 **93.0% 验证准确率**（baseline 91.0%）
- ✅ 超时样本数从 9 降至 **7**，平均验证时间从 4.06s 降至 **3.24s**
- ✅ 完整的证据链：配置文件、日志、CSV 汇总、可视化图表

---

### 快速开始

#### 环境要求
- **操作系统**: Linux (WSL2 / Ubuntu 20.04+)
- **GPU**: NVIDIA GPU with CUDA 11.8+ (tested on RTX 4060 Laptop)
- **Python**: 3.10+
- **依赖**: PyTorch 2.4.1+, auto_LiRPA

#### 安装步骤

1. **克隆仓库**（包含 auto_LiRPA 子模块）
```bash
git clone --recursive https://github.com/YOUR_USERNAME/alpha-beta-CROWN.git
cd alpha-beta-CROWN
```

2. **创建 Conda 环境**
```bash
conda create -n abcrown python=3.10
conda activate abcrown
```

3. **安装依赖**
```bash
# 安装 PyTorch (CUDA 11.8)
pip install torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu118

# 安装 auto_LiRPA
cd auto_LiRPA
pip install -e .
cd ..

# 安装其他依赖
pip install -r complete_verifier/requirements.txt
```

4. **验证安装**
```bash
cd complete_verifier
python abcrown.py --config exp_configs/mnist_crown_general.yaml
```

---

### 实验复现

#### 数据准备
模型文件已包含在仓库中：
- `saved_models/mnist_fcnn.onnx` - MNIST 全连接网络（ONNX 格式）
- `saved_models/mnist_fcnn.pth` - PyTorch 权重文件

#### M2: 基线策略对比（ε=0.02, n=0–100）

```bash
cd 项目书/scripts
bash run_m2_strategy_compare.sh
```

**预期输出**：
- 日志文件：`项目书/实验日志/2026-03-14_mnist_*_0_100.log`
- CSV 汇总：`项目书/results/m2/m2_strategy_compare_0_100.csv`
- 可视化图表：`项目书/results/m2/figures/*.png`

**结果预览**：
| 策略 | 验证准确率 | 超时数 | 平均时间(s) |
|------|-----------|--------|------------|
| baseline | 91.0% | 9 | 3.82 |
| auto | 91.0% | 9 | 5.77 |
| kfsb | **92.0%** | **8** | **3.17** |

#### M3: 分支策略消融实验（主线A）

```bash
cd 项目书/scripts
bash run_m3_branching_ablation.sh
```

**预期输出**：
- 日志文件：`项目书/results/m3/logs/*.log`
- CSV 汇总：`项目书/results/m3/m3_branching_ablation.csv`
- 节点统计：`项目书/results/m3/m3_nodes_summary.csv`
- 可视化图表：`项目书/results/m3/figures/*.png`

**结果预览**：
| 配置 | 验证准确率 | 超时数 | 平均时间(s) |
|------|-----------|--------|------------|
| baseline | 91.0% | 9 | 4.06 |
| auto | 91.0% | 9 | 6.14 |
| kfsb | 92.0% | 8 | 3.60 |
| kfsb_reduceop_max | 92.0% | 8 | 3.44 |
| **kfsb_candidates5** | **93.0%** | **7** | **3.24** |

#### M4: Epsilon 网格扫描（辅线B）

```bash
cd 项目书/scripts
bash run_m4_epsilon_grid.sh
```

**预期输出**：
- 日志文件：`项目书/results/m4/logs/*.log`
- CSV 汇总：`项目书/results/m4/m4_epsilon_grid.csv`
- 可视化图表：`项目书/results/m4/figures/*.png`

**结果预览**（kfsb 策略）：
| ε | 验证准确率 | 超时数 | 平均时间(s) |
|---|-----------|--------|------------|
| 0.01 | 100.0% | 0 | 0.31 |
| 0.02 | 92.0% | 8 | 3.27 |
| 0.03 | 68.0% | 32 | 6.66 |
| 0.05 | 11.0% | 89 | 11.38 |

---

### 项目结构

```
alpha-beta-CROWN/
├── saved_models/
│   ├── mnist_fcnn.onnx          # MNIST 全连接模型
│   └── mnist_fcnn.pth
├── 项目书/
│   ├── scripts/                  # 实验脚本
│   │   ├── run_m2_strategy_compare.sh
│   │   ├── run_m3_branching_ablation.sh
│   │   ├── run_m4_epsilon_grid.sh
│   │   ├── summarize_m2_results.py
│   │   ├── summarize_m3_results.py
│   │   ├── summarize_m4_results.py
│   │   ├── plot_m2_results.py
│   │   ├── plot_m3_results.py
│   │   └── plot_m4_results.py
│   ├── results/                  # 实验结果
│   │   ├── m2/                   # M2 基线对比
│   │   │   ├── m2_strategy_compare_0_100.csv
│   │   │   └── figures/
│   │   ├── m3/                   # M3 消融实验
│   │   │   ├── m3_branching_ablation.csv
│   │   │   ├── m3_nodes_summary.csv
│   │   │   ├── logs/
│   │   │   └── figures/
│   │   ├── m4/                   # M4 epsilon 网格
│   │   │   ├── m4_epsilon_grid.csv
│   │   │   ├── logs/
│   │   │   └── figures/
│   │   ├── 阶段实验结果总汇_2026-04-03.md
│   │   ├── 结果汇总报告_2026-04-04.md
│   │   └── 开题预期成效对照清单_2026-04-04.md
│   ├── 软件学报风格论文初稿.md      # 论文初稿
│   ├── 开题报告.md
│   └── 作业题纲.md
├── complete_verifier/            # α,β-CROWN 核心代码
└── auto_LiRPA/                   # 子模块：线性界传播库
```

---

### 核心配置文件

所有实验配置位于 `complete_verifier/exp_configs/`：

- **M2 基线对比**:
  - `mnist_baseline.yaml` - baseline 策略
  - `mnist_baseline_auto.yaml` - auto 策略
  - `mnist_baseline_kfsb.yaml` - kfsb 策略

- **M3 消融实验**:
  - `mnist_m3_baseline.yaml`
  - `mnist_m3_auto.yaml`
  - `mnist_m3_kfsb.yaml`
  - `mnist_m3_kfsb_reduceop_max.yaml`
  - `mnist_m3_kfsb_candidates5.yaml` ⭐ **最优配置**

- **M4 epsilon 网格**:
  - `mnist_m4_baseline_eps0.01.yaml` ~ `mnist_m4_baseline_eps0.05.yaml`
  - `mnist_m4_auto_eps0.01.yaml` ~ `mnist_m4_auto_eps0.05.yaml`
  - `mnist_m4_kfsb_eps0.01.yaml` ~ `mnist_m4_kfsb_eps0.05.yaml`

---

### 关键改进点

#### 1. 分支策略优化（kfsb + candidates=5）

**改进内容**：
- 采用 kfsb（k-Fsb）分支策略替代 baseline 的 babsr 策略
- 将候选分支数量从默认 3 增加到 5

**效果**：
- 验证准确率：91.0% → **93.0%** (+2.0%)
- 超时样本数：9 → **7** (-22.2%)
- 平均验证时间：4.06s → **3.24s** (-20.2%)

**原理**：
- kfsb 策略通过更智能的分支选择，优先探索最有可能完成验证的子问题
- 增加候选数量允许算法在更大的搜索空间中选择最优分支点
- 以适度增加节点访问数量（72224 vs 13014）换取更高的验证成功率

#### 2. Epsilon 网格系统性评估

在 ε=0.01–0.05 范围内系统性评估了三种策略的稳定性：
- **低扰动区（ε=0.01）**：所有策略均达到 100% 验证率
- **中扰动区（ε=0.02–0.03）**：kfsb 优势显著，验证率高 1–6%
- **高扰动区（ε=0.05）**：所有策略进入 timeout 主导区，kfsb 仍保持最低平均时间

---

### 实验结果可视化

所有图表位于 `项目书/results/*/figures/`：

**M3 消融实验**：
- `m3_verified_acc.png` - 验证准确率对比
- `m3_timeout.png` - 超时样本数对比
- `m3_mean_time.png` - 平均验证时间对比

**M4 epsilon 网��**：
- `m4_vra_epsilon.png` - 验证准确率 vs ε
- `m4_timeout_epsilon.png` - 超时数 vs ε
- `m4_mean_time_epsilon.png` - 平均时间 vs ε

---

### 论文与报告

- **论文初稿**：`项目书/软件学报风格论文初稿.md`
  - 格式：软件学报论文格式
  - 内容：引言、相关工作、方法、实验结果、讨论、结论
  - 参考文献：10 篇（Reluplex, CROWN, beta-CROWN, etc.）

- **实验报告**：
  - `项目书/results/阶段实验结果总汇_2026-04-03.md` - 完整实验数据
  - `项目书/results/结果汇总报告_2026-04-04.md` - 结果分析与结论
  - `项目书/results/开题预期成效对照清单_2026-04-04.md` - 验收清单

---

### 常见问题

**Q1: 为什么只测试了 MNIST，没有 CIFAR-10？**

A: 本项目聚焦于全连接网络（FCNN）的验证策略优化。MNIST 的 FCNN 模型已足够展示策略差异；CIFAR-10 通常使用 CNN 架构，不在本项目范围内。

**Q2: eps=0.05 的结果为什么与其他 epsilon 不同？**

A: eps=0.05 采用"稳态标准"（分块执行 + 降低资源压力），与 eps=0.01–0.03 的"同预算标准"不可直接横向比较。该结果主要用于趋势判断，不用于精确性能比较。

**Q3: 如何复现论文中的所有实验？**

A: 按顺序执行：
```bash
cd 项目书/scripts
bash run_m2_strategy_compare.sh  # 约 30 分钟
bash run_m3_branching_ablation.sh  # 约 40 分钟
bash run_m4_epsilon_grid.sh  # 约 2 小时（含 eps=0.05 分块执行）
```

**Q4: 如何修改实验参数？**

A: 编辑 `complete_verifier/exp_configs/` 下的 YAML 配置文件，主要参数：
- `data.start` / `data.end` - 样本范围
- `specification.epsilon` - 扰动半径
- `bab.branching.method` - 分支策略（babsr / fsb / kfsb）
- `bab.branching.candidates` - 候选分支数量
- `bab.timeout` - 单样本超时时间（秒）

---

### 引用

如果本项目对您的研究有帮助，请引用：

```bibtex
@misc{relu-fcnn-verification-2026,
  title={基于 alpha-beta-CROWN 的 ReLU 全连接网络鲁棒性验证实验研究},
  author={zbhzbhzbh11 et al.},
  year={2026},
  howpublished={\url{https://github.com/YOUR_USERNAME/alpha-beta-CROWN}}
}
```

以及 α,β-CROWN 原始论文：

```bibtex
@inproceedings{wang2021betacrown,
  title={{Beta-CROWN}: Efficient bound propagation with per-neuron split constraints for complete and incomplete neural network verification},
  author={Wang, Shiqi and Zhang, Huan and Xu, Kaidi and Lin, Xue and Jana, Suman and Hsieh, Cho-Jui and Kolter, J Zico},
  booktitle={Advances in Neural Information Processing Systems},
  year={2021}
}
```

---

### 许可证

本项目基于 α,β-CROWN 开源工具，遵循其原始许可证。实验代码和配置文件采用 MIT License。

---

### 联系方式

- **项目维护者**: zbhzbhzbh11
- **上游工具**: [α,β-CROWN GitHub](https://github.com/Verified-Intelligence/alpha-beta-CROWN)
- **问题反馈**: 请在 GitHub Issues 中提交

---

## English Version

### Project Overview

This project conducts robustness verification experiments on ReLU-activated fully-connected neural networks (FCNNs) using the **α,β-CROWN** tool. By comparing different verification strategies (baseline, auto, kfsb) on the MNIST dataset, we systematically evaluate the impact of branching strategy optimization on verification efficiency and validate strategy stability across multiple perturbation radii (ε=0.01–0.05).

**Key Achievements**:
- ✅ Completed M1–M4 milestones
- ✅ Proposed improved configuration `kfsb + candidates=5`, achieving **93.0% verified accuracy** at ε=0.02 (baseline: 91.0%)
- ✅ Reduced timeout samples from 9 to **7**, average verification time from 4.06s to **3.24s**
- ✅ Complete evidence chain: config files, logs, CSV summaries, visualization charts

---

### Quick Start

#### Requirements
- **OS**: Linux (WSL2 / Ubuntu 20.04+)
- **GPU**: NVIDIA GPU with CUDA 11.8+ (tested on RTX 4060 Laptop)
- **Python**: 3.10+
- **Dependencies**: PyTorch 2.4.1+, auto_LiRPA

#### Installation

1. **Clone the repository** (including auto_LiRPA submodule)
```bash
git clone --recursive https://github.com/YOUR_USERNAME/alpha-beta-CROWN.git
cd alpha-beta-CROWN
```

2. **Create Conda environment**
```bash
conda create -n abcrown python=3.10
conda activate abcrown
```

3. **Install dependencies**
```bash
# Install PyTorch (CUDA 11.8)
pip install torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu118

# Install auto_LiRPA
cd auto_LiRPA
pip install -e .
cd ..

# Install other dependencies
pip install -r complete_verifier/requirements.txt
```

4. **Verify installation**
```bash
cd complete_verifier
python abcrown.py --config exp_configs/mnist_crown_general.yaml
```

---

### Experiment Reproduction

#### Data Preparation
Model files are included in the repository:
- `saved_models/mnist_fcnn.onnx` - MNIST FCNN (ONNX format)
- `saved_models/mnist_fcnn.pth` - PyTorch weights

#### M2: Baseline Strategy Comparison (ε=0.02, n=0–100)

```bash
cd 项目书/scripts
bash run_m2_strategy_compare.sh
```

**Expected Output**:
- Log files: `项目书/实验日志/2026-03-14_mnist_*_0_100.log`
- CSV summary: `项目书/results/m2/m2_strategy_compare_0_100.csv`
- Visualization: `项目书/results/m2/figures/*.png`

**Results Preview**:
| Strategy | Verified Acc | Timeout | Mean Time(s) |
|----------|-------------|---------|--------------|
| baseline | 91.0% | 9 | 3.82 |
| auto | 91.0% | 9 | 5.77 |
| kfsb | **92.0%** | **8** | **3.17** |

#### M3: Branching Strategy Ablation (Main Line A)

```bash
cd 项目书/scripts
bash run_m3_branching_ablation.sh
```

**Expected Output**:
- Log files: `项目书/results/m3/logs/*.log`
- CSV summary: `项目书/results/m3/m3_branching_ablation.csv`
- Node statistics: `项目书/results/m3/m3_nodes_summary.csv`
- Visualization: `项目书/results/m3/figures/*.png`

**Results Preview**:
| Configuration | Verified Acc | Timeout | Mean Time(s) |
|---------------|-------------|---------|--------------|
| baseline | 91.0% | 9 | 4.06 |
| auto | 91.0% | 9 | 6.14 |
| kfsb | 92.0% | 8 | 3.60 |
| kfsb_reduceop_max | 92.0% | 8 | 3.44 |
| **kfsb_candidates5** | **93.0%** | **7** | **3.24** |

#### M4: Epsilon Grid Sweep (Auxiliary Line B)

```bash
cd 项目书/scripts
bash run_m4_epsilon_grid.sh
```

**Expected Output**:
- Log files: `项目书/results/m4/logs/*.log`
- CSV summary: `项目书/results/m4/m4_epsilon_grid.csv`
- Visualization: `项目书/results/m4/figures/*.png`

**Results Preview** (kfsb strategy):
| ε | Verified Acc | Timeout | Mean Time(s) |
|---|-------------|---------|--------------|
| 0.01 | 100.0% | 0 | 0.31 |
| 0.02 | 92.0% | 8 | 3.27 |
| 0.03 | 68.0% | 32 | 6.66 |
| 0.05 | 11.0% | 89 | 11.38 |

---

### Key Improvements

#### 1. Branching Strategy Optimization (kfsb + candidates=5)

**Improvement**:
- Adopted kfsb (k-Fsb) branching strategy instead of baseline's babsr
- Increased candidate branch count from default 3 to 5

**Effect**:
- Verified accuracy: 91.0% → **93.0%** (+2.0%)
- Timeout samples: 9 → **7** (-22.2%)
- Mean verification time: 4.06s → **3.24s** (-20.2%)

**Principle**:
- kfsb strategy prioritizes exploring subproblems most likely to complete verification through smarter branch selection
- Increasing candidate count allows the algorithm to choose optimal branching points from a larger search space
- Trades moderate increase in node visits (72224 vs 13014) for higher verification success rate

#### 2. Systematic Epsilon Grid Evaluation

Systematically evaluated stability of three strategies across ε=0.01–0.05:
- **Low perturbation (ε=0.01)**: All strategies achieve 100% verification rate
- **Medium perturbation (ε=0.02–0.03)**: kfsb shows significant advantage, 1–6% higher verification rate
- **High perturbation (ε=0.05)**: All strategies enter timeout-dominated region, kfsb maintains lowest mean time

---

### Citation

If this project helps your research, please cite:

```bibtex
@misc{relu-fcnn-verification-2026,
  title={Robustness Verification of ReLU FCNNs with alpha-beta-CROWN: An Experimental Study},
  author={zbhzbhzbh11 et al.},
  year={2026},
  howpublished={\url{https://github.com/YOUR_USERNAME/alpha-beta-CROWN}}
}
```

And the original α,β-CROWN paper:

```bibtex
@inproceedings{wang2021betacrown,
  title={{Beta-CROWN}: Efficient bound propagation with per-neuron split constraints for complete and incomplete neural network verification},
  author={Wang, Shiqi and Zhang, Huan and Xu, Kaidi and Lin, Xue and Jana, Suman and Hsieh, Cho-Jui and Kolter, J Zico},
  booktitle={Advances in Neural Information Processing Systems},
  year={2021}
}
```

---

### License

This project is based on the α,β-CROWN open-source tool and follows its original license. Experiment code and configuration files are licensed under MIT License.

---

### Contact

- **Maintainer**: zbhzbhzbh11
- **Upstream Tool**: [α,β-CROWN GitHub](https://github.com/Verified-Intelligence/alpha-beta-CROWN)
- **Issue Reporting**: Please submit via GitHub Issues

---

**Note**: Replace `YOUR_USERNAME` with your actual GitHub username before pushing to GitHub.
