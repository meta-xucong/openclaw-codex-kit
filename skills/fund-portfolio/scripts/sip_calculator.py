#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
定投计算器

Usage:
    python sip_calculator.py --monthly 3000 --years 5 --expected-return 8
    python sip_calculator.py --monthly 5000 --years 10 --strategy "智能定投"
"""

import argparse
import json
from datetime import datetime
from typing import Dict, List


def calculate_regular_sip(
    monthly_amount: float,
    years: int,
    annual_return: float
) -> Dict:
    """计算普通定投收益"""
    months = years * 12
    monthly_rate = annual_return / 100 / 12
    
    # 累计投入
    total_invested = monthly_amount * months
    
    # 未来价值（年金终值公式）
    if monthly_rate == 0:
        future_value = total_invested
    else:
        future_value = monthly_amount * ((1 + monthly_rate) ** months - 1) / monthly_rate
    
    # 总收益
    total_return = future_value - total_invested
    return_rate = (total_return / total_invested) * 100 if total_invested > 0 else 0
    
    # 生成明细
    details = []
    accumulated = 0
    for month in range(1, months + 1):
        accumulated = accumulated * (1 + monthly_rate) + monthly_amount
        if month % 12 == 0:
            details.append({
                "year": month // 12,
                "invested": monthly_amount * month,
                "value": accumulated,
                "return": accumulated - monthly_amount * month
            })
    
    return {
        "strategy": "普通定投",
        "monthly_amount": monthly_amount,
        "years": years,
        "total_months": months,
        "annual_return": annual_return,
        "total_invested": total_invested,
        "future_value": future_value,
        "total_return": total_return,
        "return_rate": return_rate,
        "details": details
    }


def calculate_smart_sip(
    monthly_amount: float,
    years: int,
    base_return: float
) -> Dict:
    """计算智能定投收益（简化模型）"""
    # 智能定投假设：低位多投20%，高位少投20%
    # 平均效果比普通定投好约10-15%
    
    regular_result = calculate_regular_sip(monthly_amount, years, base_return)
    
    # 假设智能定投能提升15%收益
    enhanced_return = base_return * 1.15
    enhanced_result = calculate_regular_sip(monthly_amount, years, enhanced_return)
    
    return {
        "strategy": "智能定投",
        "description": "低位多投、高位少投策略",
        "monthly_amount": monthly_amount,
        "years": years,
        "base_annual_return": base_return,
        "expected_annual_return": enhanced_return,
        "total_invested": regular_result["total_invested"],
        "future_value": enhanced_result["future_value"],
        "total_return": enhanced_result["total_return"],
        "return_rate": enhanced_result["return_rate"],
        "advantage_vs_regular": enhanced_result["future_value"] - regular_result["future_value"],
        "advantage_rate": ((enhanced_result["future_value"] / regular_result["future_value"]) - 1) * 100
    }


def format_report(result: Dict) -> str:
    """格式化报告"""
    lines = [
        "=" * 60,
        "定投计划报告",
        "=" * 60,
        "",
        f"【策略】{result['strategy']}",
        f"【每月定投】{result['monthly_amount']:,.0f} 元",
        f"【定投期限】{result['years']} 年（{result['total_months']}期）",
        "",
        "-" * 60,
        "预期收益测算",
        "-" * 60,
        f"累计投入：{result['total_invested']:,.0f} 元",
        f"预期市值：{result['future_value']:,.0f} 元",
        f"预期收益：{result['total_return']:+,.0f} 元（{result['return_rate']:+.1f}%）",
    ]
    
    if "advantage_vs_regular" in result:
        lines.extend([
            "",
            f"比普通定投多赚：{result['advantage_vs_regular']:,.0f} 元",
            f"收益提升：{result['advantage_rate']:.1f}%",
        ])
    
    lines.extend([
        "",
        "-" * 60,
        "投资官建议",
        "-" * 60,
        "✓ 最佳扣款日：每月1日或发薪日后3天",
        "✓ 止盈策略：年化收益达到15%时考虑部分止盈",
        "✓ 止损策略：单笔定投亏损30%时暂停，检视标的",
        "✓ 坚持纪律：至少坚持3年，避免频繁更换标的",
        "",
        "⚠️ 风险提示：以上测算基于历史数据，实际收益可能不同",
        "=" * 60,
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="定投计算器")
    parser.add_argument("--monthly", type=float, required=True, help="每月定投金额")
    parser.add_argument("--years", type=int, required=True, help="定投年限")
    parser.add_argument("--expected-return", type=float, default=8, help="预期年化收益率（%）")
    parser.add_argument("--strategy", type=str, default="普通定投", 
                       choices=["普通定投", "智能定投"],
                       help="定投策略")
    parser.add_argument("--output", type=str, help="输出JSON文件")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    if args.strategy == "智能定投":
        result = calculate_smart_sip(args.monthly, args.years, args.expected_return)
    else:
        result = calculate_regular_sip(args.monthly, args.years, args.expected_return)
    
    if args.json or args.output:
        output = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"报告已保存到: {args.output}")
        else:
            print(output)
    else:
        print(format_report(result))


if __name__ == "__main__":
    main()
