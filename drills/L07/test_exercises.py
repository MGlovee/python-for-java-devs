# -*- coding: utf-8 -*-
"""L07 判分用例。别改这个文件 —— 它就是考官。

单独跑：py -m pytest drills/L07 -q    （装了 pytest 才有效）
推荐跑：py check.py L07 -v            （零依赖）
"""
import pytest
from exercises import (averager, chunked, cycle_first, fib_cached, flatten,
                       multiply_all, pairwise, squares, take, top_frequent)


def test_01_take_basic():
    assert take([1, 2, 3, 4], 2) == [1, 2]
    assert take([1, 2, 3], 10) == [1, 2, 3], "不够 n 个就取光，不许抛 StopIteration"


def test_02_take_zero_and_empty():
    assert take([1, 2], 0) == []
    assert take([], 3) == []


def test_03_take_consumes_iterator():
    it = iter([1, 2, 3, 4, 5])
    assert take(it, 2) == [1, 2]
    assert take(it, 2) == [3, 4], "迭代器是一次性游标：第二次 take 从断点继续，不是重新数"


def test_04_squares_is_lazy():
    gen = squares([1, 2, 3])
    assert next(gen) == 1
    assert list(gen) == [4, 9], "已产出的 1 不会再出现 —— 生成器只向前"
    with pytest.raises(StopIteration):
        next(gen)


def test_05_squares_empty():
    assert list(squares([])) == []


def test_06_flatten():
    assert list(flatten([[1, 2], [], [3], [4, 5]])) == [1, 2, 3, 4, 5]
    assert list(flatten([])) == []


def test_07_averager_stream():
    gen = averager()
    assert next(gen) == 0.0, "priming：推进到第一个 yield，初始平均 0.0"
    assert gen.send(10) == 10.0
    assert gen.send(20) == 15.0
    assert gen.send(30) == 20.0, "send 的值就是 yield 表达式的结果"


def test_08_averager_keeps_running():
    gen = averager()
    next(gen)
    for v in (1, 2, 3, 4):
        gen.send(v)
    assert gen.send(0) == 2.0, "无限 while True：不会自己停"


def test_09_cycle_first():
    assert cycle_first([1, 2], 5) == [1, 2, 1, 2, 1]
    assert cycle_first(["a"], 3) == ["a", "a", "a"]
    assert cycle_first([], 4) == [], "空序列不能进 cycle（会无限挂起），先挡住"


def test_10_multiply_all():
    assert multiply_all([2, 3, 4]) == 24
    assert multiply_all([]) == 1, "空列表返回 reduce 的初值 1"
    assert multiply_all([7]) == 7
    assert multiply_all([-2, 3]) == -6


def test_11_chunked_even_and_uneven():
    assert chunked([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert chunked([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]
    assert chunked([], 3) == []


def test_12_chunked_rejects_bad_size():
    data = [1, 2, 3]
    for bad in (0, -1):
        with pytest.raises(ValueError):
            chunked(data, bad)
    assert data == [1, 2, 3], "不许修改传入列表"


def test_13_pairwise():
    assert pairwise([1, 2, 3]) == [(1, 2), (2, 3)]
    assert pairwise("abc") == [("a", "b"), ("b", "c")]
    assert pairwise([9]) == []
    assert pairwise([]) == []


def test_14_top_frequent_sorted_deterministically():
    words = ["pear", "apple", "pear", "fig", "fig", "apple", "pear"]
    assert top_frequent(words, 2) == [("pear", 3), ("apple", 2), ("fig", 2)][:2]
    got = top_frequent(words, 3)
    assert got == [("pear", 3), ("apple", 2), ("fig", 2)], "并列时按字典序升序"
    assert got[0][1] >= got[1][1] >= got[2][1], "次数降序"


def test_15_top_frequent_n_larger_than_vocab():
    assert top_frequent(["a", "b", "a"], 10) == [("a", 2), ("b", 1)]
    assert top_frequent([], 3) == []


def test_16_fib_cached_values():
    assert fib_cached(0) == 0
    assert fib_cached(1) == 1
    assert fib_cached(10) == 55


def test_17_fib_cached_is_fast():
    # 没有 lru_cache 的朴素递归 fib(100) 永远算不完；有缓存则毫秒级
    assert fib_cached(100) == 354224848179261915075
    assert fib_cached(120) == 5358359254990966640871840
