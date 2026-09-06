---
name: python-env-setup
description: 检测 Windows 机器上的 Python 解释器并给出安装或 PATH 修复建议；不会未经确认改动系统。
---

# Python 环境检查

用于确认目标机器是否有可调用的 Python。检测阶段不要求某个固定小版本；只要是受支持的 Python 3
即可继续，再由具体技能检查自己的最低版本和第三方包。

## 检测

```powershell
python scripts/check_python_env.py --json
```

脚本按 `python`、`py -3`、`python3` 顺序检查解释器，返回命令、绝对路径和版本。它只调用版本查询，
不安装软件、不修改 PATH、不读取用户配置。

## 安装边界

如果没有可用解释器，应先说明需要用户批准，并由用户使用组织批准的离线安装包或 Windows 软件管理
工具安装。安装包名称和静默参数见 `ENVIRONMENT-MCP-INVENTORY.md` 与 `dependencies.json`。

不要自动下载、执行未知安装包，也不要假设 Python、Node、Git 或浏览器驱动已经存在。
