# -*- coding: utf-8 -*-
"""L04 完整样例 —— 直接跑：py drills/L04/worked_example.py

一个 mini 报表管线：把"运算"当值传来传去，看 Python 的函数到底有多像对象。
学习顺序：跑 → 看输出 → 改掉第 ⑤ 段的 lambda 陷阱再跑 → 合上屏幕默写 compose。
"""
from __future__ import annotations

import sys
from functools import partial, reduce
from typing import Callable


# ① 参数家族：位置 / 默认 / *args / 命名关键字，四种参数出现在同一个签名里
def render(title: str, *numbers: int, sep: str = ' | ', stats: bool = False) -> str:
    line = sep.join(f'{n:>4}' for n in numbers)
    if stats:
        line += f'  (count={len(numbers)}, sum={sum(numbers)})'
    return f'{title}: {line}'


# ② 函数是一等对象：放进字典、当参数传、当返回值用
OPS: dict[str, Callable[[int, int], int]] = {
    'add': lambda x, y: x + y,
    'mul': lambda x, y: x * y,
    'max': max,                      # 内置函数也是普通对象，直接当值用
}


def reduce_all(op: str, numbers: list[int], initial: int) -> int:
    """把 reduce 的用法写清楚：OP[op] 取到函数，不加工号就是"取函数"，加了才是"调用"。"""
    return reduce(OPS[op], numbers, initial)


# ③ 闭包：外层函数返回内层函数，n 被内层"记住"
def make_threshold(n: int) -> Callable[[int], str]:
    def check(x: int) -> str:
        return f'{x} {"超过" if x > n else "不超过"} {n}'
    return check


# ④ 偏函数：固定一部分参数，生成更好用的新函数
product_all = partial(reduce_all, 'mul')          # 少传一个参数就得到新函数


def compose(*funcs: Callable[[int], int]) -> Callable[[int], int]:
    def applied(value: int) -> int:
        for func in reversed(funcs):
            value = func(value)
        return value
    return applied


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    print('① 参数家族')
    print(render('第一季度', 12, 7, 45))
    print(render('第二季度', 3, 9, sep=' / ', stats=True))
    # render('坏调用', 1, 2, True)      # 取消注释会 TypeError：stats 只能按名字传

    print('\n② 函数当值用')
    print(f"reduce_all('add', [1,2,3,4], 0) = {reduce_all('add', [1, 2, 3, 4], 0)}")
    print(f"reduce_all('mul', [1,2,3,4], 1) = {reduce_all('mul', [1, 2, 3, 4], 1)}")
    print(f"reduce_all('max', [7, 2, 9, 4], 0) = {reduce_all('max', [7, 2, 9, 4], 0)}")

    print('\n③ 闭包')
    over_100 = make_threshold(100)
    print(over_100(80))
    print(make_threshold(50)(80))

    print('\n④ 偏函数')
    print(f"product_all([2,3,5], 1) = {product_all([2, 3, 5], 1)}")
    to_base16 = partial(int, base=16)
    print(f"to_base16('ff') = {to_base16('ff')}")

    print('\n⑤ 函数复合')
    step = compose(lambda x: x + 1, lambda x: x * 2)     # 先乘 2 再加 1
    print(f'compose(+1, *2)(10) = {step(10)}')

    print('\n⑥ 经典陷阱：列表推导里的 lambda 到底记住了谁')
    late = [lambda x: x * i for i in range(3)]     # i 是自由变量，循环结束后 i == 2
    fixed = [lambda x, i=i: x * i for i in range(3)]   # 默认参数在定义时就绑定
    print('late  :', [f(10) for f in late], '  # 全是 20，因为三个 lambda 共用同一个 i')
    print('fixed :', [f(10) for f in fixed], '  # 0, 10, 20 才是想要的')
