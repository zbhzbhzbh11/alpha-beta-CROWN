# Marabou vs α,β-CROWN 方法学对比

**文档日期**: 2026-05-07
**用途**: 最终课程报告 §4.2（工具选型说明）
**状态**: 方法学对比（无实际 Marabou 实验数据）

---

## 1. 背景

课程题目原文："参考 Marabou 或 α,β-CROWN 等工具"——使用"或"字给出了选择空间。本项目选择 **α,β-CROWN 作为主实验平台**，Marabou 作为方法学参照。本文档解释两者的技术差异与选型理由。

---

## 2. 核心技术路线对比

### 2.1 α,β-CROWN：线性松弛 + 分支定界

**核心思想**: 将神经网络的非线性激活函数（ReLU）用线性上下界包裹（over-approximation），通过闭式解快速传播边界，得到输出的保守估计。当边界不够紧时，引入分支定界（Branch-and-Bound）逐步细化。

**技术栈**:
- **CROWN**: 边界传播的闭式解，单次前向传播即可得到输出边界
- **α-CROWN**: 将 ReLU 松弛的斜率参数 α 设为可优化变量，通过梯度下降收紧边界
- **β-CROWN**: 在分支后的子问题中，将分裂约束编码进边界传播，进一步收紧
- **BaB**: 对不确定的 ReLU 神经元进行分支，递归求解子问题

**优势**:
- GPU 友好：边界传播本质是矩阵运算，可高效并行
- 批量处理：支持 batch_size 参数，一次处理多个样本
- 配置灵活：YAML 驱动，易于批量实验
- 扩展性强：在 VNN-COMP 2021-2023 中多次获得冠军

**局限**:
- 线性松弛引入过近似误差，边界可能偏松
- 高 ε 下需要大量分支，可能超时

### 2.2 Marabou：SMT 求解 + 分支定界

**核心思想**: 将神经网络验证问题编码为 **可满足性模理论（SMT）约束求解问题**。Marabou 使用 Reluplex 算法（Simplex 求解器的扩展），直接在约束空间中搜索反例或证明不存在反例。

**技术栈**:
- **Reluplex**: 扩展线性规划 Simplex 算法，支持 ReLU 的分段线性约束
- **SMT 求解器**: 精确求解约束系统，不引入松弛误差
- **BaB**: 当约束系统复杂时，对 ReLU 进行分支

**优势**:
- 精确性：不引入线性松弛的过近似误差
- 解释性：可输出具体的反例（对抗样本）
- 理论完备：SMT 求解保证在有限时间内收敛（若不超时）

**局限**:
- CPU 密集：Simplex 求解器主要依赖 CPU，GPU 加速有限
- 扩展性：在大规模网络（如 ResNet）上求解时间长
- 工程成本：需要将模型转换为 Marabou 格式（.nnet 或自定义格式）

---

## 3. 详细对比表

| 维度 | α,β-CROWN | Marabou |
|---|---|---|
| **核心思想** | CROWN 线性松弛 + BaB 分支定界 | Reluplex / SMT 精确求解 + BaB |
| **ReLU 处理** | 线性上下界包裹（over-approximation） | 分段线性约束精确编码 |
| **GPU 加速** | ✅ 高度友好（矩阵运算为主） | ⚠️ 有限（Simplex 求解器主要 CPU） |
| **批量验证** | ✅ 支持 batch_size 参数 | ⚠️ 单样本串行为主 |
| **配置方式** | YAML 配置文件驱动 | 命令行参数 / Python API |
| **模型格式** | ONNX（通用） | .nnet / 自定义格式（需转换） |
| **MNIST 适用性** | ✅ 高（100 样本 ~3s/样本） | ✅ 可行（单样本秒级~分钟级） |
| **CIFAR-10 适用性** | ✅ 可行（单样本 ~13s） | ⚠️ 较慢（Conv 网络求解复杂） |
| **完整性** | ✅ BaB 收敛到完整验证 | ✅ SMT 理论完备 |
| **精确性** | ⚠️ 线性松弛引入误差 | ✅ 无松弛误差 |
| **VNN-COMP 表现** | 🏆 2021-2023 多次冠军 | ✅ 参赛工具之一 |
| **工程成本** | 低（pip 安装，YAML 配置） | 中（编译安装，格式转换） |
| **课程项目适配** | ✅ 适合批量策略对比实验 | ⚠️ 单点验证为主 |
| **本项目角色** | **主实验平台**（M0-M7 全部实验） | **方法学对照**（文献参考） |

---

## 4. 为什么本项目选择 α,β-CROWN 作为主平台？

### 4.1 题目要求允许选择

课程题目原文："参考 Marabou 或 α,β-CROWN 等工具"——使用"或"字明确给出了选择空间，并非要求两者都接入。

### 4.2 项目目标匹配度

本项目的核心目标是：
1. **对比不同验证策略**（PGD / CROWN / α-CROWN / BaB / PGD+BaB）
2. **在不同扰动半径下验证**（ε ∈ {0.01, 0.02, 0.03, 0.05}）
3. **在 MNIST 和 CIFAR-10 上实验**

这些目标需要：
- 批量运行多组实验（40+ 组配置）
- 快速迭代验证策略参数
- 统一的配置管理和结果汇总

α,β-CROWN 的 **YAML 配置驱动 + GPU 加速 + batch 处理** 完美匹配这些需求。

### 4.3 GPU 加速优势

本项目使用 NVIDIA GeForce RTX 4060 Laptop GPU。α,β-CROWN 的边界传播本质是矩阵运算，可充分利用 GPU 并行能力：
- MNIST FCNN: ~3s/样本（100 样本批量）
- CIFAR-10 Conv: ~13s/样本

Marabou 的 Simplex 求解器主要依赖 CPU，GPU 加速有限，在相同硬件下速度劣势明显。

### 4.4 配置化实验管理

α,β-CROWN 支持 YAML 配置文件，可通过修改配置快速切换：
- 分支策略（babsr / kfsb / auto）
- 分支参数（candidates / reduceop）
- 扰动半径（epsilon）
- PGD 参数（pgd_order / pgd_steps）

这使得 M2-M7 的 40+ 组实验可以通过统一的脚本批量执行和汇总。Marabou 的配置方式主要是命令行参数，批量实验管理成本更高。

### 4.5 ONNX 通用格式

α,β-CROWN 直接支持 ONNX 格式，这是神经网络模型的工业标准格式。本项目的 MNIST FCNN 和 CIFAR-10 Conv 模型均可直接导出为 ONNX，无需额外转换。

Marabou 需要将模型转换为 .nnet 或自定义格式，增加了工程成本。

### 4.6 VNN-COMP 验证

α,β-CROWN 在 VNN-COMP（神经网络验证国际竞赛）2021-2023 中多次获得冠军，证明了其在 ReLU 网络验证上的 SOTA 性能。选择 α,β-CROWN 作为主平台，可以确保实验结果的可信度和前沿性。

---

## 5. Marabou 在本项目中的角色

### 5.1 方法学对照

Marabou 作为 **SMT 求解路线的代表**，在本项目中用于方法学对照：
- 在开题报告 §2.2 中引用 Marabou 的 Reluplex 算法，说明 SMT 路线的精确性优势
- 在验证策略分析报告中对比"线性松弛 vs SMT 求解"的 trade-off
- 在最终报告中说明"为什么选择 α,β-CROWN"时，以 Marabou 为对照点

### 5.2 未实际接入的原因

1. **课程周期限制**: 安装 Marabou、学习其 API、转换模型格式、调试运行，预计需要 1-2 周。在课程周期内完成 40+ 组 α,β-CROWN 实验已接近时间上限。
2. **实验目标已达成**: 本项目的核心目标是"对比不同验证策略"，而非"对比不同验证工具"。6 种策略（PGD / CROWN / α-CROWN / BaB × 3）的对比已充分覆盖验证能力光谱。
3. **数据充分性**: α,β-CROWN 的 40+ 组实验已形成完整的证据链，足以支撑课程报告的结论。
4. **工程成本**: Marabou 的模型格式转换和批量实验管理成本较高，性价比不如在 α,β-CROWN 内部做更深入的策略对比。

---

## 6. 后续工作展望

### 6.1 Marabou 接入的可行性

本项目已形成 **ONNX + VNNLIB** 的标准化实验框架：
- 模型：ONNX 格式（`saved_models/mnist_fcnn.onnx`）
- 规范：VNNLIB 格式（可由 α,β-CROWN 的 `specifications.py` 生成）

VNNLIB 是 VNN-COMP 的标准规范格式，Marabou 也支持 VNNLIB 输入。因此，后续工作可以：
1. 安装 Marabou（从源码编译或使用 Docker）
2. 复用本项目的 ONNX 模型和 VNNLIB 规范
3. 在相同样本集上运行 Marabou，对比验证时间和结果

### 6.2 跨工具对比的价值

跨工具对比（α,β-CROWN vs Marabou）可以回答：
- 线性松弛的误差在实际任务中有多大？
- SMT 求解的精确性是否值得额外的时间成本？
- 在哪些样本上两者结论不一致？

这些问题超出了本课程项目的范围，但可作为后续研究方向。

---

## 7. 可直接放入最终报告的小节

### §4.2 工具选型：为什么选择 α,β-CROWN？

课程题目原文："参考 Marabou 或 α,β-CROWN 等工具"——使用"或"字给出了选择空间。本项目选择 **α,β-CROWN 作为主实验平台**，理由如下：

**1. 项目目标匹配度高**

本项目的核心目标是对比不同验证策略（PGD / CROWN / α-CROWN / BaB）在不同扰动半径下的表现，需要批量运行 40+ 组实验。α,β-CROWN 的 YAML 配置驱动、GPU 加速和 batch 处理能力完美匹配这些需求。

**2. GPU 加速优势**

本项目使用 NVIDIA GeForce RTX 4060 Laptop GPU。α,β-CROWN 的边界传播本质是矩阵运算，可充分利用 GPU 并行能力（MNIST ~3s/样本，CIFAR-10 ~13s/样本）。Marabou 的 Simplex 求解器主要依赖 CPU，GPU 加速有限。

**3. 配置化实验管理**

α,β-CROWN 支持 YAML 配置文件，可通过修改配置快速切换分支策略、扰动半径、PGD 参数等。这使得 M2-M7 的 40+ 组实验可以通过统一的脚本批量执行和汇总。Marabou 的配置方式主要是命令行参数，批量实验管理成本更高。

**4. ONNX 通用格式**

α,β-CROWN 直接支持 ONNX 格式（神经网络模型的工业标准），本项目的 MNIST FCNN 和 CIFAR-10 Conv 模型均可直接导出，无需额外转换。Marabou 需要将模型转换为 .nnet 或自定义格式。

**5. VNN-COMP 验证**

α,β-CROWN 在 VNN-COMP（神经网络验证国际竞赛）2021-2023 中多次获得冠军，证明了其在 ReLU 网络验证上的 SOTA 性能。

**Marabou 在本项目中的角色**

Marabou 作为 **SMT 求解路线的代表**，在本项目中用于方法学对照：
- 在开题报告中引用 Marabou 的 Reluplex 算法，说明 SMT 路线的精确性优势
- 在方法对比中说明"线性松弛 vs SMT 求解"的 trade-off

**为什么没有实际接入 Marabou？**

1. **课程周期限制**: 安装 Marabou、学习其 API、转换模型格式、调试运行，预计需要 1-2 周。在课程周期内完成 40+ 组 α,β-CROWN 实验已接近时间上限。
2. **实验目标已达成**: 本项目的核心目标是"对比不同验证策略"，而非"对比不同验证工具"。6 种策略的对比已充分覆盖验证能力光谱。
3. **工程成本**: Marabou 的模型格式转换和批量实验管理成本较高，性价比不如在 α,β-CROWN 内部做更深入的策略对比。

**后续工作展望**

本项目已形成 **ONNX + VNNLIB** 的标准化实验框架。VNNLIB 是 VNN-COMP 的标准规范格式，Marabou 也支持 VNNLIB 输入。因此，后续工作可以复用本项目的 ONNX 模型和 VNNLIB 规范，在相同样本集上运行 Marabou，对比验证时间和结果。

---

## 8. 参考文献

[1] Katz G, Barrett C, Dill D L, et al. Reluplex: An efficient SMT solver for verifying deep neural networks[C]//Computer Aided Verification. Springer, 2017: 97-117.

[2] Xu K, Shi Z, Zhang H, et al. Automatic perturbation analysis for scalable certified robustness and beyond[C]//NeurIPS, 2020.

[3] Wang S, Zhang H, Xu K, et al. Beta-CROWN: Efficient bound propagation with per-neuron split constraints for complete and incomplete neural network verification[C]//NeurIPS, 2021.

[4] Zhang H, Wang S, Xu K, et al. General cutting planes for bound-propagation-based neural network verification[C]//NeurIPS, 2022.

[5] VNN-COMP 2023 Results. https://sites.google.com/view/vnn2023

---

**文档状态**: ✅ 已完成，可直接引用至最终课程报告 §4.2
