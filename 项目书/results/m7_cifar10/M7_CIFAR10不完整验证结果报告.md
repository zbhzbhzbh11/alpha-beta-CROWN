# M7 CIFAR-10 不完整验证实验结果报告

**实验日期**: 2026-05-04
**状态**: ✅ 已完成

---

## 1. 实验目的

M2~M6 全部基于 MNIST 数据集和 FCNN 模型。课程题目要求覆盖 MNIST **和** CIFAR-10 两个数据集。M5 中已有 CIFAR-10 的 PGD+BaB 初步结果（VRA=0%），但缺少不完整验证（CROWN/α-CROWN）的独立评估。

M7 的核心目的：**将 M6 的不完整验证策略迁移到 CIFAR-10**，评估 CROWN 和 α-CROWN 在更复杂数据集上的表现，与 MNIST 形成跨数据集对比，并回答：

1. CROWN/α-CROWN 在 CIFAR-10 上能否证明任何样本 safe？
2. 与 MNIST M6 的差距有多大？差距可能来自哪些因素？
3. 是否还需要在 CIFAR-10 上补跑完整 BaB？

---

## 2. 为什么要补 CIFAR-10？

| 理由 | 说明 |
|---|---|
| **课程要求** | 开题报告和课程题目明确要求覆盖 MNIST 和 CIFAR-10 两个数据集 |
| **跨数据集对比** | MNIST FCNN 和 CIFAR-10 Conv 网络在结构、输入维度、数据复杂度上差异显著，对比结果有助于理解验证策略的泛化性 |
| **补全不完整验证链** | M5 已有 CIFAR-10 PGD+BaB 数据，缺少 CROWN/α-CROWN 不完整验证的独立评估 |
| **不增加训练成本** | 直接复用官方预训练模型 `cifar_marabou_small.pth`，无需额外训练 |

---

## 3. 使用的模型：cifar_marabou_small

| 属性 | 值 |
|---|---|
| 架构 | Conv2d(3,8,4,s=2) → ReLU → Conv2d(8,16,4,s=2) → ReLU → Flatten → FC(576,128) → ReLU → FC(128,64) → ReLU → FC(64,10) |
| 参数量 | ~57K |
| 输入 | 32×32×3 (RGB) |
| 权重来源 | Marabou 官方基准模型 (`models/marabou_cifar10/cifar_marabou_small.pth`, 344KB) |
| 训练方式 | 官方预训练（本项目未重新训练） |

### 与 MNIST FCNN 的结构差异

| 维度 | MNIST FCNN | CIFAR-10 cifar_marabou_small |
|---|---|---|
| 输入 | 28×28×1 (灰度, 784维) | 32×32×3 (RGB, 3072维) |
| 结构 | 纯 FC (784→256→128→10) | Conv×2 + FC×3 |
| 非线性层 | 2 ReLU | 4 ReLU (2 Conv + 2 FC) |
| 参数量 | ~260K | ~57K |
| 边界传播松弛源 | FC 层 ReLU 松弛 | Conv 层 patch 松弛 + FC 层 ReLU 松弛 |

---

## 4. M7 实验配置

| 配置项 | 值 |
|---|---|
| 数据集 | CIFAR-10，样本 0-20 |
| 模型 | `cifar_marabou_small`，权重 `models/marabou_cifar10/cifar_marabou_small.pth` |
| 扰动范数 | L∞ |
| ε 取值 | 1/255 (~0.0039), 2/255 (~0.0078) |
| 方法 | CROWN / α-CROWN |
| 关键配置 | `general.complete_verifier: skip`（不进入 BaB） |
| PGD | `pgd_order: skip`（保持纯边界传播对比） |
| 超时 | 120s/样本 |
| 配置目录 | `complete_verifier/exp_configs/course/m7_cifar10/`（4 个 YAML） |

---

## 5. M7 完整结果表

**数据源**: `项目书/results/m7_cifar10/m7_cifar10_incomplete.csv`

| ε | 方法 | total | safe_incomplete | unknown | **VRA (%)** | mean_time (s) | max_time (s) | has_bab |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1/255 | CROWN | 20 | 3 | 17 | **15.0** | 0.17 | 2.08 | NO |
| 1/255 | α-CROWN | 20 | 5 | 15 | **25.0** | 3.08 | 7.23 | NO |
| 2/255 | CROWN | 20 | 0 | 20 | **0.0** | 0.14 | 1.27 | NO |
| 2/255 | α-CROWN | 20 | 0 | 20 | **0.0** | 4.01 | 7.54 | NO |

### 正确性确认

- **4 组全部 `has_bab=NO`** — 确认未进入分支定界。
- **`unsafe=0`** — 不完整验证不搜索反例，符合预期。
- **`cifar_marabou_small.pth` 正确加载** — 日志中可见模型结构打印和 `cifar_marabou_small` 名称。
- **CIFAR-10 数据正确使用** — `dataset: CIFAR` 配置生效。

---

## 6. 与 MNIST M6 对比

| 数据集 | ε (绝对值) | ε (像素/255) | CROWN VRA | α-CROWN VRA | CROWN mean_t |
|---|---|---|---|---|---|
| **MNIST** | 0.01 | ~2.5/255 | **98.0%** | 98.0% | 0.20s |
| **MNIST** | 0.02 | ~5.1/255 | **82.0%** | 83.0% | 0.21s |
| **CIFAR-10** | 1/255 | 1/255 | **15.0%** | 25.0% | 0.17s |
| **CIFAR-10** | 2/255 | 2/255 | **0.0%** | 0.0% | 0.14s |

### 关键对比

在相近的 ε 值（MNIST 0.01 ≈ 2.5/255 vs CIFAR-10 2/255）下：
- MNIST CROWN VRA = **98.0%**
- CIFAR-10 CROWN VRA = **0.0%**

即使在更小的 ε（1/255，仅为 MNIST 0.01 的 40%），CIFAR-10 CROWN VRA 也仅 **15.0%**，α-CROWN 仅 **25.0%**。

CROWN 的 mean_time 在 CIFAR-10 上同样是 ~0.14~0.17s，与 MNIST 一致——边界传播的计算量取决于网络规模而非数据集或 ε 大小。

---

## 7. CIFAR-10 验证难度分析

CIFAR-10 与 MNIST 的验证难度差异来自多个因素的复合作用，不应归因于单一原因：

| 因素 | MNIST | CIFAR-10 | 对验证难度的影响 |
|---|---|---|---|
| **输入维度** | 784 (28×28×1) | 3072 (32×32×3) | 输入空间更大 → 扰动球体积更大 → 边界更松 |
| **RGB 通道** | 灰度单通道 | RGB 三通道 | 三通道间扰动的相关性增加边界传播复杂度 |
| **模型结构** | 纯 FC | Conv×2 + FC×3 | Conv 层 patch 模式的松弛中，多个重叠感受野的 ReLU 不确定性相互放大 |
| **数据集复杂度** | 手写数字（低纹理） | 自然图像（高纹理） | 自然图像的梯度更大，边界传播更难收紧 |
| **ReLU 层数** | 2 层 | 4 层 | 更多非线性层使松弛误差逐层累积更严重 |
| **模型参数量** | 260K | 57K | 参数量更少但更难验证——说明结构因素是主导 |

**重要说明**：以上因素共同导致了 CIFAR-10 验证难度远超 MNIST。卷积层的空间局部性和多层 ReLU 的松弛累积是重要原因之一，但不应将所有差异简单归为"完全由 Conv 层导致"。数据集复杂度、RGB 三通道、输入维度的差异同样显著。

---

## 8. 为什么不建议继续补跑 BaB

| 理由 | 说明 |
|---|---|
| **M5 已有 BaB 数据** | CIFAR-10 baseline + kfsb BaB（ε=2/255, 20 样本）已产出：VRA=0%，PGD 发现 16/20 unsafe，4 timeout |
| **无新增信息** | 在 CROWN/α-CROWN VRA=0% 且 PGD 已发现 80% unsafe 的情况下，再跑 BaB 不会改变核心结论 |
| **计算成本高** | CIFAR-10 BaB 单样本 ~68s（vs MNIST ~3~11s），20 样本需 20+ 分钟且大概率全 timeout |
| **已有完整的验证链** | CROWN(0.17s)→α-CROWN(3s)→PGD+BaB(13s, M5) — CIFAR-10 的不完整→完整→攻击预筛链已完整 |

---

## 9. 可写入最终报告的 3 条结论

**结论 1: CIFAR-10 上 CROWN/α-CROWN 的证明能力远低于 MNIST，跨数据集泛化差距显著。**
在相近的 ε（~2.5/255）下，MNIST CROWN VRA=98%，CIFAR-10 CROWN VRA=0%。即使在更小的 ε=1/255 下，CIFAR-10 的 α-CROWN VRA 也仅 25%。这种差距同时来自输入维度（784→3072）、RGB 三通道、Conv 结构的松弛累积以及自然图像的数据复杂度等多个因素。
——证据: `m7_cifar10_incomplete.csv` vs `m6_incomplete_compare.csv`

**结论 2: 在 CIFAR-10 上，PGD 预筛选的工程价值比 BaB 策略优化更大。**
M5 CIFAR-10 实验中 PGD 在 ε=2/255 下发现 80%（16/20）的样本为 unsafe，而 BaB 证明 0 个 safe 且有 4 个 timeout（单样本 ~68s）。在当前模型和 ε 下，PGD 以秒级代价快速筛出反例的能力比 BaB 的完备证明更具工程价值——因为这些样本用 BaB 也无法证明安全。
——证据: `项目书/results/m5/m5_cifar10_compare.csv` + 本实验

**结论 3: 验证策略对比框架从 MNIST 成功迁移到 CIFAR-10，证明了实验配置的可移植性。**
M7 在未修改任何核心代码的前提下，仅通过新增 4 个 YAML 配置文件，复用了 `cifar_marabou_small` 预训练权重和 CIFAR-10 数据加载器，完成了 CROWN/α-CROWN 不完整验证的独立评估。这证明本项目建立的"YAML 配置→运行脚本→CSV 汇总→对比分析"实验框架具有良好的数据集可移植性。
——证据: `exp_configs/course/m7_cifar10/` 下 4 个 YAML 配置 + `m7_cifar10_incomplete.csv`

---

## 10. 证据链索引

| 层级 | 路径 | 用途 |
|---|---|---|
| M7 配置 | `complete_verifier/exp_configs/course/m7_cifar10/` (4 个 YAML) | CROWN/α-CROWN × 2 ε |
| M7 CSV | `项目书/results/m7_cifar10/m7_cifar10_incomplete.csv` | 4 行完整结果 |
| M7 日志 | `项目书/results/m7_cifar10/logs/` | 4 个主日志 |
| M5 CIFAR-10 参考 | `项目书/results/m5/m5_cifar10_compare.csv` | PGD+BaB 对比基准 |
| MNIST M6 参考 | `项目书/results/m6_incomplete/m6_incomplete_compare.csv` | MNIST 不完整验证对比 |
| M7 可行性报告 | `项目书/results/m7_cifar10/M7_CIFAR10_可行性扫描报告.md` | 实验前扫描 |
| **本报告** | `项目书/results/m7_cifar10/M7_CIFAR10不完整验证结果报告.md` | M7 最终结论定稿 |
