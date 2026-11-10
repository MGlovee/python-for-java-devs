# -*- coding: utf-8 -*-
"""L04 判分用例。别改这个文件 —— 它就是考官。

单独跑：py -m pytest drills/L04 -q    （装了 pytest 才有效）
推荐跑：py check.py L04 -v            （零依赖）
"""
import pytest
from exercises import (apply_twice, call_shape, compose, dispatch, format_join,
                       make_accumulator, make_adder, make_base_converters,
                       rank_students, sum_numeric)


def test_01_call_shape_empty():
    assert call_shape() == (0, 0), "不传参数时 args 是空元组、kwargs 是空字典，不是 None"


def test_02_call_shape_mixed():
    assert call_shape(1, 'x', None, name='bob', age=3) == (3, 2)
    assert call_shape(a=1) == (0, 1), "只有关键字参数时位置参数个数为 0"


def test_03_sum_numeric_skips_non_numbers():
    assert sum_numeric(1, 2, 'x', [3], None, 4) == 7, "[3] 是列表，不是数值，整个跳过"
    assert sum_numeric() == 0


def test_04_sum_numeric_excludes_bool():
    assert sum_numeric(True, False, 3) == 3, (
        "isinstance(True, int) 是 True，用 isinstance 判数值会把布尔值算成 1")


def test_05_sum_numeric_start_keyword():
    assert sum_numeric(10, start=2) == 12, "start 是命名关键字参数，只能按名字传"
    assert sum_numeric(1, 2, 10) == 13, "不带名字就是第 3 个位置参数，被当成待加的值"
    assert sum_numeric('a', 'b', start=5) == 5


def test_06_format_join_basic():
    assert format_join('-', 'a', 1, 'b') == 'a-1-b', "非字符串要先 str()"
    assert format_join('::', 1, 2) == '1::2'
    assert format_join('-') == '', "一个元素都没有时是空串，不是分隔符"


def test_07_format_join_trailing():
    assert format_join(',', 'a', 'b', trailing=True) == 'a,b,'
    assert format_join(',', 'a', 'b', trailing=False) == 'a,b'


def test_08_format_join_trailing_positional_is_silent_bug():
    # Java 里参数顺序/类型错了编译器就拦住了；Python 有 *items 时是多出来的位置参数被**吸走**
    assert format_join('-', 'a', 'b', True) == 'a-b-True', (
        "trailing 只能用名字传；按位置传会被 *items 吞掉并 str() 成 'True'，没有报错")


def test_09_make_adder_closure():
    add3 = make_adder(3)
    assert callable(add3), "返回的是函数本身，别在 return 时加括号调用"
    assert add3(10) == 13 and add3(0) == 3
    assert make_adder(0)(5) == 5
    assert make_adder(7)(1) == 8, "另一个闭包不共享 add3 里的 n"


def test_10_apply_twice_lambda():
    assert apply_twice(lambda x: x * 2, 3) == 12
    assert apply_twice(lambda x: x * x, 3) == 81, "3*3=9，再 9*9=81"


def test_11_apply_twice_counts_calls():
    calls = []

    def spy(x: int) -> int:
        calls.append(x)
        return x + 1

    assert apply_twice(spy, 5) == 7
    assert calls == [5, 6], "函数能当参数传进去，spy 被调用两次"


def test_12_make_base_converters():
    two, sixteen = make_base_converters()
    assert two('1011') == 11
    assert sixteen('ff') == 255 and sixteen('FF') == 255
    assert two('0') == 0
    with pytest.raises(ValueError):
        two('9'), "9 不是合法的二进制位"


def test_13_compose_order():
    h = compose(lambda x: x + 1, lambda x: x * 2)
    assert h(3) == 7, "compose(f, g) 就是 f(g(x))：从右往左"
    assert h(0) == 1


def test_14_compose_identity_and_chain():
    assert compose()(5) == 5, "空复合等于恒等函数"
    triple = compose(lambda x: x * 3, lambda x: x - 1, lambda x: x * x)
    assert triple(2) == 9, "先平方(4)，再减一(3)，再乘三(9)"


def test_15_rank_students():
    students = [{'name': 'Bob', 'score': 90},
                {'name': 'Amy', 'score': 90},
                {'name': 'Cid', 'score': 95}]
    assert rank_students(students) == ['Cid', 'Amy', 'Bob'], (
        "分数降序，同分按名字升序")


def test_16_rank_students_no_mutation():
    students = [{'name': 'Zoe', 'score': 60}, {'name': 'Ann', 'score': 80}]
    snapshot = [s['name'] for s in students]
    result = rank_students(students)
    assert result == ['Ann', 'Zoe']
    assert [s['name'] for s in students] == snapshot, "只能返回新列表，不许 sort 原列表"
    assert result is not students


def test_17_make_accumulator_isolation():
    acc = make_accumulator()
    assert acc(1) == 1
    assert acc(10) == 11
    assert acc(-5) == 6
    other = make_accumulator()
    assert other(100) == 100, "新累加器不许继承 acc 的历史 —— 抓用默认参数当累加器的写法"


def test_18_dispatch_ops():
    assert dispatch('+')(2, 3) == 5
    assert dispatch('-')(2, 3) == -1
    assert dispatch('*')(2, 3) == 6
    assert dispatch('//')(7, 2) == 3
    assert dispatch('%')(7, 2) == 1
    with pytest.raises(ValueError):
        dispatch('/')
