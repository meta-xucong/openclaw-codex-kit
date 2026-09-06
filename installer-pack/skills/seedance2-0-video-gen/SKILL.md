---
name: seedance2-0-video-gen
description: 使用豆包 Seedance 2.0 根据文本、参考图片、参考视频和参考音频生成视频，并完成不可变输入确认、一次性幂等任务提交、轮询、历史查询和本地下载。用户要求使用 Seedance 生成视频、让图片/视频/音频作为参考素材，或查询此前 Seedance 任务时使用。正式生成采用带 SHA-256 指纹的两阶段确认清单；官方链接过期时只提示查看本地产物或云端产物，不自动重新生成。
---

# Seedance 2.0 视频生成

只使用本技能的脚本调用视频生成接口：

    scripts/seedance_video_gen.py

脚本仅依赖 Python 标准库，支持 Windows、macOS 和 Linux。

## 强制安全约束

1. 正式生成必须经过“离线准备确认清单 → 用户确认 → 使用同一清单生成”。禁止直接把 prompt 或媒体 URL 传给正式生成命令。
2. 用户确认后，下列输入全部不可变：prompt 的每个字符；图片、视频、音频的 URL、类型、数量和顺序；时长、比例、水印及 generate_audio。`generate_audio` 必须始终为 `true`（见约束 11）。
3. 媒体顺序必须以用户上传/提供的先后为准，原样传入 `--image` / `--video` / `--audio`，并按同一顺序编号与展示。禁止按文件名、字母序、数字序、扩展名或 URL 字典序重排。例如用户先传 `参考图2.png` 再传 `参考图1.png`，则顺序必须是 `参考图2.png`、`参考图1.png`；确认表中的「图1」= 上传顺序第 1 张（此时是 `参考图2.png`），绝不是文件名里带“1”的那张。
4. 媒体顺序的唯一事实来源（按优先级）：
   - 用户消息正文里附件 URL 的出现顺序（常见为消息末尾逐行 URL）；
   - 或 `--prepare-confirmation` 返回 JSON 中的 `images` / `videos` / `audios` 数组顺序。
   禁止用 `session-assets.json`、资源面板、文件名数字、`参考图N`/`图N` 字样去重排。拿到 URL 后不得 `sort`，确认表必须原样照抄准备结果数组，禁止按文件名“整理后再展示”。
5. 每个媒体 URL 是不可拆分的完整字符串。禁止把 `.../attachment/<id>/` 与文件名拆开后重新拼接。错误示例：把 `.../4ce9.../耳机参考图3.png` 改成 `.../269c.../耳机参考图3.png` 会导致 resource not found。默认不要传 `--image`/`--video`/`--audio`，让脚本从会话原文提取；若必须显式传入，只能整段复制用户消息中的原始 URL。
6. 调用失败时，只能修正 Python 可执行文件、脚本绝对路径、shell 引号、权限或等待参数。不得把 prompt 改成 test/demo/测试，不得缩短、翻译或润色 prompt，不得删除、替换、调序任何媒体，也不得改用无素材模式试跑。
7. 若任何业务输入需要变化，必须重新准备新清单，完整展示新输入和新指纹，并取得用户的新确认。不得手改旧清单或用旧确认批准新输入。
8. 任何返回一旦出现 task_id，禁止重新提交；只查询或轮询该 task_id。无论成功、失败、超时、链接过期或提交状态未知，都必须先把本次结果告知用户；用户要求再次生成时，必须重新准备确认清单并取得新的确认，不能沿用旧确认自动 POST。
9. 只允许本脚本发起 Seedance 请求。可以用系统 shell 启动 Python，但不得用 curl、PowerShell HTTP、手写 HTTP 或其他客户端绕过确认机制。
10. 每次实际生成前，明确告知用户并取得同意：
   - 每个视频先预扣 20000 积分，完成后返还剩余积分。
   - 官方视频链接有效期为 24 小时；链接过期后，请到本地产物或云端产物中查看。
   - 视频保存到当前智能体的 createContent/video/ 目录。
   - 中断后先检查该目录，并凭 task_id 继续查询。
   - 如果提交响应是 5xx、429、超时或网络中断，提交状态按未知处理；只允许恢复查询，不允许自动再次 POST。
11. **必须生成有声音的视频。** `generate_audio` 固定为 `true`，禁止在确认清单或 API 请求中写 `generate_audio: false`。梳理/分镜/确认环节一律写「音频生成 | 是」，禁止写「否」「后期叠加配音」「后期加 BGM」「用户自行配音」或任何把声音推给后期的表述。参考音频 `--audio` 仅表示参考素材，与「是否生成声音」无关；没有参考音频时仍必须 `generate_audio=true`。

脚本会拒绝直接生成、拒绝命令行覆盖已确认输入、拒绝过期/指纹不匹配或被篡改的清单、拒绝 `generate_audio=false`，并拒绝 test/demo/测试等诊断占位词。

## 选择 Python 解释器

只用无副作用命令检查环境，绝不能提交测试视频。

Windows 首选：

    python --version

若不存在，再依次检查：

    py -3 --version
    python --version

Windows 通常使用 `python`。使用脚本绝对路径，不依赖 `~` 展开，也不使用旧版 Windows PowerShell 不支持的 `&&`。

    python "scripts/seedance_video_gen.py" --help

macOS / Linux 首选：

    python --version

若不存在，再检查 `python --version`。macOS 通常使用 `python`。

    python "scripts/seedance_video_gen.py" --help

选定解释器后，本次任务始终使用同一个解释器。`--help`、准备清单和 dry-run 足以验证环境；不得生成测试任务。

## 输入与 API 映射

把不同媒体类型分别按用户上传/提供的先后顺序编号：图片1、图片2……；视频1、视频2……；音频1、音频2……。编号只表示该类型列表中的位置，与文件名无关。prompt 中的编号必须与各自类型的列表顺序一致；准备清单、确认表格、`--image`/`--video`/`--audio` 参数顺序三者必须相同，且都不得按文件名重排。

| 已确认输入 | API `content` 项 | 固定角色 |
|---|---|---|
| 完整 prompt | `{"type":"text","text":"..."}` | 无 |
| 每张图片 | `{"type":"image_url","image_url":{"url":"..."}}` | `reference_image` |
| 每个视频 | `{"type":"video_url","video_url":{"url":"..."}}` | `reference_video` |
| 每段音频 | `{"type":"audio_url","audio_url":{"url":"..."}}` | `reference_audio` |

实际 `content` 顺序固定为：完整 prompt、全部图片、全部视频、全部音频。各媒体类型内部严格保留确认顺序。

媒体必须是 Seedance 服务可访问的 HTTP/HTTPS URL，不能把本地文件路径直接当 URL。显式的 `--image`、`--video`、`--audio` 支持无扩展名 URL；从聊天纯文本自动判型时只接受常见图片、视频或音频扩展名。无法可靠判型时停止并要求提供明确 URL，不得猜测类型。

## 标准流程

### 1. 构建最终输入

逐项确定：

- 完整 prompt，逐字保留用户确认的内容。
- 图片、视频、音频 URL 的准确顺序（用户上传先后，禁止按文件名排序），并核对 prompt 中的“图片N / 视频N / 音频N”。
- `expected-image-count`、`expected-video-count`、`expected-audio-count`。三项都必须显式传入；没有对应素材时传 0。
- duration，支持 4–15 秒整数。
- ratio：16:9 或 9:16。
- `generate_audio` 固定为是/`true`（不得关闭）；是否加水印。参考音频 `--audio` 只表示参考素材，不得据此关闭声音生成。

有多个分镜时仍只生成一个视频、只提交一次任务。梳理方案时若涉及声音，只能说明由模型生成环境音/对白等，禁止规划「无声成片 + 后期配音/BGM」。

### 2. 离线准备确认清单

此步骤不会请求 Seedance API，不会创建 task_id，也不会扣费。

默认不传 `--image`/`--video`/`--audio`：只传 `--expected-*-count`，让脚本从用户消息原文按出现顺序提取完整 URL（可避免 attachment id 与文件名被错误重组）。若准备结果出现 `warnings` 或 `*_overriding_cli`，必须以结果中的 `images`/`videos`/`audios` 为准展示，不得继续使用命令行里拼错的 URL。

仅当会话提取失败时，才整段复制用户消息中的原始 URL 显式传入；不得拆分或改写 URL 任一路径段。以下示例对应 2 张图片、1 个参考视频、1 段参考音频：

Windows：

    python "scripts/seedance_video_gen.py" "<完整最终提示词>" --agent-id "<AgentID>" --duration 11 --expected-image-count 2 --image "<图片1 URL>" --image "<图片2 URL>" --expected-video-count 1 --video "<视频1 URL>" --expected-audio-count 1 --audio "<音频1 URL>" --prepare-confirmation

macOS / Linux：

    python "scripts/seedance_video_gen.py" "<完整最终提示词>" --agent-id "<AgentID>" --duration 11 --expected-image-count 2 --image "<图片1 URL>" --image "<图片2 URL>" --expected-video-count 1 --video "<视频1 URL>" --expected-audio-count 1 --audio "<音频1 URL>" --prepare-confirmation

纯文生视频也必须明确传入：

    --expected-image-count 0 --expected-video-count 0 --expected-audio-count 0

若无法直接取得某一类媒体 URL，可不传对应的 `--image`、`--video` 或 `--audio`；当该类 expected count 大于 0 时，脚本会向前查找最近一条真正包含该类媒体的用户消息，并跳过后续“确认”等无媒体消息。

任何实际数量与 expected count 不一致都会在 API 请求前停止。不得降低 expected count、删素材或改成无素材试跑。

准备结果是后续确认的唯一事实来源，必须核对：

- `prompt` 和 `prompt_sha256`
- `images`、`image_count`、`image_source`
- `videos`、`video_count`、`video_source`
- `audios`、`audio_count`、`audio_source`
- `duration`、`ratio`、`watermark`、`generate_audio`
- `confirmation_file` 和完整 `confirmation_fingerprint`
- `api_request_sent`，必须为 `false`

准备命令若因解释器、路径或 shell 引号失败，只修正执行问题，并以完全相同的 prompt、媒体和参数重跑准备命令。

### 3. 向用户逐项确认

完整展示：

- prompt 正文，不得只展示摘要。
- 图片、视频、音频分别用表格展示编号、完整 URL、数量和顺序；没有时明确写 0。**必须直接照抄准备命令返回的 `images`/`videos`/`audios` 数组顺序**，不得按文件名重排后再画表。参考图片示例（上传顺序为先 `参考图2` 后 `参考图1`）：

  ### 参考图片（按上传顺序，共2张）

  | 编号 | URL |
  |---|---|
  | 图1 | https://example.com/.../参考图2.png |
  | 图2 | https://example.com/.../参考图1.png |

  若做成「图1 → 参考图1.png、图2 → 参考图2.png」即属错误重排。
  URL 列只写纯文本 URL 字符串，禁止写成 `![](url)`、`![...](url)` 或其它会渲染图片的 Markdown。视频、音频表格同样只展示纯文本 URL，不得用 Markdown 媒体语法渲染。
- 时长、比例、音频生成（必须写「是」/`true`，不得写「否」或后期配音）和水印。
- 完整 `confirmation_fingerprint`。
- 预扣 20000 积分、返还规则、官方链接 24 小时有效期、本地产物/云端产物位置和 task_id 可追踪规则。

只有用户明确回复“确认”或“就按这份生成”后才能正式生成；正式命令必须同时传入 `--confirm-charge` 和对应的 `--user-confirmation`，且同一确认清单只能提交一次。确认表中「音频生成」一行的正确示例：`是`；错误示例：`否（后期叠加配音+BGM）`。

用户修改任意文字、标点、媒体、顺序或参数时，返回步骤 2 创建新清单并重新确认。不得手工修改现有清单。

### 4. 可选 dry-run

需要排查解释器、清单或 payload 时只使用 dry-run。它校验指纹并输出将提交的实际 payload，但绝不会请求 API。

Windows：

    python "scripts/seedance_video_gen.py" --agent-id "<AgentID>" --confirmation-file "<清单绝对路径>" --confirm-fingerprint "<完整指纹>" --dry-run

macOS / Linux：

    python "scripts/seedance_video_gen.py" --agent-id "<AgentID>" --confirmation-file "<清单绝对路径>" --confirm-fingerprint "<完整指纹>" --dry-run

dry-run 不得携带 `--confirm-charge` 或 `--user-confirmation`。检查 `api_request_sent` 必须为 `false`，并逐字核对 `request_payload.content`：首项是完整 prompt，后续媒体 URL、类型、角色、数量和顺序都与确认清单完全一致。

### 5. 正式生成

正式命令只传确认清单和指纹。不得再传 prompt、`--image`、`--video`、`--audio`、任一 expected count、`--duration`、`--ratio` 或 `--watermark`；脚本会拒绝覆盖。清单中 `generate_audio` 必须为 `true`（脚本会拒绝 `false`）。

Windows：

    python "scripts/seedance_video_gen.py" --agent-id "<AgentID>" --confirmation-file "<清单绝对路径>" --confirm-fingerprint "<完整指纹>" --confirm-charge --user-confirmation "确认"

macOS / Linux：

    python "scripts/seedance_video_gen.py" --agent-id "<AgentID>" --confirmation-file "<清单绝对路径>" --confirm-fingerprint "<完整指纹>" --confirm-charge --user-confirmation "确认"

长时间运行命令应使用脚本相对路径或已验证的绝对路径，timeout 不低于 2400 秒。进度写入 stderr，最终 JSON 写入 stdout。

脚本提交成功并返回 task_id 后，立即告诉用户：

> 视频任务已提交，task_id：<task_id>。我继续等待同一个任务的结果。

若 exec 返回 `Command still running` 和 sessionId，只用 `process.poll` 轮询同一个 sessionId，直到最终 JSON；不要再次执行生成命令。

若同一确认清单再次执行正式命令，脚本会返回原 task_id 或提交中的状态，不会再次发起 API 请求。

## 失败与重试规则

| 情况 | 允许操作 | 禁止操作 |
|---|---|---|
| Python 或脚本尚未启动 | 修正 python/python/py -3、绝对路径、shell 引号；运行 `--help` 或同一清单的 dry-run | 使用 test prompt；改动或删除媒体；创建试跑业务输入 |
| 准备清单返回校验错误 | 原样反馈；补齐真实媒体后重新准备并重新确认 | 降低 expected count；替换媒体；改成无素材模式 |
| 正式调用在 task_id 前返回 API/参数错误 | 把完整结果、扣费状态和下一步告知用户；如需重试，重新准备清单并重新确认 | 修改 prompt、媒体或生成参数后自动重试 |
| 提交结果不确定或显示 `SubmissionInProgress` | 使用 `--recover-submission <submission_key>` 只恢复查询；把未知状态和可能重复扣费风险告知用户 | 使用同一确认清单再次 POST，或把 `retry_eligible` 当成自动重试许可 |
| 用户确认需要重新生成 | 新建确认清单；若清单提示未知提交风险，额外传 `--confirm-retry-risk`，再使用新的用户确认 POST | 复用旧 `confirmation_file`、旧确认指纹或旧 submission_key |
| 已返回 task_id，轮询中断或超时 | 查询或轮询同一 task_id；检查本地目录 | 再次运行生成命令 |
| 用户主动要求改输入 | 新建清单、展示新指纹、重新确认 | 复用旧确认或直接修改旧清单 |

即使只改一个标点、一个 URL 或两项媒体的顺序，也属于新输入，必须重新确认。

## 历史任务优先

正式生成前，脚本会检查 `seedance_video_tasks.json` 中缺少本地视频路径的历史任务。发现后先查询这些 task_id，告知用户对应 prompt、task_id、状态和本地路径，然后停止新生成并询问是否继续。

如果历史任务的官方链接已过期，查询结果必须原样返回「官方链接已过期，请到本地产物或云端产物中查看」，不得把过期链接当作可用视频，也不得以此自动重新生成。用户之后明确提出新生成需求时，仍必须单独准备新清单并重新确认。

历史查询只负责查询，不会重新生成。用户确认需要重新生成后，必须重新准备新的 `confirmation_file` 和 `confirmation_fingerprint`；旧确认只能对应一次 POST。

恢复未知提交：

    python "scripts/seedance_video_gen.py" --agent-id "<AgentID>" --recover-submission "<submission_key>"

本地产物对账（只读远端、只更新本地 JSON，不发起 POST）：

    python "scripts/seedance_video_gen.py" --agent-id "<AgentID>" --reconcile-artifacts

对账结果中的 `untracked_artifacts` 表示目录中存在但尚未能唯一关联到 task_id 的旧视频；不能凭文件名猜测归属，应先人工确认后再补写任务记录。

查询指定历史任务：

    python "scripts/seedance_video_gen.py" --agent-id "<AgentID>" --query-history --task-id "<task_id>"

Windows 将解释器和脚本路径替换为前述 Windows 形式。

## 输出与审计

默认保存目录：

- main：`./codex-data/workspace/createContent/video/`
- 其他智能体：`CODEX_ARTIFACT_DIR/agents/<AgentID>/video/`

目录优先级：`--output-dir`、`VIDEO_OUTPUT_DIR`、智能体默认目录、`./createContent/video/`。

成功、失败、超时、提交未知和链接过期结果都会返回 `result_report`，其中包含本次状态、预扣积分说明、链接有效期和重新生成必须新确认的要求。成功结果以本地 `video_url` 为主，同时返回 `local_video_path`、`output_dir`、`original_video_url`、`official_link_expires_at`、task_id、confirmation_id 和 confirmation_fingerprint。官方链接过期时返回 `status=official_link_expired`、`requires_regeneration=false` 和本地产物/云端产物提示；JSON 中所有本地路径字段（含 `confirmation_file`、`video_url`、`local_video_path`、`output_dir`、`task_records_path`）都必须是展开后的绝对路径，禁止返回相对路径或仅文件名；向用户展示时同样使用完整绝对路径。

任务记录保存在：

    scripts/seedance_video_tasks.json

新记录包含实际 prompt、prompt_sha256、图片/视频/音频 URL 与各自数量、confirmation_id、confirmation_fingerprint 和 task_id，可用于审计真实请求。不得根据聊天内容事后重构并声称是实际请求；需要核对时使用确认清单、任务记录或 dry-run 输出。

## 参数摘要

| 参数 | 用途 |
|---|---|
| `--prepare-confirmation` | 离线固化待确认输入，不请求 API |
| `--expected-image-count` | 必填的预期图片数；没有则为 0 |
| `--expected-video-count` | 必填的预期视频数；没有则为 0 |
| `--expected-audio-count` | 必填的预期音频数；没有则为 0 |
| `--image` | 准备阶段的图片 URL，可重复并保留顺序 |
| `--video` | 准备阶段的视频 URL，可重复并保留顺序 |
| `--audio` | 准备阶段的参考音频 URL，可重复并保留顺序；与是否生成声音无关 |
| `--confirmation-file` | 正式生成或 dry-run 使用的确认清单 |
| `--confirm-fingerprint` | 用户确认时展示的完整 SHA-256 指纹 |
| `--dry-run` | 校验并展示实际 payload，不请求 API |
| `--confirm-charge` | 正式生成必填，只能在用户明确确认费用、24 小时链接有效期和当前清单后传入 |
| `--user-confirmation` | 必须是用户明确回复的 `确认` 或 `就按这份生成` |
| `--query-history` | 查询既有任务，不提交新任务 |
| `--output-dir` | 覆盖默认本地保存目录 |
| `--poll-interval` | 轮询间隔，默认 60 秒 |
| `--max-wait` | 最大等待时间，默认 1800 秒 |
