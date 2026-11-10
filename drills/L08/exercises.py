# -*- coding: utf-8 -*-
"""L08 练习工作表 —— 把每个函数里的 `raise NotImplementedError` 删掉，写上你的实现。

判分：  py check.py L08 -v
看答案：py check.py L08 --solution   （建议卡住 15 分钟以上再看）

装饰器练习全部返回可断言的值（不靠 print），"是否执行过"一律用计数器/日志列表观测。
"""
from __future__ import annotations

from collections.abc import Callable

# ---- 下面两个装饰器是"题目附件"，已实现，供第 4 题使用 ----


def mark_a(func: Callable[[], str]) -> Callable[[], str]:
    """调用 func 并在返回值后追加字母 a。"""
    def wrapper() -> str:
        return func() + "a"
    return wrapper


def mark_b(func: Callable[[], str]) -> Callable[[], str]:
    """调用 func 并在返回值后追加字母 b。"""
    def wrapper() -> str:
        return func() + "b"
    return wrapper


# ---------- 第一组：挖空题（有提示，照着填） ----------

def twice(func: Callable) -> Callable:
    """装饰器：把 func 的返回值乘 2；参数原样透传。

    提示：三层里只需要两层 —— def wrapper(*args, **kwargs): return func(...) * 2
    >>> twice(sum)  # 注意：sum 恰好接收可迭代对象，这个例子只为示意
    >>> def add(a, b): return a + b
    >>> twice(add)(2, 3)
    10
    """
    raise NotImplementedError


def shout(func: Callable[[], str]) -> Callable[[], str]:
    """装饰器：把 func 返回的字符串转大写。**必须**用 functools.wraps 保留元信息。

    提示：from functools import wraps；在 wrapper 上写 @wraps(func)。
    做完自查：shout(f).__name__ 应等于 f.__name__，且存在 f.__wrapped__。
    """
    raise NotImplementedError


def repeat(times: int) -> Callable:
    """带参数的装饰器：包装后的函数每次被调用，都把原函数执行 times 次，
    把 times 个返回值收集成列表返回。

    提示：三层结构 repeat -> decorate(func) -> wrapper(*args, **kwargs)。
    >>> @repeat(3)
    ... def tick(): ...
    >>> tick()
    [?, ?, ?]      # 列表里是 3 次调用的结果
    """
    raise NotImplementedError


def stacked_result() -> str:
    """用题目附件的 mark_a / mark_b 装饰一个返回空串的 base 函数并调用一次，返回结果。

    写法：
        @mark_a
        @mark_b
        def base():
            return ""
        return base()

    提示：装饰器**自下而上**应用 —— base 先被 mark_b 包住，再被 mark_a 包住。
    先写下你预测的字符串，再实现、再判分验证直觉。
    """
    raise NotImplementedError


def merge_dicts(a: dict, b: dict) -> dict:
    """返回新字典：a、b 的键都要，键冲突时 b 说了算。不许修改入参。

    提示：Pythonic 一行 —— return {**a, **b}（或 dict(a) 再 update）。
    >>> merge_dicts({"x": 1, "y": 2}, {"y": 3})
    {'x': 1, 'y': 3}
    """
    raise NotImplementedError


def first_index(items: list, pred: Callable[[object], bool]) -> int | None:
    """返回第一个满足 pred 的下标；找不到返回 None。

    提示：next((i for i, x in enumerate(items) if pred(x)), None) ——
    生成器表达式 + next 的默认值，找不到不抛 StopIteration。
    >>> first_index([1, 4, 7], lambda x: x > 5)
    2
    """
    raise NotImplementedError


# ---------- 第二组：只给需求（独立写） ----------

def deprecated(log: list[str]) -> Callable:
    """带参数装饰器：被包装的函数每次被调用时，先向 log 追加
    f"deprecated:{原函数名}"，再原样调用并把返回值透传。
    必须保留原函数的 __name__（用 wraps）。
    """
    raise NotImplementedError


def memoize(func: Callable) -> Callable:
    """手写记忆化装饰器：用闭包里的 dict 缓存结果，键是位置参数元组 args，
    同样的参数第二次调用不得再执行原函数。
    测试会用"带计数器的函数"来验证是否真的只算了一次。
    支持任意个可哈希的位置参数；不需要支持关键字参数。
    """
    raise NotImplementedError


def compose(*funcs: Callable[[object], object]) -> Callable[[object], object]:
    """返回一个新函数：把传入的函数**从左到右**依次作用在同一个值上。
    不带参数调用 compose() 时返回恒等函数（原值进原值出）。

    示例：compose(f, g)(x) 的值等于 g(f(x))。
    """
    raise NotImplementedError


def int_values_only(data: dict[str, object]) -> dict[str, int]:
    """用字典推导式筛出值"恰好是 int"的键值对。

    注意：bool 是 int 的子类，True/False 不算 —— 判据必须写 type(v) is int。
    示例：int_values_only({"a": 1, "b": "x", "c": True}) == {"a": 1}
    """
    raise NotImplementedError
