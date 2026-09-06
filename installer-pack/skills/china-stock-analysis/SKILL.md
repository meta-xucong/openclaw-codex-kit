---
name: china-stock-analysis
description: A股全能分析工具，提供实时行情、分时量能分析、股票筛选、个股深度财务分析、行业对比和估值计算功能。基于价值投资理论，使用akshare获取财务数据，新浪财经获取实时行情，适合各类A股投资者。
---

# China Stock Analysis Skill

中国A股全能分析工具，整合实时行情与深度财务分析，面向各类A股投资者。

## When to Use

当用户请求以下操作时调用此skill：
- 查询A股实时行情
- 分析分时量能、主力动向
- 分析某只A股基本面
- 筛选符合条件的股票
- 对比多只股票或行业内股票
- 计算股票估值或内在价值
- 查看股票的财务健康状况
- 检测财务异常风险

---

## 🔍 数据获取规范

### 必须使用 `web-search-extraction` 技能的场景

以下情况**禁止**直接使用脚本，必须先使用 `web-search-extraction` 技能获取最新数据：

| 数据类型 | 示例 | 处理方式 |
|---------|------|---------|
| 实时股价 | "茅台现在多少钱" | `web-search-extraction` → 脚本验证 |
| 最新财报 | "宁德时代Q3业绩" | `web-search-extraction` 获取 |
| 公司公告 | "比亚迪最新公告" | `web-search-extraction` 获取 |
| 行业新闻 | "光伏行业政策" | `web-search-extraction` 获取 |
| 市场数据 | "北向资金流向" | `web-search-extraction` 获取 |

### 使用示例

```
用户：茅台现在股价多少？

步骤1：使用 web-search-extraction 技能
Skill: web-search-extraction
Args: "贵州茅台 600519 实时股价"

步骤2：用脚本验证和补充分析
python scripts/realtime_quote.py 600519
```

## Prerequisites

### Python环境要求
```bash
pip install akshare pandas numpy
```

### 依赖检查
在执行任何分析前，先检查akshare是否已安装：
```bash
python -c "import akshare; print(akshare.__version__)"
```

如果未安装，提示用户安装：
```bash
pip install akshare
```

## Core Modules

### 1. Real-time Quote (实时行情)
A股实时行情查询与分时量能分析
- 数据源：新浪财经（延迟~3秒）
- 支持：沪市、深市、北交所
- 功能：实时价格、分时量能、主力动向识别

### 2. Stock Screener (股票筛选器)
筛选符合条件的股票

### 3. Financial Analyzer (财务分析器)
个股深度财务分析

### 4. Industry Comparator (行业对比)
同行业横向对比分析

### 5. Valuation Calculator (估值计算器)
内在价值测算与安全边际计算

### 6. Technical Analysis (技术分析器)
K线技术指标计算与形态识别
- 支持指标：MACD、KDJ、RSI、均线系统、布林带
- 功能：趋势判断、支撑阻力识别、交易信号生成

---

## Workflow 1: Real-time Quote (实时行情)

快速查询A股实时行情和分时量能分析。

### 实时行情查询

```bash
# 单只股票
python scripts/realtime_quote.py 600519

# 多只股票
python scripts/realtime_quote.py 600519 000858 002304

# JSON输出
python scripts/realtime_quote.py 600519 --json
```

### 分时量能分析

```bash
# 包含分时量能分析
python scripts/realtime_quote.py 600519 --minute

# 多只股票分时分析
python scripts/realtime_quote.py 600519 000858 --minute
```

**分时量能指标说明：**

| 时段 | 说明 | 信号 |
|------|------|------|
| 早盘30分 (9:30-10:00) | 主力早盘动作 | >30%为抢筹信号，>40%为强势介入 |
| 尾盘30分 (14:30-15:00) | 尾盘异动 | >25%为抢筹或出货信号 |
| 放量时段 TOP 10 | 成交量最大的10个分钟 | 识别主力建仓/出货时机 |

**主力动向信号：**
- 🔥 早盘主力抢筹明显（早盘占比>30%）
- 🔥 早盘放量异常，主力强势介入（早盘占比>40%）
- 🔥 尾盘大幅放量，可能有主力抢筹或出货（尾盘占比>25%）
- 🔥 封板状态，关注封单量

### 股票代码格式

直接使用6位数字代码，系统自动识别市场：
- **沪市**: 6开头 (如 600519)
- **深市**: 0或3开头 (如 002446, 300001)
- **北交所**: 8或4开头

---

## Workflow 2: Stock Screening (股票筛选)

用户请求筛选股票时使用。

### Step 1: Collect Screening Criteria

向用户询问筛选条件。提供以下选项供用户选择或自定义：

**估值指标：**
- PE (市盈率): 例如 PE < 15
- PB (市净率): 例如 PB < 2
- PS (市销率): 例如 PS < 3

**盈利能力：**
- ROE (净资产收益率): 例如 ROE > 15%
- ROA (总资产收益率): 例如 ROA > 8%
- 毛利率: 例如 > 30%
- 净利率: 例如 > 10%

**成长性：**
- 营收增长率: 例如 > 10%
- 净利润增长率: 例如 > 15%
- 连续增长年数: 例如 >= 3年

**股息：**
- 股息率: 例如 > 3%
- 连续分红年数: 例如 >= 5年

**财务安全：**
- 资产负债率: 例如 < 60%
- 流动比率: 例如 > 1.5
- 速动比率: 例如 > 1

**筛选范围：**
- 全A股
- 沪深300成分股
- 中证500成分股
- 创业板/科创板
- 用户自定义列表

### Step 2: Execute Screening

```bash
python scripts/stock_screener.py \
    --scope "hs300" \
    --pe-max 15 \
    --roe-min 15 \
    --debt-ratio-max 60 \
    --dividend-min 2 \
    --output screening_result.json
```

**参数说明：**
- `--scope`: 筛选范围 (all/hs300/zz500/cyb/kcb/custom:600519,000858,...)
- `--pe-max/--pe-min`: PE范围
- `--pb-max/--pb-min`: PB范围
- `--roe-min`: 最低ROE
- `--growth-min`: 最低增长率
- `--debt-ratio-max`: 最大资产负债率
- `--dividend-min`: 最低股息率
- `--output`: 输出文件路径

### Step 3: Present Results

读取 `screening_result.json` 并以表格形式呈现给用户：

| 代码 | 名称 | PE | PB | ROE | 股息率 | 评分 |
|------|------|----|----|-----|--------|------|
| 600519 | 贵州茅台 | 25.3 | 8.5 | 30.2% | 2.1% | 85 |

---

## Workflow 3: Stock Analysis (个股分析)

用户请求分析某只股票时使用。

### Step 1: Collect Stock Information

询问用户：
1. 股票代码或名称
2. 分析深度级别：
   - **摘要级**：关键指标 + 投资结论（1页）
   - **标准级**：财务分析 + 估值 + 行业对比 + 风险提示
   - **深度级**：完整调研报告，包含历史数据追踪

### Step 2: Fetch Stock Data

```bash
python scripts/data_fetcher.py \
    --code "600519" \
    --data-type all \
    --years 5 \
    --output stock_data.json
```

**参数说明：**
- `--code`: 股票代码
- `--data-type`: 数据类型 (basic/financial/valuation/holder/all)
- `--years`: 获取多少年的历史数据
- `--output`: 输出文件

### Step 3: Run Financial Analysis

```bash
python scripts/financial_analyzer.py \
    --input stock_data.json \
    --level standard \
    --output analysis_result.json
```

**参数说明：**
- `--input`: 输入的股票数据文件
- `--level`: 分析深度 (summary/standard/deep)
- `--output`: 输出文件

### Step 4: Calculate Valuation

```bash
python scripts/valuation_calculator.py \
    --input stock_data.json \
    --methods dcf,ddm,relative \
    --discount-rate 10 \
    --growth-rate 8 \
    --output valuation_result.json
```

**参数说明：**
- `--input`: 股票数据文件
- `--methods`: 估值方法 (dcf/ddm/relative/all)
- `--discount-rate`: 折现率(%)
- `--growth-rate`: 永续增长率(%)
- `--margin-of-safety`: 安全边际(%)
- `--output`: 输出文件

### Step 5: Generate Report

读取分析结果，参考 `templates/analysis_report.md` 模板生成中文分析报告。

报告结构（标准级）：
1. **公司概况**：基本信息、主营业务
2. **财务健康**：资产负债表分析
3. **盈利能力**：杜邦分析、利润率趋势
4. **成长性分析**：营收/利润增长趋势
5. **估值分析**：DCF/DDM/相对估值
6. **风险提示**：财务异常检测、股东减持
7. **投资结论**：综合评分、操作建议

---

## Workflow 4: Industry Comparison (行业对比)

### Step 1: Collect Comparison Targets

询问用户：
1. 目标股票代码（可多个）
2. 或者：行业分类 + 对比数量

### Step 2: Fetch Industry Data

```bash
python scripts/data_fetcher.py \
    --codes "600519,000858,002304" \
    --data-type comparison \
    --output industry_data.json
```

或按行业获取：
```bash
python scripts/data_fetcher.py \
    --industry "白酒" \
    --top 10 \
    --output industry_data.json
```

### Step 3: Generate Comparison

```bash
python scripts/financial_analyzer.py \
    --input industry_data.json \
    --mode comparison \
    --output comparison_result.json
```

### Step 4: Present Comparison Table

| 指标 | 贵州茅台 | 五粮液 | 洋河股份 | 行业均值 |
|------|----------|--------|----------|----------|
| PE | 25.3 | 18.2 | 15.6 | 22.4 |
| ROE | 30.2% | 22.5% | 20.1% | 18.5% |
| 毛利率 | 91.5% | 75.2% | 72.3% | 65.4% |
| 评分 | 85 | 78 | 75 | - |

---

## Workflow 5: Valuation Calculator (估值计算)

### Step 1: Collect Valuation Parameters

询问用户估值参数（或使用默认值）：

**DCF模型参数：**
- 折现率 (WACC): 默认10%
- 预测期: 默认5年
- 永续增长率: 默认3%

**DDM模型参数：**
- 要求回报率: 默认10%
- 股息增长率: 使用历史数据推算

**相对估值参数：**
- 对比基准: 行业均值 / 历史均值

### Step 2: Run Valuation

```bash
python scripts/valuation_calculator.py \
    --code "600519" \
    --methods all \
    --discount-rate 10 \
    --terminal-growth 3 \
    --forecast-years 5 \
    --margin-of-safety 30 \
    --output valuation.json
```

### Step 3: Present Valuation Results

| 估值方法 | 内在价值 | 当前价格 | 安全边际价格 | 结论 |
|----------|----------|----------|--------------|------|
| DCF | ¥2,150 | ¥1,680 | ¥1,505 | 低估 |
| DDM | ¥1,980 | ¥1,680 | ¥1,386 | 低估 |
| 相对估值 | ¥1,850 | ¥1,680 | ¥1,295 | 合理 |

---

## Workflow 6: Technical Analysis (技术分析)

### 技术分析示例

```bash
python scripts/technical_analysis.py \
    --code 000001 \
    --period daily \
    --days 100
```

**输出指标：**
- 均线系统：MA5/MA10/MA20/MA60
- MACD：DIF/DEA/MACD柱状图
- RSI：相对强弱指标
- KDJ：随机指标
- 布林带：上轨/中轨/下轨
- 支撑阻力位
- 综合技术评分

---

## Financial Anomaly Detection (财务异常检测)

在分析过程中自动检测以下异常信号：

### 检测项目

1. **应收账款异常**
   - 应收账款增速 > 营收增速 × 1.5
   - 应收账款周转天数大幅增加

2. **现金流背离**
   - 净利润持续增长但经营现金流下降
   - 现金收入比 < 80%

3. **存货异常**
   - 存货增速 > 营收增速 × 2
   - 存货周转天数大幅增加

4. **毛利率异常**
   - 毛利率波动 > 行业均值波动 × 2
   - 毛利率与同行严重偏离

5. **关联交易**
   - 关联交易占比过高（> 30%）

6. **股东减持**
   - 大股东近期减持公告
   - 高管集中减持

### 风险等级

- 🟢 **低风险**：无明显异常
- 🟡 **中风险**：1-2项轻微异常
- 🔴 **高风险**：多项异常或严重异常

---

## A-Share Specific Analysis (A股特色分析)

### 政策敏感度

根据行业分类提供政策相关提示：
- 房地产：房住不炒政策
- 新能源：补贴政策变化
- 医药：集采政策影响
- 互联网：反垄断、数据安全

### 股东结构分析

1. 控股股东类型（国企/民企/外资）
2. 股权集中度
3. 近期增减持情况
4. 质押比例

---

## Output Format

### JSON输出格式

所有脚本输出JSON格式，便于后续处理：

```json
{
  "code": "600519",
  "name": "贵州茅台",
  "analysis_date": "2025-01-25",
  "level": "standard",
  "summary": {
    "score": 85,
    "conclusion": "低估",
    "recommendation": "建议关注"
  },
  "financials": { ... },
  "valuation": { ... },
  "risks": [ ... ]
}
```

### Markdown报告

生成结构化的中文Markdown报告，参考 `templates/analysis_report.md`。

---

## 标准输出格式

### 🧭 投资官视角

#### 一、核心结论
（一句话说清投资结论：高估/低估/合理，建议买入/持有/观望）

#### 二、背后逻辑
- 财务数据分析依据
- 估值计算逻辑
- 行业对比结果
- 技术面信号（如有）

#### 三、风险在哪里
- 财务异常风险
- 估值偏高风险
- 行业政策风险
- 市场系统性风险

#### 四、适合谁
- 风险承受能力匹配
- 投资期限匹配
- 资金规模匹配

#### 五、操作策略
- 买入价位区间
- 目标价位
- 止损线设置
- 仓位建议

#### 六、如果判断错了
- 止损退出条件
- 基本面恶化信号
- 估值修正应对
- Plan B方案

---

## 数据存储

| 文件 | 位置 |
|------|------|
| 股票数据 | `${CODEX_DATA_DIR:-./codex-data}/skills/china-stock-analysis/stock_data/` |
| 分析结果 | `${CODEX_DATA_DIR:-./codex-data}/skills/china-stock-analysis/analysis/` |
| 筛选结果 | `${CODEX_DATA_DIR:-./codex-data}/skills/china-stock-analysis/screening/` |
| 估值结果 | `${CODEX_DATA_DIR:-./codex-data}/skills/china-stock-analysis/valuation/` |

**跨平台说明：**
- 默认存储在用户主目录下的 `codex-data` 文件夹
- 可通过环境变量 `CODEX_DATA_DIR` 自定义存储位置
- Windows: `C:\Users\<用户名>\codex-data\`
- macOS/Linux: `./codex-data/`

---

## Error Handling

### 网络错误
如果数据获取失败，提示用户：
1. 检查网络连接
2. 稍后重试（可能是接口限流）
3. 尝试更换数据源

**数据源说明：**
- **实时行情**：新浪财经接口（`hq.sinajs.cn`），延迟约3秒
- **财务数据**：akshare库（东方财富数据源）
- **分时数据**：新浪财经K线接口，延迟约1分钟

### 股票代码无效
提示用户检查股票代码是否正确，提供可能的匹配建议。

### 数据不完整
对于新上市股票或财务数据不完整的情况，说明数据限制并基于可用数据进行分析。

---

## Best Practices

1. **数据时效性**：财务数据以最新季报/年报为准，价格数据为当日收盘价
2. **投资建议**：所有分析仅供参考，不构成投资建议
3. **风险提示**：始终包含风险提示，特别是财务异常检测结果
4. **对比分析**：单只股票分析时，自动包含行业均值对比

## Important Notes

- 所有分析基于公开财务数据，不涉及任何内幕信息
- 估值模型的参数假设对结果影响较大，需向用户说明
- A股市场受政策影响较大，定量分析需结合定性判断
