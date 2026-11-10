# -*- coding: utf-8 -*-
"""L15 参考答案。

别整篇抄 —— 它的价值在于卡住 15 分钟后对照思路。
验证题目本身有没有写错：py check.py L15 --solution
"""
from __future__ import annotations

import io
import json

import numpy as np
import pandas as pd


def create_grid(rows: int, cols: int) -> np.ndarray:
    return np.arange(rows * cols).reshape(rows, cols)      # 视图；要独立副本才 .copy()


def column_means(matrix: np.ndarray) -> np.ndarray:
    return matrix.mean(axis=0)      # axis=0：沿行方向压缩 → 每列一个均值，形状 (cols,)


def pick_by_mask(arr: np.ndarray, threshold: float) -> list[float]:
    return arr[arr >= threshold].tolist()     # 布尔索引保留原顺序；2D 会摊平成 1D


def normalize(matrix: np.ndarray) -> np.ndarray:
    span = np.ptp(matrix)                     # numpy 2 起没有 matrix.ptp() 这个实例方法了
    if span == 0:
        return np.zeros(matrix.shape, dtype=float)
    return (matrix - matrix.min()) / span     # 标量广播到整个形状


def read_csv_frame(text: str) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(text))     # 内存里读，不落盘


def center_columns(matrix: np.ndarray) -> np.ndarray:
    return matrix - matrix.mean(axis=0)       # (cols,) 沿行方向广播 → 每列减自己的均值


def rank_names(names: list[str], scores: list[float]) -> list[str]:
    if len(names) != len(scores):
        raise ValueError(f"names({len(names)}) 与 scores({len(scores)}) 长度不一致")
    if not names:
        return []
    arr = np.asarray(scores, dtype=float)
    order = np.argsort(-arr, kind="stable")   # 取负 + 稳定排序；argsort(arr)[::-1] 会把并列也反转
    return [names[i] for i in order.tolist()]


def select_and_sort(df: pd.DataFrame, columns: list[str], by: str) -> pd.DataFrame:
    selected = df.loc[:, columns]             # 按列名取列，列顺序就按 columns 来；缺列抛 KeyError
    return selected.sort_values(by=by).reset_index(drop=True)   # 返回新表，原表不动


def group_summary(df: pd.DataFrame, key: str, value: str) -> dict[str, dict[str, float]]:
    for column in (key, value):
        if column not in df.columns:
            raise KeyError(f"表里没有这一列：{column}")
    grouped = df.groupby(key)[value].agg(["count", "sum", "mean"])
    rows = grouped.to_dict(orient="index")
    summary = {}
    for name in sorted(rows, key=str):        # 顺序自己保证，不赌 groupby 的默认行为
        row = rows[name]
        summary[str(name)] = {
            "count": int(row["count"]),       # 出口统一转纯类型：np.int64 会炸 json.dumps
            "sum": float(row["sum"]),
            "mean": float(row["mean"]),
        }
    return summary


def fill_missing(df: pd.DataFrame, column: str, fill_value: float) -> pd.DataFrame:
    if column not in df.columns:
        raise KeyError(f"表里没有这一列：{column}")
    out = df.copy()                           # copy-on-write 时代：显式复制再整列赋值
    out[column] = out[column].fillna(fill_value)   # 而不是 df[column][mask] = 值
    return out


if __name__ == "__main__":     # 自检：跑一遍自己的题，顺便看看 json 序列不序列得动
    frame = read_csv_frame("name,score,cls\n关羽,90,一班\n张飞,70,二班\n刘备,85,一班\n")
    print(json.dumps(group_summary(frame, "cls", "score"), ensure_ascii=False))
    print(rank_names(list(frame["name"]), list(frame["score"])))
    print(create_grid(2, 3).tolist(), column_means(create_grid(2, 3)).tolist())
