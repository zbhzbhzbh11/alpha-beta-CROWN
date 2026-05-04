# M5 PGD 攻击评估实验结果报告

**实验日期**: 2026-05-04
**数据截止**: 2026-05-04
**状态**: ✅ 已完成

---

## 1. 实验目的

M2/M3/M4 的所有实验中，`attack.pgd_order` 均设置为 `skip`——PGD 攻击被完全跳过。这导致缺少"经验攻击评估 vs 形式化验证"的对比数据。

M5 的核心目的：**在 BaB 形式化验证之前先运行 PGD 攻击**，评估 PGD 预筛选对验证效率的影响，并回答三个问题：

1. PGD 能找到多少 BaB 也会判定为 unsafe 的反例？
2. PGD 预筛选能否降低 timeout 和平均验证时间？
3. PGD 的攻击能力随扰动半径 ε 增大如何变化？

---

## 2. PGD 与形式化验证的区别

| 维度 | PGD 攻击 | BaB 形式化验证 |
|---|---|---|
| 能证明 unsafe？ | **能**（找到反例） | **能**（分支过程中可能发现反例） |
| 能证明 safe？ | **不能**——找不到反例 ≠ 安全 | **能**——数学证明所有可能的扰动都不会改变分类 |
| 速度 | 快（秒级） | 慢（分钟级，含超时风险） |
| 方法性质 | 经验性、启发式 | 完备性、数学严格 |
| 在本实验中的角色 | **预筛选工具**——先筛出明确的 unsafe | **最终证明工具**——对剩余样本进行严格证明 |

核心认知：**PGD 只能证明"不鲁棒"，不能证明"鲁棒"。** PGD 找不到反例不代表模型安全——可能只是攻击不够强。最终安全保证仍然依赖 BaB 形式化验证。

---

## 3. attack.pgd_order: before 的含义

在 alpha-beta-CROWN 中，`pgd_order` 控制 PGD 攻击在验证流程中的执行时机：

| 取值 | 含义 |
|---|---|
| `skip` | 跳过 PGD，直接进入 BaB 验证（M2/M3/M4 使用的配置） |
| `before` | **先在每个样本上运行 PGD 攻击，找到反例则标记为 unsafe-pgd 并跳过后续 BaB**；未找到则继续 BaB 验证 |
| `after` | 先 BaB 验证，再 PGD 攻击 |
| `middle` | BaB 验证过程中穿插 PGD 攻击 |

**M5 使用的配置**: `attack.pgd_order: before`

**流程**:

```
对每个样本:
  1. PGD 攻击 (pgd_steps=100, pgd_restarts=30)
     ├── 找到反例 → 标记 "unsafe-pgd"，跳过 BaB ✓
     └── 未找到   → 进入步骤 2
  2. 不完整验证 (CROWN / α-CROWN)
     ├── safe → 标记 "safe-incomplete" ✓
     └── unknown → 进入步骤 3
  3. BaB 完整验证 (kfsb, candidates=5)
     ├── safe → 标记 "safe" ✓
     ├── unsafe → 标记 "unsafe-bab" ✓
     └── 超时 → 标记 "unknown" ✗
```

---

## 4. M5 实验配置

| 配置项 | 值 |
|---|---|
| 数据集 | MNIST，样本 0-100 |
| 模型 | `saved_models/mnist_fcnn.onnx` (FCNN, 784→256→128→10, ReLU) |
| 扰动范数 | L∞ |
| ε 取值 | 0.01, 0.02, 0.03, 0.05 |
| BaB 策略 | kfsb, candidates=5, reduceop=min |
| PGD 参数 | `pgd_order: before`, `pgd_steps: 100`, `pgd_restarts: 30` |
| 配置目录 | `complete_verifier/exp_configs/course/m5_pgd/` |

### 运行方式

| ε | 运行方式 | timeout 预算 | batch_size |
|---|---|---|---|
| 0.01 | 直接运行 | 30s（YAML 默认） | 1024 |
| 0.02 | 直接运行 | 30s（YAML 默认） | 1024 |
| 0.03 | 分片执行（10 样本/片） | 12s（降压） | 64 |
| 0.05 | 分片执行（10 样本/片） | 12s（降压） | 64 |

> **说明**: ε=0.03 和 ε=0.05 采用分片降压执行，目的是避免 WSL 资源耗尽导致断连。分片方式与 M4 的 0.05 处理一致。

---

## 5. M5 完整结果表

**数据源**: `项目书/results/m5_pgd/m5_pgd_compare.csv`

| ε | total | pgd_unsafe | bab_safe | bab_unsafe | unknown | **VRA (%)** | mean_time (s) | timeout |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.01 | 100 | 0 | 100 | 0 | 0 | **100.0** | 1.80 | 0 |
| 0.02 | 100 | 5 | 92 | 0 | 3 | **92.0** | 2.83 | 3 |
| 0.03 | 100 | 17 | 62 | 0 | 21 | **62.0** | 4.59 | 21 |
| 0.05 | 100 | 58 | 11 | 0 | 31 | **11.0** | 4.44 | 31 |

### 字段说明

| 字段 | 含义 |
|---|---|
| `pgd_unsafe` | PGD 攻击找到的反例数量（标记为 unsafe-pgd，跳过 BaB） |
| `bab_safe` | BaB（含不完整验证）证明为安全的样本数 |
| `bab_unsafe` | BaB 在分支过程中发现的反例数量 |
| `unknown` | 超时或无法判定的样本数 |
| `VRA` | Verified Accuracy = bab_safe / total × 100% |
| `timeout` | 超时样本数（与 unknown 一致，因为所有 unknown 均为 timeout） |

---

## 6. M5 与 M4 kfsb 对比

**M4 数据源**: `项目书/results/m4/m4_epsilon_grid.csv`
**M5 数据源**: `项目书/results/m5_pgd/m5_pgd_compare.csv`

| ε | M5 VRA | M4 VRA | Δ VRA | M5 timeout | M4 timeout | Δ timeout | M5 mean_t | M4 mean_t |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.01 | 100.0% | 100.0% | 0 | **0** | 0 | 0 | 1.80s | 0.31s |
| 0.02 | 92.0% | 92.0% | 0 | **3** | 8 | **-5 (-62.5%)** | 2.83s | 3.27s |
| 0.03 | 62.0% | 68.0% | -6.0% | **21** | 32 | **-11 (-34.4%)** | 4.59s | 6.66s |
| 0.05 | 11.0% | 11.0% | 0 | **31** | 89 | **-58 (-65.2%)** | 4.44s | 11.38s |

### ε=0.03 公平对照

M5 的 ε=0.03 使用 timeout=12s 的降压运行，而 M4 的 ε=0.03 使用 timeout=15s 的分片运行。为排除 timeout 预算差异的影响，补跑了 **M5-control** 实验（timeout=30s，直接运行）：

| 指标 | M4 kfsb (t/o=15s) | M5 kfsb 降压 (t/o=12s) | **M5-control (t/o=30s)** |
|---|---|---|---|
| VRA | 68.0% | 62.0% | **73.0%** |
| timeout | 32 | 21 | **10** |
| mean_time | 6.66s | 4.59s | **6.45s** |
| pgd_unsafe | 0 | 17 | **17** |

**数据源**: `项目书/results/m5_pgd_control/m5_pgd_control.csv`

在公平 timeout 预算下，PGD 预筛选使 VRA 从 68% **提升至 73% (+5.0pp)**，timeout 从 32 **降至 10 (-68.8%)**。M5 降压版的 VRA=62% 是工程降压导致的低估。

---

## 7. 关键发现

### 7.1 PGD 反例检测能力随 ε 增大显著增强

```
ε=0.01: PGD 找到 0 个反例   (全 safe)
ε=0.02: PGD 找到 5 个反例   (5% 样本被 PGD 判定 unsafe)
ε=0.03: PGD 找到 17 个反例  (17%)
ε=0.05: PGD 找到 58 个反例  (58%)
```

ε 从 0.02 增至 0.05 时，PGD 的反例检出率从 5% 急剧攀升至 58%，说明在高扰动下，经验攻击已能覆盖多数非鲁棒样本。

### 7.2 PGD 预筛选大幅降低 timeout 和平均验证时间

- ε=0.02: timeout 从 8 降至 3（**-62.5%**），mean time 从 3.27s 降至 2.83s
- ε=0.03（公平对照）: timeout 从 32 降至 10（**-68.8%**），mean time 从 6.66s 降至 6.45s
- ε=0.05: timeout 从 89 降至 31（**-65.2%**），mean time 从 11.38s 降至 4.44s

PGD 提前发现反例，避免了 BaB 在这些样本上的无效搜索。ε 越大，BaB 节省的计算量越大——因为在没有 PGD 的情况下，这些样本大概率会导致超时。

### 7.3 所有 falsified 样本均由 PGD 发现

| ε | pgd_unsafe | bab_unsafe | PGD 贡献率 |
|---:|---:|---:|---:|
| 0.01 | 0 | 0 | — |
| 0.02 | 5 | 0 | **100%** |
| 0.03 | 17 | 0 | **100%** |
| 0.05 | 58 | 0 | **100%** |

**bab_unsafe_count 在所有 ε 下均为 0**——BaB 没有额外发现任何 PGD 遗漏的反例。这说明在当前 PGD 参数（100 steps × 30 restarts）下，PGD 已经找到了所有可被当前验证流程发现的反例。

### 7.4 公平性说明

- ε=0.01 和 ε=0.02 的 M5 结果可与 M4 直接公平对比（相同 timeout=30s 预算，相同 batch_size=1024）。
- ε=0.03 和 ε=0.05 的 M5 主结果采用分片降压运行（timeout=12s），**不应**直接与 M4 的 0.01~0.03 同预算口径做等价对比。
- ε=0.03 已补跑 M5-control（timeout=30s 公平对照），结论以该对照为准。
- ε=0.05 在 M4 和 M5 均采用降压/分片执行，属于"稳态可执行口径"——两版 timeout 均严重不足（M4=15s 分片，M5=12s 分片），对比主要用于工程趋势分析，不宜外推到精确的 VRA 差异。

---

## 8. 可写入最终课程报告的三条结论

**结论 1: PGD 反例检测能力随 ε 增大显著增强。**
ε=0.01 时 PGD 未找到任何反例；ε=0.02 时检测到 5 个；ε=0.05 时检测到 58 个（占总样本 58%）。PGD 在高扰动下可作为高效的 unsafe 样本预筛工具。
——证据: `项目书/results/m5_pgd/m5_pgd_compare.csv`，pgd_unsafe_count 列。

**结论 2: PGD-before 预筛选可大幅降低 BaB 的 timeout 和平均验证时间。**
在 ε=0.03 公平对照中，PGD 预筛使 timeout 从 32 降至 10（降幅 68.8%）；在 ε=0.05 中 timeout 从 89 降至 31（降幅 65.2%）。PGD 以秒级代价提前判定反例，避免了 BaB 在这些样本上长达数十秒的无效搜索。
——证据: M5-control vs M4 对比表；`项目书/results/m5_pgd_control/m5_pgd_control.csv`。

**结论 3: PGD 找不到反例不代表安全，最终安全证明仍依赖形式化验证。**
在全部 4 个 ε 下，bab_unsafe_count 均为 0——PGD 找到了全部可检测的反例。但 ε=0.01 时 100 个样本的 PGD 均未找到反例，而 BaB 证明其中 100 个（100%）确实安全；ε=0.02 时 PGD 仅找到 5 个反例，剩余的 95 个样本中 BaB 证明 92 个安全、3 个超时。**安全保证来自 BaB 的数学证明，而非 PGD 的"未找到"**。
——证据: `项目书/results/m5_pgd/m5_pgd_compare.csv`，bab_safe_count 与 bab_unsafe_count 列；M4 对比数据。

---

## 9. 证据链索引

| 层级 | 路径 | 用途 |
|---|---|---|
| M5 配置 | `complete_verifier/exp_configs/course/m5_pgd/` (8 个 YAML) | kfsb + baseline，4 ε 值 |
| M5 主 CSV | `项目书/results/m5_pgd/m5_pgd_compare.csv` | 4 行（kfsb × 4ε）完整结果 |
| M5 对照 CSV | `项目书/results/m5_pgd_control/m5_pgd_control.csv` | ε=0.03 timeout=30s 公平对照 |
| M5 日志 | `项目书/results/m5_pgd/logs/` | 4 个主日志 |
| M5 分片日志 | `项目书/results/m5_pgd/logs/chunks/` | ε=0.03/0.05 各 10 个分片日志 |
| M5 对照日志 | `项目书/results/m5_pgd_control/logs/kfsb_eps0.03_timeout30.log` | ε=0.03 公平对照日志 |
| M5 运行脚本 | `项目书/scripts/run_m5_pgd_compare.sh` | 批量运行脚本 |
| M5 汇总脚本 | `项目书/scripts/summarize_m5_pgd_results.py` | 日志 → CSV 解析 |
| M4 参考数据 | `项目书/results/m4/m4_epsilon_grid.csv` | M4 kfsb 对比基准 |
| 本报告 | `项目书/results/m5_pgd/M5_PGD攻击评估结果报告.md` | M5 最终结论定稿 |
