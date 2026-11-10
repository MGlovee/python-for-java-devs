# -*- coding: utf-8 -*-
"""L01 判分用例。别改这个文件 —— 它就是考官。

单独跑：py -m pytest drills/L01 -q    （装了 pytest 才有效）
推荐跑：py check.py L01 -v            （零依赖）
"""
import pytest
from exercises import (collatz_steps, count_truthy, describe_value, divmod_pair,
                       fizzbuzz, gcd, grade, is_prime, max_and_second, move_zeroes)


def test_01_divmod_pair_positive():
    assert divmod_pair(7, 2) == (3.5, 3, 1), "7/2 真除得 3.5，整除得 3，余 1"


def test_02_divmod_pair_negative_floor():
    # 这一题专门抓带着 Java 直觉来写的人：// 是向下取整，不是截断
    assert divmod_pair(-7, 2) == (-3.5, -4, 1), "-7//2 是 -4（往负无穷取整），-7%2 是 1"


def test_03_count_truthy():
    items = [0, 1, "", "a", [], [1], None, False, True, {}, {"x": 1}, set(), {0}]
    assert count_truthy(items) == 6, (
        "真值是 1、'a'、[1]、True、{'x':1}、{0}；0 '' [] None False {} set() 都是假值")


def test_04_count_truthy_all_false():
    assert count_truthy([0, "", [], None, False, {}, set()]) == 0


def test_05_describe_value():
    assert describe_value(None) == "None"
    assert describe_value([]) == "假值", "空列表不是 None，但要归到假值"
    assert describe_value(0) == "假值"
    assert describe_value([0]) == "真值", "[0] 里有一个元素，非空即真"
    assert describe_value("0") == "真值"


def test_06_fizzbuzz_head():
    assert fizzbuzz(1) == ["1"]
    assert fizzbuzz(5) == ["1", "2", "Fizz", "4", "Buzz"]


def test_07_fizzbuzz_fizzbuzz_case():
    result = fizzbuzz(15)
    assert len(result) == 15, "n=15 时要产出 15 个元素，注意 range 左闭右开"
    assert result[14] == "FizzBuzz", "第 15 个（下标 14）同时是 3 和 5 的倍数"
    assert result[2] == "Fizz" and result[4] == "Buzz" and result[9] == "Buzz"


def test_08_grade_boundaries():
    assert grade(100) == "A"
    assert grade(90) == "A"
    assert grade(89) == "B"
    assert grade(60) == "D"
    assert grade(59) == "E"
    assert grade(0) == "E"


def test_09_grade_rejects_out_of_range():
    for bad in (101, -1, 999):
        with pytest.raises(ValueError):
            grade(bad)


def test_10_is_prime_basic():
    assert not is_prime(0) and not is_prime(1), "小于 2 不是素数"
    assert is_prime(2) and is_prime(3)
    assert not is_prime(4) and not is_prime(9) and not is_prime(25)
    assert is_prime(7919) and is_prime(2)


def test_11_gcd():
    assert gcd(12, 18) == 6
    assert gcd(18, 12) == 6
    assert gcd(7, 13) == 1
    assert gcd(0, 5) == 5 and gcd(5, 0) == 5
    assert gcd(-12, 18) == 6, "返回非负"


def test_12_collatz_steps():
    assert collatz_steps(1) == 0
    assert collatz_steps(6) == 8, "6→3→10→5→16→8→4→2→1 共 8 步"
    assert collatz_steps(27) == 111


def test_13_max_and_second():
    assert max_and_second([3, 1, 5]) == (5, 3)
    assert max_and_second([5, 5, 1]) == (5, 5), "允许最大值重复"
    assert max_and_second([-3, -9, -1]) == (-1, -3), "全负数也要对"
    assert max_and_second([1, 2]) == (2, 1)


def test_14_max_and_second_needs_two():
    with pytest.raises(ValueError):
        max_and_second([7])
    with pytest.raises(ValueError):
        max_and_second([])


def test_15_move_zeroes_order():
    nums = [0, 1, 0, 3, 12]
    assert move_zeroes(nums) == [1, 3, 12, 0, 0]
    assert nums == [0, 1, 0, 3, 12], "不能改动传进来的列表 —— 返回新列表"


def test_16_move_zeroes_edges():
    assert move_zeroes([]) == []
    assert move_zeroes([1, 2, 3]) == [1, 2, 3]
    assert move_zeroes([0, 0, 0]) == [0, 0, 0]
