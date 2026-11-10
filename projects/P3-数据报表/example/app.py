#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P3 参考实现 —— CSV 数据体检 + 汇总报表（pandas 必需，Excel 导出可选）。

用法：
    py example/app.py                              # 用内联样本跑全流程（临时目录）
    py example/app.py 数据.csv --group-by 部门 --value 销售额 --out-dir 报表目录

openpyxl 未安装时跳过 xlsx 导出，只出 CSV 与统计文本，不崩溃。
"""
from __future__ import annotations

import argparse
import contextlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Optional, Union

import pandas as pd

SAMPLE_CSV = """\
部门,姓名,销售额
研发,张三,100
研发,李四,120
研发,王五,
销售,赵六,200
销售,赵六,200
销售,孙七,150
财务,周八,130
财务,吴九,999999
财务,郑十,110
"""


def load_data(path: Union[str, Path]) -> pd.DataFrame:
    """读 CSV。utf-8-sig 能吃掉 Excel 另存时的 BOM。"""
    return pd.read_csv(str(path), encoding="utf-8-sig")


def data_check(df: pd.DataFrame) -> dict:
    """数据体检：缺失、重复、异常值（IQR 1.5 倍法则）。返回纯 Python 类型，可 json.dumps。"""
    missing = {col: int(df[col].isna().sum()) for col in df.columns}
    duplicate_rows = int(df.duplicated().sum())
    outliers: dict[str, list[int]] = {}
    for col in df.select_dtypes(include="number").columns:
        s = df[col].dropna()
        if s.empty:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        if iqr <= 0:
            continue
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (df[col] < lo) | (df[col] > hi)
        idx = [int(i) for i in df.index[mask]]
        if idx:
            outliers[col] = idx
    return {"rows": int(len(df)), "missing": missing,
            "duplicate_rows": duplicate_rows, "outliers": outliers}


def summarize(df: pd.DataFrame, group_by: str, value: str) -> list[dict]:
    """分组聚合，按 sum 降序。count 为非空个数（pandas .count() 语义）。"""
    agg = (df.groupby(group_by)[value]
             .agg(["count", "sum", "mean"])
             .sort_values("sum", ascending=False)
             .reset_index())
    return [{group_by: row[group_by], "count": int(row["count"]),
             "sum": float(row["sum"]), "mean": float(row["mean"])}
            for row in agg.to_dict("records")]


def format_stats(check: dict) -> str:
    lines = [f"总行数: {check['rows']}",
             f"重复行: {check['duplicate_rows']}"]
    lines.append("缺失统计:")
    for col, n in check["missing"].items():
        lines.append(f"  {col}: {n}")
    lines.append("异常值（IQR 1.5 法则，行下标）:")
    if check["outliers"]:
        for col, idx in check["outliers"].items():
            lines.append(f"  {col}: {idx}")
    else:
        lines.append("  （无）")
    return "\n".join(lines)


def write_outputs(df: pd.DataFrame, out_dir: Union[str, Path],
                  group_by: str, value: str) -> list[Path]:
    """产出 summary.csv + stats.txt；装了 openpyxl 就再加 report.xlsx，没装优雅跳过。"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    summary = pd.DataFrame(summarize(df, group_by, value))
    summary_path = out / "summary.csv"
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    written.append(summary_path)

    stats_path = out / "stats.txt"
    stats_path.write_text(format_stats(data_check(df)), encoding="utf-8")
    written.append(stats_path)

    try:
        import openpyxl  # noqa: F401  仅探测可用性；缺失走 except
        xlsx = out / "report.xlsx"
        with pd.ExcelWriter(xlsx, engine="openpyxl") as xw:
            df.to_excel(xw, sheet_name="raw", index=False)
            summary.to_excel(xw, sheet_name="summary", index=False)
        written.append(xlsx)
    except ModuleNotFoundError:
        print("提示：未安装 openpyxl，跳过 Excel 导出（pip install openpyxl 后可用）")
    return written


def main(argv: Optional[list[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description="CSV 数据体检 + 汇总报表")
    p.add_argument("csv", nargs="?", default=None, help="数据文件（省略则用内联样本）")
    p.add_argument("--group-by", default="部门")
    p.add_argument("--value", default="销售额")
    p.add_argument("--out-dir", default=None, help="报表输出目录（省略则用临时目录）")
    args = p.parse_args(argv)

    with contextlib.ExitStack() as stack:
        if args.csv is None:
            tmp = Path(stack.enter_context(tempfile.TemporaryDirectory()))
            csv_path = tmp / "sample.csv"
            csv_path.write_text(SAMPLE_CSV, encoding="utf-8")
        else:
            csv_path = Path(args.csv)
            if not csv_path.is_file():
                print(f"错误：数据文件不存在：{csv_path}", file=sys.stderr)
                return 2
        out_dir = (Path(args.out_dir) if args.out_dir
                   else Path(stack.enter_context(tempfile.TemporaryDirectory())))

        df = load_data(csv_path)
        check = data_check(df)
        print(format_stats(check))
        try:
            rows = summarize(df, args.group_by, args.value)
        except KeyError as exc:
            print(f"错误：列不存在 {exc}", file=sys.stderr)
            return 2
        print(json.dumps(rows, ensure_ascii=False))
        for f in write_outputs(df, out_dir, args.group_by, args.value):
            print(f"已写出: {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
