# -*- coding: utf-8 -*-
"""L08 判分用例。别改这个文件 —— 它就是考官。

单独跑：py -m pytest drills/L08 -q    （装了 pytest 才有效）
推荐跑：py check.py L08 -v            （零依赖）
"""
import pytest
from exercises import (compose, deprecated, first_index, int_values_only,
                       memoize, merge_dicts, repeat, shout, stacked_result,
                       twice)


def _add(a, b):
    return a + b


def _quiet() -> str:
    return "quiet"


def test_01_twice_doubles_and_passes_args():
    doubled = twice(_add)
    assert doubled(2, 3) == 10, "先算 5 再乘 2"


def test_02_twice_composable():
    assert twice(twice(_add))(1, 1) == 8, "twice(twice(add)) 应乘 4"


def test_03_shout_transforms_return():
    loud = shout(_quiet)
    assert loud() == "QUIET"


def test_04_shout_keeps_metadata():
    loud = shout(_quiet)
    assert loud.__name__ == "_quiet", "忘写 @wraps —— __name__ 变成了 wrapper"
    assert getattr(loud, "__wrapped__", None) is not None, "wraps 还会挂 __wrapped__ 逃生口"
    assert loud.__wrapped__() == "quiet", "__wrapped__ 调的是未装饰的原函数"


def test_05_repeat_collects_results():
    counter = {"n": 0}

    def tick():
        counter["n"] += 1
        return counter["n"]

    assert repeat(3)(tick)() == [1, 2, 3]
    assert counter["n"] == 3, "确实执行了 3 次"


def test_06_repeat_zero():
    assert repeat(0)(_quiet)() == []


def test_07_stacked_result_order():
    # @mark_a 在上、@mark_b 在下：base 先被 mark_b 包（产出 "b"），再被 mark_a 包（追加 "a"）
    assert stacked_result() == "ba", "装饰器自下而上应用；写成 'ab' 说明顺序记反了"


def test_08_merge_dicts_override():
    merged = merge_dicts({"a": 1, "b": 2}, {"b": 3, "c": 4})
    assert merged == {"a": 1, "b": 3, "c": 4}, "冲突键 b 以第二个字典为准"


def test_09_merge_dicts_does_not_mutate():
    a = {"x": 1}
    b = {"y": 2}
    merged = merge_dicts(a, b)
    assert a == {"x": 1} and b == {"y": 2}, "不许修改入参"
    assert merged is not a and merged is not b


def test_10_merge_dicts_empty_side():
    assert merge_dicts({}, {"k": "v"}) == {"k": "v"}
    assert merge_dicts({}, {}) == {}


def test_11_first_index_found():
    assert first_index([1, 4, 7], lambda x: x > 5) == 2
    assert first_index(["ab", "c", "de"], lambda s: len(s) > 1) == 0, "命中的是第一个"


def test_12_first_index_missing():
    assert first_index([1, 2], lambda x: x > 9) is None, "找不到返回 None，不许抛异常"
    assert first_index([], lambda x: True) is None


def test_13_deprecated_logs_and_passes():
    log: list[str] = []

    @deprecated(log)
    def old_api(x):
        return x + 1

    assert old_api(41) == 42, "返回值必须透传"
    assert old_api(1) == 2
    assert log == ["deprecated:old_api", "deprecated:old_api"], "每次调用记一条，用原函数名"
    assert old_api.__name__ == "old_api", "还要用 wraps 保住元信息"


def test_14_memoize_skips_recompute():
    counter = {"n": 0}

    def slow(x):
        counter["n"] += 1
        return x * 2

    memo = memoize(slow)
    assert memo(3) == 6 and memo(3) == 6
    assert counter["n"] == 1, "同参数第二次必须吃缓存"
    assert memo(4) == 8
    assert counter["n"] == 2, "不同参数要真算"


def test_15_memoize_multi_args():
    calls = []

    def join2(a, b):
        calls.append((a, b))
        return f"{a}-{b}"

    memo = memoize(join2)
    assert memo("x", "y") == "x-y"
    assert memo("x", "y") == "x-y"
    assert memo("y", "x") == "y-x"
    assert len(calls) == 2, "(x,y) 与 (y,x) 是两个不同的键"


def test_16_compose_left_to_right():
    add_one = lambda x: x + 1
    double = lambda x: x * 2
    assert compose(add_one, double)(3) == 8, "先 +1 再 ×2"
    assert compose(double, add_one)(3) == 7, "顺序反过来结果不同 —— 左到右"


def test_17_compose_edges():
    assert compose(str)(5) == "5", "单个函数就是它自己"
    assert compose()(7) == 7, "空 compose 是恒等函数"


def test_18_int_values_only_filters_bool():
    data = {"a": 1, "b": "x", "c": True, "d": 2, "e": 3.5, "f": None}
    assert int_values_only(data) == {"a": 1, "d": 2}, "True/False 是 int 子类但 type 不是 int"
    assert int_values_only({}) == {}
