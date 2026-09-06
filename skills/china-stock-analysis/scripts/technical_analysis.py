#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["akshare"]
# ///
"""
A股技术分析器

计算K线技术指标，识别技术形态

Usage:
    python technical_analysis.py --code 000001 --period daily
"""

import argparse
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


def calculate_ma(prices: List[float], period: int) -> List[float]:
    """计算移动平均线"""
    if len(prices) < period:
        return []
    
    ma = []
    for i in range(len(prices)):
        if i < period - 1:
            ma.append(None)
        else:
            ma.append(sum(prices[i-period+1:i+1]) / period)
    return ma


def calculate_ema(prices: List[float], period: int) -> List[float]:
    """计算指数移动平均线"""
    if len(prices) < period:
        return []
    
    multiplier = 2 / (period + 1)
    ema = [sum(prices[:period]) / period]  # 初始值用SMA
    
    for i in range(period, len(prices)):
        ema.append((prices[i] - ema[-1]) * multiplier + ema[-1])
    
    # 补齐前面的None
    return [None] * (period - 1) + ema


def calculate_macd(prices: List[float]) -> Dict:
    """计算MACD指标"""
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)
    
    # DIF = EMA12 - EMA26
    dif = []
    for i in range(len(prices)):
        if ema12[i] is None or ema26[i] is None:
            dif.append(None)
        else:
            dif.append(ema12[i] - ema26[i])
    
    # DEA = EMA(DIF, 9)
    valid_dif = [d for d in dif if d is not None]
    dea_values = calculate_ema(valid_dif, 9) if len(valid_dif) >= 9 else []
    
    # 补齐dea
    dea = [None] * (len(prices) - len(dea_values)) + dea_values if dea_values else [None] * len(prices)
    
    # MACD = 2 * (DIF - DEA)
    macd = []
    for i in range(len(prices)):
        if dif[i] is not None and len(dea) > i and dea[i] is not None:
            macd.append(2 * (dif[i] - dea[i]))
        else:
            macd.append(None)
    
    return {
        "dif": dif[-1] if dif and dif[-1] is not None else 0,
        "dea": dea[-1] if dea and dea[-1] is not None else 0,
        "macd": macd[-1] if macd and macd[-1] is not None else 0,
        "signal": "金叉" if dif[-1] > dea[-1] and dif[-2] <= dea[-2] else \
                 "死叉" if dif[-1] < dea[-1] and dif[-2] >= dea[-2] else "无"
    }


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """计算RSI指标"""
    if len(prices) < period + 1:
        return 50.0
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    if len(gains) < period:
        return 50.0
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)


def calculate_kdj(highs: List[float], lows: List[float], closes: List[float], 
                  n: int = 9, m1: int = 3, m2: int = 3) -> Dict:
    """计算KDJ指标"""
    if len(closes) < n:
        return {"k": 50, "d": 50, "j": 50}
    
    # RSV
    rsv_list = []
    for i in range(n - 1, len(closes)):
        period_high = max(highs[i-n+1:i+1])
        period_low = min(lows[i-n+1:i+1])
        if period_high == period_low:
            rsv = 50
        else:
            rsv = 100 * (closes[i] - period_low) / (period_high - period_low)
        rsv_list.append(rsv)
    
    # K, D, J
    k = 50
    d = 50
    
    for rsv in rsv_list:
        k = (2 * k + rsv) / 3
        d = (2 * d + k) / 3
    
    j = 3 * k - 2 * d
    
    return {
        "k": round(k, 2),
        "d": round(d, 2),
        "j": round(j, 2),
        "signal": "金叉" if k > d and k <= 20 else \
                 "死叉" if k < d and k >= 80 else "无"
    }


def calculate_bollinger(prices: List[float], period: int = 20, std_dev: int = 2) -> Dict:
    """计算布林带"""
    if len(prices) < period:
        return {"upper": 0, "middle": 0, "lower": 0, "position": "unknown"}
    
    recent_prices = prices[-period:]
    middle = sum(recent_prices) / period
    variance = sum((p - middle) ** 2 for p in recent_prices) / period
    std = variance ** 0.5
    
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    
    current_price = prices[-1]
    
    if current_price > upper:
        position = "上轨上方"
    elif current_price < lower:
        position = "下轨下方"
    else:
        position = "中轨附近"
    
    return {
        "upper": round(upper, 2),
        "middle": round(middle, 2),
        "lower": round(lower, 2),
        "position": position,
        "bandwidth": round((upper - lower) / middle * 100, 2)
    }


def identify_trend(prices: List[float], ma5: List[float], ma20: List[float]) -> Dict:
    """识别趋势"""
    if len(prices) < 20 or not ma5[-1] or not ma20[-1]:
        return {"trend": "unknown", "strength": 0}
    
    # 短期vs长期均线
    short_above_long = ma5[-1] > ma20[-1]
    
    # 价格vs均线
    price_above_ma20 = prices[-1] > ma20[-1]
    
    # 均线方向
    ma5_rising = ma5[-1] > ma5[-5] if len(ma5) >= 5 and ma5[-5] else False
    ma20_rising = ma20[-1] > ma20[-10] if len(ma20) >= 10 and ma20[-10] else False
    
    if short_above_long and price_above_ma20 and ma5_rising and ma20_rising:
        trend = "上升趋势"
        strength = 3
    elif not short_above_long and not price_above_ma20 and not ma5_rising and not ma20_rising:
        trend = "下降趋势"
        strength = -3
    elif short_above_long and price_above_ma20:
        trend = "偏多震荡"
        strength = 1
    elif not short_above_long and not price_above_ma20:
        trend = "偏空震荡"
        strength = -1
    else:
        trend = "横盘整理"
        strength = 0
    
    return {"trend": trend, "strength": strength}


def identify_support_resistance(prices: List[float], highs: List[float], 
                                 lows: List[float], period: int = 20) -> Dict:
    """识别支撑阻力位"""
    if len(prices) < period:
        return {"support": 0, "resistance": 0}
    
    recent_highs = highs[-period:]
    recent_lows = lows[-period:]
    
    resistance = max(recent_highs)
    support = min(recent_lows)
    
    current = prices[-1]
    
    # 计算距离
    dist_to_support = (current - support) / current * 100 if support > 0 else 0
    dist_to_resistance = (resistance - current) / current * 100 if resistance > 0 else 0
    
    return {
        "support": round(support, 2),
        "resistance": round(resistance, 2),
        "dist_to_support": round(dist_to_support, 2),
        "dist_to_resistance": round(dist_to_resistance, 2),
        "near_support": dist_to_support < 3,
        "near_resistance": dist_to_resistance < 3
    }


def generate_technical_analysis(code: str, prices: List[float], 
                                highs: List[float], lows: List[float],
                                volumes: List[float], period: str) -> Dict:
    """生成技术分析报告"""
    
    # 计算指标
    ma5 = calculate_ma(prices, 5)
    ma10 = calculate_ma(prices, 10)
    ma20 = calculate_ma(prices, 20)
    ma60 = calculate_ma(prices, 60)
    
    macd = calculate_macd(prices)
    rsi = calculate_rsi(prices)
    kdj = calculate_kdj(highs, lows, prices)
    boll = calculate_bollinger(prices)
    trend = identify_trend(prices, ma5, ma20)
    sr = identify_support_resistance(prices, highs, lows)
    
    # 综合评分
    score = calculate_technical_score(macd, rsi, kdj, trend, boll)
    
    return {
        "analyzed_at": datetime.now().isoformat(),
        "code": code,
        "period": period,
        "current_price": prices[-1] if prices else 0,
        "moving_averages": {
            "ma5": round(ma5[-1], 2) if ma5 and ma5[-1] else None,
            "ma10": round(ma10[-1], 2) if ma10 and ma10[-1] else None,
            "ma20": round(ma20[-1], 2) if ma20 and ma20[-1] else None,
            "ma60": round(ma60[-1], 2) if ma60 and ma60[-1] else None
        },
        "indicators": {
            "macd": macd,
            "rsi": rsi,
            "kdj": kdj,
            "bollinger": boll
        },
        "trend": trend,
        "support_resistance": sr,
        "technical_score": score,
        "signals": generate_signals(macd, rsi, kdj, trend, sr),
        "suggestions": generate_technical_suggestions(score, trend, sr)
    }


def calculate_technical_score(macd: Dict, rsi: float, kdj: Dict, 
                              trend: Dict, boll: Dict) -> Dict:
    """计算技术评分"""
    score = 50  # 中性
    
    # MACD
    if macd.get("macd", 0) > 0:
        score += 10
    if macd.get("signal") == "金叉":
        score += 15
    elif macd.get("signal") == "死叉":
        score -= 15
    
    # RSI
    if 40 <= rsi <= 60:
        score += 5
    elif rsi < 30:
        score += 10  # 超卖
    elif rsi > 70:
        score -= 10  # 超买
    
    # KDJ
    if kdj.get("signal") == "金叉":
        score += 10
    elif kdj.get("signal") == "死叉":
        score -= 10
    
    # 趋势
    score += trend.get("strength", 0) * 3
    
    # 布林带位置
    if boll.get("position") == "下轨下方":
        score += 10
    elif boll.get("position") == "上轨上方":
        score -= 10
    
    score = max(0, min(100, score))
    
    if score >= 70:
        rating = "看多"
    elif score >= 55:
        rating = "偏多"
    elif score >= 45:
        rating = "中性"
    elif score >= 30:
        rating = "偏空"
    else:
        rating = "看空"
    
    return {"score": score, "rating": rating}


def generate_signals(macd: Dict, rsi: float, kdj: Dict, 
                    trend: Dict, sr: Dict) -> List[str]:
    """生成交易信号"""
    signals = []
    
    if macd.get("signal") == "金叉":
        signals.append("MACD金叉，短期看涨")
    elif macd.get("signal") == "死叉":
        signals.append("MACD死叉，短期看跌")
    
    if rsi < 30:
        signals.append("RSI超卖，可能反弹")
    elif rsi > 70:
        signals.append("RSI超买，可能回调")
    
    if kdj.get("signal") == "金叉":
        signals.append("KDJ金叉，买入信号")
    elif kdj.get("signal") == "死叉":
        signals.append("KDJ死叉，卖出信号")
    
    if sr.get("near_support"):
        signals.append(f"接近支撑位{sr['support']}，关注反弹")
    if sr.get("near_resistance"):
        signals.append(f"接近阻力位{sr['resistance']}，注意压力")
    
    if not signals:
        signals.append("暂无明确信号，观望为主")
    
    return signals


def generate_technical_suggestions(score: Dict, trend: Dict, sr: Dict) -> List[str]:
    """生成操作建议"""
    suggestions = []
    
    if score["score"] >= 70:
        suggestions.append("技术面向好，可考虑逢低买入")
    elif score["score"] <= 30:
        suggestions.append("技术面偏弱，建议观望或减仓")
    else:
        suggestions.append("技术面中性，维持现有仓位")
    
    if sr.get("near_support"):
        suggestions.append(f"可在支撑位{sr['support']}附近试探性买入")
    if sr.get("near_resistance"):
        suggestions.append(f"可在阻力位{sr['resistance']}附近减仓")
    
    suggestions.append("技术指标仅供参考，需结合基本面综合判断")
    suggestions.append("设置止损位，控制风险")
    
    return suggestions


def format_report(report: Dict) -> str:
    """格式化技术分析报告（投资官六段式）"""
    
    ma = report["moving_averages"]
    ind = report["indicators"]
    score = report["technical_score"]
    
    lines = [
        "=" * 60,
        f"技术分析报告 - {report['code']}",
        "=" * 60,
        "",
        "## 🧭 投资官视角",
        "",
        "### 一、核心结论",
        f"【当前价格】{report['current_price']:.2f}",
        f"【技术评分】{score['score']:.0f}/100 - {score['rating']}",
        f"【趋势判断】{report['trend']['trend']}",
        "",
        "### 二、背后逻辑",
        "【均线系统】",
        f"• MA5: {ma['ma5']:.2f}" if ma['ma5'] else "• MA5: N/A",
        f"• MA10: {ma['ma10']:.2f}" if ma['ma10'] else "• MA10: N/A",
        f"• MA20: {ma['ma20']:.2f}" if ma['ma20'] else "• MA20: N/A",
        f"• MA60: {ma['ma60']:.2f}" if ma['ma60'] else "• MA60: N/A",
        "",
        "【技术指标】",
        f"• MACD: DIF={ind['macd']['dif']:.2f}, DEA={ind['macd']['dea']:.2f}, "
        f"MACD={ind['macd']['macd']:.2f} ({ind['macd']['signal']})",
        f"• RSI: {ind['rsi']:.2f}",
        f"• KDJ: K={ind['kdj']['k']:.2f}, D={ind['kdj']['d']:.2f}, J={ind['kdj']['j']:.2f}",
        f"• 布林带: 上轨{ind['bollinger']['upper']}, 中轨{ind['bollinger']['middle']}, "
        f"下轨{ind['bollinger']['lower']} ({ind['bollinger']['position']})",
        "",
        "【支撑阻力】",
        f"• 支撑位: {report['support_resistance']['support']:.2f} "
        f"(距离{report['support_resistance']['dist_to_support']:.1f}%)",
        f"• 阻力位: {report['support_resistance']['resistance']:.2f} "
        f"(距离{report['support_resistance']['dist_to_resistance']:.1f}%)",
        "",
        "### 三、风险在哪里",
        "⚠️ 技术分析基于历史数据，不保证未来走势",
        "⚠️ 单一指标不可靠，需多指标共振",
        "⚠️ 突发事件可能导致技术形态失效",
        "⚠️ 震荡市技术指标容易发出错误信号",
        "",
        "### 四、适合谁",
        "• 进行中短期交易的投资者",
        "• 希望把握买卖时机的技术派投资者",
        "• 已有基本面判断、需要择时的投资者",
        "",
        "### 五、操作策略",
        "【交易信号】",
    ]
    
    for signal in report["signals"]:
        lines.append(f"• {signal}")
    
    lines.extend([
        "",
        "【操作建议】",
    ])
    
    for suggestion in report["suggestions"]:
        lines.append(f"✓ {suggestion}")
    
    lines.extend([
        "",
        "### 六、如果判断错了",
        "• 如买入后跌破支撑位，及时止损",
        "• 如卖出后突破阻力位，不要追高",
        "• 如指标背离，以价格走势为准",
        "• 建议单笔亏损不超过总资金的2%",
        "",
        "=" * 60,
        f"分析时间：{report['analyzed_at']}",
        "=" * 60
    ])
    
    return "\n".join(lines)


def fetch_mock_data(code: str, period: str) -> Tuple[List[float], List[float], List[float], List[float]]:
    """获取模拟数据（实际应使用akshare获取真实数据）"""
    import random
    
    # 生成模拟价格数据
    base_price = random.uniform(10, 100)
    prices = [base_price]
    highs = [base_price * 1.02]
    lows = [base_price * 0.98]
    volumes = [random.randint(1000000, 10000000)]
    
    for _ in range(99):
        change = random.uniform(-0.03, 0.03)
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
        highs.append(new_price * random.uniform(1.0, 1.03))
        lows.append(new_price * random.uniform(0.97, 1.0))
        volumes.append(random.randint(1000000, 10000000))
    
    return prices, highs, lows, volumes


def main():
    parser = argparse.ArgumentParser(description="A股技术分析器")
    parser.add_argument("--code", type=str, required=True,
                       help="股票代码")
    parser.add_argument("--period", type=str, default="daily",
                       choices=["daily", "weekly", "monthly"],
                       help="分析周期")
    parser.add_argument("--days", type=int, default=100,
                       help="分析天数")
    parser.add_argument("--output", type=str, help="输出JSON文件")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    try:
        # 获取数据（实际应使用akshare）
        prices, highs, lows, volumes = fetch_mock_data(args.code, args.period)
        
        # 生成分析
        report = generate_technical_analysis(
            args.code, prices, highs, lows, volumes, args.period
        )
        
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
            
    except Exception as e:
        print(f"分析失败: {e}")
        print("提示：当前使用模拟数据，实际使用时需要安装akshare并接入真实数据源")


if __name__ == "__main__":
    main()
