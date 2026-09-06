#!/usr/bin/env python
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
组合再平衡规划器

根据当前组合和目标配置生成调仓方案

Usage:
    python rebalance_planner.py --current current.json --target target.json
    python rebalance_planner.py --current "510300:35,159915:25,511880:40" --target "510300:40,159915:30,511880:30"
"""

import argparse
import json
from datetime import datetime
from typing import Dict, List, Tuple


def parse_portfolio_string(portfolio_str: str) -> Dict[str, float]:
    """解析组合字符串，格式：code1:ratio1,code2:ratio2"""
    allocations = {}
    for item in portfolio_str.split(","):
        parts = item.split(":")
        if len(parts) == 2:
            code = parts[0].strip()
            ratio = float(parts[1].strip())
            allocations[code] = ratio
    return allocations


def calculate_rebalance_plan(
    current: Dict[str, float],
    target: Dict[str, float],
    total_value: float,
    threshold: float = 5.0
) -> Dict:
    """计算再平衡方案"""
    
    # 合并所有资产代码
    all_codes = set(current.keys()) | set(target.keys())
    
    # 计算当前各资产金额
    current_amounts = {code: total_value * current.get(code, 0) / 100 for code in all_codes}
    
    # 计算目标金额
    target_amounts = {code: total_value * target.get(code, 0) / 100 for code in all_codes}
    
    # 计算差异
    differences = {}
    for code in all_codes:
        diff_pct = target.get(code, 0) - current.get(code, 0)
        diff_amount = target_amounts.get(code, 0) - current_amounts.get(code, 0)
        differences[code] = {
            "current_ratio": current.get(code, 0),
            "target_ratio": target.get(code, 0),
            "diff_ratio": diff_pct,
            "current_amount": current_amounts.get(code, 0),
            "target_amount": target_amounts.get(code, 0),
            "diff_amount": diff_amount,
            "action": "买入" if diff_amount > 0 else "卖出" if diff_amount < 0 else "持有",
            "needs_rebalance": abs(diff_pct) >= threshold
        }
    
    # 需要调仓的资产
    rebalance_items = {k: v for k, v in differences.items() if v["needs_rebalance"]}
    
    # 计算总调仓金额
    total_buy = sum(v["diff_amount"] for v in differences.values() if v["diff_amount"] > 0)
    total_sell = sum(abs(v["diff_amount"]) for v in differences.values() if v["diff_amount"] < 0)
    
    # 生成建议
    suggestions = generate_rebalance_suggestions(differences, threshold)
    
    return {
        "generated_at": datetime.now().isoformat(),
        "total_value": total_value,
        "threshold": threshold,
        "summary": {
            "total_codes": len(all_codes),
            "rebalance_codes": len(rebalance_items),
            "total_buy": round(total_buy, 2),
            "total_sell": round(total_sell, 2),
            "estimated_cost": round(total_sell * 0.001, 2)  # 假设交易成本0.1%
        },
        "differences": differences,
        "rebalance_plan": rebalance_items,
        "suggestions": suggestions,
        "execution_steps": generate_execution_steps(differences)
    }


def generate_rebalance_suggestions(differences: Dict, threshold: float) -> List[str]:
    """生成再平衡建议"""
    suggestions = []
    
    # 检查偏离度
    max_deviation = max(abs(v["diff_ratio"]) for v in differences.values())
    if max_deviation < threshold:
        suggestions.append("组合偏离度较小，可暂不调仓")
    elif max_deviation < 10:
        suggestions.append("组合有轻度偏离，建议逐步调整")
    else:
        suggestions.append("组合偏离较大，建议尽快再平衡")
    
    # 检查交易方向
    buy_codes = [k for k, v in differences.items() if v["diff_amount"] > 0]
    sell_codes = [k for k, v in differences.items() if v["diff_amount"] < 0]
    
    if len(buy_codes) > len(sell_codes):
        suggestions.append("买入标的较多，注意资金安排")
    if len(sell_codes) > 0:
        suggestions.append(f"先卖出 {', '.join(sell_codes)} 释放资金")
    
    # 成本提醒
    suggestions.append("注意交易成本，频繁调仓会侵蚀收益")
    suggestions.append("建议分批执行，避免一次性重仓")
    
    return suggestions


def generate_execution_steps(differences: Dict) -> List[Dict]:
    """生成执行步骤"""
    steps = []
    
    # 先卖出
    sell_items = [(k, v) for k, v in differences.items() if v["diff_amount"] < 0]
    sell_items.sort(key=lambda x: abs(x[1]["diff_amount"]), reverse=True)
    
    for code, info in sell_items:
        steps.append({
            "step": len(steps) + 1,
            "action": "卖出",
            "code": code,
            "amount": round(abs(info["diff_amount"]), 2),
            "ratio": f"{info['current_ratio']}% → {info['target_ratio']}%",
            "note": "先释放资金"
        })
    
    # 再买入
    buy_items = [(k, v) for k, v in differences.items() if v["diff_amount"] > 0]
    buy_items.sort(key=lambda x: x[1]["diff_amount"], reverse=True)
    
    for code, info in buy_items:
        steps.append({
            "step": len(steps) + 1,
            "action": "买入",
            "code": code,
            "amount": round(info["diff_amount"], 2),
            "ratio": f"{info['current_ratio']}% → {info['target_ratio']}%",
            "note": "用卖出资金买入"
        })
    
    return steps


def format_report(plan: Dict) -> str:
    """格式化再平衡报告（投资官六段式）"""
    s = plan["summary"]
    
    lines = [
        "=" * 60,
        "组合再平衡规划方案",
        "=" * 60,
        "",
        "## 🧭 投资官视角",
        "",
        "### 一、核心结论",
        f"【组合总价值】{plan['total_value']:,.0f} 元",
        f"【需调仓标的】{s['rebalance_codes']} / {s['total_codes']} 只",
        f"【预计卖出】{s['total_sell']:,.0f} 元",
        f"【预计买入】{s['total_buy']:,.0f} 元",
        f"【预估成本】{s['estimated_cost']:,.0f} 元（约{s['estimated_cost']/plan['total_value']*100:.2f}%）",
        "",
        "### 二、背后逻辑",
        "再平衡的本质是'高抛低吸'，通过定期调整让组合回归目标配置：",
        "• 卖出涨幅过大的资产，锁定收益",
        "• 买入跌幅较多的资产，摊低成本",
        "• 维持风险水平在可控范围内",
        f"• 当前偏离阈值设为 {plan['threshold']}%，超过才触发调仓",
        "",
        "### 三、风险在哪里",
    ]
    
    # 检查风险
    risks = []
    if s["estimated_cost"] / plan["total_value"] > 0.005:
        risks.append("交易成本较高，可能侵蚀收益")
    if s["rebalance_codes"] > 5:
        risks.append("调仓标的过多，操作复杂")
    
    if risks:
        for risk in risks:
            lines.append(f"⚠️ {risk}")
    else:
        lines.append("✓ 未发现明显风险")
    
    lines.extend([
        "",
        "### 四、适合谁",
        "• 已持有组合3个月以上、偏离目标配置的投资者",
        "• 有明确资产配置目标、希望维持风险水平的投资者",
        "• 能够承受短期交易成本、追求长期稳定收益的投资者",
        "",
        "### 五、操作策略",
        "【调仓明细】",
    ])
    
    # 显示差异
    lines.append(f"{'标的':<10} {'当前':>8} {'目标':>8} {'差异':>8} {'操作':>6} {'金额':>12}")
    lines.append("-" * 60)
    for code, info in plan["differences"].items():
        if info["needs_rebalance"]:
            lines.append(f"{code:<10} {info['current_ratio']:>7.1f}% {info['target_ratio']:>7.1f}% "
                        f"{info['diff_ratio']:>+7.1f}% {info['action']:>6} {abs(info['diff_amount']):>11,.0f}")
    
    lines.extend([
        "",
        "【执行建议】",
    ])
    for suggestion in plan["suggestions"]:
        lines.append(f"• {suggestion}")
    
    lines.extend([
        "",
        "【执行步骤】",
    ])
    for step in plan["execution_steps"]:
        lines.append(f"{step['step']}. {step['action']} {step['code']} {step['amount']:,.0f}元 "
                    f"({step['ratio']}) - {step['note']}")
    
    lines.extend([
        "",
        "### 六、如果判断错了",
        "• 如市场正处于单边上涨行情，再平衡可能踏空，可延迟执行",
        "• 如市场正处于单边下跌行情，再平衡可能加剧亏损，可分批执行",
        "• 如调仓后某资产继续下跌，不要恐慌，这是再平衡的正常成本",
        "• 建议设置'不触发区间'，偏离度在3%以内可忽略",
        "",
        "=" * 60,
        f"生成时间：{plan['generated_at']}",
        "=" * 60
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="组合再平衡规划器")
    parser.add_argument("--current", type=str, required=True,
                       help="当前配置JSON文件或格式：code1:ratio1,code2:ratio2")
    parser.add_argument("--target", type=str, required=True,
                       help="目标配置JSON文件或格式：code1:ratio1,code2:ratio2")
    parser.add_argument("--value", type=float, default=100000,
                       help="组合总价值（元）")
    parser.add_argument("--threshold", type=float, default=5.0,
                       help="触发再平衡的偏离阈值（%）")
    parser.add_argument("--output", type=str, help="输出JSON文件")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    # 解析当前配置
    if args.current.endswith('.json'):
        with open(args.current, 'r', encoding='utf-8') as f:
            current = json.load(f)
    else:
        current = parse_portfolio_string(args.current)
    
    # 解析目标配置
    if args.target.endswith('.json'):
        with open(args.target, 'r', encoding='utf-8') as f:
            target = json.load(f)
    else:
        target = parse_portfolio_string(args.target)
    
    # 计算再平衡方案
    plan = calculate_rebalance_plan(current, target, args.value, args.threshold)
    
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
