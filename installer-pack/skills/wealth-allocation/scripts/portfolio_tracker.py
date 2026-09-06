#!/usr/bin/env python
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
组合收益追踪器

追踪投资组合的收益表现

Usage:
    python portfolio_tracker.py --portfolio portfolio.json --history history.json
    python portfolio_tracker.py --initial 100000 --current 115000 --months 12
"""

import argparse
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List


def calculate_annualized_return(initial: float, current: float, years: float) -> float:
    """计算年化收益率"""
    if initial <= 0 or years <= 0:
        return 0.0
    return (pow(current / initial, 1 / years) - 1) * 100


def calculate_max_drawdown(values: List[float]) -> float:
    """计算最大回撤"""
    if not values or len(values) < 2:
        return 0.0
    
    peak = values[0]
    max_dd = 0.0
    
    for value in values:
        if value > peak:
            peak = value
        dd = (peak - value) / peak * 100
        if dd > max_dd:
            max_dd = dd
    
    return max_dd


def calculate_volatility(returns: List[float]) -> float:
    """计算波动率（年化）"""
    if not returns or len(returns) < 2:
        return 0.0
    
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / len(returns)
    std = math.sqrt(variance)
    
    # 假设月度数据，年化 = 月波动 * sqrt(12)
    return std * math.sqrt(12)


def calculate_sharpe_ratio(annual_return: float, volatility: float, risk_free_rate: float = 2.5) -> float:
    """计算夏普比率"""
    if volatility == 0:
        return 0.0
    return (annual_return - risk_free_rate) / volatility


def calculate_calmar_ratio(annual_return: float, max_drawdown: float) -> float:
    """计算卡玛比率"""
    if max_drawdown == 0:
        return 0.0
    return annual_return / max_drawdown


def track_portfolio(
    initial_value: float,
    current_value: float,
    history: List[Dict] = None,
    months: int = 12
) -> Dict:
    """追踪组合表现"""
    
    years = months / 12
    profit = current_value - initial_value
    profit_pct = (profit / initial_value) * 100 if initial_value > 0 else 0
    
    # 基础指标
    annual_return = calculate_annualized_return(initial_value, current_value, years)
    
    # 如果有历史数据，计算更详细的指标
    max_drawdown = 0
    volatility = 0
    sharpe = 0
    calmar = 0
    
    if history and len(history) > 1:
        values = [h["value"] for h in history]
        returns = []
        for i in range(1, len(history)):
            monthly_return = (history[i]["value"] - history[i-1]["value"]) / history[i-1]["value"] * 100
            returns.append(monthly_return)
        
        max_drawdown = calculate_max_drawdown(values)
        volatility = calculate_volatility(returns)
        sharpe = calculate_sharpe_ratio(annual_return, volatility)
        calmar = calculate_calmar_ratio(annual_return, max_drawdown)
    
    # 评级
    rating = calculate_rating(annual_return, max_drawdown, sharpe)
    
    return {
        "tracked_at": datetime.now().isoformat(),
        "period_months": months,
        "basic_metrics": {
            "initial_value": initial_value,
            "current_value": current_value,
            "profit": round(profit, 2),
            "profit_percentage": round(profit_pct, 2),
            "annualized_return": round(annual_return, 2)
        },
        "risk_metrics": {
            "max_drawdown": round(max_drawdown, 2),
            "volatility": round(volatility, 2),
            "sharpe_ratio": round(sharpe, 2),
            "calmar_ratio": round(calmar, 2)
        },
        "rating": rating,
        "benchmark_comparison": compare_with_benchmark(annual_return),
        "analysis": generate_analysis(annual_return, max_drawdown, sharpe, profit_pct),
        "suggestions": generate_suggestions(annual_return, max_drawdown, sharpe)
    }


def calculate_rating(annual_return: float, max_drawdown: float, sharpe: float) -> Dict:
    """计算综合评级"""
    score = 0
    
    # 收益评分（40分）
    if annual_return > 15:
        score += 40
    elif annual_return > 10:
        score += 30
    elif annual_return > 5:
        score += 20
    elif annual_return > 0:
        score += 10
    
    # 风险控制评分（30分）
    if max_drawdown < 10:
        score += 30
    elif max_drawdown < 20:
        score += 20
    elif max_drawdown < 30:
        score += 10
    
    # 夏普比率评分（30分）
    if sharpe > 1.0:
        score += 30
    elif sharpe > 0.5:
        score += 20
    elif sharpe > 0:
        score += 10
    
    # 评级
    if score >= 80:
        level = "优秀"
    elif score >= 60:
        level = "良好"
    elif score >= 40:
        level = "一般"
    else:
        level = "需改进"
    
    return {
        "score": score,
        "level": level,
        "max_score": 100
    }


def compare_with_benchmark(annual_return: float) -> Dict:
    """与基准比较"""
    benchmarks = {
        "沪深300": 8.0,  # 假设历史平均
        "中证500": 10.0,
        "货币基金": 2.5,
        "债券基金": 4.0
    }
    
    comparison = {}
    for name, benchmark_return in benchmarks.items():
        diff = annual_return - benchmark_return
        comparison[name] = {
            "benchmark_return": benchmark_return,
            "diff": round(diff, 2),
            "outperform": diff > 0
        }
    
    return comparison


def generate_analysis(annual_return: float, max_drawdown: float, sharpe: float, profit_pct: float) -> Dict:
    """生成分析结论"""
    analysis = {
        "return_comment": "",
        "risk_comment": "",
        "efficiency_comment": "",
        "overall_comment": ""
    }
    
    # 收益分析
    if annual_return > 15:
        analysis["return_comment"] = "收益表现优秀，超越大部分投资者"
    elif annual_return > 8:
        analysis["return_comment"] = "收益表现良好，达到预期目标"
    elif annual_return > 0:
        analysis["return_comment"] = "收益表现一般，刚跑赢通胀"
    else:
        analysis["return_comment"] = "收益为负，需审视投资策略"
    
    # 风险分析
    if max_drawdown < 10:
        analysis["risk_comment"] = "风险控制优秀，回撤很小"
    elif max_drawdown < 20:
        analysis["risk_comment"] = "风险控制良好，回撤在可接受范围"
    elif max_drawdown < 30:
        analysis["risk_comment"] = "风险偏高，需加强风控"
    else:
        analysis["risk_comment"] = "风险过高，需立即调整"
    
    # 效率分析
    if sharpe > 1.0:
        analysis["efficiency_comment"] = "风险调整后收益优秀，投资效率高"
    elif sharpe > 0.5:
        analysis["efficiency_comment"] = "风险调整后收益良好"
    elif sharpe > 0:
        analysis["efficiency_comment"] = "风险调整后收益一般"
    else:
        analysis["efficiency_comment"] = "承担风险但未获得相应收益"
    
    # 综合评价
    if annual_return > 10 and max_drawdown < 20:
        analysis["overall_comment"] = "组合表现优秀，建议继续保持"
    elif annual_return > 5 and max_drawdown < 25:
        analysis["overall_comment"] = "组合表现良好，可小幅优化"
    else:
        analysis["overall_comment"] = "组合需要调整，建议重新审视配置"
    
    return analysis


def generate_suggestions(annual_return: float, max_drawdown: float, sharpe: float) -> List[str]:
    """生成建议"""
    suggestions = []
    
    if annual_return < 5:
        suggestions.append("收益偏低，考虑增加权益类资产配置")
    if max_drawdown > 25:
        suggestions.append("回撤过大，建议增加债券或货币基金降低波动")
    if sharpe < 0.5:
        suggestions.append("夏普比率偏低，优化基金选择或调整配置比例")
    
    suggestions.append("定期（每月）记录组合净值，追踪长期表现")
    suggestions.append("与基准指数对比，评估主动管理能力")
    suggestions.append("关注最大回撤修复时间，评估组合韧性")
    
    return suggestions


def format_report(report: Dict) -> str:
    """格式化追踪报告（投资官六段式）"""
    b = report["basic_metrics"]
    r = report["risk_metrics"]
    a = report["analysis"]
    
    lines = [
        "=" * 60,
        "组合收益追踪报告",
        "=" * 60,
        "",
        "## 🧭 投资官视角",
        "",
        "### 一、核心结论",
        f"【评级】{report['rating']['level']}（{report['rating']['score']}/{report['rating']['max_score']}分）",
        f"【总收益】{b['profit']:,.0f} 元（{b['profit_percentage']:+.2f}%）",
        f"【年化收益】{b['annualized_return']:.2f}%",
        f"【最大回撤】{r['max_drawdown']:.2f}%",
        f"【夏普比率】{r['sharpe_ratio']:.2f}",
        "",
        "### 二、背后逻辑",
        f"• {a['return_comment']}",
        f"• {a['risk_comment']}",
        f"• {a['efficiency_comment']}",
        "",
        "【与基准对比】",
    ]
    
    for name, comp in report["benchmark_comparison"].items():
        symbol = "+" if comp["outperform"] else ""
        lines.append(f"• {name}: {comp['benchmark_return']:.1f}% ({symbol}{comp['diff']:+.1f}%)")
    
    lines.extend([
        "",
        "### 三、风险在哪里",
    ])
    
    if r["max_drawdown"] > 20:
        lines.append(f"⚠️ 最大回撤{r['max_drawdown']:.1f}%偏高，需关注风险控制")
    if r["volatility"] > 20:
        lines.append(f"⚠️ 波动率{r['volatility']:.1f}%较高，组合不够稳定")
    if r["sharpe_ratio"] < 0.3:
        lines.append(f"⚠️ 夏普比率{r['sharpe_ratio']:.2f}偏低，风险收益比不佳")
    
    if r["max_drawdown"] <= 20 and r["volatility"] <= 20 and r["sharpe_ratio"] >= 0.3:
        lines.append("✓ 风险指标在可控范围内")
    
    lines.extend([
        "",
        "### 四、适合谁",
        "• 已持有组合3个月以上、希望了解真实收益的投资者",
        "• 有明确收益目标、需要定期检视的投资者",
        "• 希望与基准对比、评估投资能力的投资者",
        "",
        "### 五、操作策略",
    ])
    
    for suggestion in report["suggestions"]:
        lines.append(f"✓ {suggestion}")
    
    lines.extend([
        "",
        "### 六、如果判断错了",
        "• 如短期收益不佳但长期逻辑未变，保持耐心，避免频繁调仓",
        "• 如连续6个月跑输基准，需重新审视投资策略",
        "• 如最大回撤超过心理承受范围，及时降低仓位",
        "• 建议设置'止损线'（如-20%）和'止盈线'（如+30%）",
        "",
        "=" * 60,
        f"追踪时间：{report['tracked_at']}",
        f"统计周期：{report['period_months']}个月",
        "=" * 60
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="组合收益追踪器")
    parser.add_argument("--initial", type=float, required=True,
                       help="初始投资金额（元）")
    parser.add_argument("--current", type=float, required=True,
                       help="当前组合价值（元）")
    parser.add_argument("--history", type=str, help="历史净值JSON文件")
    parser.add_argument("--months", type=int, default=12,
                       help="投资时长（月）")
    parser.add_argument("--output", type=str, help="输出JSON文件")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    # 加载历史数据
    history = None
    if args.history:
        with open(args.history, 'r', encoding='utf-8') as f:
            history = json.load(f)
    
    # 追踪组合
    report = track_portfolio(args.initial, args.current, history, args.months)
    
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
