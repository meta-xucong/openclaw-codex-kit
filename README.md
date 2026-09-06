# Codex Capability Kit

一个可复盘、可复制、可审计的 Codex Skill 与 Agent 能力包。内容只围绕功能、依赖和部署边界组织，
不包含账号、令牌、会话、缓存、草稿或生成产物。

## 包里有什么

- `agents/`：7 个按功能命名的 Codex Agent TOML。
- `skills/`：50 个独立 Skill；非核心 Skill 额外带 `agents/openai.yaml`，默认关闭隐式调用，避免缺依赖时误触发。
- `manifest/`：50 个 Skill 的逐项审计、7 个 Agent 的依赖闭包、运行时、MCP、API 和连接字段契约。
- `runtime/`：Windows x64 / CPython 3.12 的直接依赖锁文件和 wheelhouse 清单；不放二进制。
- `config-fragments/`：无密钥的 Codex MCP、Skill gating 和连接配置模板。
- `installer-pack/`：由脚本生成、可复制到其他电脑的完整能力包。
- `scripts/`：构建、验收和安装脚本。

## 50 个 Skill 的最终状态

| 状态 | 数量 | 含义 |
|---|---:|---|
| `core-ready` | 25 | 复制后即可使用工作流说明和 Codex 原生能力，默认安装 |
| `auto-installable-runtime` | 15 | 需要 U 盘运行时安装器提供的 Python 3.12 和离线包 |
| `guided-config` | 7 | 需要用户在连接向导中配置 API、MCP 或网络服务 |
| `unsupported` | 3 | 当前没有可验证的兼容自动入口，保持禁用 |

默认安装的是 25 个核心 Skill 和 7 个 Agent；要把全部 50 个 Skill 复制到本机：

```powershell
.\scripts\install-to-codex.ps1 -IncludeNonDefault
```

完整逐项清单见 [`manifest/skill-audit.json`](manifest/skill-audit.json)，其中每个 Skill 都有原始状态、
整改后状态、依赖类型、版本、健康检查、启用条件和失败降级说明。

## 7 个功能入口

| Agent | 适合处理 |
|---|---|
| 全能官 | 综合统筹、拆解复杂任务、跨领域协作 |
| 研究官 | 学术、行业、竞品、用户和市场研究 |
| 创作官 | 公众号、小红书、文案、脚本、图片/视频提示词 |
| 投资官 | A 股、基金、宏观、创业项目和资产配置 |
| 增长官 | 用户痛点、产品定位、获客、转化和增长实验 |
| 生活官 | 健身、饮食、旅行、天气和个人复盘 |
| 办公官 | 文档、表格、PDF、PPT、邮件、会议和文件整理 |

它们是可记忆的功能入口，不是固定的人设。真正能否执行某一步由 Skill、运行时、外部连接和健康检查共同决定。

## 在 Codex 中调用

Agent 文件安装到 `%USERPROFILE%\.codex\agents\`，Skill 安装到 `%USERPROFILE%\.agents\skills\`。
新建任务时直接点名即可：

```text
请使用自定义 Agent「研究官」，研究这个行业：……
请区分事实、来源、推测和建议，并标注数据日期。
```

也可以在当前任务中委派：

```text
请把市场研究交给「研究官」独立完成，返回证据和结论；你最后再汇总。
```

如果用户没有点名，主 Agent 仍可按任务内容使用已安装 Skill；非核心 Skill 必须在显式调用且依赖健康后才启用。
重载 Codex 或打开新任务即可读取新 Agent。完整调用词、能力边界和安全降级规则见
[`manifest/agent-catalog.md`](manifest/agent-catalog.md)。

## Windows 安装

安装能力包本身只需要 PowerShell，不要求目标机预装 Python、Node 或 Git：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install-to-codex.ps1
```

安装器只写自己拥有的 Agent/Skill 文件，不覆盖已有同名文件，除非显式加 `-Overwrite`；不会删除其他 Agent、
Skill 或全局 `AGENTS.md`。它会校验 `file-manifest.json` 与 `checksums.sha256`，并记录不含凭据的所有权清单。

### 运行时策略

需要真实 Python 功能的 Skill 使用 U 盘后续安装器提供的 Windows x64 CPython 3.12.10 per-user 运行时，
默认安装根为 `%LocalAppData%\Programs\Python\Python312`，不修改系统 PATH。随后用
`runtime/requirements-python-win-x64-py312.lock` 和 `runtime/wheelhouse-manifest.json` 安装完整的离线
传递依赖；所有文件都应在介质制作阶段记录 SHA-256。官方 Feishu MCP 的 Node.js 20 仅是可选连接依赖，
不是主安装链。具体文件名、签名、返回码、健康检查和回滚策略见 [`manifest/runtime-artifacts.json`](manifest/runtime-artifacts.json)。

## MCP、API 与连接配置

三类内容分开管理：

- MCP：当前只登记一个需向导配置的 `feishu` 服务，见 [`manifest/mcp-servers.json`](manifest/mcp-servers.json)。
- 直连 API：DashScope 网页搜索、图像服务、视频服务，见 [`manifest/api-services.json`](manifest/api-services.json)。
- 连接字段：统一的密钥、端点、认证方式、校验和能力映射，见 [`manifest/connection-fields.json`](manifest/connection-fields.json)。

模板在 `config-fragments/` 中，默认保持禁用；真实值只能写入本机私有配置或密钥管理器。没有健康检查通过时，
Agent 只能输出配置步骤或无连接降级结果，不能声称已经访问外部服务。

## 构建和验收

修改源文件后运行：

```powershell
python .\scripts\build-pack.py --check
.\scripts\verify-package.ps1
```

验收会重建包，并检查 50 个 Skill、7 个 Agent、依赖闭包、非核心 Skill 的显式门控、运行时/MCP/API 清单、
PowerShell/Python/TOML 语法、哈希、路径安全、旧平台标记、疑似密钥，以及天气/复盘/技能搜索/运行时探测的
安全烟测。

新增能力时遵循 `installer-pack/pack.json` 的扩展契约：登记 Skill 或 Agent 及其依赖，MCP/API 与连接字段
分开登记，运行时只提交锁文件和可审计元数据，然后重新构建和验收。

## 安全边界

公开仓库不包含 API Key、Token、Cookie、`.env` 实值、私有 MCP 配置、会话历史、记忆数据库、日志、缓存、
个人草稿或生成结果。外部服务必须通过本机环境变量或私有密钥管理服务配置，并在执行前确认权限、费用和数据范围。
