# Marabou 环境检查报告

**日期**: 2026-05-07  
**里程碑**: M8 — Marabou 最小可行接入实验  
**阶段**: 环境检查  

---

## 1. Python 版本

```
Python 3.14.0 (Windows x86_64)
路径: C:\Python314\python.exe
```

⚠️ **注意**: 当前环境使用的是 Windows 原生 Python 3.14.0，而非 WSL Linux Python。Python 3.14 是 pre-release 版本，很多预编译 wheel 不支持此版本。

---

## 2. maraboupy 导入检查

**结果: ❌ 不可导入**

```
ModuleNotFoundError: No module named 'maraboupy'
```

---

## 3. pip 安装 maraboupy

**结果: ❌ 安装失败**

```
ERROR: Could not find a version that satisfies the requirement maraboupy (from versions: none)
ERROR: No matching distribution found for maraboupy
```

**失败原因**: `maraboupy` 未发布到 PyPI。Marabou 是一个 C++ 项目，Python 绑定 (`maraboupy`) 需要从源码编译或使用 GitHub Releases 中的预编译 wheel。

### 3.1 GitHub Releases 预编译 wheel 情况

| Release | macOS x86_64 | macOS arm64 | manylinux x86_64 | manylinux aarch64 | **Windows** |
|---------|:---:|:---:|:---:|:---:|:---:|
| v2.0.0 (2024-04-12) | ✅ cp310, cp311 | ❌ | ✅ cp310, cp311 | ❌ | **❌ 无** |
| v1.0.0 (2023-07-14) | ✅ multi | ✅ multi | ✅ multi | ✅ multi | **❌ 无** |

**结论**: Marabou 官方从未提供 Windows 预编译 wheel。

### 3.2 pip install from GitHub

尝试 `pip install git+https://github.com/NeuralNetworkVerification/Marabou.git` 失败：

```
head: write error: No space left on device
```

磁盘空间不足（临时文件所在分区），且即便克隆成功，也需要 CMake + C++17 编译器进行源码编译。

### 3.3 代理问题

系统配置了代理服务器 `127.0.0.1:7897`（Windows Internet Settings 注册表），但代理进程未运行，导致所有 Python HTTP 请求默认失败。通过设置 `NO_PROXY=*` 环境变量可绕过。

---

## 4. Marabou CLI 可用性

**结果: ❌ 不可用**

```
which Marabou → (not found)
Marabou --help → command not found
```

Marabou 命令行工具未安装。若通过源码编译，会生成 `Marabou` 可执行文件，但当前环境无 C++ 编译工具链。

---

## 5. ONNX 模型检查

**结果: ✅ 模型文件存在**

| 项目 | 详情 |
|------|------|
| 路径 | `saved_models/mnist_fcnn.onnx` |
| 大小 | 941,412 bytes (~919 KB) |
| IR 版本 | 6 |
| Opset 版本 | 11 |

### 模型结构

```
输入:  input   [1, 1, 28, 28]  float32
  ↓
Flatten → [1, 784]
  ↓
Gemm (fc1): 784 → 256
  ↓
Relu
  ↓
Gemm (fc2): 256 → 128
  ↓
Relu
  ↓
Gemm (fc3): 128 → 10
  ↓
输出:  output  [1, 10]  float32
```

**架构总结**: 3 层全连接 ReLU 网络（784→256→128→10），共 6 个 ONNX 节点。

### onnxruntime 推理验证

✅ 使用 `onnxruntime 1.25.1` 成功加载并执行推理，输入 [1,1,28,28] → 输出 [1,10]，正常。

---

## 6. 已安装的相关包

| 包 | 版本 | 用途 |
|----|------|------|
| onnx | 1.21.0 | ONNX 模型加载/解析 |
| onnxruntime | 1.25.1 | ONNX 模型推理 |
| auto_LiRPA | (git submodule) | α,β-CROWN 核心 |
| numpy | 2.4.3 | 数值计算 |
| protobuf | 7.34.1 | ONNX 序列化 |

---

## 7. 是否可以进入下一步？

### 当前状态: ⚠️ 受阻 — 但存在替代路径

**核心问题**: `maraboupy` 无法在当前环境（Windows Python 3.14）安装。

**原因**:
1. `maraboupy` 不在 PyPI 上（非 pip 可安装包）
2. GitHub Releases 没有 Windows wheel
3. Python 3.14 过于新（even Linux wheels only support up to cp311）
4. 系统磁盘空间不足，无法承担源码编译

### 可选替代方案

| 方案 | 可行性 | 说明 |
|------|:---:|------|
| **A. WSL Linux Python + manylinux wheel** | ⭐⭐⭐ | 在 WSL Ubuntu 内安装 Python 3.10/3.11，直接 `pip install maraboupy-2.0.0-cp311-cp311-manylinux_2_17_x86_64.whl`。无需编译。 |
| **B. Docker** | ⭐⭐⭐ | `docker pull neuralnetworkverification/marabou`（如有官方镜像）或自行构建 Dockerfile |
| **C. 纯 ONNX 接口调用 Marabou CLI** | ⭐⭐ | 不使用 `maraboupy`，而是通过子进程调用编译好的 `Marabou` 可执行文件，传递 VNNLIB/ONNX |
| **D. 自行编译** | ⭐ | 需要 CMake ≥3.15、GCC ≥9 / Clang ≥11、Boost 库。当前环境磁盘不足，且需在 WSL 内操作 |

### 推荐下一步

**方案 A**: 在 WSL Ubuntu 内安装 Python 3.11，直接用 manylinux wheel 安装 maraboupy 2.0.0。这是最简路径，不涉及编译，且 maraboupy 的 Python API 功能完整（模型加载、属性编码、求解调用）。

```bash
# 在 WSL Ubuntu 内执行:
sudo apt install python3.11 python3.11-venv
python3.11 -m venv marabou_env
source marabou_env/bin/activate
pip install https://github.com/NeuralNetworkVerification/Marabou/releases/download/v2.0.0/maraboupy-2.0.0-cp311-cp311-manylinux_2_17_x86_64.whl
```

---

## 8. 环境检查结论

| 检查项 | 状态 |
|--------|:---:|
| Python 版本 | ✅ 3.14.0 (但太新，推荐 3.11) |
| maraboupy 可导入 | ❌ 未安装 |
| pip install maraboupy (PyPI) | ❌ 包不在 PyPI |
| pip install maraboupy (GitHub wheel) | ❌ 无 Windows wheel |
| Marabou CLI | ❌ 未安装 |
| ONNX 模型存在 | ✅ saved_models/mnist_fcnn.onnx |
| ONNX 模型可推理 | ✅ onnxruntime 验证通过 |
| 模型兼容 Marabou | ✅ 标准 opset 11，Flatten/Gemm/Relu 均在 Marabou 支持列表 |
| **可进入下一步** | ⚠️ 需先完成方案 A（WSL Linux Python 环境） |

**总体评估**: 核心阻塞项是 Windows 平台限制。Marabou 是一个 Linux/macOS 优先的工具，最务实的路径是在 WSL Linux 环境中安装 manylinux wheel。ONNX 模型本身格式标准，与 Marabou 完全兼容。
