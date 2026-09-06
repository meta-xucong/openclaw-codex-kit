#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
商业计划评估器

评估创业项目的商业模式和市场前景

Usage:
    python business_evaluator.py --industry "新能源" --tam 10000000000 --team-score 8
"""

import argparse
import json
from datetime import datetime
from typing import Dict, List


def evaluate_business_model(
    industry: str,
    value_proposition: str,
    customer_segment: str,
    revenue_model: str,
    competitive_advantage: str
) -> Dict:
    """评估商业模式画布"""
    
    # 评分标准
    scores = {
        "value_proposition": min(len(value_proposition) / 10, 10) if value_proposition else 5,
        "customer_clarity": min(len(customer_segment) / 8, 10) if customer_segment else 5,
        "revenue_feasibility": min(len(revenue_model) / 8, 10) if revenue_model else 5,
        "competitive_moat": min(len(competitive_advantage) / 10, 10) if competitive_advantage else 5
    }
    
    avg_score = sum(scores.values()) / len(scores)
    
    return {
        "scores": scores,
        "average": round(avg_score, 1),
        "rating": "强" if avg_score >= 7 else "中" if avg_score >= 5 else "弱",
        "comments": generate_bm_comments(scores)
    }


def generate_bm_comments(scores: Dict) -> List[str]:
    """生成商业模式评价"""
    comments = []
    
    if scores["value_proposition"] >= 8:
        comments.append("价值主张清晰，能解决用户痛点")
    elif scores["value_proposition"] < 5:
        comments.append("价值主张不够明确，需进一步打磨")
    
    if scores["customer_clarity"] >= 8:
        comments.append("目标客户定位精准")
    elif scores["customer_clarity"] < 5:
        comments.append("客户群体定义模糊")
    
    if scores["revenue_feasibility"] >= 8:
        comments.append("盈利模式可行性强")
    elif scores["revenue_feasibility"] < 5:
        comments.append("盈利模式不够清晰")
    
    if scores["competitive_moat"] >= 8:
        comments.append("具备明显的竞争壁垒")
    elif scores["competitive_moat"] < 5:
        comments.append("竞争壁垒不足，易被模仿")
    
    return comments


def evaluate_market_size(tam: float, sam: float = None, som: float = None) -> Dict:
    """评估市场规模 TAM/SAM/SOM"""
    
    tam_billion = tam / 1e8  # 转换为亿元
    
    if tam_billion >= 1000:
        size_rating = "万亿级"
        size_score = 10
    elif tam_billion >= 100:
        size_rating = "千亿级"
        size_score = 8
    elif tam_billion >= 10:
        size_rating = "百亿级"
        size_score = 6
    elif tam_billion >= 1:
        size_rating = "十亿级"
        size_score = 4
    else:
        size_rating = "亿级以下"
        size_score = 2
    
    return {
        "tam": tam,
        "tam_cn": f"{tam_billion:.0f}亿元",
        "sam": sam,
        "som": som,
        "rating": size_rating,
        "score": size_score,
        "comment": f"市场{size_rating}，{'空间巨大' if size_score >= 8 else '空间适中' if size_score >= 5 else '空间有限'}"
    }


def evaluate_team(team_score: int, founder_background: str = "") -> Dict:
    """评估团队"""
    
    # 团队评分解读
    if team_score >= 9:
        level = "顶级"
        comment = "团队背景顶尖，成功概率高"
    elif team_score >= 7:
        level = "优秀"
        comment = "团队配置良好，执行力强"
    elif team_score >= 5:
        level = "一般"
        comment = "团队基本合格，但有短板"
    else:
        level = "较弱"
        comment = "团队能力不足，风险较高"
    
    return {
        "score": team_score,
        "level": level,
        "founder_background": founder_background,
        "comment": comment,
        "key_factors": [
            "创始人行业经验",
            "团队完整性（技术+运营+市场）",
            "过往创业经历",
            "股权结构合理性"
        ]
    }


def evaluate_competition(competition_level: str, entry_barrier: str) -> Dict:
    """评估竞争格局"""
    
    competition_scores = {
        "低": 8,
        "中": 5,
        "高": 2
    }
    
    barrier_scores = {
        "高": 8,
        "中": 5,
        "低": 2
    }
    
    comp_score = competition_scores.get(competition_level, 5)
    barrier_score = barrier_scores.get(entry_barrier, 5)
    
    total_score = (comp_score + barrier_score) / 2
    
    return {
        "competition_level": competition_level,
        "entry_barrier": entry_barrier,
        "score": round(total_score, 1),
        "rating": "有利" if total_score >= 6 else "中性" if total_score >= 4 else "不利",
        "comment": f"竞争{competition_level}，进入壁垒{entry_barrier}"
    }


def calculate_overall_score(
    bm_score: float,
    market_score: int,
    team_score: int,
    competition_score: float
) -> Dict:
    """计算综合评分"""
    
    # 权重：商业模式30%，市场25%，团队30%，竞争15%
    weights = {
        "business_model": 0.30,
        "market": 0.25,
        "team": 0.30,
        "competition": 0.15
    }
    
    total = (bm_score * weights["business_model"] +
             market_score * weights["market"] +
             team_score * weights["team"] +
             competition_score * weights["competition"])
    
    if total >= 80:
        grade = "A"
        recommendation = "强烈推荐"
    elif total >= 65:
        grade = "B"
        recommendation = "推荐"
    elif total >= 50:
        grade = "C"
        recommendation = "谨慎考虑"
    else:
        grade = "D"
        recommendation = "不建议"
    
    return {
        "total_score": round(total, 1),
        "grade": grade,
        "recommendation": recommendation,
        "weights": weights
    }


def generate_evaluation(args) -> Dict:
    """生成完整评估"""
    
    # 评估各维度
    bm = evaluate_business_model(
        args.industry,
        args.value_proposition,
        args.customer_segment,
        args.revenue_model,
        args.competitive_advantage
    )
    
    market = evaluate_market_size(args.tam, args.sam, args.som)
    team = evaluate_team(args.team_score, args.founder_background)
    competition = evaluate_competition(args.competition_level, args.entry_barrier)
    
    # 综合评分
    overall = calculate_overall_score(
        bm["average"] * 10,
        market["score"],
        team["score"],
        competition["score"]
    )
    
    return {
        "evaluated_at": datetime.now().isoformat(),
        "project_name": args.project_name,
        "industry": args.industry,
        "overall": overall,
        "dimensions": {
            "business_model": bm,
            "market": market,
            "team": team,
            "competition": competition
        },
        "risks": generate_risks(args),
        "suggestions": generate_suggestions(overall["grade"])
    }


def generate_risks(args) -> List[str]:
    """生成风险提示"""
    risks = []
    
    if args.tam < 1e9:
        risks.append("市场规模较小，增长空间有限")
    if args.team_score < 6:
        risks.append("团队能力不足，执行风险高")
    if args.competition_level == "高":
        risks.append("竞争激烈，差异化难度大")
    if args.entry_barrier == "低":
        risks.append("进入壁垒低，易被模仿")
    
    if not risks:
        risks.append("未发现重大风险，但需持续跟踪")
    
    return risks


def generate_suggestions(grade: str) -> List[str]:
    """生成建议"""
    suggestions = {
        "A": [
            "项目质量优秀，可快速推进",
            "建议尽快锁定投资份额",
            "关注估值合理性，避免过高"
        ],
        "B": [
            "项目整体良好，值得投资",
            "建议尽职调查后决策",
            "可提出对赌条款保护利益"
        ],
        "C": [
            "项目有亮点但也有风险",
            "建议降低估值或增加条款",
            "可考虑小额试水"
        ],
        "D": [
            "项目风险较高，不建议投资",
            "如坚持投资，需大幅压低估值",
            "建议设置严格的对赌和回购条款"
        ]
    }
    return suggestions.get(grade, ["请重新评估"])


def format_report(evaluation: Dict) -> str:
    """格式化评估报告（投资官六段式）"""
    o = evaluation["overall"]
    d = evaluation["dimensions"]
    
    lines = [
        "=" * 60,
        f"商业计划评估报告 - {evaluation['project_name']}",
        "=" * 60,
        "",
        "## 🧭 投资官视角",
        "",
        "### 一、核心结论",
        f"【综合评级】{o['grade']}级（{o['total_score']:.0f}/100分）",
        f"【投资建议】{o['recommendation']}",
        f"【行业】{evaluation['industry']}",
        "",
        "### 二、背后逻辑",
        f"【商业模式】评分{d['business_model']['average']:.1f}/10 - {d['business_model']['rating']}",
    ]
    
    for comment in d["business_model"]["comments"]:
        lines.append(f"  • {comment}")
    
    lines.extend([
        f"【市场规模】{d['market']['tam_cn']} - {d['market']['rating']}",
        f"  • {d['market']['comment']}",
        f"【团队评估】评分{d['team']['score']}/10 - {d['team']['level']}",
        f"  • {d['team']['comment']}",
        f"【竞争格局】评分{d['competition']['score']:.1f}/10 - {d['competition']['rating']}",
        f"  • {d['competition']['comment']}",
        "",
        "### 三、风险在哪里",
    ])
    
    for risk in evaluation["risks"]:
        lines.append(f"⚠️ {risk}")
    
    lines.extend([
        "",
        "### 四、适合谁",
        "• 有风险承受能力的高净值个人或机构",
        "• 对行业有深入了解的战略投资者",
        "• 投资期限3年以上的长期投资者",
        "",
        "### 五、操作策略",
    ])
    
    for suggestion in evaluation["suggestions"]:
        lines.append(f"✓ {suggestion}")
    
    lines.extend([
        "",
        "### 六、如果判断错了",
        "• 如市场反应不及预期，及时止损，不要追加投资",
        "• 如团队核心成员离职，重新评估项目可行性",
        "• 如竞争格局恶化，考虑提前退出",
        "• 建议设置里程碑，未达成时有权调整投资条款",
        "",
        "=" * 60,
        f"评估时间：{evaluation['evaluated_at']}",
        "=" * 60
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="商业计划评估器")
    parser.add_argument("--project-name", type=str, default="未命名项目",
                       help="项目名称")
    parser.add_argument("--industry", type=str, required=True,
                       help="所属行业")
    parser.add_argument("--tam", type=float, required=True,
                       help="总市场规模TAM（元）")
    parser.add_argument("--sam", type=float, help="可服务市场SAM（元）")
    parser.add_argument("--som", type=float, help="可获得市场SOM（元）")
    parser.add_argument("--value-proposition", type=str,
                       help="价值主张（解决什么问题）")
    parser.add_argument("--customer-segment", type=str,
                       help="目标客户群体")
    parser.add_argument("--revenue-model", type=str,
                       help="盈利模式")
    parser.add_argument("--competitive-advantage", type=str,
                       help="竞争优势/壁垒")
    parser.add_argument("--team-score", type=int, required=True,
                       help="团队评分（1-10）")
    parser.add_argument("--founder-background", type=str,
                       help="创始人背景")
    parser.add_argument("--competition-level", type=str, default="中",
                       choices=["低", "中", "高"],
                       help="竞争程度")
    parser.add_argument("--entry-barrier", type=str, default="中",
                       choices=["低", "中", "高"],
                       help="进入壁垒")
    parser.add_argument("--output", type=str, help="输出JSON文件")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    evaluation = generate_evaluation(args)
    
    if args.json or args.output:
        output = json.dumps(evaluation, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"评估报告已保存到: {args.output}")
        else:
            print(output)
    else:
        print(format_report(evaluation))


if __name__ == "__main__":
    main()
