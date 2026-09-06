#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
估值分析器

使用多种方法评估创业公司估值

Usage:
    python valuation_analyzer.py --stage "天使轮" --revenue 0 --team-score 8
"""

import argparse
import json
from datetime import datetime
from typing import Dict, List


def comparable_company_analysis(industry: str, stage: str, revenue: float) -> Dict:
    """可比公司法"""
    
    # 行业估值倍数（简化数据）
    multiples = {
        "SaaS": {"天使轮": (300, 800), "Pre-A": (800, 1500), "A轮": (1500, 3000)},
        "电商": {"天使轮": (200, 500), "Pre-A": (500, 1000), "A轮": (1000, 2000)},
        "AI": {"天使轮": (500, 1200), "Pre-A": (1200, 2500), "A轮": (2500, 5000)},
        "新能源": {"天使轮": (400, 1000), "Pre-A": (1000, 2000), "A轮": (2000, 4000)},
        "消费": {"天使轮": (200, 500), "Pre-A": (500, 1000), "A轮": (1000, 2000)}
    }
    
    industry_multiples = multiples.get(industry, multiples["SaaS"])
    stage_range = industry_multiples.get(stage, (300, 1000))
    
    # 如果有收入，用收入倍数调整
    if revenue > 0:
        # P/S倍数 5-15倍
        ps_low = max(stage_range[0], revenue * 5 / 1e4)
        ps_high = min(stage_range[1], revenue * 15 / 1e4)
        valuation_low = min(ps_low, stage_range[0])
        valuation_high = max(ps_high, stage_range[1])
    else:
        valuation_low, valuation_high = stage_range
    
    return {
        "method": "可比公司法",
        "valuation_range": (round(valuation_low, 2), round(valuation_high, 2)),
        "unit": "万元",
        "median": round((valuation_low + valuation_high) / 2, 2),
        "comment": f"参考{industry}行业{stage}估值水平"
    }


def venture_capital_method(
    revenue: float,
    growth_rate: float,
    target_return: float,
    exit_multiple: float,
    years: int
) -> Dict:
    """风险投资法（倒推估值）"""
    
    # 预测退出时收入
    future_revenue = revenue * pow(1 + growth_rate / 100, years)
    
    # 退出估值 = 退出收入 * 退出倍数
    exit_valuation = future_revenue * exit_multiple
    
    # 当前估值 = 退出估值 / (1 + 目标回报率)^年数
    discount_rate = target_return / 100
    current_valuation = exit_valuation / pow(1 + discount_rate, years)
    
    # 考虑20%上下浮动
    valuation_low = current_valuation * 0.8
    valuation_high = current_valuation * 1.2
    
    return {
        "method": "风险投资法",
        "valuation_range": (round(valuation_low / 1e4, 2), round(valuation_high / 1e4, 2)),
        "unit": "万元",
        "median": round(current_valuation / 1e4, 2),
        "assumptions": {
            "future_revenue": round(future_revenue, 2),
            "exit_valuation": round(exit_valuation / 1e4, 2),
            "target_return": target_return,
            "years": years
        },
        "comment": f"假设{years}年后退出，目标{target_return}%回报"
    }


def scorecard_method(
    team_score: int,
    product_score: int,
    market_score: int,
    competition_score: int,
    timing_score: int,
    stage: str
) -> Dict:
    """Scorecard法（加权评分）"""
    
    # 权重配置
    weights = {
        "team": 0.30,
        "product": 0.25,
        "market": 0.20,
        "competition": 0.15,
        "timing": 0.10
    }
    
    # 计算加权得分
    weighted_score = (
        team_score * weights["team"] +
        product_score * weights["product"] +
        market_score * weights["market"] +
        competition_score * weights["competition"] +
        timing_score * weights["timing"]
    )
    
    # 基准估值（根据阶段）
    base_valuations = {
        "天使轮": 500,
        "Pre-A": 1500,
        "A轮": 3000,
        "B轮": 8000
    }
    
    base_valuation = base_valuations.get(stage, 1000)
    
    # 调整系数（5-10分映射到0.5-1.5倍）
    adjustment = 0.5 + (weighted_score / 10)
    
    valuation = base_valuation * adjustment
    
    return {
        "method": "Scorecard法",
        "valuation_range": (round(valuation * 0.8, 2), round(valuation * 1.2, 2)),
        "unit": "万元",
        "median": round(valuation, 2),
        "weighted_score": round(weighted_score, 1),
        "weights": weights,
        "comment": f"综合评分{weighted_score:.1f}/10，基准估值{base_valuation}万元"
    }


def analyze_valuation(methods_results: List[Dict]) -> Dict:
    """综合分析各方法结果"""
    
    # 计算中位数范围
    medians = [m["median"] for m in methods_results]
    
    if len(medians) >= 2:
        avg_valuation = sum(medians) / len(medians)
        min_valuation = min(m["valuation_range"][0] for m in methods_results)
        max_valuation = max(m["valuation_range"][1] for m in methods_results)
    else:
        avg_valuation = medians[0] if medians else 0
        min_valuation = methods_results[0]["valuation_range"][0] if methods_results else 0
        max_valuation = methods_results[0]["valuation_range"][1] if methods_results else 0
    
    return {
        "fair_value": round(avg_valuation, 2),
        "valuation_range": (round(min_valuation, 2), round(max_valuation, 2)),
        "unit": "万元",
        "methods_count": len(methods_results)
    }


def generate_analysis(args, valuation: Dict) -> Dict:
    """生成分析结论"""
    
    fair_value = valuation["fair_value"]
    
    # 合理性判断
    if fair_value < 500:
        reasonableness = "偏低"
        comment = "估值较低，可能是早期项目或存在明显短板"
    elif fair_value < 2000:
        reasonableness = "合理"
        comment = "估值在天使轮-Pre-A轮合理区间"
    elif fair_value < 5000:
        reasonableness = "偏高"
        comment = "估值较高，需有强劲的增长支撑"
    else:
        reasonableness = "很高"
        comment = "估值很高，需是明星项目或热门赛道"
    
    return {
        "reasonableness": reasonableness,
        "comment": comment,
        "investment_suggestion": generate_investment_suggestion(args, fair_value)
    }


def generate_investment_suggestion(args, fair_value: float) -> str:
    """生成投资建议"""
    
    # 简单的谈判建议
    if args.team_score >= 8 and args.market_score >= 8:
        return f"项目质量优秀，可接受{fair_value:.0f}万估值，建议尽快锁定"
    elif args.team_score >= 6 and args.market_score >= 6:
        return f"项目良好，建议估值控制在{fair_value * 0.9:.0f}万以内"
    else:
        return f"项目有短板，建议估值压低到{fair_value * 0.8:.0f}万以下"


def generate_valuation_report(args) -> Dict:
    """生成完整估值报告"""
    
    methods_results = []
    
    # 方法1：可比公司法
    comp_result = comparable_company_analysis(args.industry, args.stage, args.revenue)
    methods_results.append(comp_result)
    
    # 方法2：风险投资法（需要收入）
    if args.revenue > 0 or args.growth_rate > 0:
        vc_result = venture_capital_method(
            args.revenue,
            args.growth_rate,
            args.target_return,
            args.exit_multiple,
            args.years
        )
        methods_results.append(vc_result)
    
    # 方法3：Scorecard法
    scorecard_result = scorecard_method(
        args.team_score,
        args.product_score,
        args.market_score,
        args.competition_score,
        args.timing_score,
        args.stage
    )
    methods_results.append(scorecard_result)
    
    # 综合分析
    valuation = analyze_valuation(methods_results)
    analysis = generate_analysis(args, valuation)
    
    return {
        "generated_at": datetime.now().isoformat(),
        "project_stage": args.stage,
        "industry": args.industry,
        "methods": methods_results,
        "valuation": valuation,
        "analysis": analysis,
        "negotiation_range": {
            "conservative": round(valuation["fair_value"] * 0.8, 2),
            "fair": valuation["fair_value"],
            "aggressive": round(valuation["fair_value"] * 1.2, 2)
        },
        "risks": generate_valuation_risks(args),
        "suggestions": generate_valuation_suggestions(args, valuation)
    }


def generate_valuation_risks(args) -> List[str]:
    """生成估值风险"""
    risks = []
    
    if args.revenue == 0:
        risks.append("尚无收入，估值主要基于预期，不确定性高")
    if args.team_score < 6:
        risks.append("团队评分较低，执行风险可能影响估值实现")
    if args.market_score < 5:
        risks.append("市场空间有限，增长天花板可能低于预期")
    
    if not risks:
        risks.append("估值基础相对扎实，但仍需持续跟踪")
    
    return risks


def generate_valuation_suggestions(args, valuation: Dict) -> List[str]:
    """生成估值建议"""
    suggestions = [
        f"合理估值区间：{valuation['valuation_range'][0]:.0f}-{valuation['valuation_range'][1]:.0f}万元",
        f"谈判目标：{valuation['fair_value'] * 0.9:.0f}万元左右",
        "建议设置对赌条款，如业绩未达成调整估值",
        "考虑分期投资，根据里程碑释放资金"
    ]
    
    return suggestions


def format_report(report: Dict) -> str:
    """格式化估值报告（投资官六段式）"""
    
    v = report["valuation"]
    a = report["analysis"]
    
    lines = [
        "=" * 60,
        "创业公司估值分析报告",
        "=" * 60,
        "",
        "## 🧭 投资官视角",
        "",
        "### 一、核心结论",
        f"【公允估值】{v['fair_value']:,.0f}万元",
        f"【估值区间】{v['valuation_range'][0]:,.0f} - {v['valuation_range'][1]:,.0f}万元",
        f"【估值合理性】{a['reasonableness']}",
        f"【项目阶段】{report['project_stage']}",
        "",
        "### 二、背后逻辑",
        "【估值方法】",
    ]
    
    for method in report["methods"]:
        lines.append(f"• {method['method']}: {method['median']:,.0f}万元 ({method['comment']})")
    
    lines.extend([
        "",
        f"• {a['comment']}",
        "",
        "### 三、风险在哪里",
    ])
    
    for risk in report["risks"]:
        lines.append(f"⚠️ {risk}")
    
    lines.extend([
        "",
        "### 四、适合谁",
        "• 对行业有深入了解的专业投资者",
        "• 能够承受早期投资高风险的高净值人士",
        "• 投资期限5年以上的长期投资者",
        "",
        "### 五、操作策略",
    ])
    
    lines.append(f"【谈判建议】{a['investment_suggestion']}")
    lines.append("")
    lines.append("【估值谈判区间】")
    lines.append(f"• 保守出价：{report['negotiation_range']['conservative']:,.0f}万元")
    lines.append(f"• 公允出价：{report['negotiation_range']['fair']:,.0f}万元")
    lines.append(f"• 激进出价：{report['negotiation_range']['aggressive']:,.0f}万元")
    lines.append("")
    
    for suggestion in report["suggestions"]:
        lines.append(f"✓ {suggestion}")
    
    lines.extend([
        "",
        "### 六、如果判断错了",
        "• 如估值过高，要求增加对赌条款保护",
        "• 如项目发展不及预期，及时止损不追加",
        "• 如市场估值整体下调，重新谈判估值",
        "• 建议设置董事会席位，保持对重大事项的否决权",
        "",
        "=" * 60,
        f"生成时间：{report['generated_at']}",
        "=" * 60
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="估值分析器")
    parser.add_argument("--stage", type=str, required=True,
                       choices=["天使轮", "Pre-A", "A轮", "B轮"],
                       help="融资阶段")
    parser.add_argument("--industry", type=str, default="SaaS",
                       help="所属行业")
    parser.add_argument("--revenue", type=float, default=0,
                       help="年收入（元）")
    parser.add_argument("--growth-rate", type=float, default=100,
                       help="年增长率(%)")
    parser.add_argument("--team-score", type=int, default=6,
                       help="团队评分(1-10)")
    parser.add_argument("--product-score", type=int, default=6,
                       help="产品评分(1-10)")
    parser.add_argument("--market-score", type=int, default=6,
                       help="市场评分(1-10)")
    parser.add_argument("--competition-score", type=int, default=6,
                       help="竞争评分(1-10)")
    parser.add_argument("--timing-score", type=int, default=6,
                       help="时机评分(1-10)")
    parser.add_argument("--target-return", type=float, default=10,
                       help="目标回报倍数")
    parser.add_argument("--exit-multiple", type=float, default=5,
                       help="退出时P/S倍数")
    parser.add_argument("--years", type=int, default=5,
                       help="预计退出年限")
    parser.add_argument("--output", type=str, help="输出JSON文件")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    report = generate_valuation_report(args)
    
    if args.json or args.output:
        output = json.dumps(report, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"报告已保存到: {args.output}")
        else:
            print(output)
    else:
        print(format_report(report))


if __name__ == "__main__":
    main()
