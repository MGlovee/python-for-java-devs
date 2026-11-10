# -*- coding: utf-8 -*-
"""L01 完整样例 —— 直接跑：py drills/L01/worked_example.py

这是讲义 ③ 的那段代码。学习顺序：跑 → 看输出 → 改数字再跑 → 合上屏幕自己默写一遍。
默写不出来就再跑一遍，别急着往下翻。
"""
from __future__ import annotations


def classify(numbers: list[int]) -> dict[str, int]:
    """统计正数、负数、零的个数 —— 一次讲完缩进 / 真值 / 字典 / 循环。"""
    result = {"positive": 0, "negative": 0, "zero": 0}
    for n in numbers:
        if n > 0:
            result["positive"] += 1
        elif n < 0:
            result["negative"] += 1
        else:
            result["zero"] += 1
    return result


def fib_steps(n: int) -> list[int]:
    """不超过 n 的斐波那契数列 —— while 循环 + 元组交换。"""
    a, b = 0, 1
    out = []
    while a < n:
        out.append(a)
        a, b = b, a + b
    return out


def first_factor(number: int) -> None:
    """for/else 的唯一正确用法：找不到因子就是素数。"""
    if number < 2:
        print(f"{number} 小于 2，不算素数")
        return
    for n in range(2, number):
        if number % n == 0:
            print(f"{number} 不是素数，最小因子 {n}")
            break
    else:
        print(f"{number} 是素数")


if __name__ == "__main__":
    print(classify([3, -1, 0, 7, -8, 0]))
    print(fib_steps(50))
    print(f"不超过 1000 的斐波那契数有 {len(fib_steps(1000))} 个")
    for value in (7, 9, 2, 1):
        first_factor(value)
