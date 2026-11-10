# -*- coding: utf-8 -*-
"""L02 练习工作表 —— 删掉 `raise NotImplementedError`，写上你的实现。

判分：  py check.py L02 -v
看答案：py check.py L02 --solution
只用内置类型和标准库，不要 import pandas。
"""
from __future__ import annotations

from collections import Counter, defaultdict


# ---------- 第一组：挖空题 ----------

def slice_tail(seq: list, n: int) -> list:
    """返回 seq 的最后 n 个元素（n 可能大于长度，也可能为 0）。

    提示：`seq[a:]` 的 a 是负数时从尾部数；想不用任何分支，可以把"起点"算成正数。
    >>> slice_tail([1, 2, 3, 4, 5], 2)
    [4, 5]
    >>> slice_tail([1, 2], 5)
    [1, 2]
    """
    raise NotImplementedError


def dedup_keep_order(items: list) -> list:
    """去重且保持首次出现的顺序。

    提示：dict 从 3.7 起保证插入序，`dict.fromkeys(items)` 的键就是天然的保序去重器。
    >>> dedup_keep_order([3, 1, 3, 2, 1])
    [3, 1, 2]
    """
    raise NotImplementedError


def word_frequencies(words: list[str]) -> dict[str, int]:
    """统计词频，返回 {词: 次数}。

    提示：`Counter(words)` 就是一个 dict 子类，直接返回它即可。
    >>> word_frequencies(["a", "b", "a"]) == {"a": 2, "b": 1}
    True
    """
    raise NotImplementedError


def group_by_first_letter(words: list[str]) -> dict[str, list[str]]:
    """按首字母分组，值为该组单词列表，组内保持原顺序。空列表返回 {}。

    提示：`defaultdict(list)` 省掉 `if key not in d`。返回时记得转回普通 dict。
    >>> group_by_first_letter(["ant", "bee", "owl"])
    {'a': ['ant'], 'b': ['bee'], 'o': ['owl']}
    """
    raise NotImplementedError


def squares_of_evens(n: int) -> list[int]:
    """用**一条推导式**返回 1..n 中所有偶数的平方。

    提示：`表达式 for x in 可迭代对象 if 条件`。
    >>> squares_of_evens(6)
    [4, 16, 36]
    """
    raise NotImplementedError


def invert_index(docs: dict[str, list[str]]) -> dict[str, set[str]]:
    """把 {文档id: [词,...]} 倒排成 {词: {文档id,...}}。用**一条嵌套推导式**写完。

    提示：外层遍历 docs.items()，内层遍历词；`setdefault` 在这里用不了，要靠集合合并。
    参考做法：先收集 (词, 文档id) 的扁平序列，再聚合。
    >>> invert_index({"d1": ["a", "b"], "d2": ["b"]}) == {"a": {"d1"}, "b": {"d1", "d2"}}
    True
    """
    raise NotImplementedError


# ---------- 第二组：只给需求 ----------

def top_k_words(words: list[str], k: int) -> list[str]:
    """返回出现次数最多的 k 个词。

    排序规则：次数降序；次数相同时按**字母序升序**。返回词列表，不含次数。
    k 大于词的种类数时返回全部。不许用 Counter.most_common 之外再排序偷懒——
    要么用它的 ties 处理，要么自己排稳。
    """
    raise NotImplementedError


def sort_by_key(records: list[dict], key: str, *, reverse: bool = False) -> list[dict]:
    """按记录里某个键的值排序，返回**新列表**，不得修改传入的 records。

    记录缺该键时按 None 处理，且所有 None 一律排在最后（不管 reverse 是真是假）。
    """
    raise NotImplementedError


def chunked(seq: list, size: int) -> list[list]:
    """把列表切成每段 size 个的若干小列表，最后一段可以短。

    size 小于 1 时抛 ValueError。空列表返回 []。
    提示：range(0, len(seq), size) + 切片。
    """
    raise NotImplementedError


def merge_dicts(first: dict, second: dict) -> dict:
    """合并两个字典，**键相同时把值相加**（值都是数字），其余键保留。

    不得修改 first / second。用 3.9+ 的 `|` 运算符只是覆盖，不满足本题，需要额外处理同键。
    示例：merge_dicts({"a": 1, "b": 2}, {"b": 3, "c": 4}) == {"a": 1, "b": 5, "c": 4}
    """
    raise NotImplementedError
