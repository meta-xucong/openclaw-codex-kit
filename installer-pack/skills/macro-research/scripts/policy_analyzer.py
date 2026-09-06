#!/usr/bin/env python
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
政策解读器

解读宏观政策对市场的影响

Usage:
    python policy_analyzer.py --type "货币政策" --action "降息"
"""

import argparse
import json
from datetime import datetime
from typing import Dict, List


def analyze_monetary_policy(action: str, magnitude: str) -> Dict:
    """分析货币政策影响"""
    
    impacts = {
        "降息": {
            "description": "降低基准利率，释放流动性",
            "stock_impact": "利好股市，尤其利好高负债行业（地产、基建）",
            "bond_impact": "债券价格上涨，收益率下降",
            "currency_impact": "本币贬值压力",
            "sectors": ["房地产", "基建", "券商", "消费"],
            "risk": "过度宽松可能引发资产泡沫"
        },
        "加息": {
            "description": "提高基准利率，收紧流动性",
            "stock_impact": "利空股市，尤其利空高估值成长股",
            "bond_impact": "债券价格下跌，收益率上升",
            "currency_impact": "本币升值",
            "sectors": ["银行", "保险"],
            "avoid_sectors": ["房地产", "科技股", "成长股"],
            "risk": "可能引发经济衰退"
        },
        "降准": {
            "description": "降低存款准备金率，释放银行可贷资金",
            "stock_impact": "利好股市，尤其利好金融地产",
            "bond_impact": "短端利率下行",
            "currency_impact": "中性偏贬",
            "sectors": ["银行", "房地产", "周期股"],
            "risk": "效果递减，需配合其他政策"
        },
        "量化宽松": {
            "description": "央行直接购买资产，大规模释放流动性",
            "stock_impact": "强力利好风险资产",
            "bond_impact": "长端利率下行",
            "currency_impact": "本币贬值",
            "sectors": ["全市场", "黄金", "大宗商品"],
            "risk": "通胀风险、资产泡沫"
        }
    }
    
    return impacts.get(action, {
        "description": "未知货币政策操作",
        "stock_impact": "影响不确定",
        "bond_impact": "影响不确定",
        "currency_impact": "影响不确定"
    })


def analyze_fiscal_policy(action: str, scale: str) -> Dict:
    """分析财政政策影响"""
    
    impacts = {
        "基建投资": {
            "description": "增加基建支出，拉动投资",
            "stock_impact": "利好周期股、基建股",
            "bond_impact": "国债供给增加，收益率上行压力",
            "currency_impact": "中性",
            "sectors": ["基建", "水泥", "钢铁", "工程机械"],
            "risk": "地方政府债务压力"
        },
        "减税降费": {
            "description": "降低企业和个人税负",
            "stock_impact": "利好企业盈利，尤其利好制造业",
            "bond_impact": "财政赤字扩大，债券供给增加",
            "currency_impact": "中性",
            "sectors": ["制造业", "消费", "中小企业"],
            "risk": "财政收入下降"
        },
        "消费券": {
            "description": "发放消费券刺激需求",
            "stock_impact": "利好消费股",
            "bond_impact": "中性",
            "currency_impact": "中性",
            "sectors": ["餐饮", "零售", "旅游", "家电"],
            "risk": "短期刺激，效果有限"
        },
        "专项债": {
            "description": "扩大专项债规模",
            "stock_impact": "利好基建、周期股",
            "bond_impact": "供给增加",
            "currency_impact": "中性",
            "sectors": ["基建", "地方国企"],
            "risk": "项目质量、债务风险"
        }
    }
    
    return impacts.get(action, {
        "description": "未知财政政策操作",
        "stock_impact": "影响不确定",
        "bond_impact": "影响不确定",
        "currency_impact": "影响不确定"
    })


def analyze_industry_policy(industry: str, policy: str) -> Dict:
    """分析产业政策影响"""
    
    policies = {
        "新能源补贴": {
            "description": "对新能源行业提供补贴支持",
            "impact": "利好",
            "affected": ["新能源汽车", "光伏", "风电", "储能"],
            "duration": "中长期",
            "risk": "补贴退坡风险"
        },
        "房地产调控": {
            "description": "限制房地产融资和购房",
            "impact": "利空",
            "affected": ["房地产", "建材", "家电"],
            "duration": "长期",
            "risk": "经济下行压力"
        },
        "互联网监管": {
            "description": "加强互联网平台监管",
            "impact": "利空",
            "affected": ["互联网平台", "在线教育", "游戏"],
            "duration": "长期",
            "risk": "盈利模式重塑"
        },
        "半导体支持": {
            "description": "大力支持半导体产业发展",
            "impact": "利好",
            "affected": ["半导体", "芯片设计", "设备材料"],
            "duration": "中长期",
            "risk": "技术突破不确定性"
        },
        "双碳目标": {
            "description": "碳达峰碳中和政策",
            "impact": "结构性影响",
            "affected": ["新能源", "环保", "高耗能行业"],
            "beneficiaries": ["新能源", "电动车", "环保"],
            "victims": ["煤炭", "钢铁", "水泥"],
            "duration": "长期",
            "risk": "转型成本"
        }
    }
    
    return policies.get(policy, {
        "description": f"{policy}政策",
        "impact": "影响待观察",
        "affected": [industry],
        "duration": "不确定"
    })


def generate_policy_analysis(policy_type: str, action: str, context: str = "") -> Dict:
    """生成政策分析"""
    
    if policy_type == "货币政策":
        analysis = analyze_monetary_policy(action, "")
    elif policy_type == "财政政策":
        analysis = analyze_fiscal_policy(action, "")
    elif policy_type == "产业政策":
        analysis = analyze_industry_policy("", action)
    else:
        analysis = {"description": "未知政策类型", "impact": "无法评估"}
    
    return {
        "analyzed_at": datetime.now().isoformat(),
        "policy_type": policy_type,
        "action": action,
        "context": context,
        "analysis": analysis,
        "market_implications": generate_market_implications(analysis),
        "investment_suggestions": generate_investment_suggestions(analysis),
        "risks": generate_policy_risks(analysis)
    }


def generate_market_implications(analysis: Dict) -> Dict:
    """生成市场影响分析"""
    return {
        "short_term": analysis.get("stock_impact", "影响待观察"),
        "sectors_benefit": analysis.get("sectors", []),
        "sectors_avoid": analysis.get("avoid_sectors", []),
        "asset_allocation": suggest_asset_allocation(analysis)
    }


def suggest_asset_allocation(analysis: Dict) -> str:
    """建议资产配置"""
    impact = analysis.get("impact", "")
    
    if impact == "利好":
        return "增配权益资产，减配债券"
    elif impact == "利空":
        return "减配权益资产，增配现金"
    elif impact == "结构性影响":
        return "结构性调仓，关注受益板块"
    else:
        return "维持现有配置，密切观察"


def generate_investment_suggestions(analysis: Dict) -> List[str]:
    """生成投资建议"""
    suggestions = []
    
    sectors = analysis.get("sectors", [])
    if sectors:
        suggestions.append(f"关注受益板块：{', '.join(sectors)}")
    
    avoid = analysis.get("avoid_sectors", [])
    if avoid:
        suggestions.append(f"规避受损板块：{', '.join(avoid)}")
    
    suggestions.append("政策效果通常有滞后性，建议分批布局")
    suggestions.append("关注政策执行力度和后续配套措施")
    
    return suggestions


def generate_policy_risks(analysis: Dict) -> List[str]:
    """生成政策风险"""
    risks = []
    
    if "risk" in analysis:
        risks.append(analysis["risk"])
    
    risks.append("政策效果可能不及预期")
    risks.append("市场反应可能与政策方向背离")
    risks.append("政策持续性存在不确定性")
    
    return risks


def format_report(report: Dict) -> str:
    """格式化政策分析报告（投资官六段式）"""
    
    a = report["analysis"]
    m = report["market_implications"]
    
    lines = [
        "=" * 60,
        f"政策解读报告 - {report['policy_type']}：{report['action']}",
        "=" * 60,
        "",
        "## 🧭 投资官视角",
        "",
        "### 一、核心结论",
        f"【政策类型】{report['policy_type']}",
        f"【政策措施】{report['action']}",
        f"【政策意图】{a.get('description', '待分析')}",
        f"【市场影响】{m['short_term']}",
        "",
        "### 二、背后逻辑",
        f"• 政策背景：{report['context'] if report['context'] else '当前经济环境下的政策应对'}",
        f"• 传导机制：{a.get('description', '')}",
        f"• 股市影响：{a.get('stock_impact', '')}",
        f"• 债市影响：{a.get('bond_impact', '')}",
        f"• 汇市影响：{a.get('currency_impact', '')}",
        "",
        "### 三、风险在哪里",
    ]
    
    for risk in report["risks"]:
        lines.append(f"⚠️ {risk}")
    
    lines.extend([
        "",
        "### 四、适合谁",
        "• 关注宏观政策对投资组合影响的投资者",
        "• 需要根据政策调整资产配置的投资者",
        "• 希望把握政策主题投资机会的投资者",
        "",
        "### 五、操作策略",
        f"【资产配置】{m['asset_allocation']}",
        "",
        "【板块建议】",
    ])
    
    if m["sectors_benefit"]:
        lines.append(f"• 受益板块：{', '.join(m['sectors_benefit'])}")
    if m["sectors_avoid"]:
        lines.append(f"• 受损板块：{', '.join(m['sectors_avoid'])}")
    
    lines.extend([
        "",
        "【操作建议】",
    ])
    
    for suggestion in report["investment_suggestions"]:
        lines.append(f"✓ {suggestion}")
    
    lines.extend([
        "",
        "### 六、如果判断错了",
        "• 如政策效果不及预期，及时止损政策主题仓位",
        "• 如市场过度反应，逆向布局被错杀的优质资产",
        "• 如政策方向转变，快速调整配置",
        "• 建议设置止损线，单只政策主题股票亏损15%时考虑止损",
        "",
        "=" * 60,
        f"分析时间：{report['analyzed_at']}",
        "=" * 60
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="政策解读器")
    parser.add_argument("--type", type=str, required=True,
                       choices=["货币政策", "财政政策", "产业政策"],
                       help="政策类型")
    parser.add_argument("--action", type=str, required=True,
                       help="政策措施")
    parser.add_argument("--context", type=str, default="",
                       help="政策背景")
    parser.add_argument("--output", type=str, help="输出JSON文件")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    report = generate_policy_analysis(args.type, args.action, args.context)
    
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
