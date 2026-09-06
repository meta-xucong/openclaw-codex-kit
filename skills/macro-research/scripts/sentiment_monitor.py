#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
情绪监控器

监控市场情绪指标

Usage:
    python sentiment_monitor.py --index "沪深300"
"""

import argparse
import json
from datetime import datetime
from typing import Dict, List


def calculate_fear_greed_index(indicators: Dict) -> Dict:
    """计算恐惧贪婪指数（0-100）"""
    
    # 各指标权重
    weights = {
        "market_momentum": 0.25,      # 市场动量
        "stock_price_strength": 0.20,  # 股价强度
        "stock_price_breadth": 0.15,   # 股价宽度
        "put_call_ratio": 0.15,        #  put/call比率
        "market_volatility": 0.15,     # 市场波动
        "safe_haven_demand": 0.10      # 避险需求
    }
    
    # 计算加权得分（每个指标0-100）
    total_score = 0
    for key, weight in weights.items():
        score = indicators.get(key, 50)
        total_score += score * weight
    
    # 确定情绪等级
    if total_score >= 75:
        sentiment = "极度贪婪"
        color = "🔴"
        action = "减仓"
    elif total_score >= 55:
        sentiment = "贪婪"
        color = "🟠"
        action = "逐步减仓"
    elif total_score >= 45:
        sentiment = "中性"
        color = "🟡"
        action = "持有"
    elif total_score >= 25:
        sentiment = "恐惧"
        color = "🔵"
        action = "逐步加仓"
    else:
        sentiment = "极度恐惧"
        color = "🟢"
        action = "加仓"
    
    return {
        "index_value": round(total_score, 1),
        "sentiment": sentiment,
        "color": color,
        "suggested_action": action,
        "components": indicators
    }


def analyze_market_breadth(data: Dict) -> Dict:
    """分析市场广度"""
    
    advancing = data.get("advancing_stocks", 2000)
    declining = data.get("declining_stocks", 2000)
    total = advancing + declining
    
    if total > 0:
        advance_decline_ratio = advancing / declining if declining > 0 else 999
        breadth_indicator = (advancing / total) * 100
    else:
        advance_decline_ratio = 1
        breadth_indicator = 50
    
    return {
        "advancing_stocks": advancing,
        "declining_stocks": declining,
        "advance_decline_ratio": round(advance_decline_ratio, 2),
        "breadth_indicator": round(breadth_indicator, 1),
        "interpretation": "普涨" if breadth_indicator > 60 else "普跌" if breadth_indicator < 40 else "分化"
    }


def analyze_volume_trend(data: Dict) -> Dict:
    """分析量能趋势"""
    
    current_volume = data.get("current_volume", 1000)
    avg_volume = data.get("avg_volume", 1000)
    
    if avg_volume > 0:
        volume_ratio = current_volume / avg_volume
    else:
        volume_ratio = 1
    
    if volume_ratio > 1.5:
        trend = "放量"
        signal = "积极" if data.get("price_change", 0) > 0 else "警惕"
    elif volume_ratio < 0.7:
        trend = "缩量"
        signal = "观望"
    else:
        trend = "平量"
        signal = "中性"
    
    return {
        "volume_ratio": round(volume_ratio, 2),
        "trend": trend,
        "signal": signal
    }


def analyze_fund_flow(data: Dict) -> Dict:
    """分析资金流向"""
    
    northbound = data.get("northbound_flow", 0)  # 北向资金
    main_force = data.get("main_force_flow", 0)   # 主力资金
    retail = data.get("retail_flow", 0)           # 散户资金
    
    total_flow = northbound + main_force + retail
    
    return {
        "northbound": northbound,
        "main_force": main_force,
        "retail": retail,
        "total_flow": total_flow,
        "interpretation": "资金净流入" if total_flow > 0 else "资金净流出",
        "strength": "强" if abs(total_flow) > 100 else "中" if abs(total_flow) > 50 else "弱"
    }


def generate_sentiment_report(index_name: str, data: Dict) -> Dict:
    """生成情绪监控报告"""
    
    # 计算恐惧贪婪指数
    fear_greed = calculate_fear_greed_index(data.get("indicators", {}))
    
    # 市场广度
    breadth = analyze_market_breadth(data.get("breadth", {}))
    
    # 量能趋势
    volume = analyze_volume_trend(data.get("volume", {}))
    
    # 资金流向
    fund_flow = analyze_fund_flow(data.get("fund_flow", {}))
    
    return {
        "monitored_at": datetime.now().isoformat(),
        "index": index_name,
        "fear_greed_index": fear_greed,
        "market_breadth": breadth,
        "volume_trend": volume,
        "fund_flow": fund_flow,
        "overall_assessment": generate_overall_assessment(fear_greed, breadth, volume, fund_flow),
        "suggestions": generate_sentiment_suggestions(fear_greed, fund_flow)
    }


def generate_overall_assessment(fear_greed: Dict, breadth: Dict, 
                                volume: Dict, fund_flow: Dict) -> Dict:
    """生成综合评估"""
    
    score = fear_greed["index_value"]
    
    # 综合判断
    if score >= 70 and fund_flow["total_flow"] < 0:
        assessment = "顶部特征明显，建议减仓"
        risk_level = "高"
    elif score <= 30 and fund_flow["total_flow"] > 0:
        assessment = "底部特征显现，建议加仓"
        risk_level = "低"
    elif 40 <= score <= 60:
        assessment = "市场情绪中性，维持现有仓位"
        risk_level = "中"
    else:
        assessment = "情绪与资金背离，保持谨慎"
        risk_level = "中高"
    
    return {
        "assessment": assessment,
        "risk_level": risk_level,
        "key_signals": [
            f"恐惧贪婪指数：{fear_greed['index_value']:.0f}（{fear_greed['sentiment']}）",
            f"市场广度：{breadth['interpretation']}（上涨{breadth['breadth_indicator']:.0f}%）",
            f"量能趋势：{volume['trend']}（{volume['signal']}）",
            f"资金流向：{fund_flow['interpretation']}（力度{fund_flow['strength']}）"
        ]
    }


def generate_sentiment_suggestions(fear_greed: Dict, fund_flow: Dict) -> List[str]:
    """生成情绪操作建议"""
    
    suggestions = []
    
    # 基于恐惧贪婪指数
    if fear_greed["index_value"] >= 75:
        suggestions.append("市场情绪极度贪婪，考虑逐步减仓")
        suggestions.append("关注估值过高的板块，及时获利了结")
    elif fear_greed["index_value"] <= 25:
        suggestions.append("市场情绪极度恐惧，可能是布局良机")
        suggestions.append("关注被错杀的优质资产")
    
    # 基于资金流向
    if fund_flow["total_flow"] > 100:
        suggestions.append("资金大幅净流入，短期或有支撑")
    elif fund_flow["total_flow"] < -100:
        suggestions.append("资金大幅净流出，注意风险")
    
    # 通用建议
    suggestions.append("情绪指标仅供参考，不单独作为买卖依据")
    suggestions.append("结合基本面和技术面综合判断")
    suggestions.append("避免情绪化交易，坚持投资纪律")
    
    return suggestions


def format_report(report: Dict) -> str:
    """格式化情绪监控报告（投资官六段式）"""
    
    fg = report["fear_greed_index"]
    mb = report["market_breadth"]
    vt = report["volume_trend"]
    ff = report["fund_flow"]
    oa = report["overall_assessment"]
    
    lines = [
        "=" * 60,
        f"市场情绪监控报告 - {report['index']}",
        "=" * 60,
        "",
        "## 🧭 投资官视角",
        "",
        "### 一、核心结论",
        f"【恐惧贪婪指数】{fg['color']} {fg['index_value']:.0f}/100 - {fg['sentiment']}",
        f"【建议操作】{fg['suggested_action']}",
        f"【综合评估】{oa['assessment']}",
        f"【风险等级】{oa['risk_level']}",
        "",
        "### 二、背后逻辑",
        "【关键信号】",
    ]
    
    for signal in oa["key_signals"]:
        lines.append(f"• {signal}")
    
    lines.extend([
        "",
        "【指标详解】",
        f"• 涨跌家数比：{mb['advance_decline_ratio']:.2f}（{mb['advancing_stocks']}涨 vs {mb['declining_stocks']}跌）",
        f"• 量能水平：{vt['volume_ratio']:.2f}倍于均值（{vt['trend']}）",
        f"• 资金流向：北向{ff['northbound']:.0f}亿 + 主力{ff['main_force']:.0f}亿 + 散户{ff['retail']:.0f}亿",
        "",
        "### 三、风险在哪里",
        "⚠️ 情绪指标可能短期波动，不代表长期趋势",
        "⚠️ 极端情绪可能持续，不要逆势过早",
        "⚠️ 机构可能利用情绪指标反向操作",
        "⚠️ 单一指标不可靠，需多维度验证",
        "",
        "### 四、适合谁",
        "• 进行中短期交易的投资者",
        "• 希望把握市场情绪节奏的投资者",
        "• 有纪律性、能克服情绪干扰的投资者",
        "",
        "### 五、操作策略",
    ])
    
    for suggestion in report["suggestions"]:
        lines.append(f"✓ {suggestion}")
    
    lines.extend([
        "",
        "【情绪指数使用指南】",
        "• 0-25：极度恐惧，考虑逐步加仓",
        "• 26-45：恐惧，关注机会",
        "• 46-55：中性，持有观望",
        "• 56-75：贪婪，考虑减仓",
        "• 76-100：极度贪婪，果断减仓",
        "",
        "### 六、如果判断错了",
        "• 如情绪指标与市场走势背离，以价格走势为准",
        "• 如情绪极端但市场继续上涨，等待确认信号",
        "• 如情绪好转但市场继续下跌，警惕趋势反转",
        "• 建议设置止损线，不因情绪而扛单",
        "",
        "=" * 60,
        f"监控时间：{report['monitored_at']}",
        "=" * 60
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="情绪监控器")
    parser.add_argument("--index", type=str, default="沪深300",
                       help="监控的指数")
    parser.add_argument("--fear-greed", type=float,
                       help="恐惧贪婪指数（0-100）")
    parser.add_argument("--output", type=str, help="输出JSON文件")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    # 模拟数据（实际应从数据源获取）
    mock_data = {
        "indicators": {
            "market_momentum": args.fear_greed if args.fear_greed else 45,
            "stock_price_strength": 50,
            "stock_price_breadth": 48,
            "put_call_ratio": 45,
            "market_volatility": 52,
            "safe_haven_demand": 40
        },
        "breadth": {
            "advancing_stocks": 1800,
            "declining_stocks": 2200
        },
        "volume": {
            "current_volume": 8500,
            "avg_volume": 8000,
            "price_change": -0.5
        },
        "fund_flow": {
            "northbound": -20,
            "main_force": -50,
            "retail": 30
        }
    }
    
    report = generate_sentiment_report(args.index, mock_data)
    
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
