# Codex Starter Kit

一个可复盘、可复制、可审计的 Codex Agent 与 Skill 能力包。仓库只保留功能说明、工作流、脚本、
依赖和安装工具，不包含账号、令牌、会话、缓存、草稿或生成产物。

## 内容

- `agents/`：7 个按功能命名的 Agent TOML 配置
- `skills/`：50 个技能目录，每个目录都有独立的 `SKILL.md`
- `installer-pack/`：可脱离 Git 和网络复制的稳定安装包
- `manifest/`：技能审计、Agent 目录、MCP 模板和来源/限制说明
- `scripts/`：打包、安装和自动验证脚本
- `ENVIRONMENT-MCP-INVENTORY.md`：Windows 环境、运行时、Python 包、MCP 和凭据清单

## 功能入口

| Agent | 主要功能 |
|---|---|
| 全能官 | 综合统筹、任务拆解、跨领域协作 |
| 研究官 | 学术、行业、竞品、用户和市场研究 |
| 创作官 | 公众号、小红书、文案、脚本和提示词 |
| 投资官 | A 股、基金、宏观、创业投资和资产配置 |
| 增长官 | 用户痛点、产品定位、获客、转化和增长实验 |
| 生活官 | 健身、饮食、旅行、天气和日常复盘 |
| 办公官 | 文档、表格、PDF、PPT、邮件和会议 |

详细调用词和工作边界见 [`manifest/agent-catalog.md`](manifest/agent-catalog.md)。名称只是便于记忆的
功能入口；真正的能力由 Agent 引用的技能和依赖状态决定。

## Windows 部署

安装脚本只使用 PowerShell，不要求目标机器已安装 Python、Node 或 Git：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install-to-codex.ps1
```

默认安装全部 Agent 和状态为 `ready` 的技能。若需要把需要运行时、MCP 或凭据的技能也复制到本机，
使用：

```powershell
.\scripts\install-to-codex.ps1 -IncludeNonDefault
```

默认不会覆盖本机已有同名文件；确认要更新时才使用：

```powershell
.\scripts\install-to-codex.ps1 -Overwrite
```

目标目录遵循 Codex 约定：

- Skills：`%USERPROFILE%\.agents\skills\`
- Agents：`%USERPROFILE%\.codex\agents\`

安装器不会写入全局 `AGENTS.md`，不会删除本机其他 Agent/Skill，也不会把凭据写入安装记录。

## 打包和验证

修改源文件后重新生成能力包：

```powershell
python .\scripts\build-pack.py --check
.\scripts\verify-package.ps1
```

`installer-pack/pack.json` 是安装契约；`dependencies.json` 描述每个 Skill/Agent 的依赖、检测方式、
离线安装文件名、架构、重启、许可证、来源和下游能力；`file-manifest.json` 为包内文件提供 SHA-256。

以后新增内容不需要修改安装器代码：

1. 新增 `skills/<id>/SKILL.md`，在 `manifest/imported-skills.txt` 和 `manifest/skill-audit.json` 登记。
2. 新增 `agents/<id>.toml`，在 `manifest/agent-audit.json` 登记并列出引用技能。
3. 新增 MCP 时，在 `manifest/mcp-inventory.json` 加入服务记录和无密钥模板。
4. 运行打包和验证脚本，确认名称、引用、哈希和兼容性状态一致。

## 状态说明

- `ready`：不需要额外本地运行时即可使用工作流说明。
- `requires-runtime`：需要 Python、CLI 或第三方包。
- `requires-mcp`：需要单独配置 MCP 服务。
- `requires-credential`：需要用户自行提供 API Key/端点。
- `unsupported/disabled`：仅保留功能说明，当前不提供兼容的自动执行入口。

## 安全边界

公开仓库不包含 API Key、Token、Cookie、`.env`、私有 MCP 配置、会话历史、记忆数据库、日志、缓存、
个人草稿或生成结果。外部服务必须通过本机环境变量或私有密钥管理服务配置，并在执行前确认权限、费用和
数据范围。
