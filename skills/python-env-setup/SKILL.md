---
name: python-env-setup
description: 检测用户机器是否已有可用 Python 环境；如缺失，则在获得用户明确许可后在 macOS 或 Windows 上安装，并自动处理 PATH 配置。
---

# Python 环境检测与安装

用于检测当前机器是否存在可用的 Python 运行环境。若不存在，则指导并执行安装流程；若已安装但目标命令不在 PATH 中，则修复 PATH。

## 核心目标

**检测阶段不要求必须是 Python 3.13。**

只要机器上已经有任意可用 Python，即可视为环境已存在，例如：

- Python 3.x
- Python 2.x（仅从“有 Python 可执行环境”角度算存在，但通常不推荐）

如果用户只是说“装个 Python，能运行代码就行”，那么：

- 检测到任意 Python 可用 → 直接复用
- 没有 Python → 再进入安装流程

> 安装阶段仍然可以优先补 `Python 3.13`，但检测阶段不再把 `3.13` 当作硬门槛。

## 平台范围

本技能只处理以下平台：

- macOS
- Windows

## Windows 安装总策略

Windows 上按下面优先级执行：

1. **先检测是否已存在任意可用 Python**
2. **若已安装但 PATH 不完整，则只修 PATH**
3. **若未安装，则优先尝试无 UI、当前用户安装**
4. **若 `winget` 不可用或失败，则主回退方案直接使用 embeddable zip**
5. **只有在用户明确同意时，才尝试管理员权限安装**

## Windows 推荐安装顺序

### 方案 A：`winget`

如果机器可用 `winget`：

```powershell
winget install -e --id Python.Python.3.13
```

### 方案 B：`embeddable zip` 主回退方案

如果没有 `winget`，或 `winget` 调用失败，主回退方案直接使用 **embeddable zip**。

### 方案 C：官方安装器（仅备用）

只有当用户明确更偏好标准安装器，或确实需要标准注册式安装时，才再考虑 Python 官方 `.exe` 安装器。

## 关于 pip

`pip` **不是本技能的默认成功条件**。

只有用户明确要安装依赖、运行 `pip install` 或准备完整开发环境时，才去处理 `pip`。

## 推荐调用流程

### 场景 1：只检查

```bash
python3 scripts/check_python_env.py --json
```

### 场景 2：仅修复 PATH

```bash
python3 scripts/check_python_env.py --repair-path --json
```

### 场景 3：用户确认后执行安装

```bash
python3 scripts/check_python_env.py --install --json
```

## 默认成功标准

满足以下任一即可：

- `python` 可调用
- `python3` 可调用
- `python3.13` 可调用
- 能定位到本机已有 Python，并在补 PATH 后正常调用

## 建议的后续动作

默认最小验证：

```bash
python --version
```

Windows 当前会话如果要立即生效，可刷新 PATH：

```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
python --version
```

## 注意事项

- 检测阶段不再要求必须是 `3.13`。
- 若后续用户明确要求特定版本，再单独判断版本是否满足。
- Windows 新开的终端会自动读取新的用户级 PATH。
