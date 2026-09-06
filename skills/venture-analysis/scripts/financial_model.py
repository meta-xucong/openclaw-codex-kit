#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
财务建模器

预测创业公司未来财务表现

Usage:
    python financial_model.py --years 5 --initial-users 1000 --arpu 100
"""

import argparse
import json
from datetime import datetime
from typing import Dict, List


def calculate_unit_economics(arpu: float, cac: float, gross_margin: float, churn_rate: float) -> Dict:
    """计算单位经济模型"""
    
    # LTV = ARPU * 毛利率 / 月流失率 * 12（年化）
    monthly_churn = churn_rate / 100
    if monthly_churn > 0:
        ltv = arpu * (gross_margin / 100) / monthly_churn
    else:
        ltv = arpu * 12  # 假设留存12个月
    
    # LTV/CAC 比率
    ltv_cac_ratio = ltv / cac if cac > 0 else 0
    
    # 回本周期（月）
    payback_months = cac / (arpu * gross_margin / 100) if arpu > 0 else 0
    
    return {
        "arpu": arpu,
        "cac": cac,
        "gross_margin": gross_margin,
        "churn_rate": churn_rate,
        "ltv": round(ltv, 2),
        "ltv_cac_ratio": round(ltv_cac_ratio, 2),
        "payback_months": round(payback_months, 1),
        "healthy": ltv_cac_ratio >= 3 and payback_months <= 12
    }


def project_financials(
    years: int,
    initial_users: int,
    growth_rate: float,
    arpu: float,
    cac: float,
    gross_margin: float,
    fixed_costs: float,
    burn_rate: float
) -> List[Dict]:
    """预测未来财务数据"""
    
    projections = []
    users = initial_users
    
    for year in range(1, years + 1):
        # 用户增长
        users = int(users * (1 + growth_rate / 100))
        
        # 收入
        revenue = users * arpu * 12  # 年化收入
        
        # 成本
        cogs = revenue * (1 - gross_margin / 100)  # 销售成本
        marketing_cost = users * cac  # 营销成本（新用户获客）
        total_costs = cogs + marketing_cost + fixed_costs * 12
        
        # 利润
        gross_profit = revenue - cogs
        operating_profit = revenue - total_costs
        
        # 现金流
        cash_flow = operating_profit - burn_rate * 12
        
        projections.append({
            "year": year,
            "users": users,
            "revenue": round(revenue, 2),
            "gross_profit": round(gross_profit, 2),
            "operating_profit": round(operating_profit, 2),
            "cash_flow": round(cash_flow, 2),
            "cogs": round(cogs, 2),
            "marketing_cost": round(marketing_cost, 2),
            "fixed_costs": round(fixed_costs * 12, 2)
        })
    
    return projections


def find_break_even_year(projections: List[Dict]) -> int:
    """找到盈亏平衡年份"""
    for p in projections:
        if p["operating_profit"] > 0:
            return p["year"]
    return -1


def calculate_funding_needs(projections: List[Dict], initial_cash: float = 0) -> Dict:
    """计算融资需求"""
    
    min_cash = initial_cash
    cumulative_cash = initial_cash
    
    for p in projections:
        cumulative_cash += p["cash_flow"]
        if cumulative_cash < min_cash:
            min_cash = cumulative_cash
    
    # 融资需求 = 最大现金缺口 + 6个月运营资金缓冲
    funding_needed = abs(min_cash) + projections[0]["fixed_costs"] / 2 if min_cash < 0 else 0
    
    return {
        "initial_cash": initial_cash,
        "min_cash_required": round(min_cash, 2),
        "funding_needed": round(funding_needed, 2),
        "recommended_rounds": calculate_funding_rounds(funding_needed)
    }


def calculate_funding_rounds(total_needed: float) -> List[Dict]:
    """建议融资轮次"""
    if total_needed <= 0:
        return []
    
    rounds = []
    remaining = total_needed
    round_names = ["天使轮", "Pre-A轮", "A轮", "B轮"]
    
    for i, name in enumerate(round_names):
        if remaining <= 0:
            break
        
        # 每轮最多融18个月资金
        round_amount = min(remaining, 5000000 * (i + 1))  # 递增
        rounds.append({
            "round": name,
            "amount": round(round_amount, 2),
            "timing": f"第{i*12+6}个月"
        })
        remaining -= round_amount
    
    return rounds


def generate_model(args) -> Dict:
    """生成财务模型"""
    
    # 单位经济模型
    unit_economics = calculate_unit_economics(
        args.arpu, args.cac, args.gross_margin, args.churn_rate
    )
    
    # 财务预测
    projections = project_financials(
        args.years,
        args.initial_users,
        args.growth_rate,
        args.arpu,
        args.cac,
        args.gross_margin,
        args.fixed_costs,
        args.burn_rate
    )
    
    # 盈亏平衡点
    break_even_year = find_break_even_year(projections)
    
    # 融资需求
    funding = calculate_funding_needs(projections, args.initial_cash)
    
    return {
        "generated_at": datetime.now().isoformat(),
        "assumptions": {
            "projection_years": args.years,
            "initial_users": args.initial_users,
            "monthly_growth_rate": args.growth_rate,
            "arpu": args.arpu,
            "cac": args.cac,
            "gross_margin": args.gross_margin,
            "monthly_churn": args.churn_rate,
            "monthly_fixed_costs": args.fixed_costs,
            "monthly_burn": args.burn_rate,
            "initial_cash": args.initial_cash
        },
        "unit_economics": unit_economics,
        "projections": projections,
        "break_even_year": break_even_year,
        "funding": funding,
        "analysis": generate_analysis(unit_economics, projections, break_even_year),
        "risks": generate_risks(args, projections)
    }


def generate_analysis(unit_economics: Dict, projections: List[Dict], break_even_year: int) -> Dict:
    """生成分析结论"""
    
    analysis = {
        "unit_economics_comment": "",
        "growth_comment": "",
        "profitability_comment": "",
        "overall_comment": ""
    }
    
    # 单位经济分析
    if unit_economics["healthy"]:
        analysis["unit_economics_comment"] = f"单位经济健康，LTV/CAC={unit_economics['ltv_cac_ratio']:.1f}，回本周期{unit_economics['payback_months']:.0f}个月"
    else:
        analysis["unit_economics_comment"] = f"单位经济需改善，LTV/CAC={unit_economics['ltv_cac_ratio']:.1f}（建议>3），回本周期{unit_economics['payback_months']:.0f}个月"
    
    # 增长分析
    final_users = projections[-1]["users"]
    initial_users = projections[0]["users"]
    growth_multiple = final_users / initial_users if initial_users > 0 else 0
    analysis["growth_comment"] = f"{len(projections)}年用户增长{growth_multiple:.1f}倍，期末用户{final_users:,}人"
    
    # 盈利分析
    if break_even_year > 0:
        analysis["profitability_comment"] = f"预计第{break_even_year}年盈亏平衡"
    else:
        analysis["profitability_comment"] = "预测期内未能盈亏平衡，需延长预测或调整假设"
    
    # 综合评价
    if unit_economics["healthy"] and break_even_year <= 3:
        analysis["overall_comment"] = "财务模型健康，具备可持续发展能力"
    elif unit_economics["healthy"]:
        analysis["overall_comment"] = "单位经济可行，但盈利周期较长"
    else:
        analysis["overall_comment"] = "财务模型需优化，建议调整商业模式"
    
    return analysis


def generate_risks(args, projections: List[Dict]) -> List[str]:
    """生成风险提示"""
    risks = []
    
    if args.growth_rate > 20:
        risks.append(f"月增长率{args.growth_rate}%假设较高，实际可能难以持续")
    if args.cac > args.arpu * 3:
        risks.append("获客成本过高，单位经济可能不健康")
    if projections[-1]["operating_profit"] < 0:
        risks.append("预测期内未能盈利，需持续融资")
    if args.churn_rate > 5:
        risks.append(f"月流失率{args.churn_rate}%偏高，用户留存压力大")
    
    if not risks:
        risks.append("模型假设合理，但需持续跟踪实际数据")
    
    return risks


def format_report(model: Dict) -> str:
    """格式化财务模型报告（投资官六段式）"""
    
    lines = [
        "=" * 60,
        "财务建模报告",
        "=" * 60,
        "",
        "## 🧭 投资官视角",
        "",
        "### 一、核心结论",
        f"【单位经济】LTV={model['unit_economics']['ltv']:,.0f}元，LTV/CAC={model['unit_economics']['ltv_cac_ratio']:.1f}",
        f"【回本周期】{model['unit_economics']['payback_months']:.0f}个月",
        f"【盈亏平衡】第{model['break_even_year']}年" if model['break_even_year'] > 0 else "【盈亏平衡】预测期内未实现",
        f"【融资需求】{model['funding']['funding_needed']:,.0f}元",
        "",
        "### 二、背后逻辑",
        f"• {model['analysis']['unit_economics_comment']}",
        f"• {model['analysis']['growth_comment']}",
        f"• {model['analysis']['profitability_comment']}",
        "",
        "【财务预测】",
        f"{'年份':<6} {'用户数':>10} {'收入':>12} {'毛利':>12} {'经营利润':>12}",
        "-" * 60
    ]
    
    for p in model["projections"]:
        lines.append(f"第{p['year']:<3} {p['users']:>10,} {p['revenue']:>12,.0f} "
                    f"{p['gross_profit']:>12,.0f} {p['operating_profit']:>12,.0f}")
    
    lines.extend([
        "",
        "### 三、风险在哪里",
    ])
    
    for risk in model["risks"]:
        lines.append(f"⚠️ {risk}")
    
    lines.extend([
        "",
        "### 四、适合谁",
        "• 投资期限3-5年的长期投资者",
        "• 能够承受早期亏损的风险投资者",
        "• 对行业增长有信心的战略投资者",
        "",
        "### 五、操作策略",
    ])
    
    if model["funding"]["funding_needed"] > 0:
        lines.append("【建议融资计划】")
        for round_info in model["funding"]["recommended_rounds"]:
            lines.append(f"• {round_info['round']}: {round_info['amount']:,.0f}元 ({round_info['timing']})")
    
    lines.extend([
        "",
        "【关键假设验证】",
        "• 每月跟踪实际用户数 vs 预测",
        "• 每季度验证获客成本CAC",
        "• 持续监控用户流失率",
        "• 及时调整财务预测模型",
        "",
        "### 六、如果判断错了",
        "• 如用户增长不及预期，及时降低固定成本",
        "• 如CAC持续高于预期，重新审视获客渠道",
        "• 如流失率居高不下，优先改善产品体验",
        "• 如无法按期盈亏平衡，提前启动下一轮融资",
        "",
        "=" * 60,
        f"生成时间：{model['generated_at']}",
        "=" * 60
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="财务建模器")
    parser.add_argument("--years", type=int, default=5, help="预测年数")
    parser.add_argument("--initial-users", type=int, default=1000, help="初始用户数")
    parser.add_argument("--growth-rate", type=float, default=10, help="月增长率(%)")
    parser.add_argument("--arpu", type=float, default=100, help="每用户月收入(元)")
    parser.add_argument("--cac", type=float, default=300, help="获客成本(元)")
    parser.add_argument("--gross-margin", type=float, default=70, help="毛利率(%)")
    parser.add_argument("--churn-rate", type=float, default=3, help="月流失率(%)")
    parser.add_argument("--fixed-costs", type=float, default=50000, help="月固定成本(元)")
    parser.add_argument("--burn-rate", type=float, default=100000, help="月烧钱速度(元)")
    parser.add_argument("--initial-cash", type=float, default=0, help="初始现金(元)")
    parser.add_argument("--output", type=str, help="输出JSON文件")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    model = generate_model(args)
    
    if args.json or args.output:
        output = json.dumps(model, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"模型已保存到: {args.output}")
        else:
            print(output)
    else:
        print(format_report(model))


if __name__ == "__main__":
    main()
