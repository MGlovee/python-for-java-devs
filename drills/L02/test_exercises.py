# -*- coding: utf-8 -*-
"""L02 判分用例 —— 别改，它就是考官。"""
from __future__ import annotations

import pytest

from exercises import (chunked, dedup_keep_order, group_by_first_letter,
                       invert_index, merge_dicts, slice_tail, sort_by_key,
                       squares_of_evens, top_k_words, word_frequencies)


def test_01_slice_tail_basic():
    assert slice_tail([1, 2, 3, 4, 5], 2) == [4, 5]
    assert slice_tail(list("abcdef"), 3) == ["d", "e", "f"]


def test_02_slice_tail_edges():
    assert slice_tail([1, 2], 0) == [], "n=0 要给空列表，seq[-0:] 会给你整个列表 —— 这是本节的坑"
    assert slice_tail([1, 2], 5) == [1, 2], "n 超过长度就全给，不许抛"
    assert slice_tail([], 3) == []


def test_03_dedup_keep_order():
    assert dedup_keep_order([3, 1, 3, 2, 1]) == [3, 1, 2], "顺序按首次出现，不是排序"
    assert dedup_keep_order([]) == []
    assert dedup_keep_order(["b", "a", "b"]) == ["b", "a"]


def test_04_word_frequencies():
    assert word_frequencies(["a", "b", "a"]) == {"a": 2, "b": 1}
    assert word_frequencies([]) == {}


def test_05_group_by_first_letter():
    got = group_by_first_letter(["ant", "bee", "owl", "aardvark"])
    assert got == {"a": ["ant", "aardvark"], "b": ["bee"], "o": ["owl"]}, "组内保持原顺序"
    assert got["a"] == ["ant", "aardvark"]


def test_06_group_by_first_letter_empty():
    assert group_by_first_letter([]) == {}


def test_07_squares_of_evens():
    assert squares_of_evens(6) == [4, 16, 36]
    assert squares_of_evens(1) == []
    assert squares_of_evens(0) == [], "n<=0 不要抛，返回空"


def test_08_invert_index():
    got = invert_index({"d1": ["a", "b"], "d2": ["b"]})
    assert got == {"a": {"d1"}, "b": {"d1", "d2"}}
    assert isinstance(got["b"], (set, frozenset)), "值必须是集合，不是列表"


def test_09_invert_index_empty_doc():
    assert invert_index({"d1": []}) == {}, "没有词就不要产生空集合键"


def test_10_top_k_words_basic():
    words = ["a", "b", "a", "c", "b", "a"]
    assert top_k_words(words, 2) == ["a", "b"]


def test_11_top_k_words_tie_breaks_alphabetically():
    words = ["pear", "apple", "fig", "pear", "apple"]
    assert top_k_words(words, 2) == ["apple", "pear"], "同为 2 次时按字母序"
    assert top_k_words(words, 3) == ["apple", "pear", "fig"]


def test_12_top_k_words_more_than_available():
    assert top_k_words(["x", "y", "x"], 99) == ["x", "y"]
    assert top_k_words([], 3) == []


def test_13_sort_by_key_ascending():
    records = [{"n": 3}, {"n": 1}, {"n": 2}]
    assert sort_by_key(records, "n") == [{"n": 1}, {"n": 2}, {"n": 3}]


def test_14_sort_by_key_none_always_last():
    records = [{"n": 2}, {"m": 0}, {"n": 1}, {"n": None}]
    asc = sort_by_key(records, "n")
    assert [r.get("n") for r in asc] == [1, 2, None, None], "缺键按 None，且 None 排最后"
    desc = sort_by_key(records, "n", reverse=True)
    assert [r.get("n") for r in desc] == [2, 1, None, None], "reverse=True 也不能把 None 翻到前面"


def test_15_sort_by_key_does_not_mutate():
    records = [{"n": 2}, {"n": 1}]
    original = [dict(r) for r in records]
    out = sort_by_key(records, "n")
    assert records == original, "必须返回新列表，原列表顺序不动"
    assert out is not records


def test_16_chunked():
    assert chunked([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert chunked([1, 2, 3], 9) == [[1, 2, 3]]
    assert chunked([], 2) == []


def test_17_chunked_rejects_bad_size():
    for bad in (0, -1):
        with pytest.raises(ValueError):
            chunked([1, 2], bad)


def test_18_merge_dicts_adds_common_keys():
    assert merge_dicts({"a": 1, "b": 2}, {"b": 3, "c": 4}) == {"a": 1, "b": 5, "c": 4}


def test_19_merge_dicts_no_mutation():
    first, second = {"a": 1}, {"a": 2, "b": 3}
    out = merge_dicts(first, second)
    assert first == {"a": 1} and second == {"a": 2, "b": 3}, "两个入参都不许被改"
    assert out == {"a": 3, "b": 3}


def test_20_merge_dicts_empty_side():
    assert merge_dicts({}, {"a": 1}) == {"a": 1}
    assert merge_dicts({}, {}) == {}
