# -*- coding: utf-8 -*-
"""L04 参考答案。

别整篇抄 —— 它的价值在于卡住 15 分钟后对照思路。
验证题目本身有没有写错：py check.py L04 --solution
"""
from __future__ import annotations

import functools
from typing import Callable


def call_shape(*args, **kwargs) -> tuple[int, int]:
    return len(args), len(kwargs)


def sum_numeric(*values: object, start: int = 0) -> int:
    total = start
    for v in values:
        if type(v) in (int, float):     # type() 是精确匹配，天然排掉 bool
            total += v
    return total


def format_join(sep: str, *items: object, trailing: bool = False) -> str:
    joined = sep.join(str(item) for item in items)
    return joined + sep if trailing else joined


def make_adder(n: int) -> Callable[[int], int]:
    def add(x: int) -> int:
        return x + n          # n 是被捕获的自由变量，不在 add 的局部作用域里
    return add                # 返回函数对象本身，没加括号


def apply_twice(func: Callable[[int], int], value: int) -> int:
    return func(func(value))


def make_base_converters() -> tuple[Callable[[str], int], Callable[[str], int]]:
    return functools.partial(int, base=2), functools.partial(int, base=16)


def compose(*funcs: Callable[[int], int]) -> Callable[[int], int]:
    def applied(value: int) -> int:
        for func in reversed(funcs):     # 从右往左，所以要用 reversed
            value = func(value)
        return value
    return applied


def rank_students(students: list[dict[str, object]]) -> list[str]:
    ordered = sorted(                      # sorted 返回新列表，原列表不动
        students,
        key=lambda s: (-int(s['score']), str(s['name'])),   # 元组 key：先分数后名字
    )
    return [str(s['name']) for s in ordered]


def make_accumulator() -> Callable[[int], int]:
    total = 0

    def add(step: int) -> int:
        nonlocal total          # 没有 nonlocal，这里的 total += 会 UnboundLocalError
        total += step
        return total
    return add


def dispatch(op: str) -> Callable[[int, int], int]:
    ops: dict[str, Callable[[int, int], int]] = {
        '+': lambda x, y: x + y,
        '-': lambda x, y: x - y,
        '*': lambda x, y: x * y,
        '//': lambda x, y: x // y,
        '%': lambda x, y: x % y,
    }
    if op not in ops:
        raise ValueError(f'不支持的运算符：{op!r}')
    return ops[op]
