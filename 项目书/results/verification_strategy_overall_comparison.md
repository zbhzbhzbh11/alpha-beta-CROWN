# 不同验证策略总对比表

**生成日期**: 2026-05-04
**数据来源**: M4 (`m4_epsilon_grid.csv`)、M5 (`m5_pgd_compare.csv`)、M6 (`m6_incomplete_compare.csv`)、M5-control (`m5_pgd_control/m5_pgd_control.csv`)
**用途**: 最终课程报告 §7（实验结果）直接引用

---

## 1. 方法理论对比

| 方法 | 类型 | 能否证明鲁棒？ | 能否发现反例？ | 速度 | 局限 | 本项目对应实验 |
|---|---|---|---|---|---|---|
| **PGD 攻击** | 经验攻击 | ❌ | ✅ | 极快（秒级） | 找不到反例 ≠ 安全 | M5（`pgd_order: before`） |
| **CROWN** | 不完整验证（边界传播） | ✅（不完整） | ❌ | 极快（~0.2s/样本） | 边界偏松，ε 大时大量 unknown | M6（`bound_prop_method: crown`） |
| **α-CROWN** | 不完整验证（可优化边界传播） | ✅（更紧） | ❌ | 快（~1s/样本） | 比 CROWN 紧但慢，仍不分支 | M6（`bound_prop_method: alpha-crown`） |
| **β-CROWN + BaB (babsr)** | 完整验证（分支定界） | ✅（完备） | ✅（BaB 中发现） | 慢 | 基础分支策略，timeout 多 | M2/M3/M4 baseline |
| **β-CROWN + BaB (kfsb_c5)** | 完整验证（优化分支策略） | ✅（完备） | ✅（BaB 中发现） | 中 | 当前项目最优完整验证策略 | M3/M4 kfsb_candidates5 |
| **PGD + BaB (kfsb_c5)** | 攻击预筛 + 完整验证 | ✅（完备） | ✅（PGD 预筛） | 中 | ε 大时 timeout 仍高但大幅降低 | M5（`pgd_order: before` + kfsb） |

### 各方法的验证流程位置

```
输入样本 (x, ε)
   │
   ├─ [可选] PGD 攻击 ──────────→ 找到反例? → unsafe-pgd (结束)
   │                                     │ 未找到
   │                                     ▼
   ├─ CROWN / α-CROWN 不完整验证 ─→ 边界证明 safe? → safe-incomplete (结束)
   │                                     │ 无法判断 (unknown)
   │                                     ▼
   └─ β-CROWN + BaB 完整验证 ────→ 分支定界
                                      ├→ safe (结束)
                                      ├→ unsafe-bab (结束)
                                      └→ unknown/timeout (超时)
```

---

## 2. 不同 epsilon 下的结果总对比

**统一实验条件**: MNIST 0-100 样本，模型 `saved_models/mnist_fcnn.onnx`，L∞ 扰动

> **公平性说明**: M4 的 ε=0.03（kfsb 分片 t/o=15s）和 M5 的 ε=0.03（分片 t/o=12s）及 ε=0.05（M4 分片 t/o=15s，M5 分片 t/o=12s）的 timeout 预算不完全一致，横向对比主要用于**工程趋势分析**。ε=0.03 已补跑 M5-control（t/o=30s 公平对照），结论以对照为准。ε=0.01 和 ε=0.02 的 M4/M5/M6 均使用 t/o=30s 预算，可直接公平对比。

### 2.1 epsilon = 0.01

| 方法 | VRA (%) | safe | unsafe/pgd_unsafe | unknown/timeout | mean_time (s) | 说明 |
|---|---|---|---|---|---|---|
| **CROWN** (M6) | 98.0 | 98 | 0 | 2 | **0.20** | 速度最快，2 个样本边界不够紧 |
| **α-CROWN** (M6) | 98.0 | 98 | 0 | 2 | 0.26 | 与 CROWN 相同（同一批 2 个难证样本） |
| **BaB-kfsb** (M4) | **100.0** | 100 | 0 | 0 | 0.31 | 完备，CROWN 漏掉的 2 个被 BaB 证明 |
| **PGD+BaB** (M5) | **100.0** | 100 | 0 | 0 | 1.80 | PGD 未找到反例（ε 太小），全 safe |

**结论**: ε=0.01 时所有方法均能证明 ≥98% 的样本，差异很小。CROWN 速度最快。

### 2.2 epsilon = 0.02

| 方法 | VRA (%) | safe | unsafe/pgd_unsafe | unknown/timeout | mean_time (s) | 说明 |
|---|---|---|---|---|---|---|
| **CROWN** (M6) | 82.0 | 82 | 0 | 18 | **0.21** | 18 个样本无法不分支证明 |
| **α-CROWN** (M6) | 83.0 | 83 | 0 | 17 | 0.72 | α 优化多证明 1 个 |
| **BaB-kfsb** (M4) | **92.0** | 92 | 0 | 8 | 3.27 | BaB 分支将 unknown 从 18→8 |
| **PGD+BaB** (M5) | **92.0** | 92 | 5 | **3** | 2.83 | PGD 发现 5 个反例，timeout 降至 3 |

**结论**: ε=0.02 时方法差异开始显现。CROWN unknown=18，BaB 降至 8，PGD 进一步降至 3。PGD 首次找到反例（5 个）。

### 2.3 epsilon = 0.03

| 方法 | VRA (%) | safe | unsafe/pgd_unsafe | unknown/timeout | mean_time (s) | 说明 |
|---|---|---|---|---|---|---|
| **CROWN** (M6) | 41.0 | 41 | 0 | 59 | **0.26** | 不分支，59% 无法证明 |
| **α-CROWN** (M6) | 46.0 | 46 | 0 | 54 | 1.58 | α 优化多证明 5% |
| **BaB-kfsb** (M4) | 68.0 | 68 | 0 | 32 | 6.66 | BaB 将 unknown 从 54→32 |
| **PGD+BaB-降压** (M5) | 62.0 | 62 | 17 | 21 | 4.59 | t/o=12s，PGD 发现 17 个反例 |
| **PGD+BaB-公平** (M5-control) | **73.0** | 73 | 17 | **10** | 6.45 | t/o=30s 公平对照，VRA 最优 |

**结论**: ε=0.03 是方法分化最显著的 ε 值。α-CROWN 比 CROWN 多证明 5%（精度/速度 trade-off 最典型）。PGD+BaB（公平 t/o=30s）VRA 73% 为所有方法最高。PGD 发现 17 个反例，所有 falsified 均由 PGD 发现。

### 2.4 epsilon = 0.05

| 方法 | VRA (%) | safe | unsafe/pgd_unsafe | unknown/timeout | mean_time (s) | 说明 |
|---|---|---|---|---|---|---|
| **CROWN** (M6) | 4.0 | 4 | 0 | 96 | **0.23** | 96% unknown，不分支的极限 |
| **α-CROWN** (M6) | 5.0 | 5 | 0 | 95 | 2.78 | 边际提升仅 1% |
| **BaB-kfsb** (M4) | 11.0 | 11 | 0 | 89 | 11.38 | BaB 大量 timeout |
| **PGD+BaB** (M5) | 11.0 | 11 | **58** | **31** | **4.44** | PGD 发现 58 个反例！timeout 降幅 65.2% |

**结论**: ε=0.05 时任务极端困难，所有方法 VRA ≤11%。CROWN 仅需 0.23s 但只证明 4%。PGD 发现 58% 的反例，使 timeout 从 89→31（降幅 65.2%）。**此时 PGD 的工程价值大于 BaB 的策略差异**——PGD 以秒级代价快速判定了一半以上的样本。

---

## 3. 总体趋势分析

### 3.1 ε 增大时各方法 VRA 均下降

```
ε=0.01:  CROWN 98% | α-CROWN 98% | BaB 100% | PGD+BaB 100%
ε=0.02:  CROWN 82% | α-CROWN 83% | BaB 92%  | PGD+BaB 92%
ε=0.03:  CROWN 41% | α-CROWN 46% | BaB 68%  | PGD+BaB 73% (fair)
ε=0.05:  CROWN 4%  | α-CROWN 5%  | BaB 11%  | PGD+BaB 11%
```

趋势单调：ε 每增大一个级别，各方法 VRA 均显著下降。ε=0.03 是"中等难度"与"极难"的分水岭。

### 3.2 CROWN 速度最快但 unknown 最多

CROWN 的 mean_time 几乎不随 ε 增长（始终 ~0.20~0.26s），因为边界传播的计算量仅取决于网络结构（784→256→128→10），与 ε 大小无关。但 unknown 数从 2（ε=0.01）急剧增至 96（ε=0.05），说明**纯边界传播在 ε 大时空有速度却无结论**。

### 3.3 α-CROWN 比 CROWN 更紧但耗时增加

α-CROWN 通过优化 α 参数收紧边界，在 ε=0.03 时效果最好（+5% VRA），但耗时增长 6~12 倍。在低 ε（0.01）和高 ε（0.05）边际收益仅 0~1%。α-CROWN 的 α 优化是典型的**精度/速度 trade-off**——在中等难度任务上最有价值。

### 3.4 BaB 证明能力更强但高 ε 下 timeout 多

BaB 通过分支定界将 CROWN unknown 的样本进一步解析。ε=0.02 时 BaB 将 unknown 从 18→8；ε=0.03 时从 54→32。但 ε=0.05 时 BaB timeout 高达 89/100，说明**在高扰动下即使是完备的分支定界也接近计算能力边界**。

### 3.5 PGD+BaB 在高 ε 下能显著降低 timeout 和 mean_time

PGD 预筛选在 ε=0.05 时效果最显著：
- timeout: 89→31（**-65.2%**）
- mean_time: 11.38s→4.44s（**-61.0%**）

PGD 以秒级代价提前判定反例，避免了 BaB 在这些样本上的无效搜索。ε 越大，PGD 的工程价值越突出。

### 3.6 kfsb_candidates5 是本项目主要分支策略改进点

M3 消融实验确认 `kfsb + candidates=5` 为当前最优完整验证配置（VRA +2.0% vs baseline，timeout -2）。M4 证实该优势在 ε=0.01~0.03 区间持续成立。M5 证实该配置与 PGD 预筛选兼容良好。

---

## 4. 公平性声明

下表中标注了每组实验的 timeout 预算，**相同预算的行可直接公平对比**：

| ε | 方法 | timeout 预算 | 运行方式 | 公平对比状态 |
|---:|---|---|---|---|
| 0.01 | M4 BaB | 30s | 直接 | ✅ 与 M5/M6 同预算 |
| 0.01 | M5 PGD+BaB | 30s | 直接 | ✅ 与 M4/M6 同预算 |
| 0.01 | M6 CROWN/α-CROWN | 30s | 直接 | ✅ 与 M4/M5 同预算 |
| 0.02 | 全部 | 30s | 直接 | ✅ 三方同预算 |
| 0.03 | M4 BaB kfsb | **15s** | 分片 | ⚠️ 与 M6 (30s) 不完全一致 |
| 0.03 | M5 PGD+BaB | **12s** | 分片 | ⚠️ 与 M6 (30s) 不一致；已补 M5-control (30s) |
| 0.03 | **M5-control** | **30s** | 直接 | ✅ 公平对照基准 |
| 0.03 | M6 CROWN/α-CROWN | 30s | 直接 | ✅ 与 M5-control 同预算 |
| 0.05 | M4 BaB kfsb | **15s** | 分片 | ⚠️ 与 M6 (30s) 不一致 |
| 0.05 | M5 PGD+BaB | **12s** | 分片 | ⚠️ 与 M6 (30s) 不一致 |
| 0.05 | M6 CROWN/α-CROWN | 30s | 直接 | ⚠️ 不完整验证不分支，与 BaB 方法本质不同 |

**使用建议**:
- ε=0.01、0.02：三方直接对比，结论可靠。
- ε=0.03：使用 M5-control (t/o=30s) 与 M6 (t/o=30s) 对比；M4 (t/o=15s) 和 M5 (t/o=12s) 标注为"工程降压口径"。
- ε=0.05：所有 BaB 方法均采用降压/分片，差异主要在工程可执行性。M6 (t/o=30s) 因不分支无法与 BaB 方法直接等价比。

---

## 5. 可写入最终课程报告的 5 条结论

**结论 1: kfsb_candidates5 是当前模型和数据集上最优的完整验证配置。**
M3 消融实验中 VRA=93.0%（vs baseline 91.0%），timeout=7（vs 9）。M4 确认该优势在 ε=0.01~0.03 区间持续成立。改进来自将默认的 babsr 分支策略替换为 kfsb 并将候选数从 10 调至 5。
——证据: `m3_branching_ablation.csv`、`m4_epsilon_grid.csv`

**结论 2: PGD-before 预筛选在高 ε 下能大幅降低 timeout 和 mean_time，预筛选 ε 越大效果越显著。**
ε=0.05 时 timeout 从 89 降至 31（-65.2%），mean_time 从 11.38s 降至 4.44s（-61.0%）。PGD 以秒级代价提前判定反例，避免了 BaB 在这些样本上的无效搜索。但 PGD 找不到反例不代表安全——ε=0.02 时 PGD 仅找到 5 个反例，剩余 92 个 safe 仍由 BaB 证明。
——证据: `m5_pgd_compare.csv` vs `m4_epsilon_grid.csv` kfsb 行

**结论 3: CROWN 不完整验证速度极快（~0.2s/样本）且与 ε 无关，但 VRA 随 ε 急剧下降。**
CROWN mean_time 始终 ~0.20~0.26s（ε 从 0.01 到 0.05 几乎不变），但 VRA 从 98% 降至 4%。CROWN 在低 ε（≤0.01）时是高效的完整替代方案；在高 ε 时速度快但无实质结论。
——证据: `m6_incomplete_compare.csv` crown 行

**结论 4: α-CROWN 在中等 ε（0.03）时相对 CROWN 的提升最大，是典型的精度/速度 trade-off。**
ε=0.03 时 α-CROWN VRA 比 CROWN 高 5%（41%→46%），以 6.1 倍耗时换取。在低 ε（0.01）和高 ε（0.05）边际收益仅 0~1%。α 优化在"临界难度"任务上最有价值。
——证据: `m6_incomplete_compare.csv` crown vs alphacrown 同行对比

**结论 5: 本项目形成了从"极快但弱"到"较慢但强"的完整验证策略梯度，支持按场景择优。**
```
低 ε (0.01):      CROWN (0.20s, 98% VRA) 即可满足
中低 ε (0.02):    BaB/PGD+BaB (2.8s, 92% VRA) 性价比最优
中等 ε (0.03):    PGD+BaB (6.5s, 73% VRA) 公平最优
高 ε (0.05):      所有方法趋于超时/unknown 主导，PGD 预筛工程价值最大
```
——证据: 本报告 §2 全部数据表

---

## 6. 证据索引

| 数据 | 路径 |
|---|---|
| M4 BaB 完整结果 | `项目书/results/m4/m4_epsilon_grid.csv` |
| M5 PGD+BaB 结果 | `项目书/results/m5_pgd/m5_pgd_compare.csv` |
| M5-control 公平对照 | `项目书/results/m5_pgd_control/m5_pgd_control.csv` |
| M6 CROWN/α-CROWN 结果 | `项目书/results/m6_incomplete/m6_incomplete_compare.csv` |
| M3 分支消融 | `项目书/results/m3/m3_branching_ablation.csv` |
| M2/M3/M4 最终结论 | `项目书/results/M2_M3_M4_最终结论表_2026-05-04.md` |
| M5 详细报告 | `项目书/results/m5_pgd/M5_PGD攻击评估结果报告.md` |
| M6 详细报告 | `项目书/results/m6_incomplete/M6_不完整验证结果报告.md` |
| **本文件** | `项目书/results/verification_strategy_overall_comparison.md` |
