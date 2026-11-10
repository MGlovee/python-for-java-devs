# -*- coding: utf-8 -*-
"""L15 判分用例（选做课）。别改这个文件 —— 它就是考官。

只用已装的 numpy 2.4.3 / pandas 3.0.1：不联网、不落盘，数据全部在内存里造。
推荐跑：py check.py L15 -v
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest
from exercises import (center_columns, column_means, create_grid, fill_missing,
                       group_summary, normalize, pick_by_mask, rank_names,
                       read_csv_frame, select_and_sort)

CSV = "name,score,cls\n关羽,90,一班\n张飞,70,二班\n刘备,85,一班\n"


def students() -> pd.DataFrame:
    """固定 3 行：一班两人（90/85），二班一人（70）。"""
    return read_csv_frame(CSV)


# ---------- ndarray：造形 / 轴 / 布尔索引 ----------

def test_01_create_grid_is_row_major_with_shape_metadata():
    got = create_grid(2, 3)
    assert isinstance(got, np.ndarray), "要 ndarray，不是 list 套 list"
    assert got.shape == (2, 3), "shape 是 (行, 列)，跟 Java 的 [rows][cols] 同序"
    assert got.tolist() == [[0, 1, 2], [3, 4, 5]], "按行铺（C 序），不是按列铺"
    assert got.dtype.kind == "i", "arange 出来是整型，别中途悄悄变 float"
    assert create_grid(1, 4).tolist() == [[0, 1, 2, 3]], "1 行也要保持二维"
    assert create_grid(4, 1).tolist() == [[0], [1], [2], [3]], "1 列同理"


def test_02_column_means_compresses_along_rows():
    got = column_means(np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]))
    assert got.shape == (2,), f"axis=0 压缩掉行 → 每列一个均值，收到 {got.shape}"
    assert np.allclose(got, [3.0, 4.0]), (
        f"axis 用反了会得到每行均值 [1.5, 3.5, 5.5]，实际是 {got.tolist()}")


def test_03_column_means_stays_one_dimensional():
    assert column_means(np.array([[7.0, 9.0]])).tolist() == [7.0, 9.0], "单行矩阵也能按列算"
    assert column_means(np.array([[2.0], [4.0]])).tolist() == [3.0], "单列时结果长度为 1"
    assert column_means(np.arange(6.0).reshape(2, 3)).ndim == 1, (
        "默认没有 keepdims，结果是 1 维；想要 (1, 3) 才传 keepdims=True")


def test_04_pick_by_mask_keeps_order_and_returns_python_list():
    arr = np.array([1, 5, 3, 7])
    got = pick_by_mask(arr, 4)
    assert isinstance(got, list), f"要 .tolist() 转成普通 list，收到 {type(got).__name__}"
    assert got == [5, 7], "布尔索引保留原顺序"
    assert pick_by_mask(arr, 100) == [], "没命中给空列表，不是 None"
    assert pick_by_mask(arr, -1) == [1, 5, 3, 7], "全都命中时也别丢元素"


def test_05_pick_by_mask_flattens_two_dimensions():
    matrix = np.array([[1, 5], [3, 7]])
    assert pick_by_mask(matrix, 4) == [5, 7], (
        "布尔索引的结果永远是 1 维：形状 (2,2) 里挑出 2 个元素，就只剩 (2,)")


# ---------- 归一化 / 广播 ----------

def test_06_normalize_maps_whole_matrix_to_unit_range():
    got = normalize(np.array([[0.0, 10.0], [20.0, 30.0]]))
    assert got.shape == (2, 2), "形状不许变"
    assert np.allclose(got, [[0.0, 1 / 3], [2 / 3, 1.0]]), (
        "(x - min) / (max - min) 用的是**全体**元素的 min/max，不是逐列")


def test_07_normalize_guards_divide_by_zero_and_int_input():
    flat = normalize(np.full((2, 3), 5.0))
    assert np.isfinite(flat).all(), "全相等时 max-min=0，除零会冒出 nan/inf"
    assert flat.tolist() == [[0.0] * 3, [0.0] * 3], "约定：全相等 → 全 0"
    assert np.allclose(normalize(np.array([[2, 4], [6, 8]])), [[0.0, 1 / 3], [2 / 3, 1.0]]), (
        "整型数组进、浮点结果出")


def test_08_center_columns_broadcasts_one_row_of_means():
    matrix = np.array([[0.0, 10.0], [20.0, 30.0]])
    got = center_columns(matrix)
    assert got.shape == matrix.shape, f"广播后形状必须不变，收到 {got.shape}"
    assert np.allclose(got, [[-10.0, -10.0], [10.0, 10.0]]), (
        f"每列减自己的均值（(0+20)/2=10、(10+30)/2=20）")
    assert np.allclose(got.mean(axis=0), [0.0, 0.0]), "中心化之后每列均值应为 0"


def test_09_center_columns_does_not_mutate_input():
    matrix = np.arange(6.0).reshape(2, 3)
    before = matrix.copy()
    got = center_columns(matrix)
    assert np.array_equal(matrix, before), "不许就地改传进来的数组"
    assert not np.shares_memory(got, matrix), "减法给的是新数组；reshape/切片才是视图"
    assert center_columns(np.array([[5.0, 5.0]])).tolist() == [[0.0, 0.0]], "单行也要保持二维"


# ---------- DataFrame：读入 / 选列 / 分组 / 缺失值 ----------

def test_10_read_csv_frame_reads_from_memory():
    df = students()
    assert isinstance(df, pd.DataFrame), "要 DataFrame，不是 ndarray"
    assert list(df.columns) == ["name", "score", "cls"], "第一行是表头"
    assert df.shape == (3, 3), "表头不算数据行"
    assert df["score"].dtype.kind in "if", "数字列自动转成数值型，不是字符串"
    assert df["score"].tolist() == [90, 70, 85]
    assert df["name"].tolist() == ["关羽", "张飞", "刘备"]


def test_11_read_csv_frame_marks_empty_field_as_na():
    df = read_csv_frame("name,score\n关羽,\n张飞,70\n")
    assert df["score"].isna().tolist() == [True, False], "空字段 read_csv 就当缺失"
    assert df["score"].mean() == pytest.approx(70.0), "mean 默认跳过 NaN，不用自己过滤"
    assert df["score"].tolist()[0] != df["score"].tolist()[0], "NaN != NaN，判缺失只能用 isna()"


def test_12_rank_names_sorts_descending_and_stably():
    names = ["关羽", "张飞", "刘备", "赵云"]
    scores = [90.0, 70.0, 85.0, 70.0]
    assert rank_names(names, scores) == ["关羽", "刘备", "张飞", "赵云"], (
        "降序；并列的张飞/赵云要保持输入顺序（argsort(scores)[::-1] 会把并列也反过来）")
    assert rank_names(["独苗"], [10.0]) == ["独苗"]
    assert rank_names([], []) == []


def test_13_rank_names_rejects_length_mismatch():
    with pytest.raises(ValueError):
        rank_names(["关羽", "张飞"], [90.0]), "两个列表长度不一致必须抛 ValueError"


def test_14_select_and_sort_uses_labels_and_resets_index():
    got = select_and_sort(students(), ["score", "name"], "score")
    assert list(got.columns) == ["score", "name"], "列顺序按传入的 columns，不是原表顺序"
    assert got["score"].tolist() == [70, 85, 90], "默认升序（降序要 ascending=False）"
    assert list(got.index) == [0, 1, 2], f"排序后要 reset_index(drop=True)，收到 {list(got.index)}"
    assert got["name"].tolist() == ["张飞", "刘备", "关羽"]


def test_15_select_and_sort_does_not_mutate_input():
    df = students()
    before = df.copy()
    select_and_sort(df, ["cls", "score"], "cls")
    assert df.equals(before), "sort_values 返回新表；改到原表说明你走了 inplace 思路"
    assert list(df.columns) == ["name", "score", "cls"]
    with pytest.raises(KeyError):
        select_and_sort(df, ["score", "分数"], "score"), "列名写错要抛 KeyError，别静默给子集"


def test_16_group_summary_returns_sorted_plain_python_values():
    got = group_summary(students(), "cls", "score")
    assert got == {"一班": {"count": 2, "sum": 175.0, "mean": 87.5},
                   "二班": {"count": 1, "sum": 70.0, "mean": 70.0}}, (
        f"(90+85)/2 与 70/1，实际 {got}")
    assert list(got.keys()) == sorted(got.keys()), "外层键必须自己排序，别赌 groupby 的默认顺序"
    assert all(type(v) in (int, float) for row in got.values() for v in row.values()), (
        f"np.int64/np.float64 不是 int/float，出口要转换：{got}")
    json.dumps(got)          # P3 的验收口径：统计结果要能直接序列化


def test_17_group_summary_count_skips_nan_and_validates_columns():
    got = group_summary(read_csv_frame("cls,score\n一班,90\n一班,\n二班,70\n"), "cls", "score")
    assert got["一班"]["count"] == 1, "count 是**非空**个数：NaN 那行不算（跟 SQL 的 COUNT(col) 一致）"
    assert got["一班"]["mean"] == pytest.approx(90.0), "NaN 也不参与均值，别当 0 平均进去"
    assert got["二班"]["count"] == 1 and got["二班"]["sum"] == pytest.approx(70.0)
    df = students()
    with pytest.raises(KeyError):
        group_summary(df, "班级", "score"), "分组列不存在要抛 KeyError"
    with pytest.raises(KeyError):
        group_summary(df, "cls", "分数"), "值列不存在要抛 KeyError"


def test_18_fill_missing_returns_new_frame_without_touching_original():
    df = read_csv_frame("name,score\n关羽,\n张飞,70\n刘备,\n")
    got = fill_missing(df, "score", 60.0)
    assert got["score"].tolist() == [60.0, 70.0, 60.0], "只填这一列的缺失"
    assert got["name"].tolist() == ["关羽", "张飞", "刘备"] and got.shape == (3, 2), "其他列与行数不变"
    assert df["score"].isna().sum() == 2, (
        "原表两处缺失还在 —— 改成 0 说明你用了链式赋值，pandas 3 下它会静默失效")
    assert list(got.index) == list(df.index) == [0, 1, 2]
    with pytest.raises(KeyError):
        fill_missing(df, "分数", 0.0), "列名不存在要抛 KeyError"
