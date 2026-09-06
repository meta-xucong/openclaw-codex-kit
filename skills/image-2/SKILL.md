---
name: image-2
description: 使用 Image-2 异步任务接口进行图片生成和图片编辑，采用带内部 SHA-256 完整性校验的两阶段确认清单：先离线固化提示词、参考图、agent_id 与参数并交用户确认，确认后用同一清单正式生成，确保已确认输入不会被替换。支持文生图、图生图和多参考图，参考图通过 --image 传入，请求携带 agent-id，任务完成后直接返回图片 URL。
---

# Image-2 图像生成

集成 `custom-image-2-vip` 模型，支持文生图和图生图。Image-2 是异步任务接口：脚本先 POST 到 `/async` 端点创建任务拿到 `task_id`，随后自动轮询 `/v1/images/tasks/{task_id}`，任务完成后直接返回 `result.data[].url`（或顶层 `image_url`）中的图片地址。

正式生成采用参考 Seedance 的两阶段确认机制：**离线准备确认清单 → 用户确认 → 使用同一清单生成**，确保用户确认的提示词、参考图顺序/数量和生成参数在跨平台调用或失败重试时不会被替换。脚本仅使用 Python 标准库，Windows 和 macOS 均可直接运行。

## 强制调用约束

- **只能使用 Python 调用本技能**，必须通过 `python`/`python3` 执行本技能提供的脚本。
- **禁止** 使用 PowerShell、curl、HTTP 客户端、直接拼接口请求，或任何非 Python 方式绕过脚本直接调用 API。
- 正式生成必须经过“准备确认清单 → 用户确认 → 使用同一清单生成”。**禁止**直接把 prompt 或 `--image` 传给正式生成命令；脚本会拒绝直接生成。
- 准备确认清单时必须传入当前任务的 `--agent-id`。`agent_id` 仅用于请求上下文和确认绑定，不用于自动提取参考图。
- 用户确认后，下列输入全部不可变：prompt 的每个字符、参考图 URL/路径及其顺序与数量、尺寸、模型。任何一项需要变化都必须重新准备新清单并重新确认，不得手改旧清单。
- 参考图只能通过一个或多个 `--image` 参数传入；顺序必须以用户上传/提供的先后为准，原样传入并按同一顺序编号与展示，禁止按文件名、字母序或数字序重排。
- 优先通过 `--image` 传入**原始完整 URL**（聊天中的附件 URL），**禁止**先把 URL 下载为本地临时文件再传给 `--image`。确认清单与确认表中的参考图一律展示完整 URL（纯文本），与准备结果 `images` 数组完全一致；仅当平台确实只提供本地文件、拿不到 URL 时，才传入本地绝对路径。
- 只有用户明确回复“确认”“就按这份生成”等肯定答复后才能正式生成。
- `confirmation_fingerprint`、`prompt_sha256` 和 `confirmation_file` 都是 Agent 的内部校验或执行数据；不得在面向用户的确认表、对话消息、最终结果或命令说明中展示、复述或引用。
- 如果当前环境没有可用的 Python 环境，不要改用其他方式调用；先提醒用户安装 Python（可引导使用 `python-env-setup` 技能）。

## 零依赖说明

此插件采用 Python 标准库实现，**无需安装任何第三方 Python 依赖包**。

## 标准流程

### 1. 构建最终输入

逐项确定：

- 完整 prompt，逐字保留用户确认的内容。
- 参考图**完整 URL** 的准确顺序（用户上传先后，禁止按文件名排序；优先使用聊天/会话中的原始附件 URL，而非本地临时路径）。没有参考图时为文生图。
- 尺寸（仅支持下方“尺寸说明”中的 2K 预设）、模型。

### 2. 离线准备确认清单（不请求 API）

此步骤不会请求 Image-2 API、不会创建 task_id、不会扣费。脚本会固化输入、写入确认清单文件并计算供 Agent 内部使用的 SHA-256 指纹。

文生图（macOS / Linux）：

    python3 "$HOME/.sosoagent/skills/image-2/scripts/image_2_gen.py" "描述词" \
      --agent-id "<AgentID>" --size "2048x2048" --prepare-confirmation

图生图，可传入一张或多张参考图（支持本地路径或 URL，按上传顺序）：

    python3 "$HOME/.sosoagent/skills/image-2/scripts/image_2_gen.py" "编辑要求" \
      --agent-id "<AgentID>" \
      --image "/path/to/image-1.png" \
      --image "/path/to/image-2.png" \
      --size "2048x2048" --prepare-confirmation

Windows 将 `python3 "$HOME/..."` 替换为 `python "C:\Users\<User>\.sosoagent\skills\image-2\scripts\image_2_gen.py" ...`。

准备结果（JSON）必须由 Agent 在内部核对：

- `mode`（generation / edit）、`prompt`、`prompt_sha256`
- `images`、`image_count`（图生图模式下参考图顺序与数量）
- `agent_id`、`size`、`model`
- `confirmation_file`（绝对路径）和完整 `confirmation_fingerprint`
- `api_request_sent` 必须为 `false`
- `warnings`：若**非空**，说明有参考图是本地/临时路径而非完整 URL，应按提示改用原始 URL 重新准备，不要直接展示本地路径

准备命令若因解释器、路径或 shell 引号失败，只修正执行问题，并以完全相同的 prompt、参考图和参数重跑准备命令。

### 3. 向用户逐项确认

完整展示以下用户可确认的生成输入（不得只给摘要）：

- 生成模式、prompt 正文。
- `agent_id`（请求上下文）。
- 参考图用「编号 | URL」表格展示编号、**完整 URL**、数量和顺序（**必须直接照抄准备结果中的 `images` 数组**，禁止按文件名重排、**禁止展示本地临时路径**）；文生图时明确写 0。URL 列只写纯文本，不要用 `![](url)` 等 Markdown 媒体语法渲染。若准备结果的 `warnings` 非空（存在本地/临时路径），先改用原始 URL 重新准备再展示。
- 尺寸、模型。
- 在等待用户确认时提前告知：**如果出现图片展示异常等情况，可以在「产物/云端」查看生成的图片。**

不得向用户展示、复述或暗示 `confirmation_fingerprint`、`prompt_sha256`、确认清单绝对路径或任何 SHA-256 值。它们仅由 Agent 保留并用于后续命令校验。

只有用户明确确认后才能进入正式生成。用户修改任意文字、参考图、顺序或参数时，返回步骤 2 重新准备新清单并重新确认。

### 4. 正式生成

正式命令只传 Agent 内部保留的确认清单和指纹，不得再传 prompt、`--image`、`--agent-id`、`--size`、`--model`（脚本会拒绝覆盖）；`agent_id` 从已确认清单读取并随请求发送。不得在执行前后向用户展示指纹、清单路径或包含它们的完整命令。

macOS / Linux：

    python3 "$HOME/.sosoagent/skills/image-2/scripts/image_2_gen.py" \
      --confirmation-file "<清单绝对路径>" \
      --confirm-fingerprint "<完整指纹>" --confirm

Windows：

    python "C:\Users\<User>\.sosoagent\skills\image-2\scripts\image_2_gen.py" \
      --confirmation-file "<清单绝对路径>" \
      --confirm-fingerprint "<完整指纹>" --confirm

外层执行超时建议不低于 300 秒。轮询进度写入 stderr，最终结果写入 stdout；加 `--json` 以纯 JSON 输出。

### 可选 dry-run

排查清单或参数时使用，校验指纹并展示将提交的输入，但绝不请求 API：

    python3 "$HOME/.sosoagent/skills/image-2/scripts/image_2_gen.py" \
      --confirmation-file "<清单绝对路径>" \
      --confirm-fingerprint "<完整指纹>" --dry-run

## 接口规则

- 文生图调用 `/api/llm/openai/v1/images/generations/async`，请求体为 JSON，响应返回 `task_id` 与 `status=processing`。
- 图生图调用 `/api/llm/openai/v1/images/edits/async`（`multipart/form-data`，每个参考图使用重复的 `image` 字段），响应返回 `task_id` 与 `status=processing`，与文生图共用同一套异步轮询逻辑。
- 创建任务和轮询任务时，HTTP header 均携带确认清单中的 `agent-id`，用于绑定当前智能体请求上下文。
- 创建任务后，脚本以 GET 轮询 `/api/llm/openai/v1/images/tasks/{task_id}`，默认每 3 秒一次、总等待上限 600 秒，直到 `status=completed`。
- 任务完成后从 `result.data[].url`（或顶层 `image_url`）获取图片地址直接返回，不再转存 OSS。
- `status` 为 `failed/canceled/expired` 等终态时直接报错退出。
- 两个接口都使用 `model=custom-image-2-vip`。

## 超时要求

- 接口改为**异步任务**后，单个 HTTP 请求（创建任务、每次轮询）都很快；真正耗时的是**任务排队与生成**，复杂中文 prompt、海报排版、多元素合成可能需要 **120-180 秒**，极端情况下更久。
- 脚本会**在进程内持续轮询**直到任务完成，从调用方视角它仍是一个长耗时命令，**外层执行超时**（例如 `exec timeout`）建议至少 **300 秒**；不要使用 `90-120 秒` 的短超时。
- 脚本内置**轮询总超时**默认 **600 秒**（环境变量 `IMAGE_2_TASK_POLL_TIMEOUT` 可调，单位秒），轮询间隔默认 **3 秒**（`IMAGE_2_TASK_POLL_INTERVAL`）。轮询总超时是兜底上限，不表示每次都要等满。
- `timeout` **不是 prompt 文本的一部分**。不要把“请等待 180 秒”之类的话写进生成提示词里指望生效；真正生效的是**外层执行器超时**和**脚本内轮询总超时**。
- 轮询进度会输出到 stderr（不影响 `--json` 的 stdout 结果），可用于判断任务仍在排队/生成中。

### 推荐超时组合

| 场景 | 外层执行超时 | 脚本内轮询总超时 |
|------|--------------|------------------|
| 普通出图 | `300s` | 默认 `600s` 即可 |
| 复杂海报 / 长中文 prompt | `600s` | `600-900s` |

> 原则：**外层执行超时 ≥ 脚本内轮询总超时 > 预期生成耗时**。

## 输出规则

- 工具返回的 `images` 字段就是最终可交付的图片地址，为任务接口返回的图片 URL（带签名的限时链接，约 24 小时有效，如需长期保存请及时下载）。
- 不要输出或转述原始 `b64_json`。
- 如果界面已经展示图片，默认不要在正文里重复粘贴图片链接；只有用户明确索取下载地址、原图地址或分享地址时，才返回 `images` 字段中的完整地址。
- 当工具返回多张图片时，不需要展示序号和第几张的说明，直接平铺输出。

## 尺寸说明

| 比例 | 推荐参数 | 适用场景 |
|------|----------|----------|
| 1:1 | `2048x2048` | 社交媒体、海报、架构图 |
| 2:3 | `1360x2048` | 人像海报、商品长图 |
| 3:2 | `2048x1360` | 摄影横图、内容配图 |
| 3:4 | `1536x2048` | 竖版海报、人物展示 |
| 16:9 | `2048x1152` | 电脑壁纸、横版封面 |
| 9:16 | `1152x2048` | 手机壁纸、竖版封面 |
| 4:3 | `2048x1536` | 展示页、幻灯片素材 |
| 4:5 | `1632x2048` | 社媒 feed、卡片封面 |
| 5:4 | `2048x1632` | 横版广告、详情头图 |
| 21:9 | `2048x864` | 电影感横幅、超宽 banner |

> 当前 `image-2` 仅支持以上 10 组 2K 推荐尺寸；传入其他像素值会直接报错。

## 注意事项

- API key 从本机 `~/.sosoagent/sosoclaw.json` 的 `API_KEY` 字段读取（也可用环境变量 `IMAGE_2_API_KEY` / `SOSOCLAW_API_KEY` / `OPENAI_API_KEY` 覆盖）。
- 异步任务从创建到完成通常需要 10-60 秒；复杂海报、长中文 prompt、图生图编辑可能需要 120-180 秒甚至更久，期间脚本会持续轮询并输出进度到 stderr。
- `--image` 支持本地文件路径和 HTTP/HTTPS URL，URL 会在正式生成时自动下载为临时文件。
- `--agent-id` 仅在准备确认清单阶段传入；正式阶段从确认清单读取，并在创建、轮询请求中携带 `agent-id` header。
- 确认清单默认写入 `~/.sosoagent/workspace/createContent/image/.confirmations/`，可用 `--confirmation-output` 覆盖；清单文件权限 600。
- 如果出现“长时间无输出像是卡住了”的现象，先看 stderr 的轮询进度：若仍在 `processing` 说明任务未结束；若完全没有输出，优先检查外层执行超时是否过短。

## 参数摘要

| 参数 | 用途 |
|---|---|
| `--prepare-confirmation` | 离线固化待确认输入，不请求 API |
| `--image` | 准备阶段的参考图路径/URL，可重复并保留顺序 |
| `--agent-id` | 准备阶段必填的请求上下文标识；正式阶段从确认清单读取 |
| `--size` | 尺寸（2K 预设） |
| `--model` | 模型名称 |
| `--confirmation-file` | 正式生成或 dry-run 使用的确认清单 |
| `--confirm-fingerprint` | Agent 内部保存的完整 SHA-256 指纹；仅用于确认清单一致性校验，不得展示给用户 |
| `--confirm` | 正式生成必填，表示用户已确认当前清单 |
| `--dry-run` | 校验并展示将提交的输入，不请求 API |
| `--confirmation-output` | 覆盖默认确认清单输出目录/路径 |
| `--json` | 以纯 JSON 格式输出结果 |
