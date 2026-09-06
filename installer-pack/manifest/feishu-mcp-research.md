# 飞书 MCP 实现核查

核查日期：2026-09-07。结论只用于能力包的连接引导，不代表本仓库分发第三方运行时或凭据。

## 推荐候选

| 候选 | 许可证/发布物 | Windows 运行时 | 维护与制品 | 风险判断 |
|---|---|---|---|---|
| [larksuite/lark-openapi-mcp](https://github.com/larksuite/lark-openapi-mcp) | MIT；npm `@larksuiteoapi/lark-mcp@0.5.1` | Node.js >=20；锁定本地 Node/npm cache | Lark 官方仓库；提供 npm 包；README 明确标注 Beta | 最可信候选，但 API 可能变化，仍需应用权限、App ID/Secret；官方 CLI 只接受 `-s/--app-secret` 参数，因此必须使用本机凭据代理 |
| [cso1z/Feishu-MCP](https://github.com/cso1z/Feishu-MCP) | MIT；npm `feishu-mcp`，仓库有 v0.2.3 | Node.js + pnpm/npm；支持 STDIO/SSE | 第三方，近期仍有提交；README 提供 npm、源码和 Docker 路径 | 功能覆盖广但权限面较大；第三方包、凭据缓存和 user/tenant 模式需要独立审查 |
| [shou-nian/feishu-mcp-server](https://github.com/shou-nian/feishu-mcp-server) | 仓库未声明许可证；Python `>=3.11` + uv | Python/uv；STDIO | 代码和测试目录完整，但暂无 release、预编译 Windows 制品或许可证声明 | 可读源码但不能作为可合法再分发的默认制品；保持候选/人工批准 |
| [Lark-Base-Team/lark-base-mcp-node-server](https://github.com/Lark-Base-Team/lark-base-mcp-node-server) | README 声称 MIT；npm `@lark-base-open/mcp-node-server` | Node.js；只覆盖 Base/Bitable | 面向多维表格，仓库规模和发布信息有限 | 不是文档/云盘/Wiki 的完整替代；仅在用户明确需要 Base 时单独接入 |

## 结论与安装边界

官方实现已经足够可靠，可以登记为 `mcp.feishu` 的推荐候选，但它仍是 `guided-config`：

1. Starter Kit 不捆绑 Node.js、npm 包、App Secret 或 OAuth 会话；Node 安装包和 npm tarball/传递依赖都标记为 `pending`，直到私有介质完成锁定。
2. 安装器可在 U 盘中准备经过 Authenticode、SHA-256 和 npm integrity 锁定的 Node.js 与 npm cache；启用后的健康检查必须使用 `npm exec --offline`，禁止 `npx --yes` 联网下载。
3. 连接板块必须让用户选择 tenant/user/OAuth 模式、输入 App ID/Secret、配置权限，并把 Secret 放入 Windows Credential Manager 或进程级凭据代理；不得写入 `config.toml`、日志或安装记录。
4. 只有离线包、凭据代理和只读健康检查全部通过后才生成并启用 `[mcp_servers.feishu]`；失败时保持 `enabled=false`。
5. 官方 README 和 CLI 文档给出了真实的 `lark-mcp mcp` 入口；本包的 TOML 只使用本地 wrapper 占位符，不把 `npx` 当成离线运行时。

来源：

- [官方仓库 README](https://github.com/larksuite/lark-openapi-mcp/blob/main/README.md)
- [官方 CLI 文档](https://github.com/larksuite/lark-openapi-mcp/blob/main/docs/reference/cli/cli.md)
- [官方 package.json](https://raw.githubusercontent.com/larksuite/lark-openapi-mcp/main/package.json)
- [官方 MIT 许可证](https://raw.githubusercontent.com/larksuite/lark-openapi-mcp/main/LICENSE)
