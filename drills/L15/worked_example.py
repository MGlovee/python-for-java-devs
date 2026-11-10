# -*- coding: utf-8 -*-
"""L15 完整样例 —— 直接跑：py -X utf8 drills/L15/worked_example.py

numpy + pandas 的一条最小分析链：造数组 → 轴/广播 → 索引 → 读 CSV → 筛选/分组/合并/缺失值。
全程**不联网、不落盘**（CSV 用 io.StringIO 从内存读），退出码 0。
"""
from __future__ import annotations

import io
import sys
import warnings

import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CSV = """部门,姓名,销售额
研发,张三,100
研发,李四,120
研发,王五,
销售,赵六,200
销售,孙七,150
财务,周八,130
财务,吴九,999999
"""


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def demo_view_vs_copy() -> None:
    section("1. ndarray 是连续内存 + 形状元数据；切片/reshape 是**视图**")
    base = np.arange(6)                       # 一整块 6 个 int64，不是 6 个对象
    grid = base.reshape(2, 3)                # 没拷贝，只换了 (shape, strides)
    print("grid =", grid.tolist(), "dtype:", grid.dtype, "strides:", grid.strides)
    grid[0, 0] = 99
    print("改视图 grid[0,0]=99 之后，原数组 base =", base.tolist(), "← 被一起改了")
    print("shares_memory(base, grid):", np.shares_memory(base, grid))
    safe = base.reshape(2, 3).copy()          # 要独立副本必须 .copy()
    safe[0, 0] = 0
    print("copy() 之后再改，base =", base.tolist(), "shares_memory:",
          np.shares_memory(base, safe))
    print("Java 对照：Arrays.copyOfRange 会复制，int[][] 是行引用；这两点在这里都不成立")


def demo_axis() -> None:
    section("2. 轴 axis：axis=0 是「沿行的方向压缩」")
    m = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    print("m =\n", m.tolist(), "shape:", m.shape)
    print("mean(axis=0) 每列均值 =", m.mean(axis=0).tolist(), "shape:", m.mean(axis=0).shape)
    print("mean(axis=1) 每行均值 =", m.mean(axis=1).tolist(), "shape:", m.mean(axis=1).shape)
    k = m.mean(axis=1, keepdims=True)
    print("keepdims=True →", k.tolist(), "shape:", k.shape, "（形状不塌，能继续广播）")
    print("argmax(axis=1) 每行最大值**下标** =", m.argmax(axis=1).tolist())


def demo_broadcast() -> None:
    section("3. 广播：形状从右往左对齐，长度 1 或缺席的轴自动复制")
    m = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    col_means = m.mean(axis=0)                # (3,)
    print("m - 每列均值 =", (m - col_means).tolist(), "→ (2,3) 减 (3,)，对齐最后一轴，OK")
    row_sums = m.sum(axis=1)                  # (2,)
    try:
        m + row_sums                          # (2,3) + (2,) → 最后一轴 3 对 2，炸
    except ValueError as err:
        print("踩坑：m + 每行和 报 ValueError:", err)
    print("修法：keepdims=True →", (m + m.sum(axis=1, keepdims=True)).tolist())


def demo_indexing() -> None:
    section("4. 布尔索引 / 花式索引 / argsort")
    scores = np.array([90.0, 70.0, 85.0, 70.0])
    names = np.array(["关羽", "张飞", "刘备", "赵云"])
    print("scores[scores >= 80] =", scores[scores >= 80].tolist(), "（掩码也是逐元素的）")
    print("names[scores >= 80]  =", names[scores >= 80].tolist())
    print("names[[3, 0]]        =", names[[3, 0]].tolist(), "（花式索引：按下标列表取，返回拷贝）")
    order = np.argsort(-scores, kind="stable")
    print("argsort(-scores) 降序下标 =", order.tolist(), "→", names[order].tolist(),
          "（并列的张飞/赵云保持原顺序；argsort(scores)[::-1] 会把并列也反转）")


def demo_dataframe() -> None:
    section("5. DataFrame ≈ 带列名的 List<Map>")
    df = pd.read_csv(io.StringIO(CSV))        # 内存里读，零落盘
    print("shape:", df.shape, "列:", list(df.columns))
    print("列类型:", {c: str(t) for c, t in df.dtypes.items()})

    print("\n取两列：", df[["部门", "销售额"]].head(2).to_dict(orient="records"))
    big = df[df["销售额"] > 150]
    print("条件筛选（销售额 > 150）：", big["姓名"].tolist(), "← 缺失行因为 NaN 比较恒 False 被滤掉")
    print("value_counts 部门分布：", df["部门"].value_counts().to_dict())

    print("\n按 pandas 3 的行为：链式赋值**静默失效**，下面只演示不改数据")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        df["销售额"][df["销售额"] > 150] = 0
        print("捕获到告警类型：", [str(w.message).splitlines()[0] for w in caught][:1])
    print("原表没变，> 150 的仍是：", df[df["销售额"] > 150]["销售额"].tolist())

    clone = df.copy()
    clone.loc[df["销售额"] > 150, "销售额"] = 0      # 一步到位，才是真的改
    print("正确写法 df.loc[条件, 列] = 值 → 改完 > 150 的变成：",
          clone.loc[clone["销售额"] > 150, "销售额"].tolist(),
          "（只动这一列，其他列不变）")


def demo_group_merge_missing() -> None:
    section("6. groupby / merge / 缺失值三件套")
    df = pd.read_csv(io.StringIO(CSV))

    grouped = df.groupby("部门")["销售额"].agg(["count", "sum", "mean"])
    print("groupby().agg() ≈ SQL 的 GROUP BY + COUNT/SUM/AVG：\n", grouped)
    print("研发 count =", int(grouped.loc["研发", "count"]), "（销售额为空那行不计入，不是 len(组)）")

    budget = pd.DataFrame({"部门": ["研发", "销售"], "预算": [500, 800]})
    joined = pd.merge(df, budget, on="部门", how="inner")
    print("\nmerge how=inner ≈ SQL INNER JOIN，列顺序（pandas 3 不再把 on 列提到最前）：",
          list(joined.columns), "行数:", len(joined), "（财务没预算 → 整组被丢掉）")
    left_join = pd.merge(df, budget, on="部门", how="left")
    print("how=left 时财务的预算是：", left_join[left_join["部门"] == "财务"]["预算"].tolist())

    na_total = int(df["销售额"].isna().sum())
    filled = df.copy()
    filled["销售额"] = filled["销售额"].fillna(df["销售额"].median())
    print(f"\n缺失：isna().sum() = {na_total}，fillna(中位数 {df['销售额'].median()}) 后剩 "
          f"{int(filled['销售额'].isna().sum())}；原表仍缺 {int(df['销售额'].isna().sum())} 个")

    def slow(x):
        return float(x) * 2 if pd.notna(x) else x

    applied = df["销售额"].apply(slow)
    vectorized = df["销售额"] * 2
    print("apply(逐元素调 Python 函数) 与向量化结果相同：",
          applied.tolist()[:3], "vs", vectorized.tolist()[:3], "← 但前者逐行回调，量大时慢一个量级")


def main() -> None:
    demo_view_vs_copy()
    demo_axis()
    demo_broadcast()
    demo_indexing()
    demo_dataframe()
    demo_group_merge_missing()
    section("收尾")
    print("几十行、只想读几列 CSV → 标准库 csv + statistics 就够，不必为它拉一个 pandas。")
    print("要分组透视、缺失值、异常值判定、几万以上行 → 才上 pandas（P3 就属于这一类）。")


if __name__ == "__main__":
    main()
