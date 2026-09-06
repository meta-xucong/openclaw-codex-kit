#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
周期判断器

基于美林时钟判断经济周期阶段

Usage:
    python cycle_analyzer.py --gdp-growth 5.5 --inflation 2.1
"""

import argparse
import json
from datetime import datetime
from typing import Dict, List


def identify_cycle_phase(gdp_growth: float, inflation: float, 
                         gdp_trend: float = 0, inflation_trend: float = 0) -> Dict:
    """识别经济周期阶段（美林时钟）"""
    
    # 判断增长和通胀相对于趋势的位置
    growth_high = gdp_growth > gdp_trend if gdp_trend else gdp_growth > 5.0
    inflation_high = inflation > 2.5
    
    # 美林时钟四阶段
    if growth_high and inflation_high:
        phase = "过热期"
        description = "经济增长强劲，通胀上升"
        color = "🔴"
        characteristics = [
            "企业盈利强劲",
            "大宗商品价格上涨",
            "央行开始收紧货币政策",
            "股市可能见顶"
        ]
    elif growth_high and not inflation_high:
        phase = "复苏期"
        description = "经济增长强劲，通胀温和"
        color = "🟢"
        characteristics = [
            "企业盈利改善",
            "就业市场好转",
            "货币政策宽松",
            "股市表现最佳"
        ]
    elif not growth_high and not inflation_high:
        phase = "衰退期"
        description = "经济增长放缓，通胀下降"
        color = "🔵"
        characteristics = [
            "企业盈利下滑",
            "失业率上升",
            "央行降息刺激经济",
            "债券表现最佳"
        ]
    else:  # not growth_high and inflation_high
        phase = "滞胀期"
        description = "经济增长放缓，通胀高企"
        color = "🟡"
        characteristics = [
            "企业盈利受压",
            "成本上升",
            "央行两难（保增长vs控通胀）",
            "现金为王"
        ]
    
    return {
        "phase": phase,
        "color": color,
        "description": description,
        "characteristics": characteristics,
        "gdp_growth": gdp_growth,
        "inflation": inflation,
        "gdp_vs_trend": "高于趋势" if growth_high else "低于趋势",
        "inflation_level": "高通胀" if inflation_high else "低通胀"
    }


def get_asset_allocation(phase: str) -> Dict:
    """获取大类资产配置建议"""
    
    allocations = {
        "复苏期": {
            "stocks": 50,
            "bonds": 30,
            "commodities": 10,
            "cash": 10,
            "rationale": "经济向好，企业盈利改善，股票最佳",
            "preferred_sectors": ["金融", "工业", "可选消费"],
            "avoid_sectors": ["公用事业", "必需消费"]
        },
        "过热期": {
            "stocks": 30,
            "bonds": 20,
            "commodities": 40,
            "cash": 10,
            "rationale": "通胀上升，大宗商品受益，股票估值受压",
            "preferred_sectors": ["能源", "原材料", "科技"],
            "avoid_sectors": ["债券敏感行业"]
        },
        "滞胀期": {
            "stocks": 20,
            "bonds": 20,
            "commodities": 30,
            "cash": 30,
            "rationale": "经济停滞+通胀，现金为王，商品抗通胀",
            "preferred_sectors": ["能源", "必需消费", "医疗"],
            "avoid_sectors": ["周期股", "成长股"]
        },
        "衰退期": {
            "stocks": 20,
            "bonds": 50,
            "commodities": 10,
            "cash": 20,
            "rationale": "经济下行，降息周期，债券最佳",
            "preferred_sectors": ["公用事业", "必需消费", "REITs"],
            "avoid_sectors": ["周期股", "金融"]
        }
    }
    
    return allocations.get(phase, allocations["复苏期"])


def get_china_specific_factors() -> List[str]:
    """中国市场特殊因素"""
    return [
        "政策调控：中国政策干预能力强，可能改变周期节奏",
        "结构性转型：从投资驱动向消费驱动转型",
        "房地产周期：房地产对经济和政策影响重大",
        "外部环境：美联储政策、地缘政治影响"
    ]


def generate_cycle_analysis(gdp_growth: float, inflation: float, 
                           gdp_trend: float, inflation_trend: float) -> Dict:
    """生成周期分析"""
    
    cycle = identify_cycle_phase(gdp_growth, inflation, gdp_trend, inflation_trend)
    allocation = get_asset_allocation(cycle["phase"])
    
    return {
        "analyzed_at": datetime.now().isoformat(),
        "cycle": cycle,
        "allocation": allocation,
        "china_factors": get_china_specific_factors(),
        "transition_probability": estimate_transition(cycle["phase"]),
        "suggestions": generate_cycle_suggestions(cycle["phase"])
    }


def estimate_transition(current_phase: str) -> Dict:
    """估算周期转换概率"""
    
    transitions = {
        "复苏期": {"next": "过热期", "probability": "高", "triggers": ["通胀抬头", "政策收紧"]},
        "过热期": {"next": "滞胀期", "probability": "中", "triggers": ["增长放缓", "通胀高企"]},
        "滞胀期": {"next": "衰退期", "probability": "中", "triggers": ["经济下滑", "政策放松"]},
        "衰退期": {"next": "复苏期", "probability": "高", "triggers": ["政策见效", "库存见底"]}
    }
    
    return transitions.get(current_phase, {"next": "不确定", "probability": "低"})


def generate_cycle_suggestions(phase: str) -> List[str]:
    """生成周期操作建议"""
    
    suggestions = {
        "复苏期": [
            "积极增配股票，把握上涨行情",
            "关注早周期板块（金融、工业）",
            "逐步降低债券配置",
            "关注政策刺激方向"
        ],
        "过热期": [
            "逐步获利了结股票",
            "增配大宗商品抗通胀",
            "关注央行政策转向信号",
            "准备应对回调"
        ],
        "滞胀期": [
            "降低股票仓位，保留现金",
            "配置抗通胀资产（黄金、资源）",
            "关注政策变化",
            "等待周期转机"
        ],
        "衰退期": [
            "增配债券，享受降息红利",
            "关注防御性板块",
            "准备抄底资金",
            "等待复苏信号"
        ]
    }
    
    return suggestions.get(phase, ["观望为主"])


def format_report(report: Dict) -> str:
    """格式化周期分析报告（投资官六段式）"""
    
    c = report["cycle"]
    a = report["allocation"]
    t = report["transition_probability"]
    
    lines = [
        "=" * 60,
        "经济周期分析报告（美林时钟）",
        "=" * 60,
        "",
        "## 🧭 投资官视角",
        "",
        "### 一、核心结论",
        f"【当前阶段】{c['color']} {c['phase']}",
        f"【阶段特征】{c['description']}",
        f"【GDP增速】{c['gdp_growth']}%（{c['gdp_vs_trend']}）",
        f"【通胀水平】{c['inflation']}%（{c['inflation_level']}）",
        "",
        "### 二、背后逻辑",
        "【阶段特征】",
    ]
    
    for char in c["characteristics"]:
        lines.append(f"• {char}")
    
    lines.extend([
        "",
        f"【周期转换】下一阶段可能是{t['next']}（概率{t['probability']}）",
        f"• 触发因素：{', '.join(t.get('triggers', []))}",
        "",
        "### 三、风险在哪里",
        "⚠️ 周期判断可能滞后，实际经济已发生变化",
        "⚠️ 政策干预可能改变周期节奏",
        "⚠️ 外部冲击（地缘政治、金融危机）可能打乱周期",
        "⚠️ 中国结构转型期，传统周期规律可能弱化",
        "",
        "### 四、适合谁",
        "• 进行大类资产配置的机构投资者",
        "• 希望把握经济周期投资机会的个人投资者",
        "• 投资期限1-3年的中长期投资者",
        "",
        "### 五、操作策略",
        "【大类资产配置】",
        f"• 股票：{a['stocks']}% - {a['rationale']}",
        f"• 债券：{a['bonds']}%",
        f"• 大宗商品：{a['commodities']}%",
        f"• 现金：{a['cash']}%",
        "",
        "【板块建议】",
    ])
    
    if a.get("preferred_sectors"):
        lines.append(f"• 推荐板块：{', '.join(a['preferred_sectors'])}")
    if a.get("avoid_sectors"):
        lines.append(f"• 规避板块：{', '.join(a['avoid_sectors'])}")
    
    lines.extend([
        "",
        "【操作建议】",
    ])
    
    for suggestion in report["suggestions"]:
        lines.append(f"✓ {suggestion}")
    
    lines.extend([
        "",
        "【中国市场特殊因素】",
    ])
    
    for factor in report["china_factors"]:
        lines.append(f"• {factor}")
    
    lines.extend([
        "",
        "### 六、如果判断错了",
        "• 如周期判断错误，及时根据最新数据修正",
        "• 如进入非预期阶段，快速调整资产配置",
        "• 建议保留10-20%现金应对不确定性",
        "• 设置资产再平衡机制，每季度检视一次",
        "",
        "=" * 60,
        f"分析时间：{report['analyzed_at']}",
        "=" * 60
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="周期判断器")
    parser.add_argument("--gdp-growth", type=float, required=True,
                       help="GDP增速(%)")
    parser.add_argument("--inflation", type=float, required=True,
                       help="通胀率(%)")
    parser.add_argument("--gdp-trend", type=float, default=5.0,
                       help="GDP趋势增速(%)")
    parser.add_argument("--inflation-trend", type=float, default=2.0,
                       help="通胀趋势(%)")
    parser.add_argument("--output", type=str, help="输出JSON文件")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    report = generate_cycle_analysis(
        args.gdp_growth,
        args.inflation,
        args.gdp_trend,
        args.inflation_trend
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


if __name__ == "__main__":
    main()
