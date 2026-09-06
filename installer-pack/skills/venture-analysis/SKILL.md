---
name: venture-analysis
description: 创业投资分析工具，提供商业计划评估、财务建模、估值分析、尽职调查功能。帮助投资者理性评估早期项目投资机会，控制投资风险。
version: 1.0.0
---

# 创业投资技能

创业投资分析工具，提供商业计划评估、财务建模、估值分析、尽职调查功能。

## When to Use

当用户请求以下操作时调用此skill：
- 评估创业项目投资价值
- 分析商业计划可行性
- 进行早期项目估值
- 制作财务预测模型
- 执行尽职调查
- 评估投资风险

---

## 🔍 数据获取规范

### 必须使用 `web-search-extraction` 技能的场景

以下情况**必须**先使用 `web-search-extraction` 技能获取最新信息：

| 数据类型 | 示例 | 处理方式 |
|---------|------|---------|
| 行业数据 | "某行业最新市场规模" | `web-search-extraction` 获取 |
| 竞品信息 | "某公司的竞争对手" | `web-search-extraction` 获取 |
| 融资动态 | "某赛道最新融资情况" | `web-search-extraction` 获取 |
| 政策影响 | "某行业监管政策变化" | `web-search-extraction` 获取 |

### 使用示例

```
用户：帮我评估这个AI项目

步骤1：使用 web-search-extraction 技能获取行业数据
Skill: web-search-extraction
Args: "AI人工智能 2024 2025 市场规模 融资趋势"

步骤2：用脚本进行评估分析
python scripts/business_evaluator.py --industry "AI" ...
```

### 注意

- 创业投资分析需要结合最新行业数据
- **脚本提供分析框架，实时数据必须通过搜索获取**
- 涉及具体估值倍数时，要参考最新市场案例

## Core Modules

### 1. Business Plan Evaluator (商业计划评估器)
商业模式画布分析、竞争力评估

### 2. Financial Modeler (财务建模器)
收入预测、成本结构、现金流模型

### 3. Valuation Analyzer (估值分析器)
早期项目估值方法

### 4. Due Diligence Checklist (尽职调查清单)
投资前核查要点

---

## Workflow 1: Business Plan Evaluation (商业计划评估)

### 商业模式画布分析

**价值主张**
- 解决什么痛点？
- 目标客户是谁？
- 差异化优势？

**市场分析**
- TAM（总市场规模）
- SAM（可服务市场）
- SOM（可获得市场）

**竞争格局**
- 直接竞争对手
- 间接竞争对手
- 进入壁垒

**盈利模式**
- 收入来源
- 成本结构
- 盈亏平衡点

### 评估项目

```bash
python scripts/business_evaluator.py \
    --industry "新能源" \
    --tam 10000000000 \
    --team-score 8 \
    --product-score 7 \
    --market-score 6
```

---

## Workflow 2: Financial Modeling (财务建模)

### 预测模型

**收入预测**
- 用户增长曲线
- ARPU（客单价）
- 复购率
- 收入 = 用户数 × ARPU × 复购率

**成本结构**
- 固定成本（人员、租金）
- 变动成本（原材料、营销）
- 边际成本趋势

**现金流预测**
- 经营性现金流
- 投资性现金流
- 融资需求

### 制作财务模型

```bash
python scripts/financial_model.py \
    --years 5 \
    --initial-users 1000 \
    --growth-rate 50 \
    --arpu 100 \
    --cac 50 \
    --burn-rate 100000
```

---

## Workflow 3: Valuation Analysis (估值分析)

### 早期项目估值方法

**可比公司法**
- 找到同行业已融资公司
- 对比估值倍数（P/S、P/E）
- 考虑阶段折扣

**风险投资法**
- 预测退出时的估值
- 考虑稀释比例
- 计算目标回报率
- 倒推当前估值

**Scorecard法**
- 团队（30%）
- 产品（25%）
- 市场（20%）
- 竞争（15%）
- 时机（10%）

### 进行估值

```bash
python scripts/valuation_analyzer.py \
    --stage "天使轮" \
    --revenue 0 \
    --team-score 8 \
    --market-growth 30 \
    --target-return 10
```

---

## Workflow 4: Due Diligence (尽职调查)

### 核查清单

**法律尽调**
- [ ] 公司注册文件
- [ ] 股权结构
- [ ] 知识产权
- [ ] 重大合同
- [ ] 诉讼情况

**财务尽调**
- [ ] 财务报表
- [ ] 银行流水
- [ ] 税务合规
- [ ] 关联交易
- [ ] 债务情况

**业务尽调**
- [ ] 核心团队背景
- [ ] 技术验证
- [ ] 客户访谈
- [ ] 供应商访谈
- [ ] 竞品分析

### 生成尽调清单

```bash
python scripts/due_diligence.py --stage "A轮" --output dd_checklist.md
```

---

## 投资风险评估

### 风险等级

| 风险类型 | 权重 | 评估要点 |
|----------|------|----------|
| 团队风险 | 30% | 创始人能力、团队完整性 |
| 市场风险 | 25% | 市场规模、增长性 |
| 产品风险 | 20% | 技术可行性、差异化 |
| 竞争风险 | 15% | 壁垒、护城河 |
| 财务风险 | 10% | 烧钱速度、融资能力 |

### 投资建议矩阵

| 综合评分 | 建议 | 投资比例 |
|----------|------|----------|
| 85-100 | 强烈推荐 | 可投上限 |
| 70-84 | 推荐 | 正常投资 |
| 55-69 | 谨慎 | 减少投资 |
| <55 | 不推荐 | 不投资 |

---

## 标准输出格式

### 🧭 投资官视角

#### 一、核心结论
（投或不投，估值区间）

#### 二、背后逻辑
- 商业模式分析
- 财务预测依据
- 估值方法说明

#### 三、风险在哪里
- 最大风险点
- 失败概率评估
- 下行保护

#### 四、适合谁
- 风险承受能力
- 投资期限匹配
- 专业背景要求

#### 五、操作策略
- 投资金额建议
- 估值谈判区间
- 条款清单要点

#### 六、如果判断错了
- 退出机制
- 止损线
- 后续轮次策略

---

## 数据存储

| 文件 | 位置 |
|------|------|
| 商业评估 | `${CODEX_DATA_DIR:-./codex-data}/skills/venture-analysis/business_evaluations.json` |
| 财务模型 | `${CODEX_DATA_DIR:-./codex-data}/skills/venture-analysis/financial_models.json` |
| 估值分析 | `${CODEX_DATA_DIR:-./codex-data}/skills/venture-analysis/valuations.json` |
| 尽调清单 | `${CODEX_DATA_DIR:-./codex-data}/skills/venture-analysis/due_diligence/` |

**跨平台说明：**
- 默认存储在用户主目录下的 `codex-data` 文件夹
- 可通过环境变量 `CODEX_DATA_DIR` 自定义存储位置
- Windows: `C:\Users\<用户名>\codex-data\`
- macOS/Linux: `./codex-data/`

---

## Important Notes

- 早期投资高风险，单笔不超过可投资资产的10%
- 建议分散投资多个项目
- 做好全部亏损的心理准备
- 关注退出路径（IPO/并购/股权转让）
- 所有分析仅供参考，不构成投资建议
