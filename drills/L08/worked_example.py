# -*- coding: utf-8 -*-
"""L08 完整样例 —— 直接跑：py drills/L08/worked_example.py

学习顺序：跑 → 看输出 → 改数字再跑 → 合上屏幕默写一遍。
"计时"装饰器这里用**调用计数器**代替 time，输出完全确定；
类型注解段只演示"运行时不强制"这一件事。
"""
from __future__ import annotations

from functools import singledispatch, wraps
from typing import Protocol, TypeVar


# ---------- 1) 装饰器三步走的终点：高阶函数 + @ 语法糖 ----------

CALL_COUNT: dict[str, int] = {}


def counted(func):
    """统计调用次数 —— 结构与原文 17 课的 record_time 一模一样，只是把计时换成计数。"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        CALL_COUNT[func.__name__] = CALL_COUNT.get(func.__name__, 0) + 1
        return func(*args, **kwargs)

    return wrapper


@counted
def fetch_user(user_id: int) -> str:
    """模拟取用户。"""
    return f"user-{user_id}"


# ---------- 2) 带参数的装饰器（三层）+ 装饰器栈顺序 ----------

def repeat(times: int):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return [func(*args, **kwargs) for _ in range(times)]
        return wrapper
    return decorate


def tag(open_: str, close_: str):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return f"{open_}{func(*args, **kwargs)}{close_}"
        return wrapper
    return decorate


@tag("<i>", "</i>")
@tag("<b>", "</b>")            # 自下而上：先被 <b> 包，再被 <i> 包 → i 在外层
def hello():
    return "hello"


# ---------- 3) 类装饰器：给类打补丁 ≈ 运行时版 Lombok ----------

def add_repr(cls):
    """给任意类补一个 __repr__ —— 参数是被装饰的类本身。"""

    def __repr__(self):
        fields = ", ".join(f"{k}={v!r}" for k, v in vars(self).items())
        return f"{type(self).__name__}({fields})"

    cls.__repr__ = __repr__
    return cls


@add_repr
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y


# ---------- 4) 类型注解：只是给工具看的"注释"，运行时零强制 ----------

def total(values: list[int]) -> int:
    return sum(values)


T = TypeVar("T")


class Sized(Protocol):
    """Protocol 演示：结构化子类型 —— 不写 implements，长得像就行。"""

    def __len__(self) -> int: ...


def describe_len(obj: Sized) -> str:
    return f"len={len(obj)}"


def first(items: list[T]) -> T:
    return items[0]


# ---------- 5) singledispatch：按第一个参数的运行时类型分派 ----------

@singledispatch
def render(x) -> str:
    return f"str({x})"


@render.register
def _(x: int) -> str:
    return f"#{x:#x}"


@render.register
def _(x: list) -> str:
    return "[" + ", ".join(render(i) for i in x) + "]"


if __name__ == "__main__":
    print("fetch_user(1), fetch_user(2) →", fetch_user(1), fetch_user(2))
    print("计数器 CALL_COUNT             :", CALL_COUNT, "—— 装饰过的函数已被 wrapper 替换")
    print("fetch_user.__name__           :", fetch_user.__name__, "(@wraps 保住的名字)")
    print("fetch_user.__wrapped__(9)     :", fetch_user.__wrapped__(9), "(绕过装饰的逃生口)")

    print("repeat(3) 结果                :", repeat(3)(lambda: "ping")())
    print("嵌套 @tag 输出顺序            :", hello(), "—— 后装饰的在外层")

    print("类装饰器 add_repr             :", Point(1, 2))

    print("total.__annotations__         :", total.__annotations__, "—— 注解只是元数据")
    try:
        print("total([1, '2']) 运行时炸不炸   :", total([1, "2"]))
    except TypeError as e:
        print("total([1, '2']) 照样运行期炸  :", type(e).__name__, "-", e,
              "—— 注解不拦，mypy 才会提前报")

    print("Protocol 结构化子类型          :", describe_len([1, 2, 3]),
          describe_len("abcd"), "—— 三者都没声明实现过 Sized")
    print("TypeVar 同一次调用 T 一致      :", first([True, 2]), first(["a", "b"]))

    print("singledispatch 分派            :", render(255), render([1, 2]), render(2.5))

    # Pythonic 一行流巡礼（对照番外篇《Python编程惯例》）
    names, scores = ["关羽", "张飞"], [95, 88]
    print("dict(zip(...))                :", dict(zip(names, scores)))
    print("enumerate 代替下标            :", list(enumerate(names, start=1)))
    print("'L' in name 代替 find != -1   :", "羽" in "关羽")
    print("max(key=...) 取最值元素        :", max(zip(names, scores), key=lambda p: p[1]))

    # 经典坑回顾：嵌套列表 aliasing —— [[0]*3]*5 是 5 个引用指向同一个内层列表
    wrong = [[0] * 3] * 5
    wrong[0][0] = 9
    print("[[0]*3]*5 的连锁反应           :", wrong, "← 全变了！")
    right = [[0] * 3 for _ in range(5)]
    right[0][0] = 9
    print("推导式版才是独立行             :", right)
