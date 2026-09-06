#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
基金组合风险评估器

评估基金组合的风险指标

Usage:
    python risk_assessor.py --portfolio portfolio.json
    python risk_assessor.py --funds "510300:40,159915:30,511880:30"
"""

import argparse
import json
import math
from datetime import datetime
from typing import Dict, List


# 模拟历史波动率数据（实际应从数据源获取）
FUND_VOLATILITY = {
    "510300": 18.5,   # 沪深300ETF
    "159915": 25.3,   # 创业板ETF
    "511880": 2.1,    # 货币ETF
    "511010": 4.5,    # 国债ETF
    "515880": 28.7,   # 科技ETF
    "512000": 22.4,   # 券商ETF
    "512690": 20.8,   # 酒ETF
    "510050": 17.2,   # 上证50ETF
    "default": 15.0
}


def calculate_portfolio_volatility(allocations: Dict[str, float]) -> float:
    """计算组合波动率（简化版，假设相关系数为0.8）"""
    weights = []
    volatilities = []
    
    for code, weight in allocations.items():
        weights.append(weight / 100)
        volatilities.append(FUND_VOLATILITY.get(code, FUND_VOLATILITY["default"]))
    
    # 简化计算：组合波动率 = sqrt(sum(w_i^2 * σ_i^2) + 2*ρ*sum(w_i*w_j*σ_i*σ_j))
    # 假设相关系数 ρ = 0.8
    rho = 0.8
    
    variance = 0
    n = len(weights)
    for i in range(n):
        for j in range(n):
            if i == j:
                variance += weights[i]**2 * volatilities[i]**2
            else:
                variance += rho * weights[i] * weights[j] * volatilities[i] * volatilities[j]
    
    return math.sqrt(variance)


def calculate_max_drawdown(volatility: float) -> float:
    """根据波动率估算最大回撤（简化：最大回撤 ≈ 2.5 * 年化波动率）"""
    return volatility * 2.5


def calculate_sharpe_ratio(expected_return: float, volatility: float, risk_free_rate: float = 2.5) -> float:
    """计算夏普比率"""
    if volatility == 0:
        return 0
    return (expected_return - risk_free_rate) / volatility


def calculate_downside_risk(allocations: Dict[str, float]) -> Dict:
    """计算下行风险指标"""
    stock_ratio = sum(allocations.get(code, 0) for code in ["510300", "159915", "515880", "512000", "512690", "510050"])
    bond_ratio = sum(allocations.get(code, 0) for code in ["511010"])
    cash_ratio = sum(allocations.get(code, 0) for code in ["511880"])
    
    # 下行风险评分（0-100，越高风险越大）
    downside_score = stock_ratio * 0.8 + bond_ratio * 0.2 + cash_ratio * 0.05
    
    return {
        "stock_ratio": stock_ratio,
        "bond_ratio": bond_ratio,
        "cash_ratio": cash_ratio,
        "downside_score": min(downside_score, 100),
        "risk_level": "高" if downside_score > 60 else "中" if downside_score > 30 else "低"
    }


def assess_risk(portfolio_data: Dict) -> Dict:
    """评估组合风险"""
    allocations = portfolio_data.get("allocations", {})
    expected_return = portfolio_data.get("expected_return", 6.0)
    
    # 计算各项指标
    volatility = calculate_portfolio_volatility(allocations)
    max_drawdown = calculate_max_drawdown(volatility)
    sharpe_ratio = calculate_sharpe_ratio(expected_return, volatility)
    downside = calculate_downside_risk(allocations)
    
    # 风险评级
    if volatility < 8:
        risk_rating = "低风险"
        risk_score = 20
    elif volatility < 15:
        risk_rating = "中低风险"
        risk_score = 40
    elif volatility < 22:
        risk_rating = "中等风险"
        risk_score = 60
    elif volatility < 30:
        risk_rating = "中高风险"
        risk_score = 80
    else:
        risk_rating = "高风险"
        risk_score = 95
    
    return {
        "assessed_at": datetime.now().isoformat(),
        "risk_rating": risk_rating,
        "risk_score": risk_score,
        "metrics": {
            "annual_volatility": round(volatility, 2),
            "estimated_max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "downside_risk": downside["downside_score"],
            "stock_allocation": downside["stock_ratio"],
            "bond_allocation": downside["bond_ratio"],
            "cash_allocation": downside["cash_ratio"]
        },
        "analysis": {
            "volatility_comment": get_volatility_comment(volatility),
            "drawdown_comment": get_drawdown_comment(max_drawdown),
            "sharpe_comment": get_sharpe_comment(sharpe_ratio),
            "structure_comment": get_structure_comment(downside)
        },
        "warnings": generate_warnings(volatility, max_drawdown, sharpe_ratio, downside),
        "suggestions": generate_suggestions(volatility, max_drawdown, sharpe_ratio, downside)
    }


def get_volatility_comment(volatility: float) -> str:
    if volatility < 8:
        return "波动率较低，组合相对稳定"
    elif volatility < 15:
        return "波动率适中，属于正常范围"
    elif volatility < 25:
        return "波动率偏高，需关注市场波动"
    else:
        return "波动率很高，需做好心理准备"


def get_drawdown_comment(drawdown: float) -> str:
    if drawdown < 10:
        return "最大回撤可控，本金安全性高"
    elif drawdown < 20:
        return "可能出现中等回撤，需有一定承受能力"
    elif drawdown < 35:
        return "回撤风险较大，建议分散投资"
    else:
        return "回撤风险很高，需严格止损"


def get_sharpe_comment(sharpe: float) -> str:
    if sharpe > 1.0:
        return "风险调整后收益优秀"
    elif sharpe > 0.5:
        return "风险调整后收益良好"
    elif sharpe > 0:
        return "风险调整后收益一般"
    else:
        return "风险调整后收益较差，需优化"


def get_structure_comment(downside: Dict) -> str:
    stock = downside["stock_ratio"]
    bond = downside["bond_ratio"]
    cash = downside["cash_ratio"]
    
    if stock > 60:
        return f"权益占比过高({stock:.0f}%)，建议增加固收配置"
    elif cash > 30:
        return f"现金占比过高({cash:.0f}%)，资金效率偏低"
    elif bond > 50:
        return f"固收占比过高({bond:.0f}%)，收益可能偏低"
    else:
        return "资产配置相对均衡"


def generate_warnings(volatility: float, drawdown: float, sharpe: float, downside: Dict) -> List[str]:
    warnings = []
    
    if volatility > 25:
        warnings.append("组合波动率过高，可能超出一般投资者承受能力")
    if drawdown > 30:
        warnings.append("预估最大回撤超过30%，需做好心理准备")
    if sharpe < 0.3:
        warnings.append("夏普比率偏低，风险收益比不够理想")
    if downside["stock_ratio"] > 70:
        warnings.append("股票型基金占比过高，建议适当降低")
    
    return warnings if warnings else ["未发现明显风险隐患"]


def generate_suggestions(volatility: float, drawdown: float, sharpe: float, downside: Dict) -> List[str]:
    suggestions = []
    
    if volatility > 20:
        suggestions.append("考虑增加债券基金或货币基金降低波动")
    if drawdown > 25:
        suggestions.append("设置止损线，建议单只基金亏损15%时考虑调整")
    if sharpe < 0.5:
        suggestions.append("优化基金选择，提高风险调整后收益")
    if downside["cash_ratio"] > 20:
        suggestions.append("现金占比偏高，建议逐步投入或增加权益配置")
    
    suggestions.append("定期（每季度）检视组合风险指标")
    suggestions.append("市场剧烈波动时，可考虑临时降低仓位")
    
    return suggestions


def format_report(assessment: Dict, portfolio_data: Dict) -> str:
    """格式化风险评估报告（投资官六段式）"""
    m = assessment["metrics"]
    a = assessment["analysis"]
    
    lines = [
        "=" * 60,
        "基金组合风险评估报告",
        "=" * 60,
        "",
        "## 🧭 投资官视角",
        "",
        "### 一、核心结论",
        f"【风险评级】{assessment['risk_rating']}（评分：{assessment['risk_score']}/100）",
        f"【年化波动率】{m['annual_volatility']}% - {a['volatility_comment']}",
        f"【预估最大回撤】{m['estimated_max_drawdown']}% - {a['drawdown_comment']}",
        "",
        "### 二、背后逻辑",
        f"• 夏普比率：{m['sharpe_ratio']} - {a['sharpe_comment']}",
        f"• 权益占比：{m['stock_allocation']:.0f}%",
        f"• 固收占比：{m['bond_allocation']:.0f}%",
        f"• 现金占比：{m['cash_allocation']:.0f}%",
        f"• {a['structure_comment']}",
        "",
        "### 三、风险在哪里",
    ]
    
    for warning in assessment["warnings"]:
        lines.append(f"⚠️ {warning}")
    
    lines.extend([
        "",
        "### 四、适合谁",
    ])
    
    if assessment["risk_score"] < 40:
        lines.append("适合保守型投资者，追求本金安全，能承受小幅波动")
    elif assessment["risk_score"] < 70:
        lines.append("适合稳健型投资者，追求平衡收益，能承受中等波动")
    else:
        lines.append("适合积极型投资者，追求较高收益，能承受大幅波动")
    
    lines.extend([
        "",
        "### 五、操作策略",
    ])
    
    for suggestion in assessment["suggestions"]:
        lines.append(f"✓ {suggestion}")
    
    lines.extend([
        "",
        "### 六、如果判断错了",
        "• 如市场出现系统性风险，及时降低权益仓位至30%以下",
        "• 如单只基金回撤超过20%，考虑止损或转换",
        "• 如组合波动率持续高于预期，重新评估资产配置",
        "• 建议预留3-6个月生活费作为应急资金，不投入市场",
        "",
        "=" * 60,
        f"评估时间：{assessment['assessed_at']}",
        "=" * 60
    ])
    
    return "\n".join(lines)


def parse_funds_string(funds_str: str) -> Dict[str, float]:
    """解析基金字符串，格式：code1:ratio1,code2:ratio2"""
    allocations = {}
    for item in funds_str.split(","):
        parts = item.split(":")
        if len(parts) == 2:
            code = parts[0].strip()
            ratio = float(parts[1].strip())
            allocations[code] = ratio
    return allocations


def main():
    parser = argparse.ArgumentParser(description="基金组合风险评估器")
    parser.add_argument("--portfolio", type=str, help="组合JSON文件路径")
    parser.add_argument("--funds", type=str, help="基金配置，格式：code1:ratio1,code2:ratio2")
    parser.add_argument("--expected-return", type=float, default=6.0, help="预期年化收益率(%)")
    parser.add_argument("--output", type=str, help="输出JSON文件")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    # 获取组合数据
    if args.portfolio:
        with open(args.portfolio, 'r', encoding='utf-8') as f:
            portfolio_data = json.load(f)
    elif args.funds:
        allocations = parse_funds_string(args.funds)
        portfolio_data = {
            "allocations": allocations,
            "expected_return": args.expected_return
        }
    else:
        # 默认示例组合
        portfolio_data = {
            "allocations": {"510300": 40, "159915": 30, "511880": 30},
            "expected_return": args.expected_return
        }
    
    # 评估风险
    assessment = assess_risk(portfolio_data)
    
    if args.json or args.output:
        output = json.dumps(assessment, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"评估报告已保存到: {args.output}")
        else:
            print(output)
    else:
        print(format_report(assessment, portfolio_data))


if __name__ == "__main__":
    main()
