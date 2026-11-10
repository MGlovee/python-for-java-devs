# -*- coding: utf-8 -*-
"""L01 练习工作表 —— 把每个函数里的 `raise NotImplementedError` 删掉，写上你的实现。

判分：  py check.py L01 -v
看答案：py check.py L01 --solution   （建议卡住 15 分钟以上再看）
"""
from __future__ import annotations


# ---------- 第一组：挖空题（有提示，照着填） ----------

def divmod_pair(a: int, b: int) -> tuple[float, int, int]:
    """返回 (a 真除 b, a 整除 b, a 除 b 的余数)。

    提示：/  //  %
    >>> divmod_pair(7, 2)
    (3.5, 3, 1)
    """
    raise NotImplementedError


def count_truthy(items: list) -> int:
    """统计列表里"真值"元素的个数。

    提示：Python 里 0、""、[]、{}、set()、None、False 都是假值，其余为真值。
    >>> count_truthy([0, 1, "", "a", [], [1], None, False, True])
    3
    """
    raise NotImplementedError


def describe_value(value) -> str:
    """三态判空：是 None 返回 "None"；不是 None 但是假值返回 "假值"；否则返回 "真值"。

    提示：先 `is None`，再直接 `if value:`。顺序反了就分不出 None 和 0。
    >>> describe_value(None), describe_value([]), describe_value([0])
    ('None', '假值', '真值')
    """
    raise NotImplementedError


def fizzbuzz(n: int) -> list[str]:
    """返回 1..n 的 FizzBuzz 字符串列表：3 的倍数 "Fizz"，5 的倍数 "Buzz"，
    既是 3 又是 5 的倍数 "FizzBuzz"，其余是数字本身的字符串。

    提示：先判 15 的倍数；用 range(1, n + 1)，注意 range 左闭右开。
    >>> fizzbuzz(5)
    ['1', '2', 'Fizz', '4', 'Buzz']
    """
    raise NotImplementedError


def grade(score: int) -> str:
    """百分制转等级：90-100 -> "A"，80-89 -> "B"，70-79 -> "C"，60-69 -> "D"，0-59 -> "E"。

    score 不在 0..100 内时抛 ValueError（消息内容随便写）。
    提示：if / elif / else，从高分往低分判最省事。
    """
    raise NotImplementedError


# ---------- 第二组：只给需求（独立写） ----------

def is_prime(n: int) -> bool:
    """判断 n 是否为素数。小于 2 一律 False。

    要求：用一层循环试除到 sqrt(n) 即可。可以试试 Python 特有的 for/else：
    循环没被 break 打断时，else 分支会执行 —— 那正是"是素数"。
    """
    raise NotImplementedError


def gcd(a: int, b: int) -> int:
    """辗转相除求最大公约数，返回非负结果。gcd(0, 5) == 5。"""
    raise NotImplementedError


def collatz_steps(n: int) -> int:
    """Collatz 猜想步数：n 为偶数则 n/=2，为奇数则 n=3n+1，回到 1 需要多少步。
    n 已经等于 1 时步数为 0。"""
    raise NotImplementedError


def max_and_second(numbers: list[int]) -> tuple[int, int]:
    """返回 (最大值, 次大值)，元素不足 2 个时抛 ValueError。

    允许最大值和次大值相等：max_and_second([5, 5, 1]) == (5, 5)。
    要求：一趟循环 O(n) 做完，不许 sort，也不许用 max()。
    """
    raise NotImplementedError


def move_zeroes(nums: list[int]) -> list[int]:
    """返回一个新列表：非零元素保持原有先后顺序，所有 0 被挪到末尾。
    不得修改传入的 nums。

    示例：move_zeroes([0, 1, 0, 3, 12]) == [1, 3, 12, 0, 0]
    """
    raise NotImplementedError
