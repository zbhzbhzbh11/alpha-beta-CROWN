# M8 Marabou 最小可行接入 — 结果报告

**日期**: 2026-05-07  
**里程碑**: M8 — Marabou 最小可行接入实验  
**状态**: ✅ 完成  

---

## 1. 实验目的

M8 的目标是**实际接入 Marabou**，不再停留在方法学层面的文献对照。具体而言：

1. 在隔离环境中安装并运行 Marabou Python API（maraboupy 2.0.0）；
2. 用 Marabou 读取本项目的 ONNX 模型（`saved_models/mnist_fcnn.onnx`）；
3. 对 MNIST 单样本执行完整验证（complete verification），并与 alpha-beta-CROWN 的验证结果对照；
4. 验证跨工具一致性，为后续更大规模的工具对比打下基础。

## 2. 为什么要接入 Marabou

| 维度 | 说明 |
|------|------|
| **学术完整性** | 课程开题报告明确提出了 Marabou 交叉对比的目标。M2–M7 已完成 α,β-CROWN 内部策略对比，尚缺外部工具参照系 |
| **方法论对照** | Marabou 是 SMT-based complete solver，α,β-CROWN 是 bound-propagation-based solver，二者互补。同时使用可评估"求解速度 vs 精确性"的 trade-off |
| **独立验证** | Marabou 与 α,β-CROWN 使用完全不同的算法路径，结果一致性能交叉验证两个工具的正确性 |
| **可复现性** | 建立标准化的跨工具对比 pipeline，使后续研究者可在一台机器上同时运行两种验证器 |

## 3. 环境隔离说明

Marabou 未安装在项目的 Windows Python 3.14 或 `.venv` 中，而是部署在完全独立的 WSL 环境：

```
┌─────────────────────────────────────────────────┐
│  Windows (MSYS2)             WSL2 Ubuntu 24.04   │
│  ┌─────────────────┐        ┌──────────────────┐ │
│  │ Python 3.14     │        │ micromamba        │ │
│  │ (auto_LiRPA)    │        │ marabou-env       │ │
│  │                 │        │ Python 3.11.15    │ │
│  │ M2–M7 不变      │        │ maraboupy 2.0.0   │ │
│  │                 │        │ torch 2.11.0+cpu  │ │
│  └─────────────────┘        │ onnx 1.21.0       │ │
│                              │ onnxruntime 1.25  │ │
│  ONNX 模型:                 └──────────────────┘ │
│  //wsl.localhost/Ubuntu-New/home/han/            │
│  alpha-beta-CROWN/saved_models/mnist_fcnn.onnx   │
└─────────────────────────────────────────────────┘
```

| 隔离维度 | 措施 |
|----------|------|
| Python 版本 | WSL 使用 3.11.15，Windows 保持 3.14.0 |
| 包管理器 | micromamba（用户级），不影响系统 apt/dpkg |
| 虚拟环境 | `marabou-env`，与 `.venv` 完全独立 |
| 核心代码 | 未修改 `complete_verifier/` 任何文件 |
| M2–M7 结果 | 未覆盖任何已有实验数据 |

## 4. ONNX 模型读取

Marabou 直接通过 ONNX 解析模型，无需 PyTorch/onnx2pytorch 转换，避免了模型表示差异。

```
模型: saved_models/mnist_fcnn.onnx
大小: 919 KB
结构: Flatten → Gemm(784→256) → ReLU → Gemm(256→128) → ReLU → Gemm(128→10)
Marabou 解析: 0.13s ✅
输入变量: 784 (IDs 0–783)
输出变量: 10 (IDs 1552–1561)
总方程数: 由 Marabou 内部编码 ReLU 分段线性约束
```

与 alpha-beta-CROWN 使用 `onnx2pytorch → auto_LiRPA BoundedModule` 的路径不同，Marabou 直接从 ONNX 构建内部表示，保证了模型结构的原始语义。

## 5. 单样本验证设置

| 参数 | 值 |
|------|-----|
| 样本 | MNIST test sample 0 (标签: 7) |
| 模型预测 | 7 (正确) |
| 扰动范数 | L∞ |
| Epsilon | 0.01 |
| 输入约束 | x' ∈ [0, 1] ∩ [x − ε, x + ε] |
| Marabou 方法 | Complete SMT, 逐 target 编码 |
| Marabou 超时 | 30s/target |
| α,β-CROWN 方法 | Incomplete CROWN + α-CROWN boundary propagation |
| α,β-CROWN 设置 | α 优化: 20 iterations, lr=0.05, lr_decay=0.5 |

### Marabou 验证逻辑

对每个 target label j ≠ true_label (7)：
1. 编码约束: `output[j] − output[7] ≥ 0`
2. 编码输入约束: `x' ∈ [x₀ − ε, x₀ + ε] ∩ [0, 1]`
3. SMT 求解，检查是否存在满足所有约束的赋值
4. **UNSAT** → 不存在反例（该 target safe）
5. **SAT** → 找到反例（总体 unsafe）
6. 所有 target 均为 UNSAT → 样本 safe

### alpha-beta-CROWN 验证逻辑

1. 一次性计算所有 10 个输出类的上下界（CROWN + α-CROWN α 优化）
2. 检查 `∀ j ≠ 7: UB(j) < LB(7)` → safe
3. 任一类不满足 → unknown（incomplete 无法确认）

## 6. Marabou vs alpha-beta-CROWN 对比

### 总体结果

| 工具 | 样本 | ε | 结果 | 耗时 | 方法 |
|------|------|---|:---:|------|------|
| Marabou | 0 | 0.01 | **safe** | 4.269s | Complete SMT |
| alpha-beta-CROWN | 0 | 0.01 | **safe** | 0.495s | Incomplete bounds |

✅ 两个工具结果一致。

### Marabou 逐 target 详情

| Target | 退出码 | 耗时 | 说明 |
|--------|:---:|------|------|
| 2 | UNSAT | 1.050s | 最难的 target（logit 差 −9.355） |
| 3 | UNSAT | 0.457s | |
| 9 | UNSAT | 0.379s | |
| 8 | UNSAT | 0.362s | |
| 0 | UNSAT | 0.409s | |
| 5 | UNSAT | 0.806s | |
| 1 | UNSAT | 0.383s | |
| 4 | UNSAT | 0.217s | |
| 6 | UNSAT | 0.206s | 最远的 target（logit 差 −28.022） |

### alpha-beta-CROWN 边界

| 类 | 下界 (LB) | 上界 (UB) | UB − LB(7) |
|----|-----------|-----------|------------|
| 0 | −3.745 | −1.539 | −11.247 |
| 1 | −4.578 | −3.331 | −13.039 |
| 2 | 1.216 | 3.701 | **−6.007** |
| 3 | 0.466 | 2.335 | −7.373 |
| 4 | −9.218 | −6.052 | −15.760 |
| 5 | −4.399 | −1.747 | −11.455 |
| 6 | −17.838 | −14.587 | −27.546 |
| **7** | **9.708** | 12.844 | — |
| 8 | −3.117 | −1.145 | −10.853 |
| 9 | −3.220 | −0.653 | −10.361 |

**安全性判定**: ∀j ≠ 7, UB(j) < LB(7) → **SAFE**

### 时间复杂度对比

| 维度 | Marabou | α,β-CROWN |
|------|---------|------------|
| 单 sample 耗时 | 4.27s (9 targets) | 0.50s (1 pass) |
| 每 target 耗时 | 0.47s 平均 | — |
| 最慢 target | 1.05s (class 2) | — |
| 方法特性 | 逐个 target 串行求解 | 一次性批量传播 |

在 ε=0.01 的简单场景下，α,β-CROWN 的 incomplete bound propagation 速度约为 Marabou complete SMT 的 8.6 倍，且结果一致。

## 7. Exit Code 检查 Bug

### 问题描述

Marabou 的 `solve()` 返回 `exitCode` 为字符串 `"unsat"` 时，代码使用了：

```python
if "sat" in exitCode.lower():   # BUG: "sat" in "unsat" → True!
    verdict = "SAT"
```

导致 UNSAT 被误判为 SAT。

### 修复

```python
if exitCode.strip().lower() == "sat":
    verdict = "SAT"
elif exitCode.strip().lower() == "unsat":
    verdict = "UNSAT"
```

### 影响

- 第一个版本的输出曾报告 "SAT（找到反例）"，实为 UNSAT
- 已完全修复并重跑，最终结果正确
- 此 bug 未影响任何已写入的 M2–M7 结果

## 8. 当前结果能说明什么

1. **Marabou 最小可行接入已实现**：在隔离环境中成功安装、导入、运行 maraboupy 2.0.0，读取了本项目的 ONNX 模型，并完成了单样本完整验证。

2. **跨工具一致性得到验证**：sample 0、ε=0.01 下，Marabou（SMT complete）和 α,β-CROWN（bound propagation incomplete）得出一致结论。两个独立算法路径的一致性增加了各自结果的可信度。

3. **标准化对比 pipeline 已建立**：从 ONNX 读取 → 输入编码 → 求解 → 结果解析的端到端流程已在两套工具上分别实现，可直接复用到其他样本和 epsilon。

4. **环境隔离方案可行**：micromamba + WSL 的组合可以在不影响主 Python 环境的前提下运行 Linux-only 的 Marabou，为后续跨平台工具接入提供了模板。

## 9. 当前结果不能说明什么

1. **不能说明两个工具在更复杂场景下的表现**：ε=0.01 是最简单的扰动半径（α,β-CROWN 的实验显示所有策略在 ε=0.01 下均为 100% verified）。在更大的 ε（0.02–0.05）或更难样本上，两个工具的精度和耗时关系可能不同。

2. **不能说明 alpha-beta-CROWN 在所有场景下都比 Marabou 快**：仅一个样本、一个 epsilon、specific 配置，无法做广义的"性能对比"。Marabou 的 complete 特性在难样本上可能是必要的。

3. **不能推广到 CIFAR-10 或其他模型**：当前模型是 MNIST FCNN（784→256→128→10, 纯 ReLU），结构和规模都很简单。

4. **不构成大规模 benchmark**：单样本对照是 feasibility check，不是统计显著的性能评估。

## 10. 文件清单

### 新增/更新的完整文件列表

| # | 文件路径 | 类型 | 说明 |
|---|----------|------|------|
| 1 | `项目书/results/m8_marabou/Marabou环境检查报告.md` | 报告 | 阶段 1: Windows 侧环境检查 |
| 2 | `项目书/results/m8_marabou/WSL环境检查报告.md` | 报告 | 阶段 1: WSL 环境确认 |
| 3 | `项目书/results/m8_marabou/Marabou_WSL安装报告.md` | 报告 | 阶段 2: WSL 独立环境安装过程 |
| 4 | `项目书/results/m8_marabou/M8_Marabou_vs_ABCROWN_单样本对比报告.md` | 报告 | 阶段 5–6: 详细技术对比 |
| 5 | `项目书/results/m8_marabou/M8_Marabou最小接入结果报告.md` | 报告 | **本文** — M8 最终汇总 |
| 6 | `项目书/results/m8_marabou/m8_marabou_one_sample.json` | 数据 | Marabou 单样本结果 (safe, 4.27s, 9 targets UNSAT) |
| 7 | `项目书/results/m8_marabou/m8_abcrown_one_sample.json` | 数据 | α,β-CROWN 单样本结果 (safe, 0.50s) |
| 8 | `项目书/results/m8_marabou/logs/check_onnx_wsl.log` | 日志 | ONNX 读取测试日志 |
| 9 | `项目书/results/m8_marabou/logs/one_sample_eps0.01_wsl.log` | 日志 | 单样本验证完整日志 |
| 10 | `项目书/scripts/m8_marabou_check_onnx.py` | 脚本 | ONNX 读取测试 |
| 11 | `项目书/scripts/m8_marabou_verify_mnist_one.py` | 脚本 | Marabou 单样本验证（含 bug 修复） |
| 12 | `项目书/scripts/m8_abcrown_verify_one.py` | 脚本 | α,β-CROWN 单样本对照 |
| 13 | `complete_verifier/exp_configs/course/m8_marabou_compare.yaml` | 配置 | 对照实验 YAML（备用） |

### 不新增文件

- M2–M7 的所有结果文件（`项目书/results/m2/`, `m3/`, `m4/`）
- `complete_verifier/` 核心代码
- auto_LiRPA 子模块

## 11. 可写入中期报告的 3 条结论

### 结论 1：Marabou 工具接入成功

> 在 WSL Ubuntu 24.04 中通过 micromamba 建立独立 Python 3.11 环境，成功安装 maraboupy 2.0.0（预编译 manylinux wheel，未编译源码），实现了 Marabou 与本项目 ONNX 模型（MNIST 3 层 FCNN）的端到端验证链路。这是本项目首次接入外部独立验证工具。

### 结论 2：跨工具结果一致性验证通过

> 在 MNIST sample 0、ε=0.01（L∞）条件下，Marabou（complete SMT solver）与 alpha-beta-CROWN（incomplete bound propagation）得出一致结论：样本安全（safe），9 个 target label 均不可达。两个工具通过完全不同的算法路径（SMT vs CROWN bound）到达同一结论，相互验证了各自的正确性。

### 结论 3：建立了可复用的跨工具对比 pipeline

> M8 产出了标准化的 Marabou/α,β-CROWN 对比脚本（`m8_marabou_verify_mnist_one.py` 和 `m8_abcrown_verify_one.py`），支持参数化配置（sample_idx、epsilon、timeout），可直接复用于其他样本和扰动半径。环境隔离方案（micromamba + WSL）为后续接入更多 Linux-only 工具提供了模板。

## 12. 是否建议扩展到 5 样本

✅ **建议扩展到 5 样本**。理由：

| 维度 | 当前单样本 | 扩展到 5 样本后 |
|------|-----------|-----------------|
| 一致性验证 | 1/1 样本一致 | 可验证 N/5 样本一致率 |
| 分歧发现 | 无分歧 | 可能出现 CROWN=unknown 而 Marabou 能给出明确结果的样本 |
| 统计意义 | 个案 | 可计算平均耗时比、一致率 |
| 报告质量 | 存在性证明 | 有一定统计基础 |

**推荐下一步**: M8-plus: 5 samples × ε=0.01/0.02，Marabou vs α,β-CROWN 对照。约需 10 × (4.3s × 2) ≈ 1–2 分钟 Marabou 时间。
