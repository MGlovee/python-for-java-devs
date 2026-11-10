# -*- coding: utf-8 -*-
"""L15 练习工作表（**选做课**）—— numpy / pandas 的最小可用集。

本机已装 numpy 2.4.3、pandas 3.0.1，直接 `import` 就行；**不要**自己写 try/except 兜住
`ModuleNotFoundError`，判分器看到它会记成「缺依赖」，那是给阅卷人看的信号，不是你的 bug。

一句话心智：
    numpy 管"一整块同类型的数字"（ndarray：一次运算作用到全部元素，别写 for 循环）
    pandas 管"带列名的表"（Series / DataFrame ≈ 带索引的 List<Map>）

铁律：
    1) 数据全在内存里造。CSV 一律用 `io.StringIO` + `pd.read_csv(StringIO(text))`，
       **禁止 tempfile、禁止任何落盘**，判分器在无网络无写入的环境里跑。
    2) 返回给调用方的东西要"好断言"：能返回 list/dict 就别丢一个 ndarray 或 Series 出去，
       并且必须把 numpy 标量转成纯 Python `int`/`float`（P3 项目里 json.dumps 就炸在这）。
"""
from __future__ import annotations

import io

import numpy as np
import pandas as pd


# ---------- 第一组：挖空题（有提示，照着填） ----------

def create_grid(rows: int, cols: int) -> np.ndarray:
    """造 `rows × cols` 的二维数组，值从 0 递增、按行铺（第 2 行是 `[cols, cols+1, …]`）。

    提示：`np.arange(rows * cols).reshape(rows, cols)` —— 先拉成一维，再改形状。
    对照 Java：`new int[rows][cols]` 是"行的数组，每行指向另一个数组"；
              ndarray 是**一整块连续内存 + (shape, strides) 元数据**，reshape 只是换元数据。
    坑：`reshape` 返回的是**视图**（view），改视图会改到原数组；要独立副本得 `.copy()`。
    """
    raise NotImplementedError


def column_means(matrix: np.ndarray) -> np.ndarray:
    """求每一**列**的平均值，返回长度为 cols 的**一维**数组。

    提示：`matrix.mean(axis=0)`。`axis=0` 读作"沿行的方向压缩"，压缩掉轴 0 就剩下列；
          `axis=1` 才是每行均值。想要形状保持 `(1, cols)` 才加 `keepdims=True`，本题不要。
    对照 Java：这一行替掉了 `for (int c…) { for (int r…) sum += m[r][c]; }` 整个双重循环。
    """
    raise NotImplementedError


def pick_by_mask(arr: np.ndarray, threshold: float) -> list[float]:
    """布尔索引：取出所有 `>= threshold` 的元素，**按原顺序**返回 Python list。

    提示：`arr[arr >= threshold]` 得到的还是 ndarray，用 `.tolist()` 转成 list 才好断言。
    坑：比较运算在数组上是**逐元素**的，所以 `if arr >= 3:` 会抛
        `ValueError: truth value of an array with more than one element is ambiguous`；
        多个条件用 `&` / `|` 并且**每个条件加括号**，`and` / `or` 直接报错。
    """
    raise NotImplementedError


def normalize(matrix: np.ndarray) -> np.ndarray:
    """min-max 归一化到 `[0, 1]`：`(x - min) / (max - min)`；**全相等时返回全 0**（别除零）。

    提示：`span = np.ptp(matrix)`（等价于 `matrix.max() - matrix.min()`），先判 `span == 0` 再除。
    注意：numpy 2 起 **`matrix.ptp()` 这个实例方法被删了**，只能写 `np.ptp(matrix)`；
          旧教程里 `arr.ptp()` 的写法现在直接 AttributeError。
    """
    raise NotImplementedError


def read_csv_frame(text: str) -> pd.DataFrame:
    """不落地读 CSV 文本：字符串 → DataFrame（第一行当表头）。

    提示：`pd.read_csv(io.StringIO(text))` —— `read_csv` 收路径、句柄、bytes，
          内存里的字符串包一层 `StringIO` 就行，别为了测试去写临时文件。
    注意：数字列会自动转成 int64/float64，文本列在 pandas 3 里是新的 `str`  dtype（不是 object）。
    """
    raise NotImplementedError


# ---------- 第二组：只给需求（独立写） ----------

def center_columns(matrix: np.ndarray) -> np.ndarray:
    """把每一列减去**该列**的均值（中心化），返回形状不变的新数组。

    要求：1) 结果 `shape` 跟 `matrix` 完全一致，不许降成一维；
          2) 一行搞定，不许 `for c in range(matrix.shape[1])` 逐列循环；
          3) 每列的均值必须是 `axis=0` 那一个（`axis=1` 会得到形状 (rows,) 广播不上去）；
          4) 不许改动传进来的 `matrix`。
    """
    raise NotImplementedError


def rank_names(names: list[str], scores: list[float]) -> list[str]:
    """按分数**从高到低**返回对应的名字列表（并列时保持输入里的先后顺序）。

    要求：1) 用 `np.argsort`，不许 `sorted(..., key=...)`（那练不到 argsort）；
          2) 并列必须**稳定**：`np.argsort(-scores, kind="stable")`；
             `np.argsort(scores)[::-1]` 是错的——它把并列项的顺序也一起反转了；
          3) 返回普通 `list[str]`；空输入给空列表；
          4) 两个列表长度不一致 → 抛 `ValueError`。
    """
    raise NotImplementedError


def select_and_sort(df: pd.DataFrame, columns: list[str], by: str) -> pd.DataFrame:
    """取指定列（**列顺序按 columns 给的来**）并按 `by` 列升序排序，索引重置成 0..n-1。

    要求：1) 用 `df.loc[:, columns]` 一类的按列名取列，不要靠下标猜；
          2) 排序后 `reset_index(drop=True)`，否则索引是打乱的原始行号；
          3) 传进来的表**一个字都不许变**（`sort_values` 本来就返回新表，别用 inplace 思路）；
          4) `columns` 里有不存在的列名 → 抛 `KeyError`。
    """
    raise NotImplementedError


def group_summary(df: pd.DataFrame, key: str, value: str) -> dict[str, dict[str, float]]:
    """分组统计：返回 `{组名: {"count": 个数, "sum": 合计, "mean": 均值}}`，外层键按字典序排好。

    要求：1) 用 `df.groupby(key)[value].agg([...])`，不许自己写循环累加
             （这就是 Java `Collectors.groupingBy + reducing` 的那一步）；
          2) **`count` 是非空个数**：value 列里的 NaN 不参与计数，也不参与 sum/mean（跟 SQL 一致）；
          3) 值必须是纯 Python `int` / `float`：`json.dumps(结果)` 不许抛
             （numpy 标量长得很像 int，但 `json.dumps` 立刻 `TypeError`，P3 就坑在这）；
          4) 外层键排序后再构造 —— groupby 默认按键排序，但**别把巧合当契约**；
          5) `key` 或 `value` 列不存在 → 抛 `KeyError`。
    """
    raise NotImplementedError


def fill_missing(df: pd.DataFrame, column: str, fill_value: float) -> pd.DataFrame:
    """把 `column` 列的缺失值填成 `fill_value`，**返回新表**，传进来的表一字不变。

    要求：1) 用 `isna()` / `fillna()` 这一套三件套；`column == None` 那种比较永远判不出缺失；
          2) **禁止链式赋值** `df[column][mask] = …`：pandas 3 默认 copy-on-write，
             它只会给你一条 `ChainedAssignmentError` 告警，然后**静默不改原表**；
          3) 其他列、行数、索引都保持原样；只填这一列的缺失；
          4) `column` 不在表里 → 抛 `KeyError`。
    """
    raise NotImplementedError
