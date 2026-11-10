# -*- coding: utf-8 -*-
"""L07 练习工作表 —— 把每个函数里的 `raise NotImplementedError` 删掉，写上你的实现。

判分：  py check.py L07 -v
看答案：py check.py L07 --solution   （建议卡住 15 分钟以上再看）

本课全部内存运算：列表、生成器、itertools/functools，不碰磁盘不联网。
"""
from __future__ import annotations

from collections.abc import Iterable, Iterator


# ---------- 第一组：挖空题（有提示，照着填） ----------

def take(iterable: Iterable, n: int) -> list:
    """手动执行迭代协议：从 iterable 取前 n 个元素放进列表返回；不够 n 个就取光。

    提示：`it = iter(iterable)`，然后循环 n 次 `next(it)`，
    捕到 StopIteration 就 break —— for 循环背后就是这套动作。
    >>> take([1, 2, 3, 4], 2)
    [1, 2]
    >>> take([1], 5)
    [1]
    """
    raise NotImplementedError


def squares(numbers: list[int]) -> Iterator[int]:
    """生成器函数：依次产出每个数的平方。要求用 yield，不许先建列表再返回。

    提示：for x in numbers: yield x * x
    调用本函数时函数体一行都不执行，next() 时才推进到下一个 yield。
    >>> next(squares([1, 2, 3]))
    1
    """
    raise NotImplementedError


def flatten(nested: list[list[int]]) -> Iterator[int]:
    """把一层嵌套的列表拍平，依次产出元素。

    提示：`yield from 子列表` —— 把内层生成器的产出"委托"出去，
    等价于 for x in sub: yield x，但只写一个表达式。
    >>> list(flatten([[1, 2], [], [3]]))
    [1, 2, 3]
    """
    raise NotImplementedError


def averager() -> Iterator:
    """流式求平均数的协程：每次 yield 当前平均值，调用方用 send(v) 送入新数值。

    要求：初始平均值为 0.0；调用方先 next(gen) 推进一次（priming），之后每次 send 返回新平均值。
    提示：
        total = count = 0
        avg = 0.0
        while True:
            value = yield avg      # send 进来的值就是 yield 表达式的结果
            ...
    >>> g = averager(); next(g); g.send(10); g.send(20)
    15.0
    """
    raise NotImplementedError


def cycle_first(items: list, n: int) -> list:
    """把 items 无限循环，取前 n 个返回。items 为空时返回 []。

    提示：`from itertools import cycle`；cycle 是无限序列，
    别 list() 它 —— 用 islice 或直接手动 next n 次。
    >>> cycle_first([1, 2], 5)
    [1, 2, 1, 2, 1]
    """
    raise NotImplementedError


def multiply_all(nums: list[int]) -> int:
    """用 functools.reduce 求所有数的乘积；空列表返回 1（reduce 的初值）。

    提示：`from functools import reduce` 和 `from operator import mul`，
    reduce 的第三个参数是初始值。
    >>> multiply_all([2, 3, 4])
    24
    """
    raise NotImplementedError


# ---------- 第二组：只给需求（独立写） ----------

def chunked(data: list, size: int) -> list[list]:
    """把 data 切成每块 size 个的连续子列表，最后一块可以不足 size。
    size < 1 时抛 ValueError。不许修改传入的 data。

    示例：chunked([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    """
    raise NotImplementedError


def pairwise(iterable: Iterable) -> list[tuple]:
    """返回相邻元素组成的重叠二元组：(s0,s1), (s1,s2), ...
    元素不足 2 个时返回 []。

    思路任选：itertools.pairwise（3.10+），或 zip(it, islice(it, 1, None))，
    或先 list 再切片。
    示例：pairwise([1, 2, 3]) == [(1, 2), (2, 3)]
    """
    raise NotImplementedError


def top_frequent(words: list[str], n: int) -> list[tuple[str, int]]:
    """统计词频，返回出现次数最多的前 n 个 (词, 次数)。

    排序规则必须唯一确定：次数降序，次数相同按词的字典序升序。
    n 大于不同词的个数时，返回全部词。用 collections.Counter 或 dict 统计都行。
    示例：top_frequent(["b", "a", "b"], 2) == [("b", 2), ("a", 1)]
    """
    raise NotImplementedError


def fib_cached(n: int) -> int:
    """第 n 个斐波那契数（fib(0)=0, fib(1)=1），用"朴素递归 + functools.lru_cache"实现。

    要求：递归函数本体照常调用自身，靠 @lru_cache 装饰器消除重复计算；
    fib_cached(100) 必须秒出（不缓存的话宇宙寿命内算不完）。
    """
    raise NotImplementedError
