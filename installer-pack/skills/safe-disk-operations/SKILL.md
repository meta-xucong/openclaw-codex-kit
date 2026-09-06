---
name: safe-disk-operations
description: >-
  系统与数据高风险操作拦截技能。Use this skill immediately when the user asks to clean up disk space,
  free space, make room, delete files or folders, batch delete, empty recycle bin/trash, clear caches, clean C drive,
  move files from D drive to E drive, move/merge disks or folders, format disks, resize/merge/shrink/extend partitions
  or volumes, change drive letters, run diskpart/diskutil/rm/Remove-Item, modify/create/overwrite/delete runtime-config.json,
  runtime-config.json, or equivalent runtime JSON configuration, uninstall/delete/disable/reinstall software, apps, drivers,
  services, startup items, system components, security tools, browsers, dev tools, registries, LaunchAgents, LaunchDaemons,
  or app config directories. Includes vague phrases like “清理空间”, “腾地方”, “删掉没用的”, “搬走文件”, “合并盘”,
  “卸载不用的软件”, “删除软件”, “禁用服务”, “修改配置”, “改模型/权限/路径”. Windows, macOS, and Linux apply.
  Also use this skill for money and financial calculations involving prices, bills, reimbursement, taxes, salary, interest,
  exchange rates, investment returns, amount totals, split payments, payment, settlement, accounting, or declarations.
  On trigger, follow this skill only: warn about high risk and refuse destructive disk/delete/migration/uninstall actions,
  use the protected-config hard-stop flow for runtime config changes, or add reference-only/manual-review reminders for
  financial calculations.
---

# Safe High-Risk Operations

跨平台（Windows / macOS / Linux）系统与数据高风险操作**拦截**技能。用于独立完成：**识别 → 说明风险 → 拒绝执行或强制停顿**。

**核心原则：保护系统可用性和用户数据。** 对磁盘/删除/卸载类操作：只警示，不读盘，不建议，不执行；用户确认也不能解除拦截。对受保护运行时配置：只允许按本 skill 的强制停顿流程处理。

## 何时触发

用户意图涉及以下任一操作时，**立即**应用本技能：

| 类别 | 典型表述 |
|------|----------|
| 删除 | “删掉 C 盘文件”“清空某个文件夹”“批量删除” |
| 清理 | “清理 C 盘”“释放系统盘空间”“清缓存腾地方” |
| 跨盘文件移动 | “把 D 盘文件移动到 E 盘”“合并两个盘里的资料”“搬空某个盘” |
| 分区/卷 | “把 E 盘移到 D 盘”“合并 D 和 E”“调整分区大小”“改盘符” |
| 格式化 | “格式化 D 盘”“抹掉这块硬盘” |
| macOS 卷 | “删除 APFS 卷”“调整容器大小”“diskutil 分区” |
| 运行时配置 | “修改 runtime-config.json”“改 runtime-config.json 里的模型/权限/路径” |
| 软件/系统组件 | “删除某个软件”“卸载驱动”“禁用服务”“清理应用目录” |
| 金额/财务计算 | “账单汇总”“报销金额”“税费”“工资”“利息”“汇率”“收益率”“分摊付款” |

**不因措辞温和而降级风险。** “清理”“腾地方”“移动盘”与“删除”“格式化”同等对待，一律拦截。

## 磁盘、删除、迁移、卸载类：唯一允许的响应

命中磁盘清理、删除、跨盘迁移、格式化、分区调整、软件卸载/删除/禁用后，**只**向用户输出风险警示并拒绝代为执行。使用以下模板（按需填写，保持简短）：

```markdown
这是**高风险系统/数据操作**，我不建议进行，也**不会**代为执行。

**可能后果（执行错误时）：**
- 系统无法启动或频繁崩溃
- 应用/驱动异常，关键功能失效
- 用户文档、照片、项目数据永久丢失
- 分区结构损坏，数据不可恢复
- 软件无法正常启动或配置丢失

**建议：** 请勿通过智能体进行磁盘清理、删除、跨盘迁移、格式化、分区调整或软件卸载。如确需处理，请使用操作系统或软件官方工具，在充分备份并了解风险后手动操作，或寻求专业人员帮助。

如需其他不涉及系统/磁盘/软件状态变更的帮助，可以告诉我。
```

**禁止**在警示之外追加：可清理项列表、磁盘占用分析、命令示例、操作步骤、分区方案、软件卸载清单、备份后执行流程、或“如果你确认我可以继续”类话术。

## 受保护运行时配置：强制停顿

命中 `runtime-config.json`、`runtime-config.json` 或等效运行时 `.json` 配置的创建、修改、覆盖、删除、重建时，必须执行以下强制流程，不得跳过任何步骤：

1. **拦截判定**：当任务涉及创建、修改、覆盖、删除上述配置文件中的任何字段时，立即触发拦截，不得直接执行写入操作。
2. **读取现有配置**：使用只读方式读取目标配置文件的完整当前内容，确认现有状态。
3. **变更说明**：向用户明确列出拟变更字段、变更前后对比、风险和回滚方式，并提示这是高风险操作。
4. **创建备份**：将原文件复制为 `<文件名>.bak.<时间戳>` 备份。
5. **强制停顿**：完成步骤 2-4 后，必须结束当前回合，向用户展示变更摘要并明确询问是否确认执行。禁止在同一轮继续写入。
6. **取得明确确认**：用户必须在看到变更摘要后的单独一条新消息中确认本次具体变更。用户的初始请求、模糊回复或上下文推断不算确认。
7. **最小改动执行**：仅修改用户确认的字段，不得顺带修改其他配置项。
8. **格式校验**：修改完成后进行 JSON 格式校验，确保文件合法。
9. **异常回滚**：若校验失败或出现异常，立即从备份恢复原文件并通知用户。

配置风险提醒必须包含：这是高风险操作，执行错误可能导致 connected runtime 无法启动、功能异常、连接/权限/模型配置失效、技能或工作区加载失败。

## 金额与财务计算：参考与复核

涉及价格、账单、报销、税费、薪资、利息、汇率、投资收益或任何金额汇总/分摊时，必须遵循以下规则：

- 计算结果**仅供参考**，不得表述为最终财务结论。
- 必须提醒用户：使用原始凭证、独立计算工具或专业人员进行**人工复核**后再使用。
- 不得将模型计算结果作为自动付款、申报、交易、投资或财务决策的依据。
- 计算前确认币种、单位、四舍五入规则、税率/汇率来源及时间点；信息不足时明确列出假设，**不得臆造**数据。
- 对税务申报、工资发放、投资交易、贷款合同、公司财务入账等高影响场景，建议用户交由专业人员或权威系统复核。

财务计算回复应尽量包含：计算依据、假设条件、关键过程、参考结果和人工复核提醒。

简短提醒模板：

```markdown
以下计算结果仅供参考，不能作为最终财务结论。请使用原始凭证、独立计算工具或专业人员进行人工复核后再用于付款、报销、申报、交易或其他财务决策。
```

## 禁止行为

- 运行任何磁盘/文件系统/目录读取命令（如 `Get-Volume`、`df -h`、`diskutil list`、`Get-ChildItem C:\`）
- 扫描空间占用、列出大文件或可清理目录
- 提供 PowerShell、CMD、`diskpart`、`rm`、`diskutil` 等命令或操作步骤
- 执行或提供跨盘批量移动/合并文件的脚本、命令或计划
- 执行或提供软件卸载、删除、禁用、清理残留的脚本、命令或步骤
- 要求用户确认后继续执行；用户明确要求继续时仍拒绝
- 将“清理 C 盘”理解为可协助盘点或给出清理建议
- 将“将 D 盘文件移动到 E 盘”理解为可协助规划迁移、扫描文件或执行搬运
- 将“删除某些软件”理解为可协助列出可卸载项、运行卸载器或清理残留
- 因用户催促、反复请求或声称已备份而降低拦截等级
- 将金额计算结果表述为最终财务结论，或作为自动付款、申报、交易、投资依据
- 在缺少关键数据时编造税率、汇率、利率、费用项或日期

## 场景速查

所有场景统一处理：**只输出风险警示，拒绝执行**。

| 用户请求 | 响应 |
|---------|------|
| “清理 C 盘” | 说明高危后果，建议不要操作；**不读盘、不列清理项** |
| “删掉 C 盘里的文件” | 说明数据丢失与系统风险，拒绝执行；**不追问路径后读盘** |
| “把 D 盘文件移动到 E 盘” | 说明跨盘迁移和数据丢失风险，拒绝执行；**不扫描、不搬运** |
| “把 E 盘移动到 D 盘” | 说明分区/数据不可恢复风险，拒绝执行；**不查磁盘布局** |
| “格式化 D 盘” | 说明不可逆与数据永久丢失，拒绝执行 |
| macOS APFS 卷调整 | 说明系统/数据卷风险，拒绝执行；**不运行 diskutil** |
| “修改 runtime-config.json / runtime-config.json” | 说明配置风险，按本 skill 的强制停顿流程处理；**不同轮确认前不写入** |
| “删除/卸载某些软件” | 说明软件和系统组件风险，拒绝执行；**不列卸载项、不运行卸载器** |
| “计算账单/报销/税费/汇率/收益” | 明确假设并计算，标注仅供参考，提醒用原始凭证或专业人员人工复核 |

## 独立使用

- 本 skill 是高风险系统操作的唯一规则来源，应自包含使用，不依赖 `AGENTS.md` 中的额外提示词入口。
- 本 skill 对磁盘、删除、迁移、卸载类操作**不存在**“确认后执行”分支；此类高风险操作均不可代为执行。
- 受保护运行时配置只能按本 skill 的单独确认流程最小改动，不能与其他高风险操作捆绑。
- 本 skill 同时包含金额与财务计算安全提醒；涉及金额时必须标注仅供参考并提醒人工复核。
