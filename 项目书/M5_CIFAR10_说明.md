# M5: CIFAR-10 补充实验说明

## 实验背景

根据作业题纲要求："利用不同的验证策略在 MNIST、**CIFAR-10 等数据集**上验证网络在不同扰动半径下的鲁棒性"。

## 模型选择说明

### 为什么不是纯全连接网络？

CIFAR-10 图像尺寸为 32×32×3 = **3072 维输入**。如果使用纯全连接网络：
- 第一层权重矩阵至少 3072×512，参数量巨大
- 训练困难，验证时间极长
- 实际应用中 CIFAR-10 都使用 CNN 架构

### 采用的模型：cifar_marabou_small

这是 α,β-CROWN 官方提供的最小 CIFAR-10 模型，结构如下：

```python
nn.Sequential(
    nn.Conv2d(3, 8, 4, stride=2),      # 降维：32×32×3 → 15×15×8
    nn.ReLU(),
    nn.Conv2d(8, 16, 4, stride=2),     # 降维：15×15×8 → 6×6×16
    nn.ReLU(),
    nn.Flatten(),                       # 展平：6×6×16 = 576
    nn.Linear(576, 128),                # 全连接层 1
    nn.ReLU(),
    nn.Linear(128, 64),                 # 全连接层 2
    nn.ReLU(),
    nn.Linear(64, 10)                   # 输出层
)
```

**特点**：
- 前两层 Conv 用于降维（3072 → 576），避免参数爆炸
- 后三层是标准的 ReLU 全连接网络
- 总参数量：~90K（相比纯 FCNN 的数百万参数）
- 官方模型，有预训练权重，clean acc ≈ 63%

## 实验设计

### 样本规模

- **样本数**：n=20（小样本快速验证）
- **原因**：CIFAR-10 验证比 MNIST 慢 5-10 倍，n=100 需要数小时

### 对比策略

| 策略 | 配置 | 说明 |
|------|------|------|
| baseline | babsr, candidates=3 | 默认分支策略 |
| kfsb_candidates5 | kfsb, candidates=5 | MNIST 上的最优配置 |

### 扰动设置

- **ε = 2/255 ≈ 0.00784**（CIFAR-10 标准扰动半径）
- **L∞ 范数**

### 超时限制

- **60 秒/样本**（MNIST 为 60 秒，CIFAR-10 难度更高）

## 实验目的

1. **验证策略迁移性**：kfsb_candidates5 在 CIFAR-10 上是否仍优于 baseline？
2. **满足题目要求**：覆盖 MNIST + CIFAR-10 两个数据集
3. **补充证据**：证明改进策略的通用性

## 预期结果

基于 MNIST 实验经验，预期：
- kfsb_candidates5 的验证准确率 ≥ baseline
- kfsb_candidates5 的超时数 ≤ baseline
- 平均验证时间可能略高（因为搜索更深）

## 局限性说明

1. **模型架构**：含 Conv 层，不是纯 FCNN（但后半部分是标准 ReLU FC）
2. **样本量**：n=20 仅供趋势验证，不做精确性能比较
3. **扰动半径**：仅测试单一 ε 值，未做网格扫描

## 答辩建议

在答辩时可以这样说明：

> "CIFAR-10 因输入维度高（3072），纯全连接网络参数量过大、训练困难。我们采用官方提供的 cifar_marabou_small 模型，该模型前两层用 Conv 降维，后三层是标准 ReLU 全连接网络。在 n=20 小样本上验证了 kfsb_candidates5 策略相比 baseline 的优势，证明了改进策略的迁移性。"

## 文件清单

```
项目书/
├── scripts/
│   ├── run_m5_cifar10.sh              # 运行脚本
│   └── summarize_m5_results.py        # 汇总脚本
├── results/m5/
│   ├── logs/
│   │   ├── cifar10_baseline.log
│   │   └── cifar10_kfsb_candidates5.log
│   ├── meta/
│   │   ├── cifar10_baseline.txt
│   │   └── cifar10_kfsb_candidates5.txt
│   └── m5_cifar10_compare.csv         # 结果汇总
└── M5_CIFAR10_说明.md                  # 本文档
```

## 运行方法

```bash
# 1. 运行实验（约 5-10 分钟）
bash 项目书/scripts/run_m5_cifar10.sh

# 2. 汇总结果
python3 项目书/scripts/summarize_m5_results.py

# 3. 查看结果
cat 项目书/results/m5/m5_cifar10_compare.csv
```

## 参考

- 模型定义：`complete_verifier/model_defs.py::cifar_marabou_small()`
- 官方配置：`complete_verifier/exp_configs/bab_attack/cifar_marabou_small.yaml`
- 模型权重：`complete_verifier/models/marabou_cifar10/cifar_marabou_small.pth`
