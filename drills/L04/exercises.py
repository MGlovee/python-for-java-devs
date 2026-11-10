# -*- coding: utf-8 -*-
"""L04 练习工作表 —— 参数家族 / LEGB / 函数是一等对象。

判分：  py check.py L04 -v
看答案：py check.py L04 --solution   （建议卡住 15 分钟以上再看）
"""
from __future__ import annotations

from typing import Callable


# ---------- 第一组：挖空题（有提示，照着填） ----------

def call_shape(*args, **kwargs) -> tuple[int, int]:
    """返回 (位置参数个数, 关键字参数个数)。

    提示：`*args` 收到的是**元组**，`**kwargs` 收到的是**字典**，两者都能 `len()`。
    一个参数都没传时它们分别是空元组和空字典，不是 None。
    >>> call_shape(1, 2, name='bob')
    (2, 1)
    """
    raise NotImplementedError


def sum_numeric(*values: object, start: int = 0) -> int:
    """把 values 里的数值累加到 start 上，非数值直接跳过。

    要求：**布尔值不算数值** —— `isinstance(True, int)` 在 Python 里是 True，
    所以必须先显式把 bool 排除掉。
    提示：`type(v) in (int, float)` 一行就能同时排掉 bool（type 是精确匹配）。
    >>> sum_numeric(1, 2, True, 'x', 3)
    6
    """
    raise NotImplementedError


def format_join(sep: str, *items: object, trailing: bool = False) -> str:
    """把 items 逐个 `str()` 后用 sep 连接；trailing=True 时末尾再补一个 sep。

    `trailing` 写在 `*items` 之后，是**只能按名字传**的命名关键字参数 ——
    按位置传不会报错，只会被 `*items` 吞进去（这是 Python 和 Java 最大的差别）。
    >>> format_join('-', 'a', 1, 'b')
    'a-1-b'
    >>> format_join(',', 'a', 'b', trailing=True)
    'a,b,'
    """
    raise NotImplementedError


def make_adder(n: int) -> Callable[[int], int]:
    """返回一个函数，它把收到的数加上 n（闭包）。

    提示：函数里 `def add(x): return x + n`，然后 **return add**（返回函数本身，别加括号）。
    >>> make_adder(3)(10)
    13
    """
    raise NotImplementedError


def apply_twice(func: Callable[[int], int], value: int) -> int:
    """把 func 连续作用两次：func(func(value))。

    提示：注意 func 是**函数对象**，调用它才加括号。
    >>> apply_twice(lambda x: x * 2, 3)
    12
    """
    raise NotImplementedError


def make_base_converters() -> tuple[Callable[[str], int], Callable[[str], int]]:
    """返回 (二进制解析函数, 十六进制解析函数)，用 functools.partial 固定 int 的 base。

    提示：`import functools` → `functools.partial(int, base=2)`。
    >>> two, sixteen = make_base_converters()
    >>> two('1011'), sixteen('ff')
    (11, 255)
    """
    raise NotImplementedError


# ---------- 第二组：只给需求（独立写） ----------

def compose(*funcs: Callable[[int], int]) -> Callable[[int], int]:
    """从右往左复合函数，返回一个新函数。

    要求：`compose(f, g)(x)` 等于 `f(g(x))`；一个函数都不传时返回恒等函数。
    例：h = compose(lambda x: x + 1, lambda x: x * 2)；h(3) == 7（先乘 2 再加 1）。
    """
    raise NotImplementedError


def rank_students(students: list[dict[str, object]]) -> list[str]:
    """返回排名后的姓名列表：分数高的在前，同分按姓名字典序升序。

    要求：不许改动传入的 students（返回新列表）；只准用一次 `sorted`，靠 key 解决二级排序。
    例：[{'name':'Bob','score':90}, {'name':'Amy','score':90}, {'name':'Cid','score':95}]
        -> ['Cid', 'Amy', 'Bob']
    """
    raise NotImplementedError


def make_accumulator() -> Callable[[int], int]:
    """返回一个函数：每次调用传入一个增量，返回"到目前为止的累计和"。

    要求：每调用 `make_accumulator()` 得到一个**独立**的累计器，互不串号。
    提示：外层一个变量，内层用 `nonlocal` 改它。不许用默认参数当累加器（那是个陷阱）。
    例：acc = make_accumulator(); acc(1) -> 1; acc(10) -> 11; acc2 = make_accumulator(); acc2(5) -> 5
    """
    raise NotImplementedError


def dispatch(op: str) -> Callable[[int, int], int]:
    """返回二元运算函数：'+'、'-'、'*'、'//'、'%' 分别对应加、减、乘、整除、取余。

    要求：op 不认识时抛 ValueError；不许写 if 链，用**字典 + lambda**（函数是值，能放进字典）。
    例：dispatch('//')(7, 2) == 3
    """
    raise NotImplementedError
