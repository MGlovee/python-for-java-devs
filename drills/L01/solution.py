# -*- coding: utf-8 -*-
"""L01 参考答案。

别整篇抄 —— 它的价值在于卡住 15 分钟后对照思路。
验证题目本身有没有写错：py check.py L01 --solution
"""
from __future__ import annotations

import math


def divmod_pair(a: int, b: int) -> tuple[float, int, int]:
    return (a / b, a // b, a % b)


def count_truthy(items: list) -> int:
    return sum(1 for x in items if x)


def describe_value(value) -> str:
    if value is None:
        return "None"
    return "真值" if value else "假值"


def fizzbuzz(n: int) -> list[str]:
    out = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            out.append("FizzBuzz")
        elif i % 3 == 0:
            out.append("Fizz")
        elif i % 5 == 0:
            out.append("Buzz")
        else:
            out.append(str(i))
    return out


def grade(score: int) -> str:
    if not 0 <= score <= 100:
        raise ValueError(f"分数必须在 0..100 之间，收到 {score}")
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "E"


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for factor in range(2, math.isqrt(n) + 1):
        if n % factor == 0:
            return False
    return True


def gcd(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b          # 一行完成"滚动"，Python 的元组交换在这里最好用
    return a


def collatz_steps(n: int) -> int:
    steps = 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps += 1
    return steps


def max_and_second(numbers: list[int]) -> tuple[int, int]:
    if len(numbers) < 2:
        raise ValueError("至少需要 2 个数字")
    first = second = numbers[0]
    for x in numbers:
        if x > first:
            first, second = x, first      # 老的冠军降为亚军
        elif x > second:
            second = x
    return first, second


def move_zeroes(nums: list[int]) -> list[int]:
    non_zero = [x for x in nums if x != 0]        # 推导式，L02 的主角
    return non_zero + [0] * (len(nums) - len(non_zero))
