# Marabou WSL 安装报告

**日期**: 2026-05-07  
**里程碑**: M8 — 阶段 2  

---

## 1. 安装方式

使用 micromamba（miniforge 的轻量替代）在 WSL Ubuntu 24.04 LTS 内创建独立的 Python 3.11 环境。

| 项目 | 详情 |
|------|------|
| 包管理器 | micromamba 2.6.0 |
| 环境名称 | marabou-env |
| Python 版本 | 3.11.15 |
| 环境路径 | `/home/han/.micromamba/envs/marabou-env` |
| 与原环境隔离 | ✅ 完全独立，不影响 alpha-beta-CROWN 主环境 |

## 2. Marabou 安装详情

| 项目 | 详情 |
|------|------|
| 安装来源 | GitHub Release v2.0.0 |
| Wheel 文件 | `maraboupy-2.0.0-cp311-cp311-manylinux_2_17_x86_64.whl` |
| 安装方式 | `pip install` from local `.whl` |
| 编译 | ❌ 无编译（预编译 manylinux wheel） |
| 安装成功 | ✅ |
| 导入验证 | ✅ `from maraboupy import Marabou` OK |

## 3. 安装的依赖包

| 包 | 版本 | 用途 |
|----|------|------|
| numpy | 2.4.4 | 数值计算 |
| onnx | 1.21.0 | ONNX 模型加载 |
| onnxruntime | 1.25.1 | ONNX 推理及验证 |
| torch | 2.11.0+cpu | 深度学习框架 |
| torchvision | 0.26.0+cpu | MNIST 数据加载 |
| onnx2pytorch | 0.5.3 | ONNX → PyTorch 模型转换 |
| auto_LiRPA | 0.7.0 (submodule) | α,β-CROWN 核心算法 |

## 4. 网络访问说明

- GitHub 主站 (`github.com`) 被代理阻止
- GitHub API (`api.github.com`) 可访问
- micromamba 和 maraboupy wheel 均通过 GitHub API 下载
- PyPI (`pypi.org`) 在 WSL 内可直接访问

## 5. 重要路径记录

```
micromamba 二进制:    /home/han/micromamba
micromamba 根路径:    /home/han/.micromamba
marabou-env Python:   /home/han/.micromamba/envs/marabou-env/bin/python
maraboupy wheel:      /home/han/maraboupy-2.0.0-cp311-cp311-manylinux_2_17_x86_64.whl
ONNX 模型:            /home/han/alpha-beta-CROWN/saved_models/mnist_fcnn.onnx
```

## 6. 激活环境命令

```bash
# 在 WSL 内:
export MAMBA_ROOT_PREFIX=/home/han/.micromamba
/home/han/micromamba run -n marabou-env python <script.py>
```

或从 MSYS2:
```bash
MSYS_NO_PATHCONV=1 wsl bash -c '
export MAMBA_ROOT_PREFIX=/home/han/.micromamba
/home/han/micromamba run -n marabou-env python <script.py>
'
```

## 7. 结论

Marabou (maraboupy 2.0.0) 已在 WSL Ubuntu 24.04 内成功安装，环境完全隔离，可正常导入和运行。
