# -*- coding: utf-8 -*-
"""L08 参考答案。

别整篇抄 —— 它的价值在于卡住 15 分钟后对照思路。
验证题目本身有没有写错：py check.py L08 --solution
"""
from __future__ import annotations

from collections.abc import Callable
from functools import wraps


def mark_a(func: Callable[[], str]) -> Callable[[], str]:
    def wrapper() -> str:
        return func() + "a"
    return wrapper


def mark_b(func: Callable[[], str]) -> Callable[[], str]:
    def wrapper() -> str:
        return func() + "b"
    return wrapper


def twice(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs) * 2      # 增强：改返回值；参数照单全收再原样转交
    return wrapper


def shout(func: Callable[[], str]) -> Callable[[], str]:
    @wraps(func)                              # 保住 __name__/__doc__，并挂上 __wrapped__
    def wrapper() -> str:
        return func().upper()
    return wrapper


def repeat(times: int) -> Callable:
    def decorate(func):                       # 带参数 = 多一层工厂
        @wraps(func)
        def wrapper(*args, **kwargs):
            return [func(*args, **kwargs) for _ in range(times)]
        return wrapper
    return decorate


def stacked_result() -> str:
    @mark_a
    @mark_b                                   # 等价于 base = mark_a(mark_b(base))
    def base():
        return ""
    return base()                             # 内层 mark_b 先执行 → "ba"


def merge_dicts(a: dict, b: dict) -> dict:
    return {**a, **b}                         # 解包构造新字典，后面的覆盖前面的


def first_index(items: list, pred: Callable[[object], bool]) -> int | None:
    return next((i for i, x in enumerate(items) if pred(x)), None)


def deprecated(log: list[str]) -> Callable:
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            log.append(f"deprecated:{func.__name__}")
            return func(*args, **kwargs)
        return wrapper
    return decorate


def memoize(func: Callable) -> Callable:
    cache: dict[tuple, object] = {}           # 闭包持有的可变状态 —— @lru_cache 手练版

    @wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    return wrapper


def compose(*funcs: Callable[[object], object]) -> Callable[[object], object]:
    def composed(x: object) -> object:
        for f in funcs:
            x = f(x)                          # 左到右；funcs 为空时原值返回 = 恒等
        return x
    return composed


def int_values_only(data: dict[str, object]) -> dict[str, int]:
    return {k: v for k, v in data.items() if type(v) is int}   # isinstance 会把 bool 放进来的坑
