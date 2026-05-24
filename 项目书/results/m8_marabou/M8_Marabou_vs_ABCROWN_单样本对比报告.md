# M8 Marabou vs alpha-beta-CROWN 单样本对比报告

**日期**: 2026-05-07  
**里程碑**: M8 — Marabou 最小可行接入实验  
**阶段**: 阶段 5-6 — 单样本对照  

---

## 1. 实验设置

| 参数 | 值 |
|------|-----|
| 样本索引 | 0 |
| 真实标签 | 7 |
| 模型预测 | 7 (正确) |
| 扰动范数 | L∞ |
| Epsilon | 0.01 |
| 输入范围 | [0, 1] |

---

## 2. 单样本对比结果

| 工具 | 样本 | epsilon | 结果 | 时间 | 方法类型 |
| --- | --- | --- | --- | --- | --- |
| Marabou | 0 | 0.01 | **safe** | 4.269s | Complete SMT (逐 target) |
| alpha-beta-CROWN | 0 | 0.01 | **safe** | 0.495s | Incomplete (CROWN + α-CROWN) |

✅ **两个工具结果一致**：样本 0 在 ε=0.01 下是安全的。

---

## 3. 详细结果

### 3.1 Marabou 逐 target 求解详情

| Target | 退出状态 | 耗时 | f_target − f_true |
|--------|----------|------|-------------------|
| 2 | UNSAT | 1.050s | −9.355 |
| 3 | UNSAT | 0.457s | −10.449 |
| 9 | UNSAT | 0.379s | −13.472 |
| 8 | UNSAT | 0.362s | −13.949 |
| 0 | UNSAT | 0.409s | −14.319 |
| 5 | UNSAT | 0.806s | −14.857 |
| 1 | UNSAT | 0.383s | −15.550 |
| 4 | UNSAT | 0.217s | −18.977 |
| 6 | UNSAT | 0.206s | −28.022 |

- 总求解时间: **4.269s** (9 targets)
- 平均每 target: **0.474s**
- 最难的 target: class 2 (1.050s) — 与 true label 7 最接近

### 3.2 alpha-beta-CROWN 边界详情

| 类别 | 下界 (LB) | 上界 (UB) |
|------|-----------|-----------|
| 0 | −3.745 | −1.539 |
| 1 | −4.578 | −3.331 |
| 2 | 1.216 | 3.701 |
| 3 | 0.466 | 2.335 |
| 4 | −9.218 | −6.052 |
| 5 | −4.399 | −1.747 |
| 6 | −17.838 | −14.587 |
| **7** ★ | **9.708** | 12.844 |
| 8 | −3.117 | −1.145 |
| 9 | −3.220 | −0.653 |

安全性判定: ∀j ≠ 7, UB(j) − LB(7) < 0 → **SAFE**

---

## 4. 分析

### 4.1 结果一致性

两个独立工具（Marabou SMT + α,β-CROWN bound propagation）对同一样本、同一 epsilon 得出一致结论。这验证了两个工具的正确性——通过不同算法路径到达相同的验证结果。

### 4.2 时间对比

| 指标 | Marabou | α,β-CROWN |
|------|---------|-----------|
| 总时间 | 4.269s | **0.495s** |
| 方法 | Complete (逐 target SMT) | Incomplete (bound propagation) |
| 最慢 target | 1.050s (class 2) | — (一次性计算所有边界) |

α,β-CROWN 的 incomplete verification 速度快约 **8.6 倍**，但在该样本上两者精确度一致（都证明了 safety）。

### 4.3 方法学差异

| 维度 | Marabou | alpha-beta-CROWN |
|------|---------|-------------------|
| 算法类型 | Complete SMT solver | Incomplete bound propagation |
| 可靠性 | Sound & complete | Sound but incomplete |
| 输出 | SAT/UNSAT 明确判定 | 边界 (LB/UB) → 导出 SAFE/UNKNOWN |
| 可扩展性 | 每个 target 单独求解 | 一次性传播所有边界 |
| 可并行化 | 逐 target 天然并行 | 单次计算 |

---

## 5. 技术总结

### 已实现

| 项目 | 状态 |
|------|:---:|
| Marabou 环境搭建 (WSL, 独立 env) | ✅ |
| ONNX 模型解析 | ✅ |
| 单样本 SMT 编码与求解 | ✅ |
| alpha-beta-CROWN 边界传播 | ✅ |
| 两个工具结果一致 | ✅ |
| 文件清单完整 | ✅ |

### 经验教训

1. **exit code 检查必须精确匹配**: `"sat" in "unsat"` 导致误判，已修复为 `== "sat"`
2. **Marabou 的 UNSAT 证明可靠但较慢**: 9 个 target 总计 4.3s，每个约 0.5s
3. **α,β-CROWN 在 ε=0.01 下快速且精确**: 0.5s 完成所有边界计算

---

## 6. 能否写入中期报告

✅ **可以写入**。两个工具结果一致，验证了 M8 "Marabou 最小可行接入"的成功。可作为"跨工具验证一致性"的典型案例。

---

## 7. 是否建议扩展到 5 样本

✅ **建议**。单样本验证已证明 pipeline 可行，扩展到 5 样本可以：
1. 统计两个工具在更多样本上的一致性
2. 发现 CROWN incomplete 与 Marabou complete 出现分歧的样本（更有研究价值）
3. 为中期报告提供更丰富的数据

---

## 8. 文件清单

| 文件 | 内容 |
|------|------|
| `项目书/results/m8_marabou/Marabou环境检查报告.md` | 初始环境检查 |
| `项目书/results/m8_marabou/WSL环境检查报告.md` | WSL 环境确认 |
| `项目书/results/m8_marabou/Marabou_WSL安装报告.md` | WSL 安装过程 |
| `项目书/results/m8_marabou/logs/check_onnx_wsl.log` | ONNX 读取日志 |
| `项目书/results/m8_marabou/logs/one_sample_eps0.01_wsl.log` | 单样本验证日志 |
| `项目书/results/m8_marabou/m8_marabou_one_sample.json` | Marabou 结果 JSON |
| `项目书/results/m8_marabou/m8_abcrown_one_sample.json` | α,β-CROWN 结果 JSON |
| `项目书/scripts/m8_marabou_check_onnx.py` | ONNX 读取脚本 |
| `项目书/scripts/m8_marabou_verify_mnist_one.py` | Marabou 验证脚本 |
| `项目书/scripts/m8_abcrown_verify_one.py` | α,β-CROWN 验证脚本 |
| `项目书/results/m8_marabou/M8_Marabou_vs_ABCROWN_单样本对比报告.md` | 本文 |
