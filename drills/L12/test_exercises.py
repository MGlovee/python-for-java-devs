# -*- coding: utf-8 -*-
"""L12 判分用例。别改这个文件 —— 它就是考官。

并发测试只断言"可验证的结果"：总和、计数、返回值、字典内容。
不断言线程执行顺序，不测墙钟时间，不用 sleep 制造竞争。
推荐跑：py check.py L12 -v
"""
from __future__ import annotations

import threading

import pytest
from exercises import (async_lengths, barrier_two_phases, chunk_items, divide_in_threads,
                       event_outcome, increment_shared, map_in_threads,
                       recommend_concurrency, run_async_squares, sum_from_queue)


def _double(n: int) -> int:
    return n * 2


def _identity(n: int) -> int:
    return n


def test_01_map_in_threads_basic():
    assert map_in_threads(_double, [1, 2, 3], 3) == [2, 4, 6]


def test_02_map_in_threads_keeps_input_order():
    items = list(range(200))
    assert map_in_threads(_identity, items, 8) == items, (
        "结果顺序必须跟输入一致 —— 用 as_completed 就过不了这条")
    assert map_in_threads(_double, [], 4) == []


def test_03_increment_shared_exact():
    assert increment_shared(8, 500) == 4000, "有锁保护就不许丢更新"
    assert increment_shared(1, 7) == 7, "单线程也必须给出同样结果"


def test_04_increment_shared_zero_work():
    assert increment_shared(4, 0) == 0
    assert increment_shared(1, 0) == 0


def test_05_sum_from_queue_all_items_counted():
    assert sum_from_queue(list(range(1, 101)), 4) == 5050, "每个元素恰好被取走一次"


def test_06_sum_from_queue_edges():
    assert sum_from_queue([], 3) == 0
    assert sum_from_queue([7], 5) == 7, "线程比数据多也不许卡住"


def test_07_event_outcome_triggered():
    done = threading.Event()
    done.set()
    assert event_outcome(done, 0.01) == "触发", "已经 set 过就不该等"


def test_08_event_outcome_timeout():
    never = threading.Event()
    assert event_outcome(never, 0.02) == "超时", "wait 的返回值就是答案"
    assert event_outcome(never, 0) == "超时", "timeout=0 表示只看一眼"
    never.set()
    assert event_outcome(never, 0) == "触发"


def test_09_run_async_squares():
    assert run_async_squares([0, 1, 2, 3]) == [0, 1, 4, 9]
    assert run_async_squares([]) == []


def test_10_run_async_squares_order_and_size():
    nums = list(range(100))
    assert run_async_squares(nums) == [n * n for n in nums]


def test_11_async_lengths():
    got = async_lengths(["ab", "abc", "x"], 0.001)
    assert dict(sorted(got.items())) == {"ab": 2, "abc": 3, "x": 1}
    assert async_lengths([], 0.001) == {}


def test_12_async_lengths_dedups_keys():
    assert async_lengths(["a", "a"], 0) == {"a": 1}, "同名键合并，不许抛"


def test_13_recommend_concurrency_truth_table():
    assert recommend_concurrency(True, True) == "process", "CPU 密集优先看 GIL"
    assert recommend_concurrency(True, False) == "process"
    assert recommend_concurrency(False, True) == "async"
    assert recommend_concurrency(False, False) == "thread"


def test_14_chunk_items_splits_contiguously():
    assert chunk_items([1, 2, 3, 4, 5], 2) == [[1, 2, 3], [4, 5]]
    assert chunk_items([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]
    assert chunk_items(list(range(7)), 3) == [[0, 1, 2], [3, 4], [5, 6]], "除不尽时靠前多分一个"


def test_15_chunk_items_edges():
    assert chunk_items([], 3) == [[], [], []], "长度必须恰好等于 workers"
    assert chunk_items([1, 2], 5) == [[1], [2], [], [], []]
    with pytest.raises(ValueError):
        chunk_items([1], 0)
    with pytest.raises(ValueError):
        chunk_items([1], -3)


def test_16_barrier_two_phases_results():
    first, second = barrier_two_phases([1, 2, 3, 4])
    assert first == [2, 4, 6, 8], "阶段一按输入顺序摆放"
    assert second == [n * n for n in first], "阶段二是阶段一的平方"


def test_17_barrier_two_phases_edges():
    assert barrier_two_phases([]) == ([], []), "Barrier(0) 会报错，空输入要提前返回"
    assert barrier_two_phases([5]) == ([10], [100])


def test_18_divide_in_threads_collects_errors():
    assert divide_in_threads([10, 5], 2) == ["5.0", "2.5"]
    assert divide_in_threads([1, 2, 3], 0) == ["error", "error", "error"], (
        "子线程里的异常要在这层收住，不能整体崩")
    assert divide_in_threads([], 3) == []
