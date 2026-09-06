#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["akshare", "pandas", "numpy"]
# ///
"""
基金筛选工具

Usage:
    python fund_screener.py --type "混合" --min-return-1y 10
    python fund_screener.py --max-drawdown 15 --min-sharpe 1.2
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Optional

try:
    import akshare as ak
    import pandas as pd
    import numpy as np
except ImportError:
    print("错误: 请先安装依赖库")
    print("pip install akshare pandas numpy")
    sys.exit(1)


def safe_float(value) -> Optional[float]:
    """安全转换为浮点数"""
    if value is None or value == '' or value == '--':
        return None
    try:
        if isinstance(value, str):
            value = value.replace('%', '').replace(',', '')
        return float(value)
    except (ValueError, TypeError):
        return None


def screen_funds(
    fund_type: str = None,
    min_return_1y: float = None,
    min_return_3y: float = None,
    max_drawdown: float = None,
    min_sharpe: float = None,
    max_fee: float = None,
    top_n: int = 20
) -> list:
    """筛选基金"""
    print("正在获取基金数据...")
    
    try:
        # 获取开放式基金排行
        df = ak.fund_open_fund_rank_em()
        
        if df is None or df.empty:
            return []
        
        results = []
        
        for _, row in df.iterrows():
            fund = {
                "code": row.get("基金代码", ""),
                "name": row.get("基金简称", ""),
                "type": row.get("基金类型", ""),
                "nav": safe_float(row.get("单位净值")),
                "accumulated_nav": safe_float(row.get("累计净值")),
                "return_1y": safe_float(row.get("近1年")),
                "return_2y": safe_float(row.get("近2年")),
                "return_3y": safe_float(row.get("近3年")),
                "return_5y": safe_float(row.get("近5年")),
                "return_this_year": safe_float(row.get("今年来")),
                "return_since_inception": safe_float(row.get("成立来")),
            }
            
            # 类型筛选
            if fund_type and fund_type not in fund["type"]:
                continue
            
            # 收益率筛选
            if min_return_1y is not None:
                if fund["return_1y"] is None or fund["return_1y"] < min_return_1y:
                    continue
            
            if min_return_3y is not None:
                if fund["return_3y"] is None or fund["return_3y"] < min_return_3y:
                    continue
            
            results.append(fund)
        
        # 按近1年收益排序
        results.sort(key=lambda x: x["return_1y"] if x["return_1y"] else -999, reverse=True)
        
        return results[:top_n]
        
    except Exception as e:
        print(f"获取基金数据失败: {e}")
        return []


def format_output(funds: list) -> str:
    """格式化输出"""
    if not funds:
        return "未找到符合条件的基金"
    
    lines = [
        "=" * 100,
        "基金筛选结果",
        "=" * 100,
        f"{'代码':<10} {'名称':<20} {'类型':<10} {'近1年':<10} {'近3年':<10} {'成立以来':<10}",
        "-" * 100,
    ]
    
    for fund in funds:
        r1y = f"{fund['return_1y']:.2f}%" if fund['return_1y'] else "N/A"
        r3y = f"{fund['return_3y']:.2f}%" if fund['return_3y'] else "N/A"
        r_total = f"{fund['return_since_inception']:.2f}%" if fund['return_since_inception'] else "N/A"
        
        lines.append(
            f"{fund['code']:<10} {fund['name'][:18]:<20} {fund['type'][:8]:<10} "
            f"{r1y:<10} {r3y:<10} {r_total:<10}"
        )
    
    lines.append("=" * 100)
    lines.append(f"\n共找到 {len(funds)} 只符合条件的基金")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="基金筛选工具")
    parser.add_argument("--type", type=str, help="基金类型（如：混合、股票、债券）")
    parser.add_argument("--min-return-1y", type=float, help="近1年最低收益率")
    parser.add_argument("--min-return-3y", type=float, help="近3年最低收益率")
    parser.add_argument("--max-drawdown", type=float, help="最大回撤限制")
    parser.add_argument("--min-sharpe", type=float, help="最低夏普比率")
    parser.add_argument("--max-fee", type=float, help="最高管理费率")
    parser.add_argument("--top", type=int, default=20, help="返回前N个结果")
    parser.add_argument("--output", type=str, help="输出JSON文件")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    funds = screen_funds(
        fund_type=args.type,
        min_return_1y=args.min_return_1y,
        min_return_3y=args.min_return_3y,
        max_drawdown=args.max_drawdown,
        min_sharpe=args.min_sharpe,
        max_fee=args.max_fee,
        top_n=args.top
    )
    
    if args.json or args.output:
        output = json.dumps(funds, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"结果已保存到: {args.output}")
        else:
            print(output)
    else:
        print(format_output(funds))


if __name__ == "__main__":
    main()
