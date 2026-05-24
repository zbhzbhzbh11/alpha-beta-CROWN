# WSL 环境检查报告

**日期**: 2026-05-07  
**里程碑**: M8 — Marabou 最小可行接入实验  
**阶段**: 阶段 1 — WSL 环境确认  

---

## 1. 当前 Shell 环境

| 项目 | 详情 |
|------|------|
| Shell 类型 | MSYS2 / MINGW64 (bash on Windows) |
| 内核 | MINGW64_NT-10.0-26200 x86_64 Msys |
| 是否真实 Linux | ❌ 否 — 需要通过 `wsl` 命令访问 Linux 环境 |

---

## 2. WSL 状态

| 项目 | 详情 |
|------|------|
| WSL 版本 | WSL2 |
| 默认发行版 | Ubuntu-New (Running, *) |
| 其他发行版 | Ubuntu (Stopped) |
| Linux 内核 | 6.6.87.2-microsoft-standard-WSL2 |
| 发行版版本 | Ubuntu 24.04.1 LTS (Noble Numbat) |
| WSL 内网络 | ✅ 正常（可访问 pypi.org） |

```
PRETTY_NAME="Ubuntu 24.04.1 LTS"
VERSION_ID="24.04"
```

---

## 3. WSL 内 Python 环境

| 项目 | 详情 |
|------|------|
| 默认 Python | Python 3.12.3 |
| Python 3.11 | ❌ 未安装 |
| Python 3.10 | ❌ 未安装 |
| pip3 | ✅ /usr/bin/pip3 |
| conda | ❌ 未安装（但存在 ~/.conda 目录残留） |
| apt | ✅ /usr/bin/apt |

---

## 4. 仓库与 ONNX 模型访问

| 项目 | 详情 |
|------|------|
| 仓库路径 (WSL 内) | /home/han/alpha-beta-CROWN |
| ONNX 模型路径 | /home/han/alpha-beta-CROWN/saved_models/mnist_fcnn.onnx |
| 文件大小 | 941,412 bytes |
| WSL 可访问 | ✅ 正常 |

---

## 5. MSYS2 ↔ WSL 路径转换问题

### 问题
MSYS2 bash 会自动将 Unix 风格路径（`/home/...`）转换为 Windows 路径（`E:/codetools/GIT/Git/home/...`），导致 `wsl` 命令收到错误的路径参数。

### 解决方案
在所有 `wsl` 命令前添加 `MSYS_NO_PATHCONV=1` 禁用路径转换。

```bash
MSYS_NO_PATHCONV=1 wsl bash -c "<command>"
```

### 终端编码问题
WSL 输出中的警告信息有乱码，但不影响实际命令输出。可通过重定向 stderr 或设置 `LANG=C` 绕过。

---

## 6. maraboupy 依赖分析

| 需求 | 当前状态 |
|------|----------|
| Linux 环境 | ✅ WSL2 Ubuntu 24.04 |
| Python 3.10/3.11 | ❌ 需安装 Python 3.11 |
| manylinux wheel | ✅ maraboupy-2.0.0-cp311-cp311-manylinux_2_17_x86_64.whl 可用 |
| pip 网络 | ✅ WSL 内可访问 pypi.org |

---

## 7. 下一步操作

需要安装 Python 3.11：
```bash
sudo apt update && sudo apt install python3.11 python3.11-venv python3.11-dev -y
```

然后创建独立虚拟环境并安装 maraboupy wheel。

---

## 8. 环境检查结论

| 检查项 | 状态 |
|--------|:---:|
| WSL 可用 | ✅ Ubuntu 24.04 LTS, WSL2 |
| WSL 网络正常 | ✅ |
| 仓库可访问 | ✅ /home/han/alpha-beta-CROWN |
| ONNX 模型可访问 | ✅ saved_models/mnist_fcnn.onnx |
| Python 3.11 可用 | ❌ 需安装 |
| 可继续阶段 2 | ✅ 安装 Python 3.11 后即可 |
