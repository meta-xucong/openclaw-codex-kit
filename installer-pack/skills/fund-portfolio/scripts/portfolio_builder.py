#!/usr/bin/env python
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
基金组合构建器

根据风险偏好构建基金投资组合

Usage:
    python portfolio_builder.py --risk-level "稳健型" --amount 100000
    python portfolio_builder.py --risk-level "积极型" --amount 500000 --period "5年"
"""

import argparse
import json
from datetime import datetime
from typing import Dict, List


def get_allocation_model(risk_level: str) -> Dict:
    """获取配置模型"""
    models = {
        "保守型": {
            "description": "追求本金安全，能接受较低收益",
            "expected_return": 4,
            "max_drawdown": 5,
            "allocation": {
                "货币基金": 30,
                "债券基金": 50,
                "混合基金": 15,
                "股票基金": 5
            }
        },
        "稳健型": {
            "description": "追求稳健增值，能承受小幅波动",
            "expected_return": 6,
            "max_drawdown": 12,
            "allocation": {
                "货币基金": 15,
                "债券基金": 40,
                "混合基金": 30,
                "股票基金": 15
            }
        },
        "平衡型": {
            "description": "追求平衡收益，能承受中等波动",
            "expected_return": 8,
            "max_drawdown": 20,
            "allocation": {
                "货币基金": 10,
                "债券基金": 30,
                "混合基金": 35,
                "股票基金": 25
            }
        },
        "积极型": {
            "description": "追求较高收益，能承受较大波动",
            "expected_return": 10,
            "max_drawdown": 30,
            "allocation": {
                "货币基金": 5,
                "债券基金": 20,
                "混合基金": 35,
                "股票基金": 40
            }
        },
        "激进型": {
            "description": "追求高收益，能承受大幅波动",
            "expected_return": 12,
            "max_drawdown": 40,
            "allocation": {
                "货币基金": 0,
                "债券基金": 10,
                "混合基金": 30,
                "股票基金": 60
            }
        }
    }
    return models.get(risk_level, models["稳健型"])


def generate_portfolio(risk_level: str, amount: float, period_years: int) -> Dict:
    """生成基金组合方案"""
    model = get_allocation_model(risk_level)
    
    portfolio = {
        "generated_at": datetime.now().isoformat(),
        "risk_level": risk_level,
        "description": model["description"],
        "total_amount": amount,
        "investment_period": f"{period_years}年",
        "expected_annual_return": model["expected_return"],
        "expected_max_drawdown": model["max_drawdown"],
        "allocation": {},
        "fund_recommendations": {}
    }
    
    # 计算各类基金金额
    for fund_type, ratio in model["allocation"].items():
        fund_amount = amount * ratio / 100
        portfolio["allocation"][fund_type] = {
            "ratio": ratio,
            "amount": fund_amount
        }
        
        # 推荐基金类型说明
        recommendations = {
            "货币基金": ["余额宝类", "货币基金", "流动性管理"],
            "债券基金": ["纯债基金", "二级债基", "固收+"],
            "混合基金": ["偏债混合", "平衡混合", "偏股混合"],
            "股票基金": ["沪深300指数", "中证500指数", "行业主题基金"]
        }
        portfolio["fund_recommendations"][fund_type] = recommendations.get(fund_type, [])
    
    # 添加建议
    portfolio["advice"] = [
        f"建议投资期限至少{max(period_years, 3)}年",
        "分散投资，单只基金不超过总仓位30%",
        "每季度检视一次，年度再平衡",
        "定投方式入场，避免一次性重仓",
        f"预期年化收益{model['expected_return']}%，但过往业绩不代表未来"
    ]
    
    return portfolio


def format_report(portfolio: Dict) -> str:
    """格式化报告"""
    lines = [
        "=" * 60,
        "基金组合配置方案",
        "=" * 60,
        "",
        f"【风险等级】{portfolio['risk_level']}",
        f"【投资金额】{portfolio['total_amount']:,.0f} 元",
        f"【投资期限】{portfolio['investment_period']}",
        f"【风险描述】{portfolio['description']}",
        "",
        "-" * 60,
        "预期收益与风险",
        "-" * 60,
        f"预期年化收益：{portfolio['expected_annual_return']}%",
        f"预期最大回撤：{portfolio['expected_max_drawdown']}%",
        "",
        "-" * 60,
        "资产配置方案",
        "-" * 60,
        ""
    ]
    
    for fund_type, data in portfolio['allocation'].items():
        lines.append(f"■ {fund_type}: {data['ratio']}% ({data['amount']:,.0f}元)")
        recommendations = portfolio['fund_recommendations'].get(fund_type, [])
        if recommendations:
            lines.append(f"  建议类型：{'、'.join(recommendations)}")
        lines.append("")
    
    lines.extend([
        "-" * 60,
        "投资官建议",
        "-" * 60
    ])
    
    for i, advice in enumerate(portfolio['advice'], 1):
        lines.append(f"{i}. {advice}")
    
    lines.extend([
        "",
        "=" * 60,
        "⚠️ 风险提示：以上配置基于历史数据，实际收益可能不同",
        "=" * 60
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="基金组合构建器")
    parser.add_argument("--risk-level", type=str, required=True,
                       choices=["保守型", "稳健型", "平衡型", "积极型", "激进型"],
                       help="风险等级")
    parser.add_argument("--amount", type=float, required=True,
                       help="投资金额（元）")
    parser.add_argument("--period", type=str, default="3年",
                       help="投资期限（如：1年、3年、5年）")
    parser.add_argument("--output", type=str, help="输出JSON文件")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    # 解析期限
    period_years = 3
    if "年" in args.period:
        try:
            period_years = int(args.period.replace("年", ""))
        except:
            pass
    
    portfolio = generate_portfolio(args.risk_level, args.amount, period_years)
    
    if args.json or args.output:
        output = json.dumps(portfolio, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"方案已保存到: {args.output}")
        else:
            print(output)
    else:
        print(format_report(portfolio))


if __name__ == "__main__":
    main()
