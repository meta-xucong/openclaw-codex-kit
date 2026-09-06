# Codex Agent Kit

这是一个可复盘、可部署到其他电脑的 Codex Agent 与 Skill 扩展包。

## 包含内容

- `agents/`：7 个自定义 Codex Agent 配置
- `skills/`：50 个已迁移技能目录
- `manifest/`：迁移清单、来源说明和 MCP 状态
- `scripts/`：安装和校验脚本

### 7 个 Agent

- 全能官
- 研究官
- 创作官
- 投资官
- 增长官
- 生活官
- 办公官

详细的职责、适用场景和调用模板见 [`manifest/agent-catalog.md`](manifest/agent-catalog.md)。

## 在另一台 Windows 电脑部署

1. 安装 Git，并登录 Codex/GitHub。
2. 克隆本仓库。
3. 在仓库根目录运行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install-to-codex.ps1
```

默认不会覆盖目标电脑已有的同名 Agent 或技能。确认要更新同名内容时运行：

```powershell
.\scripts\install-to-codex.ps1 -Overwrite
```

安装后重启 Codex 或新建任务，让它重新加载 `~/.codex/agents/` 和 `~/.codex/skills/`。

## 如何调用

在新任务中直接说明：

```text
请启动并使用自定义 Agent「研究官」，研究以下问题：……
```

也可以要求主 Agent 委派任务：

```text
请把这个任务交给「办公官」独立完成，最后返回可交付文件。
```

## MCP 和安全边界

本仓库不包含新的 MCP 服务定义。飞书技能文件保留了工作流说明，但实际运行仍需要对应的飞书工具或 MCP。

本仓库**不包含** API Key、Gateway Token、`.env`、第三方服务主配置、会话历史、记忆数据库和运行日志。不要把这些内容补进公开仓库；如果未来配置私有凭据，请使用本机环境变量或私有密钥管理服务。

技能目录中的运行缓存、历史任务状态、个人草稿和生成结果也不纳入版本库；这些内容会被 `.gitignore` 排除，避免把一次性运行状态误当成可部署代码。

## 兼容性

- 技能目录包含工作流说明、脚本、参考资料和模板。
- 本仓库不包含任何完整运行时、账号配置或外部服务凭据。
- 部分技能需要额外的 MCP、命令行工具或 Python/Node.js 依赖；安装后请按具体技能说明配置。
