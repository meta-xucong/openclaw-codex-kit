# Codex config fragments

These are renderable, no-secret templates. The connection/configuration layer must replace placeholders,
validate the resulting TOML, and merge only the selected fragment into the user's `config.toml`.

- `feishu-official-stdio.template.toml` is disabled by default and uses the official npm MCP package.
- `codex-skills-gating.template.toml` shows the `[[skills.config]]` shape for disabling unmet Skills.
- `connections.template.json` is a structured rendering input for a configuration UI; it is not a secret store.

Never copy a template with placeholders into an enabled configuration. Health-check the resulting connection,
then reload Codex.
