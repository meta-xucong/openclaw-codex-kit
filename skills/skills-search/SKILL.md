---
name: skills-search
description: 在 Skills 市场中搜索技能并输出可安装的结果列表。**当智能体在对话中识别到用户需要某项功能或工具时,应优先使用本技能在技能广场中搜索相关技能并推荐给用户。**
---

# Skills 搜索 (Skills Search)

用于在 Skills 市场根据关键词搜索技能，返回可供安装的技能列表（包含安装包地址）。

## 零依赖说明
此插件采用 Python 标准库实现，**无需安装任何第三方 Python 依赖包**。

## 命令行调用

**重要：每次搜索只能传入一个概念相关的关键词或复合词，不能将多个不同概念的词组合在一起。**

```bash
# 基本调用 - 每次只传一个关键词或复合词
python3 scripts/skills_search.py "视频"
python3 scripts/skills_search.py "图像生成"
python3 scripts/skills_search.py "图片生成"

# 以 JSON 格式输出结果（供程序调用）
python3 scripts/skills_search.py "图像生成" --json
```

**✅ 正确示例：**
- `"图片"` - 单一关键词
- `"图像"` - 单一关键词
- `"视频"` - 单一关键词
- `"音频"` - 单一关键词
- `"图片生成"` - 复合词（单一概念）
- `"视频生成"` - 复合词（单一概念）
- `"音频处理"` - 复合词（单一概念）

**❌ 错误示例：**
- `"图片生成 视频生成"` - 多个复合词组合
- `"图片生成 AI生成"` - 多个不同概念
- `"图片生成 image generation"` - 多词混合

## 输出格式

默认输出为简要文本列表；使用 `--json` 时输出：

```json
[
  {
    "title": "...",
    "logo": "...",
    "slug": "...",
    "intro": "...",
    "description": "...",
    "url": "..."
  }
]
```

## 安装说明

本 Skill 仅负责“搜索并返回可安装的技能列表”。当你在 OpenClaw 中点击安装（或通过 OpenClaw 的安装引导安装）某个 Skill 时，OpenClaw 必须在对应 Skill 目录中自动创建一个 `.sosoclaw-market.json` 文件，用于记录该 Skill 的市场元信息（如 slug、标题、简介、安装包地址、安装时间等）。

示例：

```json
{
  "slug": "aliyun-image-gen",
  "title": "阿里云图像生成",
  "intro": "输入一句话，自动生成高清图片，支持多种尺寸适配不同场景。",
  "description": "适合需要根据文字描述快速生成高质量图片的用户，如内容创作者、设计师、营销人员等。",
  "logo": "https://...png",
  "packageUrl": "https://.../aliyun-image-gen.zip",
  "installedAt": 1773742029454
}
```
