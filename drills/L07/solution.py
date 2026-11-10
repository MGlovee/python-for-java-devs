# -*- coding: utf-8 -*-
"""L07 参考答案。

别整篇抄 —— 它的价值在于卡住 15 分钟后对照思路。
验证题目本身有没有写错：py check.py L07 --solution
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Iterator
from functools import lru_cache, reduce
from itertools import cycle, islice
from operator import mul


def take(iterable: Iterable, n: int) -> list:
    out = []
    it = iter(iterable)                 # ① 拿迭代器（可迭代 ≠ 迭代器）
    for _ in range(n):
        try:
            out.append(next(it))        # ② 手动推进游标
        except StopIteration:           # ③ 序列耗尽 —— for 循环把这步藏在背后
            break
    return out


def squares(numbers: list[int]) -> Iterator[int]:
    for x in numbers:
        yield x * x                     # 每 yield 一次就"冻结"在此处，等下一次 next


def flatten(nested: list[list[int]]) -> Iterator[int]:
    for sub in nested:
        yield from sub                  # 委托给子迭代器，等价于内层 for-yield


def averager() -> Iterator:
    total = count = 0
    avg = 0.0
    while True:
        value = yield avg               # send(v) 送进来的值 = 这个 yield 表达式的结果
        total += value
        count += 1
        avg = total / count


def cycle_first(items: list, n: int) -> list:
    if not items:
        return []
    return list(islice(cycle(items), n))    # islice 从无限序列截取前 n 个


def multiply_all(nums: list[int]) -> int:
    return reduce(mul, nums, 1)             # 第三参数是初值：空列表也得 1


def chunked(data: list, size: int) -> list[list]:
    if size < 1:
        raise ValueError(f"size 必须 >= 1，收到 {size}")
    return [data[i:i + size] for i in range(0, len(data), size)]


def pairwise(iterable: Iterable) -> list[tuple]:
    a, b = iter(iterable), iter(iterable)
    next(b, None)                           # 第二条腿向后错一格
    return list(zip(a, b))


def top_frequent(words: list[str], n: int) -> list[tuple[str, int]]:
    ranked = sorted(Counter(words).items(), key=lambda kv: (-kv[1], kv[0]))
    return ranked[:n]                       # 先定全序再截断，结果唯一确定


@lru_cache(maxsize=None)
def fib_cached(n: int) -> int:
    if n < 2:
        return n
    return fib_cached(n - 1) + fib_cached(n - 2)
