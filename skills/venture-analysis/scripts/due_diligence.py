#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
尽职调查清单生成器

生成创业投资尽调Checklist

Usage:
    python due_diligence.py --stage "A轮" --output dd_checklist.md
"""

import argparse
import json
from datetime import datetime
from typing import Dict, List


def generate_legal_dd(stage: str) -> Dict:
    """生成法律尽调清单"""
    
    base_items = [
        {"item": "公司营业执照、公司章程", "importance": "高", "status": "待核查"},
        {"item": "股权结构图及股东名册", "importance": "高", "status": "待核查"},
        {"item": "历史融资协议及股东协议", "importance": "高", "status": "待核查"},
        {"item": "董事会/股东会决议文件", "importance": "中", "status": "待核查"},
        {"item": "知识产权证书（专利/商标/软著）", "importance": "高", "status": "待核查"},
        {"item": "重大合同（客户/供应商）", "importance": "高", "status": "待核查"},
        {"item": "诉讼、仲裁、行政处罚查询", "importance": "高", "status": "待核查"},
        {"item": "员工劳动合同及社保缴纳", "importance": "中", "status": "待核查"},
        {"item": "关联交易清单", "importance": "中", "status": "待核查"},
        {"item": "债务及担保情况", "importance": "高", "status": "待核查"}
    ]
    
    stage_specific = {
        "天使轮": [],
        "Pre-A": [
            {"item": "期权池设置及激励计划", "importance": "中", "status": "待核查"}
        ],
        "A轮": [
            {"item": "期权池设置及激励计划", "importance": "中", "status": "待核查"},
            {"item": "核心员工竞业禁止协议", "importance": "高", "status": "待核查"},
            {"item": "数据合规及隐私政策", "importance": "高", "status": "待核查"}
        ],
        "B轮": [
            {"item": "期权池设置及激励计划", "importance": "中", "status": "待核查"},
            {"item": "核心员工竞业禁止协议", "importance": "高", "status": "待核查"},
            {"item": "数据合规及隐私政策", "importance": "高", "status": "待核查"},
            {"item": "海外业务合规（如有）", "importance": "高", "status": "待核查"},
            {"item": "VIE架构文件（如有）", "importance": "高", "status": "待核查"}
        ]
    }
    
    items = base_items + stage_specific.get(stage, [])
    
    return {
        "category": "法律尽调",
        "item_count": len(items),
        "high_priority": len([i for i in items if i["importance"] == "高"]),
        "items": items
    }


def generate_financial_dd(stage: str) -> Dict:
    """生成财务尽调清单"""
    
    base_items = [
        {"item": "近三年审计报告（如有）", "importance": "高", "status": "待核查"},
        {"item": "最近12个月银行流水", "importance": "高", "status": "待核查"},
        {"item": "科目余额表及明细账", "importance": "中", "status": "待核查"},
        {"item": "收入确认政策及依据", "importance": "高", "status": "待核查"},
        {"item": "主要客户及收入占比", "importance": "高", "status": "待核查"},
        {"item": "主要供应商及采购占比", "importance": "中", "status": "待核查"},
        {"item": "税务合规证明", "importance": "高", "status": "待核查"},
        {"item": "关联方往来明细", "importance": "中", "status": "待核查"}
    ]
    
    stage_specific = {
        "天使轮": [],
        "Pre-A": [
            {"item": "现金流预测及资金使用计划", "importance": "高", "status": "待核查"}
        ],
        "A轮": [
            {"item": "现金流预测及资金使用计划", "importance": "高", "status": "待核查"},
            {"item": "毛利率分析及同行业对比", "importance": "中", "status": "待核查"},
            {"item": "应收账款账龄分析", "importance": "中", "status": "待核查"}
        ],
        "B轮": [
            {"item": "现金流预测及资金使用计划", "importance": "高", "status": "待核查"},
            {"item": "毛利率分析及同行业对比", "importance": "中", "status": "待核查"},
            {"item": "应收账款账龄分析", "importance": "中", "status": "待核查"},
            {"item": "分产品线/区域收入明细", "importance": "中", "status": "待核查"},
            {"item": "成本结构分析及优化空间", "importance": "中", "status": "待核查"}
        ]
    }
    
    items = base_items + stage_specific.get(stage, [])
    
    return {
        "category": "财务尽调",
        "item_count": len(items),
        "high_priority": len([i for i in items if i["importance"] == "高"]),
        "items": items
    }


def generate_business_dd(stage: str) -> Dict:
    """生成业务尽调清单"""
    
    base_items = [
        {"item": "核心团队背景调查", "importance": "高", "status": "待核查"},
        {"item": "商业模式验证", "importance": "高", "status": "待核查"},
        {"item": "产品/服务技术验证", "importance": "高", "status": "待核查"},
        {"item": "核心客户访谈（至少3家）", "importance": "高", "status": "待核查"},
        {"item": "竞品分析报告", "importance": "高", "status": "待核查"},
        {"item": "市场规模及增长验证", "importance": "中", "status": "待核查"},
        {"item": "渠道及合作伙伴调研", "importance": "中", "status": "待核查"}
    ]
    
    stage_specific = {
        "天使轮": [],
        "Pre-A": [
            {"item": "用户留存及活跃度数据", "importance": "高", "status": "待核查"},
            {"item": "获客成本及渠道效率", "importance": "高", "status": "待核查"}
        ],
        "A轮": [
            {"item": "用户留存及活跃度数据", "importance": "高", "status": "待核查"},
            {"item": "获客成本及渠道效率", "importance": "高", "status": "待核查"},
            {"item": "单位经济模型验证", "importance": "高", "status": "待核查"},
            {"item": "关键岗位人员访谈", "importance": "中", "status": "待核查"}
        ],
        "B轮": [
            {"item": "用户留存及活跃度数据", "importance": "高", "status": "待核查"},
            {"item": "获客成本及渠道效率", "importance": "高", "status": "待核查"},
            {"item": "单位经济模型验证", "importance": "高", "status": "待核查"},
            {"item": "关键岗位人员访谈", "importance": "中", "status": "待核查"},
            {"item": "行业专家访谈", "importance": "中", "status": "待核查"},
            {"item": "供应链/运营实地考察", "importance": "中", "status": "待核查"}
        ]
    }
    
    items = base_items + stage_specific.get(stage, [])
    
    return {
        "category": "业务尽调",
        "item_count": len(items),
        "high_priority": len([i for i in items if i["importance"] == "高"]),
        "items": items
    }


def generate_dd_checklist(stage: str) -> Dict:
    """生成完整尽调清单"""
    
    legal = generate_legal_dd(stage)
    financial = generate_financial_dd(stage)
    business = generate_business_dd(stage)
    
    total_items = legal["item_count"] + financial["item_count"] + business["item_count"]
    high_priority_items = legal["high_priority"] + financial["high_priority"] + business["high_priority"]
    
    return {
        "generated_at": datetime.now().isoformat(),
        "stage": stage,
        "summary": {
            "total_items": total_items,
            "high_priority": high_priority_items,
            "categories": 3
        },
        "checklists": {
            "legal": legal,
            "financial": financial,
            "business": business
        },
        "timeline": generate_dd_timeline(stage),
        "key_focus": generate_key_focus(stage)
    }


def generate_dd_timeline(stage: str) -> List[Dict]:
    """生成尽调时间线"""
    
    timelines = {
        "天使轮": [
            {"week": "第1周", "task": "业务尽调（团队+产品+客户）", "owner": "投资经理"},
            {"week": "第2周", "task": "法律+财务基础尽调", "owner": "法务+财务顾问"},
            {"week": "第3周", "task": "尽调报告及投资决策", "owner": "投资委员会"}
        ],
        "Pre-A": [
            {"week": "第1周", "task": "业务尽调（团队+产品+客户+数据）", "owner": "投资经理"},
            {"week": "第2周", "task": "财务尽调", "owner": "财务顾问"},
            {"week": "第3周", "task": "法律尽调", "owner": "法务顾问"},
            {"week": "第4周", "task": "尽调报告及投资决策", "owner": "投资委员会"}
        ],
        "A轮": [
            {"week": "第1-2周", "task": "业务尽调（深度）", "owner": "投资团队"},
            {"week": "第2-3周", "task": "财务尽调（审计）", "owner": "会计师事务所"},
            {"week": "第3-4周", "task": "法律尽调（律师）", "owner": "律师事务所"},
            {"week": "第5周", "task": "尽调报告及投资决策", "owner": "投资委员会"}
        ],
        "B轮": [
            {"week": "第1-2周", "task": "业务尽调（深度+行业专家）", "owner": "投资团队"},
            {"week": "第2-4周", "task": "财务尽调（全面审计）", "owner": "四大会计师事务所"},
            {"week": "第3-5周", "task": "法律尽调（全面）", "owner": "知名律师事务所"},
            {"week": "第6周", "task": "尽调报告及投资决策", "owner": "投资委员会"}
        ]
    }
    
    return timelines.get(stage, timelines["天使轮"])


def generate_key_focus(stage: str) -> List[str]:
    """生成重点关注事项"""
    
    focus = {
        "天使轮": [
            "团队背景真实性",
            "产品/技术可行性",
            "商业模式初步验证",
            "股权结构清晰度"
        ],
        "Pre-A": [
            "用户数据真实性",
            "获客成本合理性",
            "收入增长趋势",
            "核心团队稳定性"
        ],
        "A轮": [
            "财务数据真实性",
            "单位经济模型健康度",
            "市场竞争格局",
            "法律合规性"
        ],
        "B轮": [
            "盈利能力路径",
            "规模化扩张可行性",
            "海外合规（如有）",
            "退出路径清晰度"
        ]
    }
    
    return focus.get(stage, focus["天使轮"])


def format_checklist(checklist: Dict) -> str:
    """格式化尽调清单（投资官六段式）"""
    
    s = checklist["summary"]
    
    lines = [
        "=" * 60,
        f"{checklist['stage']}尽职调查清单",
        "=" * 60,
        "",
        "## 🧭 投资官视角",
        "",
        "### 一、核心结论",
        f"【尽调项目】共{s['total_items']}项（高优先级{s['high_priority']}项）",
        f"【尽调维度】法律 + 财务 + 业务",
        f"【预计周期】{len(checklist['timeline'])}周",
        "",
        "### 二、背后逻辑",
        "尽职调查是投资前的'体检'，目的是：",
        "• 验证商业计划的真实性",
        "• 发现潜在风险和问题",
        "• 为估值谈判提供依据",
        "• 设计交易条款的基础",
        "",
        "### 三、风险在哪里",
        "⚠️ 数据造假风险：收入、用户数等关键指标可能虚报",
        "⚠️ 法律风险：知识产权纠纷、股权争议、合规问题",
        "⚠️ 团队风险：核心人员稳定性、竞业禁止",
        "⚠️ 市场风险：竞争格局变化、政策风险",
        "",
        "### 四、适合谁",
        "• 准备投资创业项目的机构或个人",
        "• 投资金额超过100万的风险投资",
        "• 需要全面了解被投企业的投资者",
        "",
        "### 五、操作策略",
        "",
        "【尽调时间线】",
    ]
    
    for item in checklist["timeline"]:
        lines.append(f"• {item['week']}: {item['task']} ({item['owner']})")
    
    lines.extend([
        "",
        "【重点关注】",
    ])
    
    for focus in checklist["key_focus"]:
        lines.append(f"• {focus}")
    
    lines.extend([
        "",
        "【法律尽调清单】",
        f"共{checklist['checklists']['legal']['item_count']}项（高优先级{checklist['checklists']['legal']['high_priority']}项）",
    ])
    
    for item in checklist["checklists"]["legal"]["items"]:
        priority_mark = "【高】" if item["importance"] == "高" else ""
        lines.append(f"□ {item['item']} {priority_mark}")
    
    lines.extend([
        "",
        "【财务尽调清单】",
        f"共{checklist['checklists']['financial']['item_count']}项（高优先级{checklist['checklists']['financial']['high_priority']}项）",
    ])
    
    for item in checklist["checklists"]["financial"]["items"]:
        priority_mark = "【高】" if item["importance"] == "高" else ""
        lines.append(f"□ {item['item']} {priority_mark}")
    
    lines.extend([
        "",
        "【业务尽调清单】",
        f"共{checklist['checklists']['business']['item_count']}项（高优先级{checklist['checklists']['business']['high_priority']}项）",
    ])
    
    for item in checklist["checklists"]["business"]["items"]:
        priority_mark = "【高】" if item["importance"] == "高" else ""
        lines.append(f"□ {item['item']} {priority_mark}")
    
    lines.extend([
        "",
        "### 六、如果判断错了",
        "• 如尽调发现重大问题，及时终止投资或大幅压低估值",
        "• 如尽调时间不足，优先完成高优先级项目",
        "• 如对方不配合尽调，视为重大风险信号",
        "• 建议聘请专业第三方机构（律师、会计师）协助尽调",
        "",
        "=" * 60,
        f"生成时间：{checklist['generated_at']}",
        "=" * 60
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="尽职调查清单生成器")
    parser.add_argument("--stage", type=str, required=True,
                       choices=["天使轮", "Pre-A", "A轮", "B轮"],
                       help="投资阶段")
    parser.add_argument("--output", type=str, help="输出文件路径")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    checklist = generate_dd_checklist(args.stage)
    
    if args.json:
        output = json.dumps(checklist, ensure_ascii=False, indent=2)
        print(output)
    elif args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(format_checklist(checklist))
        print(f"尽调清单已保存到: {args.output}")
    else:
        print(format_checklist(checklist))


if __name__ == "__main__":
    main()
