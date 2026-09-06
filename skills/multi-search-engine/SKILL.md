---
name: "multi-search-engine"
description: "【强制】所有网络搜索必须使用本技能。聚合9个国内可直接访问的搜索引擎，支持高级搜索语法、时间筛选、站内搜索和WolframAlpha知识查询。无需API密钥。当用户需要搜索信息、查找资料、调研市场、竞品情报或进行任何数据搜集时触发。"
---

# 多引擎搜索 v2.1.0

> ⚠️ **重要：所有网络搜索任务必须使用本技能**，禁止直接调用其他搜索方式。

聚合国内可直接访问的搜索引擎，为市场调研和情报搜集提供基础设施。

## 全网数据搜集工作流（SOP）

> **重要提示**：本技能仅提供搜索策略和关键词规划，**实际网页搜索必须使用 `web-search-extraction` 技能**。

当执行市场调研或竞品情报搜集时，必须遵循以下标准操作流程：

### Step 1: 需求解析
分析用户问题的核心要素：
- **目标对象**：要找什么？（产品/公司/报告/数据/文献）
- **范围边界**：地域、时间、行业限制
- **输出要求**：列表/对比/深度分析
- **信息深度**：仅需清单 / 需要详细信息 / 需要深度分析

**输出**：明确搜索任务清单

### Step 2: 关键词拆解（3分钟）
将问题拆解为**至少3个不同维度**的搜索关键词：

**原则**：
- 同义词扩展：产品名 → 品类名 → 功能描述
- 场景扩展：通用词 → 场景词 → 痛点词
- 来源扩展：新闻 → 知乎 → 微信 → 报告

**示例**："国内有哪些OpenClaw相关产品"
| 维度 | 关键词 | 目的 |
|------|--------|------|
| 直接 | `OpenClaw 竞品 替代品` | 找直接竞品 |
| 品类 | `AI Agent 开发平台 国内` | 找同类产品 |
| 功能 | `智能体搭建工具 低代码` | 找功能相似产品 |
| 对比 | `OpenClaw 类似产品 对比` | 找对比分析文章 |
| 场景 | `AI助手 工作流自动化 国内` | 找场景替代方案 |

**输出**：5-8个搜索关键词清单

### Step 3: 多引擎交叉搜索（10分钟）
**每个关键词至少用2个不同引擎搜索**

**搜索矩阵**：
| 引擎 | 用途 | 优先级 |
|------|------|--------|
| 百度 | 中文综合结果 | P0 |
| Bing INT | 国际视角/英文内容 | P0 |
| 知乎站内 | 专业讨论/深度分析 | P1 |
| 微信公众号 | 行业文章/产品评测 | P1 |
| 头条 | 新闻动态/最新信息 | P2 |

**执行标准**：
- 每个关键词至少搜2个引擎
- 每个搜索结果页查看前10条
- 记录有效信息的来源URL
- 截图或复制关键信息原文

**输出**：原始搜索结果清单（带来源）

### Step 4: 信息提取（10分钟）
**按统一字段提取信息**：

**产品/公司类信息字段**：
```
- 产品名称：（官方名称）
- 所属公司：（公司全称）
- 产品定位：（一句话描述）
- 核心功能：（3-5个主要功能）
- 目标用户：（主要客群）
- 价格策略：（定价模式/价格区间）
- 差异化特点：（与竞品的主要区别）
- 信息来源：（URL链接）
- 可信度评级：（A/B/C/D）
```

**报告/数据类信息字段**：
```
- 报告标题：
- 发布机构：
- 发布时间：
- 核心数据：（关键数字）
- 主要结论：（3-5条）
- 信息来源：（URL/PDF链接）
- 可信度评级：（A/B/C/D）
```

**可信度评级标准**：
| 等级 | 标准 | 示例 |
|------|------|------|
| A | 官方数据/权威机构 | 公司官网、艾瑞报告、Gartner |
| B | 专业媒体/分析师 | 36氪、虎嗅、知乎专栏 |
| C | 用户评论/社群讨论 | 知乎回答、脉脉、微信群 |
| D | 推测/传闻 | 无明确来源的信息 |

**输出**：结构化信息提取表

### Step 5: 信息整合（5分钟）
**去重规则**：
- 同一产品在不同来源出现 → 合并信息，标注多来源验证
- 同一信息多次出现 → 取最高可信度来源

**验证规则**：
- 关键信息（如融资额、用户数）需至少2个独立来源验证
- 单来源信息标注"待验证"

**补全规则**：
- 信息缺口 > 30% → 补充新的搜索关键词
- 关键字段缺失 → 针对性搜索补全

**分类规则**：
- 按产品类型分类（直接竞品/间接竞品/潜在竞品）
- 按信息类型分类（产品信息/市场数据/用户评价/行业分析）

**输出**：整合后的信息分类表

### Step 6: 结构化输出（5分钟）
**必须包含的章节**：

```markdown
## 搜索结果汇总

### 执行摘要
- 搜索关键词：[列出使用的关键词]
- 搜索范围：[引擎/时间范围]
- 核心发现：[3-5条关键结论]

### [分类标题，如：直接竞品清单]
| 名称 | 公司 | 定位 | 核心功能 | 来源 | 可信度 |
|------|------|------|----------|------|--------|
| ... | ... | ... | ... | [链接] | A/B/C/D |

### 信息缺口
- [列出未找到或待验证的信息]

### 建议下一步
- [基于信息缺口提出的建议]
```

**时间控制**：
- 简单查询（清单类）：总时间 ≤ 15分钟
- 标准查询（分析类）：总时间 ≤ 30分钟
- 深度查询（研究类）：总时间 ≤ 60分钟

## Search Engines

### 🟢 国内可直接访问（9个）
- **Baidu**: `https://www.baidu.com/s?wd={keyword}`
- **Bing CN**: `https://cn.bing.com/search?q={keyword}&ensearch=0`
- **Bing INT**: `https://cn.bing.com/search?q={keyword}&ensearch=1`
- **360**: `https://www.so.com/s?q={keyword}`
- **Sogou**: `https://sogou.com/web?query={keyword}`
- **WeChat**: `https://wx.sogou.com/weixin?type=2&query={keyword}`
- **Toutiao**: `https://so.toutiao.com/search?keyword={keyword}`
- **Jisilu**: `https://www.jisilu.cn/explore/?keyword={keyword}`
- **WolframAlpha**: `https://www.wolframalpha.com/input?i={keyword}`

## 使用示例

```javascript
// 基础搜索 - 百度
web_fetch({"url": "https://www.baidu.com/s?wd=python教程"})

// 国际搜索 - Bing国际版
web_fetch({"url": "https://cn.bing.com/search?q=machine+learning&ensearch=1"})

// 站内搜索
web_fetch({"url": "https://www.baidu.com/s?wd=site:zhihu.com+人工智能"})

// 文件类型限定
web_fetch({"url": "https://www.baidu.com/s?wd=市场报告+filetype:pdf"})

// 时间筛选（过去一周）
web_fetch({"url": "https://www.baidu.com/s?wd=AI新闻&tbs=qdr:w"})

// 微信公众号搜索
web_fetch({"url": "https://wx.sogou.com/weixin?type=2&query=产品经理"})

// 头条资讯搜索
web_fetch({"url": "https://so.toutiao.com/search?keyword=新能源"})

// 知识计算 - WolframAlpha
web_fetch({"url": "https://www.wolframalpha.com/input?i=100+USD+to+CNY"})
```

## Advanced Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `site:` | `site:github.com python` | Search within site |
| `filetype:` | `filetype:pdf report` | Specific file type |
| `""` | `"machine learning"` | Exact match |
| `-` | `python -snake` | Exclude term |
| `OR` | `cat OR dog` | Either term |

## Time Filters

| Parameter | Description |
|-----------|-------------|
| `tbs=qdr:h` | Past hour |
| `tbs=qdr:d` | Past day |
| `tbs=qdr:w` | Past week |
| `tbs=qdr:m` | Past month |
| `tbs=qdr:y` | Past year |

## 使用建议

### 搜索场景推荐

| 场景 | 推荐引擎 | 原因 |
|------|----------|------|
| 一般搜索 | Baidu / Bing CN | 中文结果丰富 |
| 国际内容 | Bing INT | 国内可访问的国际搜索 |
| 公众号文章 | WeChat | 微信生态内容 |
| 新闻资讯 | Toutiao | 实时热点 |
| 投资研究 | Jisilu | 专业投资社区 |
| 知识计算 | WolframAlpha | 数学、换算、数据查询 |

### 高级搜索技巧

**站内搜索**: `site:zhihu.com 人工智能`
**文件类型**: `filetype:pdf 市场报告`
**精确匹配**: `"机器学习"`
**排除关键词**: `苹果 -手机`
**时间筛选**: `&tbs=qdr:w` (过去一周)

## 站内直达技巧

通过搜索引擎直接访问特定网站：

| 技巧 | 示例 | 效果 |
|------|------|------|
| `site:github.com` | `site:github.com python` | 在GitHub中搜索 |
| `site:zhihu.com` | `site:zhihu.com 人工智能` | 在知乎中搜索 |
| `site:csdn.net` | `site:csdn.net 教程` | 在CSDN中搜索 |
| `site:bilibili.com` | `site:bilibili.com 教程` | 在B站中搜索 |

## WolframAlpha Queries

- Math: `integrate x^2 dx`
- Conversion: `100 USD to CNY`
- Stocks: `AAPL stock`
- Weather: `weather in Beijing`

## 实战示例

### 示例1：搜集竞品清单

**用户提问**："帮我搜索一下国内关于OpenClaw相关产品的信息，有哪些产品"

**执行流程**：

1. **关键词拆解**：
   - `OpenClaw 竞品 替代品`
   - `AI Agent 开发平台 国内`
   - `智能体搭建工具 低代码`
   - `OpenClaw 类似产品`

2. **多引擎搜索**（每个关键词至少用2个引擎）：
   ```
   百度: OpenClaw 竞品 替代品
   Bing INT: OpenClaw alternatives China
   知乎: site:zhihu.com OpenClaw 竞品
   微信: OpenClaw 类似产品
   ```

3. **信息提取维度**：
   - 产品名称
   - 所属公司
   - 核心功能
   - 目标用户
   - 差异化特点

4. **输出格式**：
   ```markdown
   ## OpenClaw 国内竞品清单

   ### 直接竞品（AI Agent开发平台）
   | 产品 | 公司 | 核心功能 | 特点 |
   |------|------|----------|------|
   | 产品A | XX科技 | 可视化搭建、多模型支持 | 企业级 |
   | 产品B | YY智能 | 低代码、插件生态 | 开发者友好 |

   ### 间接竞品（相关工具）
   ...

   ### 市场洞察
   - 趋势1：...
   - 趋势2：...
   ```

### 示例2：行业报告搜集

**用户提问**："找一下2024年AI Agent行业的市场报告"

**关键词组合**：
- `2024 AI Agent 市场报告 filetype:pdf`
- `AI Agent 行业研究 艾瑞 易观`
- `AI Agent market report 2024 China`

**搜索策略**：
- 优先搜索PDF文件
- 关注艾瑞、易观、IDC等研究机构
- 中英文关键词结合

## Documentation

- `references/advanced-search.md` - 高级搜索指南
- `CHANGELOG.md` - 版本历史

## License

MIT
