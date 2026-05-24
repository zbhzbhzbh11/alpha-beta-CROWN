# M8 Marabou 5 样本工具对比报告

**日期**: 2026-05-07  
**里程碑**: M8-plus — 5 样本小规模工具对照  
**状态**: ✅ 完成  

---

## 1. 实验定位

> ⚠️ **这是最小工具对比，不是大规模 benchmark。**

本实验将 M8 单样本 feasibility check 扩展到 5 个 MNIST 样本，目的是：

| 目的 | 说明 |
|------|------|
| 补齐课程题目中的 Marabou 工具参照 | 开题报告承诺了 Marabou 交叉对比，单样本不够充分 |
| 验证跨工具 pipeline 的可复用性 | 确认批处理脚本在多样本上稳定运行 |
| 为中期报告提供有统计分量的数据 | 5 样本的一致率、平均耗时比有参考价值 |
| 探索是否出现工具分歧 | CROWN=unknown 而 Marabou 能判定 safe/unsafe 的样本更有研究意义 |

**大规模实验仍以 alpha-beta-CROWN 为主平台**。Marabou 在本项目中扮演"外部独立验证器"角色，不替代 α,β-CROWN 的主体地位。

---

## 2. 实验设置

| 参数 | 值 |
|------|-----|
| 样本 | MNIST test samples 0, 1, 2, 3, 4 |
| 模型 | `saved_models/mnist_fcnn.onnx` (3-layer FCNN) |
| 扰动范数 | L∞ |
| Epsilon | 0.01 |
| Marabou timeout | 30s/target |
| α,β-CROWN 方法 | CROWN + α-CROWN (20 iters) |
| Marabou 环境 | WSL Ubuntu 24.04, micromamba marabou-env, Python 3.11 |
| α,β-CROWN 环境 | 同上（共用一个 marabou-env，加载 auto_LiRPA submodule） |

---

## 3. 5 样本结果表

| Sample | True | Pred | Marabou | Marabou Time | α,β-CROWN | α,β-CROWN Time | 一致 |
|--------|------|------|:---:|------|:---:|------|:---:|
| 0 | 7 | 7 | **safe** | 4.47s | **safe** | 0.67s | ✅ |
| 1 | 2 | 2 | **safe** | 4.05s | **safe** | 0.45s | ✅ |
| 2 | 1 | 1 | **safe** | 5.47s | **safe** | 0.46s | ✅ |
| 3 | 0 | 0 | **safe** | 4.13s | **safe** | 0.51s | ✅ |
| 4 | 4 | 4 | **safe** | 4.17s | **safe** | 0.41s | ✅ |

### 统计汇总

| 指标 | Marabou | α,β-CROWN |
|------|---------|------------|
| 结果分布 | safe × 5 | safe × 5 |
| 平均耗时 | **4.46s** | **0.50s** |
| 最小耗时 | 4.05s | 0.41s |
| 最大耗时 | 5.47s | 0.67s |
| 耗时标准差 | 0.58s | 0.10s |
| 一致率 | — | **5/5 (100%)** |
| Timeout | 0 | 0 |
| Error | 0 | 0 |

---

## 4. 分析

### 4.1 一致率：5/5 (100%)

在 ε=0.01 的条件下，所有 5 个样本均被两个工具一致判定为 **safe**。这是预期内的结果——ε=0.01 是极小的扰动半径，α,β-CROWN 在 M4 实验中已验证 ε=0.01 下所有策略均为 100% VRA。Marabou 的 complete SMT 验证进一步确认了这些样本确实不存在对抗扰动。

### 4.2 耗时对比

```
α,β-CROWN:  0.50s avg  ████
Marabou:     4.46s avg  ████████████████████████████████████████

速度比: α,β-CROWN 快约 8.9 倍
```

Marabou 较慢的原因：
- 逐个 target 加载网络并编码 SMT 查询（每个 sample 需 9 次加载+求解）
- Complete SMT 搜索需要探索 ReLU 的分段线性分支空间
- 相比之下，α,β-CROWN 一次性计算所有输出边界，无需逐 target 迭代

### 4.3 未出现 timeout 或分歧

5 个样本均未触发 timeout，且两个工具结果一致。这进一步确认了在 ε=0.01 的简单条件下：
- α,β-CROWN 的 incomplete bounds 已足够紧（足以证明安全性）
- Marabou 的 complete search 未发现 CROWN 遗漏的对抗样本
- 两个工具相互验证了正确性

**局限性**：在 ε=0.01 下未出现 CROWN=unknown 而 Marabou 能给出明确结果的样本。这种分歧样本在 ε≥0.02 时才更可能出现，尚待后续实验。

---

## 5. 样本多样性覆盖

| 维度 | 覆盖情况 |
|------|----------|
| 真实标签 | 7, 2, 1, 0, 4（5 种不同类别） |
| 预测正确 | 5/5（全部正确） |
| 模型置信度 | 最高 sample 3 (logit=12.08), 最低 sample 1 (logit=12.26 但 gap 较大) |
| Marabou 最慢样本 | Sample 2 (5.47s, true=1, 第二高 logit 为 class 0: −5.88，gap 大) |

---

## 6. 可写入中期报告的结论

### 结论 1：跨工具一致性在 5 样本上得到验证（100% 一致）

> 在 MNIST 5 个测试样本（labels: 0,1,2,4,7）、ε=0.01（L∞）下，Marabou（complete SMT solver）与 α,β-CROWN（incomplete bound propagation）给出完全一致的验证结果：所有样本均为 safe。两套独立算法路径的一致性相互验证了工具的正确性。该结果可作为中期报告中"外部工具验证"部分的实证支撑。

### 结论 2：α,β-CROWN 在 ε=0.01 下达到 complete 级精度

> 在 5 个样本上，α,β-CROWN 的 incomplete bounds 全部成功证明了安全性（未出现 unknown），达到与 Marabou complete SMT 等同的精度，但速度快约 9 倍（0.50s vs 4.46s avg）。这表明在低 epsilon 条件下，α,β-CROWN 的 CROWN + α-CROWN bound tightening 已足够紧致，无需 complete search 即可获得确定性结论。

### 结论 3：标准化跨工具对比 pipeline 已建立并可复用

> M8 批处理脚本（`m8_marabou_verify_mnist_batch.py`）支持参数化配置样本范围、epsilon、timeout，自动输出 CSV/JSON 结果，覆盖 Marabou 和 α,β-CROWN 双引擎。该 pipeline 可直接复用于更大 epsilon、更多样本、甚至其他模型（需满足 ONNX + ReLU-only 约束），为本项目的工具对比维度提供了可持续的基础设施。

---

## 7. 当前结果不能说明什么

1. **不能推广到 ε ≥ 0.02**：ε=0.01 是最简单条件，不能代表中等或大 epsilon 下两个工具的关系
2. **不能推广到难样本**：5 个样本全部预测正确，未包含预测错误或歧义样本
3. **不构成统计显著 benchmark**：5 样本是 feasibility check，不是性能评估
4. **不能在 CIFAR-10 或其他模型上类推**：当前模型是 MNIST FCNN（784→256→128→10）

---

## 8. 下一步建议

| 优先级 | 建议 | 预期发现 |
|--------|------|----------|
| ⭐⭐⭐ | ε=0.02 对照（5 样本） | 可能出现 CROWN≠Marabou 的分歧（CROWN=unknown, Marabou=safe/unsafe） |
| ⭐⭐ | ε=0.03 对照（5 样本） | 分歧率可能升高，Marabou timeout 可能出现 |
| ⭐ | ε=0.05 对照（仅探索性） | timeout 概率大，仅用于趋势观察 |
| ⭐⭐ | 增加故意选错的样本 | 验证两工具对 unsafe 样本的一致判断 |

**不推荐**立即扩展到 100 样本，除非需要统计显著的结果用于正式发表。中期报告 5–10 样本已足够形成"跨工具一致性"的实证章节。

---

## 9. 文件清单

| 文件 | 内容 |
|------|------|
| `项目书/results/m8_marabou/m8_marabou_5samples_eps0.01.csv` | 5 样本结果 CSV |
| `项目书/results/m8_marabou/m8_marabou_5samples_eps0.01.json` | 5 样本结果 JSON |
| `项目书/scripts/m8_marabou_verify_mnist_batch.py` | 批处理验证脚本 |
| `项目书/results/m8_marabou/M8_Marabou_5样本工具对比报告.md` | 本文 |
