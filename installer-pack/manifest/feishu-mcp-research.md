# 飞书 MCP 实现核查

核查日期：2026-09-07。结论只用于能力包的连接引导，不代表本仓库分发第三方运行时或凭据。

## 推荐候选

| 候选 | 许可证/发布物 | Windows 运行时 | 维护与制品 | 风险判断 |
|---|---|---|---|---|
| [larksuite/lark-openapi-mcp](https://github.com/larksuite/lark-openapi-mcp) | MIT；npm `@larksuiteoapi/lark-mcp@0.5.1` | Node.js >=20；npx/本地 Node | Lark 官方仓库；提供 npm 包；README 明确标注 Beta | 最可信候选，但 API 可能变化，仍需应用权限、App ID/Secret、联网；不适合主链路静默安装 |
| [cso1z/Feishu-MCP](https://github.com/cso1z/Feishu-MCP) | MIT；npm `feishu-mcp`，仓库有 v0.2.3 | Node.js + pnpm/npm；支持 STDIO/SSE | 第三方，近期仍有提交；README 提供 npm、源码和 Docker 路径 | 功能覆盖广但权限面较大；第三方包、凭据缓存和 user/tenant 模式需要独立审查 |
| [shou-nian/feishu-mcp-server](https://github.com/shou-nian/feishu-mcp-server) | 仓库未声明许可证；Python `>=3.11` + uv | Python/uv；STDIO | 代码和测试目录完整，但暂无 release、预编译 Windows 制品或许可证声明 | 可读源码但不能作为可合法再分发的默认制品；保持候选/人工批准 |
| [Lark-Base-Team/lark-base-mcp-node-server](https://github.com/Lark-Base-Team/lark-base-mcp-node-server) | README 声称 MIT；npm `@lark-base-open/mcp-node-server` | Node.js；只覆盖 Base/Bitable | 面向多维表格，仓库规模和发布信息有限 | 不是文档/云盘/Wiki 的完整替代；仅在用户明确需要 Base 时单独接入 |

## 结论与安装边界

官方实现已经足够可靠，可以登记为 `mcp.feishu` 的推荐候选，但它仍是 `guided-config`：

1. Starter Kit 不捆绑 Node.js、npm 包、App Secret 或 OAuth 会话。
2. 安装器可在 U 盘中准备经过签名和哈希锁定的 Node.js 安装包；连接板块再安装/缓存 npm 包。
3. 连接板块必须让用户选择 tenant/user/OAuth 模式、输入 App ID/Secret、配置权限，并执行只读健康检查。
4. 只有健康检查通过后才生成并启用 `[mcp_servers.feishu]`；失败时保持 `enabled=false`。
5. 官方 README 和 CLI 文档给出了真实的 `npx @larksuiteoapi/lark-mcp mcp` 入口；本包的 TOML 只使用占位符，不把占位符当成可运行配置。

来源：

- [官方仓库 README](https://github.com/larksuite/lark-openapi-mcp/blob/main/README.md)
- [官方 CLI 文档](https://github.com/larksuite/lark-openapi-mcp/blob/main/docs/reference/cli/cli.md)
- [官方 package.json](https://raw.githubusercontent.com/larksuite/lark-openapi-mcp/main/package.json)
- [官方 MIT 许可证](https://raw.githubusercontent.com/larksuite/lark-openapi-mcp/main/LICENSE)
