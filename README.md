# 神经网络鲁棒性验证策略对比实验

[English](#english-version) | [中文](#中文版本)

---

## 中文版本

### 项目概述

本项目基于 **α,β-CROWN**（VNN-COMP 多届冠军验证器），对 ReLU 神经网络进行系统性的验证策略对比实验。覆盖 MNIST（FCNN）和 CIFAR-10（ConvNet）两个数据集，形成从"极快但弱"到"较慢但强"的完整验证能力光谱。

**全部实验里程碑（M2–M8）**：

| 里程碑 | 内容 | 状态 |
|---|---|---|
| M2 | 基线策略对比（baseline/auto/kfsb） | ✅ |
| M3 | 分支策略消融（主线 A）— kfsb_candidates5 最优 | ✅ |
| M4 | ε 网格扫描（辅线 B）— 3策略×4ε | ✅ |
| M5 | PGD 攻击评估 — pgd_order=before 预筛选 | ✅ |
| M6 | CROWN/α-CROWN 不完整验证独立对比 | ✅ |
| M7 | CIFAR-10 最小验证（跨数据集迁移） | ✅ |
| M8 | Marabou 跨工具对比 + 论文复现（ICLR'21, VNN-COMP'21） | ✅ |

**核心成果**：
- 提出改进配置 `kfsb + candidates=5`，ε=0.02 下 VRA **93.0%**（baseline 91.0%），timeout -2，mean_time -0.81s
- PGD 预筛选在 ε=0.05 下将 timeout 从 89 降至 31（**-65.2%**）
- 完整验证链：CROWN(0.2s) → α-CROWN(1s) → BaB(6s) → PGD+BaB(4s)
- MNIST→CIFAR-10 跨数据集对比：Conv 网络的边界传播松弛远严重于 FCNN

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
git clone --recursive https://github.com/zbhzbhzbh11/alpha-beta-CROWN.git
cd alpha-beta-CROWN
```

2. **创建 Conda 环境**
```bash
conda create -n abcrown python=3.10
conda activate abcrown
```

3. **安装依赖**
```bash
pip install torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu118
cd auto_LiRPA && pip install -e . && cd ..
pip install -r complete_verifier/requirements.txt
```

4. **验证安装**
```bash
cd complete_verifier
python abcrown.py --config exp_configs/course/m3/mnist_m3_kfsb_candidates5.yaml --start 0 --end 1
```

---

### 实验复现

#### 数据准备

模型文件已包含在仓库中：
- `saved_models/mnist_fcnn.onnx` — MNIST FCNN（784→256→128→10, ReLU）
- `saved_models/mnist_fcnn.pth` — PyTorch 权重
- `complete_verifier/models/marabou_cifar10/cifar_marabou_small.pth` — CIFAR-10 ConvNet

#### M2: 基线策略对比（ε=0.02, n=0–100）

```bash
cd 项目书/scripts && bash run_m2_strategy_compare.sh
```

| 策略 | VRA | Timeout | Mean Time |
|------|:---:|:---:|:---:|
| baseline | 91.0% | 9 | 3.82s |
| auto | 91.0% | 9 | 5.77s |
| **kfsb** | **92.0%** | **8** | **3.17s** |

#### M3: 分支策略消融 — 主线 A

```bash
cd 项目书/scripts && bash run_m3_branching_ablation.sh
```

| 配置 | VRA | Timeout | Mean Time |
|------|:---:|:---:|:---:|
| baseline | 91.0% | 9 | 4.06s |
| auto | 91.0% | 9 | 6.14s |
| kfsb | 92.0% | 8 | 3.60s |
| kfsb_reduceop_max | 92.0% | 8 | 3.44s |
| **kfsb_candidates5** | **93.0%** | **7** | **3.24s** |

#### M4: ε 网格扫描 — 辅线 B

```bash
cd 项目书/scripts && bash run_m4_epsilon_grid.sh
```

**kfsb 策略结果**：

| ε | VRA | Timeout | Mean Time |
|---:|:---:|:---:|:---:|
| 0.01 | 100.0% | 0 | 0.31s |
| 0.02 | 92.0% | 8 | 3.27s |
| 0.03 | 68.0% | 32 | 6.66s |
| 0.05 | 11.0% | 89 | 11.38s |

#### M5: PGD 攻击预筛评估

```bash
cd 项目书/scripts && bash run_m5_pgd_compare.sh
python 项目书/scripts/summarize_m5_pgd_results.py
```

**kfsb + pgd_order=before 结果**：

| ε | VRA | PGD Unsafe | Timeout | Mean Time |
|---:|:---:|:---:|:---:|:---:|
| 0.01 | 100.0% | 0 | 0 | 1.80s |
| 0.02 | 92.0% | 5 | **3** | 2.83s |
| 0.03 | 62.0% | 17 | **21** | 4.59s |
| 0.05 | 11.0% | **58** | **31** | 4.44s |

> ε=0.03 公平对照（timeout=30s）：VRA=73.0%, timeout=10。详见 `项目书/results/m5_pgd_control/`。

#### M6: CROWN / α-CROWN 不完整验证

```bash
cd 项目书/scripts
# 运行脚本：直接执行位于 complete_verifier/ 的 abcrown.py
# 配置目录: complete_verifier/exp_configs/course/m6_incomplete/
```
```bash
# 例：CROWN ε=0.02, 100样本
cd complete_verifier
python abcrown.py --config exp_configs/course/m6_incomplete/mnist_m6_crown_eps0.02.yaml
```

| ε | CROWN VRA | α-CROWN VRA | CROWN t | α-CROWN t |
|---:|:---:|:---:|:---:|:---:|
| 0.01 | 98.0% | 98.0% | 0.20s | 0.26s |
| 0.02 | 82.0% | 83.0% | 0.21s | 0.72s |
| 0.03 | 41.0% | 46.0% | 0.26s | 1.58s |
| 0.05 | 4.0% | 5.0% | 0.23s | 2.78s |

#### M7: CIFAR-10 最小验证

```bash
cd complete_verifier
# CROWN ε=1/255, 20样本
python abcrown.py --config exp_configs/course/m7_cifar10/cifar10_m7_crown_eps1_255.yaml
```

| ε | CROWN VRA | α-CROWN VRA | CROWN t | α-CROWN t |
|---:|:---:|:---:|:---:|:---:|
| 1/255 | 15.0% | 25.0% | 0.17s | 3.08s |
| 2/255 | 0.0% | 0.0% | 0.14s | 4.01s |

对比 MNIST（ε≈2.5/255 CROWN VRA=98%）→ CIFAR-10 Conv 网络验证难度显著更高。

#### M8: Marabou 跨工具对比 + 论文复现

**跨工具对照（5 样本 × 3 ε）**

```bash
cd 项目书/scripts
python m8_abcrown_verify_one.py          # α,β-CROWN 单样本验证
python m8_marabou_verify_mnist_one.py    # Marabou 单样本验证
python m8_marabou_verify_mnist_batch.py  # Marabou 批量验证（输出 CSV）
```

| ε | 一致率 | Marabou avg time | α,β-CROWN avg time |
|---:|:---:|:---:|:---:|
| 0.01 | 5/5 ✅ | 4.46s | 0.50s |
| 0.02 | 4/5 ⚠️ | 3.53s | 0.40s |
| 0.03 | 4/5 ⚠️ | 45.73s | 0.41s |

**论文实验对标（α,β-CROWN ICLR'21 + VNN-COMP'21）**

```bash
cd complete_verifier
# 论文配置（iter=20, lr_beta=0.03, batch=4096, kfsb_c5, timeout=120s）
python abcrown.py --config exp_configs/course/m8_paper_repro/mnist_fcnn_paper_baB.yaml
```

| 论文结论 | 复现状态 |
|---|---|
| ① CROWN 速度 ~0.2s 且不随 ε 增长 | ✅ M6: 0.20–0.26s 恒定 |
| ② α-CROWN 边界比 CROWN 更紧 | ✅ M6: VRA +1~5pp |
| ③ BaB complete >> incomplete | ✅ Paper 配置 80% vs 46% (ε=0.03) |
| ④ α,β-CROWN > Marabou（竞赛排名一致） | ✅ 4/5 vs 3/5, 0.66s vs 45.7s |
| ⑤ CIFAR-10 >> MNIST 难度 | ✅ 98% → 0% VRA 断层 |

---

### 验证策略总对比

**完整对比**: 见结题报告 §4.1 及项目书/最终汇报_实验分析与结论.md §6

| 方法 | 类型 | 证明 safe？ | 发现 unsafe？ | 速度 | 本项目 |
|---|---|---|---|---|---|
| PGD | 经验攻击 | ❌ | ✅ | 极快 | M5 |
| CROWN | 不完整验证 | ✅(不完备) | ❌ | ~0.2s | M6 |
| α-CROWN | 不完整验证(更紧) | ✅(不完备) | ❌ | ~1s | M6 |
| β-CROWN+BaB | 完整验证 | ✅(完备) | ✅(BaB中) | ~6s | M4 |
| PGD+BaB | 攻击预筛+完整验证 | ✅(完备) | ✅(PGD预筛) | ~4s | M5 |

**验证能力光谱**: CROWN(0.2s) → α-CROWN(1s) → BaB(6s) → PGD+BaB(4s)

---

### 核心改进：kfsb_candidates5

| 指标 | baseline (babsr) | kfsb_candidates5 | 改善 |
|---|---|---|---|
| VRA | 91.0% | **93.0%** | **+2.0%** |
| Timeout | 9 | **7** | **-2** |
| Mean Time | 4.06s | **3.24s** | **-0.81s** |
| Max Time | 56.27s | **35.90s** | **-20.37s** |

M4 证实该优势在 ε=0.01~0.03 区间持续成立。M5 证实该配置与 PGD 预筛选兼容。

---

### 项目结构

```
alpha-beta-CROWN/
├── saved_models/
│   ├── mnist_fcnn.onnx / mnist_fcnn.pth
├── complete_verifier/
│   ├── abcrown.py                  # 主验证入口
│   ├── exp_configs/course/
│   │   ├── m3/                     # M3 消融配置 (5)
│   │   ├── m4/                     # M4 ε网格配置 (12)
│   │   ├── m5_pgd/                 # M5 PGD配置 (8)
│   │   ├── m6_incomplete/          # M6 不完整验证配置 (8)
│   │   ├── m7_cifar10/             # M7 CIFAR-10配置 (4)
│   │   ├── m8_marabou_compare.yaml # M8 Marabou 对比配置
│   │   └── m8_paper_repro/         # M8 论文对标配置 (5)
│   └── models/marabou_cifar10/     # CIFAR-10 预训练权重
├── 项目书/
│   ├── scripts/                    # 运行 & 汇总脚本
│   │   ├── run_m{2,3,4}*.sh
│   │   ├── run_m5_pgd_compare.sh
│   │   ├── run_m5_cifar10.sh
│   │   ├── summarize_m{2,3,4,5}*.py
│   │   ├── summarize_m5_pgd_results.py
│   │   ├── m8_abcrown_verify_one.py
│   │   ├── m8_marabou_verify_mnist_one.py
│   │   ├── m8_marabou_verify_mnist_batch.py
│   ├── results/
│   │   ├── m2/ m3/ m4/             # M2-M4 结果
│   │   ├── m5_pgd/                 # M5 PGD 结果+报告
│   │   ├── m5_pgd_control/         # M5 公平对照
│   │   ├── m6_incomplete/          # M6 结果+报告
│   │   ├── m7_cifar10/             # M7 结果+报告
│   │   ├── m8_marabou/             # M8 Marabou 结果+报告
│   │   └── M2_M3_M4_最终结论表_2026-05-04.md
│   ├── 结题报告_软件学报格式.md       # ★ 最终结题论文
│   ├── 项目全景梳理文档.md
│   ├── 最终汇报_实验分析与结论.md
│   └── 开题报告.md
└── auto_LiRPA/                     # 子模块
```

---

### 论文与报告

| 文档 | 路径 |
|---|---|
| **结题报告（最终论文）** | `项目书/结题报告_软件学报格式.md` |
| 最终实验分析与结论 | `项目书/最终汇报_实验分析与结论.md` |
| 完成情况汇报 PPT | `项目书/results/完成情况汇报.pptx` |
| 项目全景梳理 | `项目书/项目全景梳理文档.md` |
| 开题报告 | `项目书/开题报告.md` |
| 开题 vs 当前进展对比 | `项目书/开题报告vs当前进展对比.md` |
| 题目要求 vs 进展对照评分 | `项目书/题目要求vs当前进展_对照与评分.md` |
| M2/M3/M4 最终结论表 | `项目书/results/M2_M3_M4_最终结论表_2026-05-04.md` |
| M5 PGD 报告 | `项目书/results/m5_pgd/M5_PGD攻击评估结果报告.md` |
| M6 不完整验证报告 | `项目书/results/m6_incomplete/M6_不完整验证结果报告.md` |
| M7 CIFAR-10 报告 | `项目书/results/m7_cifar10/M7_CIFAR10不完整验证结果报告.md` |
| M8 Marabou 对比报告 | `项目书/results/m8_marabou/M8_Marabou_5样本工具对比报告.md` |
| 完整验证链路梳理 | `项目书/完整验证链路梳理.md` |
| 当前局限分析与解决方案 | `项目书/当前局限分析与解决方案.md` |

---

### 常见问题

**Q1: M5 和 M4 的 timeout 预算是否一致？**

ε=0.01/0.02 一致（30s），可直接对比。ε=0.03 M5 补跑了 M5-control（timeout=30s 公平对照），结论以对照为准。ε=0.05 两版均降压/分片，对比主要用于工程趋势分析。详见 `项目书/最终汇报_实验分析与结论.md` §3.4。

**Q2: CIFAR-10 验证为什么比 MNIST 难得多？**

在相近 ε 下，MNIST CROWN VRA=98%，CIFAR-10 CROWN VRA=0%。差距来自输入维度(784→3072)、RGB 三通道、Conv 结构松弛累积和自然图像数据复杂度等多因素共同作用，不应归因于单一原因。

**Q3: M6 为什么不产生 unsafe？**

CROWN/α-CROWN 是边界传播方法，计算输出下界，不主动搜索反例。只能判定 safe-incomplete 或 unknown。发现 unsafe 需要 PGD 攻击（M5）或 BaB 分支过程中发现反例。

**Q4: 如何复现全部实验？**

```bash
cd 项目书/scripts
bash run_m2_strategy_compare.sh    # ~30 min
bash run_m3_branching_ablation.sh  # ~40 min
bash run_m4_epsilon_grid.sh        # ~2 hours
bash run_m5_pgd_compare.sh         # ~30 min
# M6/M7 直接运行 abcrown.py，见上方对应章节
# M8 Marabou 对比 → 项目书/scripts/m8_marabou_verify_mnist_batch.py
```

**Q5: 如何修改实验参数？**

编辑 `complete_verifier/exp_configs/course/` 下的 YAML 配置文件：
- `data.start` / `data.end` — 样本范围
- `specification.epsilon` — 扰动半径
- `bab.branching.method` — 分支策略（babsr/kfsb）
- `bab.branching.candidates` — 候选分支数
- `bab.timeout` — 单样本超时（秒）
- `general.complete_verifier` — `bab`（完整）/ `skip`（不完整验证）

---

### 许可证与引用

本项目基于 α,β-CROWN 开源工具。实验代码和配置文件采用 MIT License。

```bibtex
@misc{nn-verification-strategy-comparison-2026,
  title={神经网络鲁棒性验证策略对比实验},
  author={zbhzbhzbh11},
  year={2026},
  howpublished={\url{https://github.com/zbhzbhzbh11/alpha-beta-CROWN}}
}

@inproceedings{wang2021betacrown,
  title={{Beta-CROWN}: Efficient bound propagation with per-neuron split
         constraints for complete and incomplete neural network verification},
  author={Wang, Shiqi and Zhang, Huan and Xu, Kaidi and Lin, Xue and
          Jana, Suman and Hsieh, Cho-Jui and Kolter, J Zico},
  booktitle={Advances in Neural Information Processing Systems},
  year={2021}
}
```

---

## English Version

### Project Overview

Systematic verification strategy comparison on ReLU neural networks using **α,β-CROWN**, covering MNIST (FCNN) and CIFAR-10 (ConvNet). Forms a complete verification capability spectrum from "fast but weak" to "slow but strong."

**All Milestones (M2–M8)**: ✅ Complete

| Milestone | Content |
|---|---|
| M2 | Baseline strategy comparison (baseline/auto/kfsb) |
| M3 | Branching ablation (Main Line A) — kfsb_candidates5 optimal |
| M4 | ε-grid sweep (Auxiliary Line B) — 3 strategies × 4ε |
| M5 | PGD attack evaluation — pgd_order=before pre-filtering |
| M6 | CROWN/α-CROWN incomplete verification |
| M7 | CIFAR-10 minimum verification (cross-dataset) |
| M8 | Marabou cross-tool comparison + Paper reproduction (ICLR'21, VNN-COMP'21) |

**Key Results**:
- `kfsb + candidates=5`: VRA **93.0%** (baseline 91.0%), timeout -2, mean_time -0.81s
- PGD pre-filtering: timeout reduced by **65.2%** at ε=0.05
- Full spectrum: CROWN(0.2s) → α-CROWN(1s) → BaB(6s) → PGD+BaB(4s)
- MNIST→CIFAR-10: ConvNet boundary relaxation far more severe than FCNN

### Quick Start

See Chinese version above for full installation and reproduction instructions.

### Experiment Results Summary

**MNIST FCNN (kfsb, ε=0.02)**:

| Method | VRA | Timeout | Mean Time |
|---|---|---|---|
| CROWN (M6) | 82.0% | 18 | 0.21s |
| α-CROWN (M6) | 83.0% | 17 | 0.72s |
| BaB (M4) | 92.0% | 8 | 3.27s |
| PGD+BaB (M5) | 92.0% | **3** | 2.83s |
| **kfsb_c5 (M3)** | **93.0%** | **7** | **3.24s** |

**CIFAR-10 ConvNet (ε=2/255, 20 samples)**:

| Method | VRA | PGD Unsafe |
|---|---|---|
| CROWN (M7) | 0.0% | — |
| α-CROWN (M7) | 0.0% | — |
| PGD+BaB (M5) | 0.0% | 16/20 |

### Key Documents

| Document | Path |
|---|---|
| **Final paper** | `项目书/结题报告_软件学报格式.md` |
| Full experiment analysis | `项目书/最终汇报_实验分析与结论.md` |
| Presentation PPT | `项目书/results/完成情况汇报.pptx` |
| Project overview | `项目书/项目全景梳理文档.md` |
| Proposal | `项目书/开题报告.md` |
| Requirements vs progress | `项目书/题目要求vs当前进展_对照与评分.md` |
| M5 PGD report | `项目书/results/m5_pgd/M5_PGD攻击评估结果报告.md` |
| M6 incomplete verif. | `项目书/results/m6_incomplete/M6_不完整验证结果报告.md` |
| M7 CIFAR-10 report | `项目书/results/m7_cifar10/M7_CIFAR10不完整验证结果报告.md` |
| M8 Marabou report | `项目书/results/m8_marabou/M8_Marabou_5样本工具对比报告.md` |

### License & Citation

MIT License. See Chinese version above for BibTeX citations.

### Contact

- **Maintainer**: zbhzbhzbh11
- **Upstream**: [α,β-CROWN](https://github.com/Verified-Intelligence/alpha-beta-CROWN)
- **Issues**: GitHub Issues
