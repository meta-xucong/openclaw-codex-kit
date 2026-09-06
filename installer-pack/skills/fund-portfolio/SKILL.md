---
name: fund-portfolio
description: 基金理财工具，提供基金筛选、组合配置、定投策略、风险评估功能。帮助用户构建适合自己的基金投资组合，实现财富稳健增值。
version: 1.0.0
---

# 基金理财技能

基金筛选、组合配置、定投策略、风险评估工具。帮助用户构建适合自己的基金投资组合。

## When to Use

当用户请求以下操作时调用此skill：
- 筛选符合条件的基金
- 构建基金投资组合
- 制定定投策略
- 评估基金风险
- 计算定投收益
- 优化现有基金组合

---

## 🔍 数据获取规范

### 必须使用 `web-search-extraction` 技能的场景

以下情况**必须**先使用 `web-search-extraction` 技能获取最新数据：

| 数据类型 | 示例 | 处理方式 |
|---------|------|---------|
| 实时净值 | "某基金今天净值" | `web-search-extraction` 获取 |
| 基金排名 | "最近收益好的基金" | `web-search-extraction` 获取 |
| 新发基金 | "最近有什么新基金" | `web-search-extraction` 获取 |
| 基金经理变动 | "某基金经理离职" | `web-search-extraction` 获取 |

### 使用示例

```
用户：最近有什么好的债券基金？

步骤1：使用 web-search-extraction 技能获取最新基金数据
Skill: web-search-extraction
Args: "债券基金 2024 2025 收益排名 推荐"

步骤2：如数据获取失败，基于专业知识提供推荐
- 说明数据获取情况
- 提供市场上口碑好的基金参考
- 给出筛选标准
```

### 注意

- `fund_screener.py` 依赖 akshare，可能因网络/接口问题无法获取数据
- **当脚本返回空时，必须使用 `web-search-extraction` 获取数据**
- 不能仅依赖脚本输出，要结合实时搜索

## Prerequisites

### Python环境要求
```bash
pip install akshare pandas numpy matplotlib
```

### 依赖检查
```bash
python -c "import akshare; print(akshare.__version__)"
```

## Core Modules

### 1. Fund Screener (基金筛选器)
根据条件筛选优质基金

### 2. Portfolio Builder (组合构建器)
根据风险偏好构建基金组合

### 3. SIP Calculator (定投计算器)
计算定投收益、制定定投计划

### 4. Risk Assessor (风险评估器)
评估基金风险指标

---

## Workflow 1: Fund Screening (基金筛选)

### 筛选维度

**基金类型：**
- 货币基金（低风险）
- 债券基金（中低风险）
- 混合基金（中风险）
- 股票基金（高风险）
- 指数基金（被动投资）
- QDII基金（海外投资）

**业绩指标：**
- 近1年收益率
- 近3年收益率
- 近5年收益率
- 年化收益率
- 最大回撤
- 夏普比率

**风险评估：**
- 波动率
- 下行风险
- 回撤修复时间

**费用指标：**
- 管理费
- 托管费
- 申购费
- 赎回费

### 执行筛选

```bash
python scripts/fund_screener.py \
    --type "混合" \
    --min-return-1y 10 \
    --max-drawdown 20 \
    --min-sharpe 1.0 \
    --output fund_result.json
```

---

## Workflow 2: Portfolio Building (组合构建)

### 风险等级划分

| 等级 | 描述 | 建议配置 |
|------|------|----------|
| 保守型 | 不能承受本金损失 | 货基40% + 债基50% + 混基10% |
| 稳健型 | 可接受小幅波动 | 债基40% + 混基40% + 股基20% |
| 平衡型 | 可接受中等波动 | 混基40% + 股基40% + 债基20% |
| 积极型 | 追求较高收益 | 股基60% + 混基30% + 债基10% |
| 激进型 | 可承受大幅波动 | 股基80% + 混基20% |

### 构建组合

```bash
python scripts/portfolio_builder.py \
    --risk-level "稳健型" \
    --amount 100000 \
    --period "3年" \
    --output portfolio.json
```

---

## Workflow 3: SIP Planning (定投计划)

### 定投策略

**普通定投：**
- 固定金额、固定时间
- 适合：新手、没时间关注市场

**智能定投：**
- 低位多投、高位少投
- 根据估值调整金额
- 适合：有一定经验的投资者

**价值平均策略：**
- 每期目标市值固定增长
- 自动实现低买高卖
- 适合：纪律性强的投资者

### 定投计算

```bash
python scripts/sip_calculator.py \
    --monthly 3000 \
    --years 5 \
    --expected-return 8 \
    --strategy "普通定投"
```

**输出示例：**
```
定投计划报告
==============
每月定投：3000元
定投期限：5年（60期）
预期年化：8%

累计投入：180,000元
预期市值：约220,000元
预期收益：+22.2%

最佳开始时间：每月1日或发薪日后3天
止盈建议：年化收益达到15%时考虑部分止盈
```

---

## Workflow 4: Risk Assessment (风险评估)

### 评估维度

**基金层面：**
- 历史最大回撤
- 波动率（标准差）
- 下行风险
- 回撤修复时间

**组合层面：**
- 集中度风险
- 相关性分析
- 尾部风险
- 压力测试

### 风险评估

```bash
python scripts/risk_assessor.py \
    --portfolio portfolio.json \
    --output risk_report.json
```

---

## 标准输出格式

### 🧭 投资官视角

#### 一、核心结论
（一句话说清推荐方案）

#### 二、背后逻辑
- 基金筛选依据
- 组合配置理由
- 数据支撑

#### 三、风险在哪里
- 市场风险
- 流动性风险
- 基金经理风险

#### 四、适合谁
- 风险承受能力匹配
- 投资期限匹配
- 资金规模匹配

#### 五、操作策略
- 具体配置比例
- 定投计划
- 调仓规则

#### 六、如果判断错了
- 止损线设置
- 退出策略
- Plan B方案

---

## 数据存储

| 文件 | 位置 |
|------|------|
| 基金组合 | `${CODEX_DATA_DIR:-./codex-data}/skills/fund-portfolio/portfolios.json` |
| 定投计划 | `${CODEX_DATA_DIR:-./codex-data}/skills/fund-portfolio/sip_plans.json` |
| 风险评估 | `${CODEX_DATA_DIR:-./codex-data}/skills/fund-portfolio/risk_reports.json` |

**跨平台说明：**
- 默认存储在用户主目录下的 `codex-data` 文件夹
- 可通过环境变量 `CODEX_DATA_DIR` 自定义存储位置
- Windows: `C:\Users\<用户名>\codex-data\`
- macOS/Linux: `./codex-data/`

---

## Important Notes

- 基金历史业绩不代表未来表现
- 定投不能规避基金投资的固有风险
- 建议分散投资，单只基金不超过总仓位30%
- 定期检视组合，至少每季度评估一次
- 所有建议仅供参考，不构成投资建议
