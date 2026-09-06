#!/usr/bin/env python
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
资产配置工具 - 基于标准普尔家庭资产配置模型

Usage:
    python asset_allocator.py --amount 1000000 --period "5年" --max-drawdown 15
    python asset_allocator.py --amount 500000 --experience "新手" --monthly-expense 15000
"""

import argparse
import json
from datetime import datetime
from typing import Dict, List


def determine_risk_level(
    max_drawdown: float,
    period_years: float,
    experience: str
) -> str:
    """确定风险等级"""
    # 经验调整
    exp_factor = {"新手": -10, "中等": 0, "丰富": 10}
    adjusted_drawdown = max_drawdown + exp_factor.get(experience, 0)
    
    # 期限调整
    if period_years < 1:
        adjusted_drawdown -= 10
    elif period_years > 5:
        adjusted_drawdown += 5
    
    if adjusted_drawdown < 5:
        return "保守型"
    elif adjusted_drawdown < 15:
        return "稳健型"
    elif adjusted_drawdown < 25:
        return "平衡型"
    elif adjusted_drawdown < 35:
        return "积极型"
    else:
        return "激进型"


def get_allocation_template(risk_level: str) -> Dict:
    """获取配置模板"""
    templates = {
        "保守型": {
            "survival": 0.60,      # 生存资产
            "growth": 0.35,        # 增值资产
            "aggressive": 0.05,    # 进攻资产
            "expected_return": 4,
            "max_drawdown": 5
        },
        "稳健型": {
            "survival": 0.50,
            "growth": 0.40,
            "aggressive": 0.10,
            "expected_return": 6,
            "max_drawdown": 12
        },
        "平衡型": {
            "survival": 0.40,
            "growth": 0.45,
            "aggressive": 0.15,
            "expected_return": 8,
            "max_drawdown": 20
        },
        "积极型": {
            "survival": 0.30,
            "growth": 0.45,
            "aggressive": 0.25,
            "expected_return": 10,
            "max_drawdown": 30
        },
        "激进型": {
            "survival": 0.20,
            "growth": 0.40,
            "aggressive": 0.40,
            "expected_return": 12,
            "max_drawdown": 40
        }
    }
    return templates.get(risk_level, templates["稳健型"])


def generate_allocation_plan(
    total_amount: float,
    risk_level: str,
    monthly_expense: float,
    period_years: float
) -> Dict:
    """生成资产配置方案"""
    template = get_allocation_template(risk_level)
    
    # 计算各层金额
    survival_amount = total_amount * template["survival"]
    growth_amount = total_amount * template["growth"]
    aggressive_amount = total_amount * template["aggressive"]
    
    # 生存资产细分
    emergency_fund = max(monthly_expense * 6, survival_amount * 0.40)
    short_term = max(monthly_expense * 6, survival_amount * 0.40)
    safe_buffer = survival_amount - emergency_fund - short_term
    
    plan = {
        "generated_at": datetime.now().isoformat(),
        "risk_level": risk_level,
        "total_amount": total_amount,
        "monthly_expense": monthly_expense,
        "investment_period_years": period_years,
        "expected_annual_return": template["expected_return"],
        "expected_max_drawdown": template["max_drawdown"],
        "allocation": {
            "survival": {
                "ratio": template["survival"],
                "amount": survival_amount,
                "details": {
                    "emergency_fund": {
                        "amount": emergency_fund,
                        "ratio": emergency_fund / total_amount,
                        "tools": ["货币基金", "活期存款"],
                        "purpose": "3-6个月生活费"
                    },
                    "short_term": {
                        "amount": short_term,
                        "ratio": short_term / total_amount,
                        "tools": ["短债基金", "定期存款"],
                        "purpose": "1年内可能用到的钱"
                    },
                    "safe_buffer": {
                        "amount": max(0, safe_buffer),
                        "ratio": max(0, safe_buffer) / total_amount,
                        "tools": ["国债", "大额存单"],
                        "purpose": "绝对安全垫"
                    }
                }
            },
            "growth": {
                "ratio": template["growth"],
                "amount": growth_amount,
                "details": {
                    "index_funds": {
                        "amount": growth_amount * 0.40,
                        "ratio": template["growth"] * 0.40,
                        "tools": ["沪深300ETF", "中证500ETF"],
                        "purpose": "市场平均收益"
                    },
                    "bond_funds": {
                        "amount": growth_amount * 0.35,
                        "ratio": template["growth"] * 0.35,
                        "tools": ["纯债基金", "二级债基"],
                        "purpose": "稳定收益"
                    },
                    "quality_stocks": {
                        "amount": growth_amount * 0.25,
                        "ratio": template["growth"] * 0.25,
                        "tools": ["蓝筹股", "高股息股票"],
                        "purpose": "长期增值"
                    }
                }
            },
            "aggressive": {
                "ratio": template["aggressive"],
                "amount": aggressive_amount,
                "details": {
                    "growth_funds": {
                        "amount": aggressive_amount * 0.60,
                        "ratio": template["aggressive"] * 0.60,
                        "tools": ["成长型基金", "科技主题基金"],
                        "purpose": "超额收益"
                    },
                    "sector_etfs": {
                        "amount": aggressive_amount * 0.40,
                        "ratio": template["aggressive"] * 0.40,
                        "tools": ["行业ETF", "商品基金"],
                        "purpose": "主题机会"
                    }
                }
            }
        },
        "rebalance": {
            "frequency": "每季度",
            "method": "阈值再平衡",
            "threshold": "5%",
            "notes": "当某类资产偏离目标比例超过5%时进行调整"
        },
        "advice": [
            "生存资产是安全垫，确保3-6个月生活费随时可取",
            "增值资产是核心，建议长期持有至少3年",
            "进攻资产是高风险部分，亏损30%需重新评估",
            "每季度检视一次，避免频繁调仓",
            "市场恐慌时不要满仓，保持生存资产比例"
        ]
    }
    
    return plan


def format_report(plan: Dict) -> str:
    """格式化报告"""
    lines = [
        "=" * 70,
        "资产配置方案",
        "=" * 70,
        "",
        f"【风险等级】{plan['risk_level']}",
        f"【总资金】{plan['total_amount']:,.0f} 元",
        f"【投资期限】{plan['investment_period_years']} 年",
        "",
        "-" * 70,
        "预期收益与风险",
        "-" * 70,
        f"预期年化收益：{plan['expected_annual_return']}%",
        f"预期最大回撤：{plan['expected_max_drawdown']}%",
        "",
        "-" * 70,
        "三层资产配置",
        "-" * 70,
        "",
        f"■ 生存资产（要花的钱）{plan['allocation']['survival']['ratio']*100:.0f}%",
        f"  金额：{plan['allocation']['survival']['amount']:,.0f} 元",
    ]
    
    for name, detail in plan['allocation']['survival']['details'].items():
        if detail['amount'] > 0:
            lines.append(f"  ├── {detail['purpose']}: {detail['amount']:,.0f} 元")
            lines.append(f"  │   工具：{'、'.join(detail['tools'])}")
    
    lines.extend([
        "",
        f"■ 增值资产（生钱的钱）{plan['allocation']['growth']['ratio']*100:.0f}%",
        f"  金额：{plan['allocation']['growth']['amount']:,.0f} 元",
    ])
    
    for name, detail in plan['allocation']['growth']['details'].items():
        lines.append(f"  ├── {detail['purpose']}: {detail['amount']:,.0f} 元")
        lines.append(f"  │   工具：{'、'.join(detail['tools'])}")
    
    lines.extend([
        "",
        f"■ 进攻资产（赚钱的钱）{plan['allocation']['aggressive']['ratio']*100:.0f}%",
        f"  金额：{plan['allocation']['aggressive']['amount']:,.0f} 元",
    ])
    
    for name, detail in plan['allocation']['aggressive']['details'].items():
        lines.append(f"  ├── {detail['purpose']}: {detail['amount']:,.0f} 元")
        lines.append(f"  │   工具：{'、'.join(detail['tools'])}")
    
    lines.extend([
        "",
        "-" * 70,
        "再平衡策略",
        "-" * 70,
        f"频率：{plan['rebalance']['frequency']}",
        f"方法：{plan['rebalance']['method']}",
        f"阈值：偏离目标比例 {plan['rebalance']['threshold']} 时调整",
        "",
        "-" * 70,
        "投资官建议",
        "-" * 70,
    ])
    
    for i, advice in enumerate(plan['advice'], 1):
        lines.append(f"{i}. {advice}")
    
    lines.extend([
        "",
        "=" * 70,
        "⚠️ 风险提示：以上配置基于标准普尔模型，实际收益可能不同",
        "=" * 70,
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="资产配置工具")
    parser.add_argument("--amount", type=float, required=True, help="总资金（元）")
    parser.add_argument("--period", type=str, default="3年", help="投资期限（如：1年、3年、5年）")
    parser.add_argument("--max-drawdown", type=float, default=15, help="最大回撤容忍度（%）")
    parser.add_argument("--monthly-expense", type=float, default=10000, help="月支出（元）")
    parser.add_argument("--experience", type=str, default="中等", 
                       choices=["新手", "中等", "丰富"],
                       help="投资经验")
    parser.add_argument("--output", type=str, help="输出JSON文件")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    # 解析期限
    period_years = 3
    if "年" in args.period:
        try:
            period_years = float(args.period.replace("年", ""))
        except:
            pass
    
    # 确定风险等级
    risk_level = determine_risk_level(
        args.max_drawdown,
        period_years,
        args.experience
    )
    
    # 生成配置方案
    plan = generate_allocation_plan(
        args.amount,
        risk_level,
        args.monthly_expense,
        period_years
    )
    
    if args.json or args.output:
        output = json.dumps(plan, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"方案已保存到: {args.output}")
        else:
            print(output)
    else:
        print(format_report(plan))


if __name__ == "__main__":
    main()
