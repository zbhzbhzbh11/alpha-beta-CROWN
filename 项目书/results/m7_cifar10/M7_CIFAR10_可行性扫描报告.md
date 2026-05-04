# M7 CIFAR-10 最小可行验证 — 可行性扫描报告

**日期**: 2026-05-04
**状态**: 扫描完成，具备直接运行条件

---

## 1. 已有资源扫描

### 1.1 预训练模型权重

| 模型 | 架构 | 参数量 | 权重文件 | 大小 | 来源 |
|---|---|---|---|---|---|
| **cifar_marabou_small** | Conv2d(3,8,4,s=2)→ReLU→Conv2d(8,16,4,s=2)→ReLU→Flatten→FC(576→128)→ReLU→FC(128→64)→ReLU→FC(64→10) | ~57K | `complete_verifier/models/marabou_cifar10/cifar_marabou_small.pth` | 344KB | 官方 Marabou 基准模型 |
| cifar_marabou_medium | Conv2d(3,16)→Conv2d(16,32)→FC(1152→128)→FC(128→10) | ~180K | `models/marabou_cifar10/cifar_marabou_medium.pth` | 可用 | 同上 |
| cifar_marabou_large | 更大 | ~500K | `models/marabou_cifar10/cifar_marabou_large.pth` | 可用 | 同上 |

另有 `models/sdp/` 下多个 CIFAR SDP 模型权重和 `models/cifar10_resnet/` 下 ResNet 权重。

### 1.2 数据加载

`complete_verifier/data_utils.py:105-106` 原生支持 CIFAR-10：

```python
elif arguments.Config["data"]["dataset"] == 'CIFAR':
    loader = datasets.CIFAR10
```

配置中 `dataset: CIFAR` 即可加载 CIFAR-10 测试集。

### 1.3 已有配置

| 文件 | ε | 策略 | pgd_order | 状态 |
|---|---|---|---|---|
| `exp_configs/mnist_cifar10_baseline.yaml` | 2/255 | babsr (baseline) | before | 已存在 |
| `exp_configs/mnist_cifar10_kfsb.yaml` | 2/255 | kfsb_candidates5 | before | 已存在 |

### 1.4 已有实验结果

**数据源**: `项目书/results/m5/m5_cifar10_compare.csv`

| 策略 | VRA | safe | unsafe | timeout | mean_time | max_time |
|---|---|---|---|---|---|---|
| baseline (babsr) | **0.0%** | 0 | 16 | 4 | 15.44s | 86.93s |
| kfsb_candidates5 | **0.0%** | 0 | 16 | 4 | 13.41s | 68.04s |

- 20 个样本，ε=2/255，`pgd_order: before`
- PGD 发现 16/20 为 unsafe-pgd（反例检测率 80%）
- 4 个样本 timeout（BaB 无法在 60s 内完成）
- 0 个样本被证明 safe
- 单样本最慢达 68s（kfsb）和 87s（baseline），验证极重

**关键观察**：CIFAR-10 marabou_small 的 BaB 验证远超 MNIST FCNN 的计算负担——8K+ domains visited, 59K+ nodes, 每轮上千个子问题。这是 Conv+ReLU 结构导致的分支规模膨胀。

### 1.5 已有运行脚本

`项目书/scripts/run_m5_cifar10.sh`：运行 baseline + kfsb_candidates5。

---

## 2. 是否具备直接运行条件

**是。** 满足全部条件：

| 条件 | 状态 |
|---|---|
| 模型权重存在 | ✅ `models/marabou_cifar10/cifar_marabou_small.pth` |
| 模型定义存在 | ✅ `model_defs.py::cifar_marabou_small()` |
| 数据加载支持 | ✅ `data_utils.py` 支持 `dataset: CIFAR` |
| 已有参考配置 | ✅ `exp_configs/mnist_cifar10_kfsb.yaml` |
| 已有参考结果 | ✅ `项目书/results/m5/m5_cifar10_compare.csv` (VRA=0%) |

**不需要训练新模型**。`cifar_marabou_small` 是 Marabou 官方发布的标准基准模型，权重直接可用。

---

## 3. 需要新增的文件

### 3.1 M7 配置（4 个）

**目录**: `complete_verifier/exp_configs/course/m7_cifar10/`

| 文件 | ε | 方法 | 说明 |
|---|---|---|---|
| `cifar10_m7_crown_eps1_255.yaml` | 1/255 | CROWN | 不完整验证，不分支 |
| `cifar10_m7_crown_eps2_255.yaml` | 2/255 | CROWN | 不完整验证，不分支 |
| `cifar10_m7_alphacrown_eps1_255.yaml` | 1/255 | α-CROWN | 更紧的不完整验证 |
| `cifar10_m7_alphacrown_eps2_255.yaml` | 2/255 | α-CROWN | 更紧的不完整验证 |

**设计理由**：
- 优先 CROWN/α-CROWN（不分支）——从 MNIST M6 学到的教训是 CIFAR-10 BaB 极重（单样本 68s），不完整验证风险低、结论产出快。
- 保守超时（120s）——CIFAR-10 卷积 + 全连接组合比 MNIST 纯 FC 网络重得多。
- 如果 CROWN/α-CROWN 有结果，再视情况决定是否补 BaB-kfsb。

### 3.2 运行脚本（1 个）

**文件**: `项目书/scripts/run_m7_cifar10_incomplete.sh`

遍历 2 方法 × 2 ε = 4 组，每组 20 样本。

### 3.3 汇总脚本（1 个）

**文件**: `项目书/scripts/summarize_m7_cifar10_results.py`

---

## 4. 最小运行路径

```
Step 1: 创建配置 (4 个 YAML)
Step 2: 冒烟测试 (1 样本, ε=1/255, CROWN)
Step 3: 小样本测试 (5 样本, ε=1/255 和 2/255)
Step 4: 完整运行 (20 样本, 4 组)
Step 5: 汇总 CSV
Step 6: 与 MNIST M6 对比，讨论迁移效果
```

---

## 5. 预计风险

| 风险 | 等级 | 说明 |
|---|---|---|
| **CIFAR-10 不完整验证可能全部 unknown** | 高 | 从 BaB 结果看，ε=2/255 时 PGD 发现 80% unsafe、0% safe。CROWN/α-CROWN 边界可能根本无法证明任何样本 safe。如果 VRA=0%，这本身也是有效结论——说明 Conv 网络对边界传播的挑战远大于 FC 网络 |
| **ε=1/255 可能仍然过难** | 中 | 2/255 已是 0% VRA。1/255 是 CIFAR-10 鲁棒性验证的标准最小 ε，但 marabou_small 模型可能本身鲁棒性就很差 |
| **alpha-CROWN OOM** | 低 | marabou_small(~57K 参数)比 MNIST FCNN(~260K)小，batch_size=1024 应安全 |
| **PGD 预筛影响** | 低 | 配置中 `pgd_order: skip` 保持干净对比；若要加 PGD，修改一个字符即可 |
| **超时** | 中 | CROWN 不分支不会超时（无递归），但单样本边界传播可能比 MNIST 慢（Conv 操作更贵） |

---

## 6. 建议执行策略

### 6.1 先 CROWN/α-CROWN，暂不 BaB

**理由**：
1. CIFAR-10 BaB 极重（单样本 ~68s），20 样本可能需要 20+ 分钟且大概率全部 timeout。
2. CROWN/α-CROWN 不分支，速度可控，即使 VRA=0% 也是有效结论——它量化展示了"Conv 网络 + 边界传播"的证明能力上限。
3. 这与 MNIST M6 形成自然对比：MNIST FCNN 上 CROWN 能证明 98%（ε=0.01），CIFAR-10 Conv 网络上能证明多少？

### 6.2 如果 CROWN/α-CROWN VRA>0%，再视情况补 BaB

如果 CROWN 在不完整验证下有非零 VRA，说明有样本边界已足够紧——可以选最优配置跑 1~2 个 BaB 样本验证流程可行性。

### 6.3 如果 CROWN/α-CROWN VRA=0%

这本身就是一个有价值的结果：说明对于卷积网络，纯边界不分支完全无法产生安全证明。最终报告中可写：

> "在 MNIST FCNN 上 CROWN 能证明 98%（ε=0.01）的样本；在 CIFAR-10 Conv 网络上 CROWN 完全无法证明安全（VRA=0%）。这说明卷积层的存在显著恶化了边界传播的松弛程度——多层 Conv 的空间局部性使得激活区域的过近似误差在深层累积放大。这也解释了为什么 CIFAR-10 的 BaB 验证比 MNIST 重得多——分支需要削减的松弛误差更大。"

---

## 7. 与 MNIST M6 的预期对比

| 维度 | MNIST FCNN | CIFAR-10 Conv |
|---|---|---|
| 模型结构 | FC 784→256→128→10 | Conv(3,8)→Conv(8,16)→FC(576→128)→FC(128→64)→FC(64→10) |
| 参数量 | ~260K | ~57K（更少） |
| 输入维度 | 28×28×1=784 | 32×32×3=3072（更大） |
| 非线性层 | 2 ReLU FC 层 | 2 ReLU Conv 层 + 2 ReLU FC 层 |
| 边界传播难度 | 低（纯 FC，松弛可控） | 高（Conv 的 patch 松弛 = 多个重叠区域的取大/取小，过近似严重） |
| CROWN ε=0.01 预期 VRA | 98% | 可能很低或 0% |

---

## 8. 结论

**具备直接运行条件。** 权重、模型定义、数据加载均已就绪，无需训练新模型。

**最小实施路径**: 4 个 YAML + 1 个运行脚本 + 1 个汇总脚本，优先 CROWN/α-CROWN，保守超时，20 样本。

**主要风险**: CIFAR-10 Conv 网络对边界传播的挑战远大于 MNIST FCNN，CROWN/α-CROWN VRA 可能为 0%。即使如此，这也是可写入报告的有效对比结论。

**与现有 M5 的关系**: M5 CIFAR-10 已有 PGD+BaB 结果（VRA=0%, unsafe=16/20）。M7 补充 CROWN/α-CROWN 不完整验证，形成"CROWN→α-CROWN→BaB→PGD+BaB"的完整 CIFAR-10 验证策略对比。
