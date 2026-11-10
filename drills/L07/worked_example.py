# -*- coding: utf-8 -*-
"""L07 完整样例 —— 直接跑：py drills/L07/worked_example.py

对照讲义 ②：同一个"斐波那契序列"用三种身份写三遍（迭代器类 → 生成器函数 → 协程），
再用 itertools/functools 各露一手。全程内存运算，不碰磁盘。
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache, reduce
from itertools import accumulate, chain, compress, cycle, groupby, islice, product
from operator import mul


# ---------- 1) 迭代器协议：__iter__ / __next__ 手写一遍 ----------

class Fib:
    """迭代器版斐波那契 —— 相当于写了一个 Iterator<Integer>，但不用接口关键字。"""

    def __init__(self, num: int):
        self.num = num
        self.a, self.b = 0, 1
        self.idx = 0

    def __iter__(self):
        return self                    # 迭代器对自己调 iter() 返回自身

    def __next__(self):
        if self.idx < self.num:
            self.a, self.b = self.b, self.a + self.b
            self.idx += 1
            return self.a
        raise StopIteration()          # 序列耗尽的唯一信号


# ---------- 2) 生成器：语法简化版的迭代器 ----------

def fib_gen(num: int):
    a, b = 0, 1
    for _ in range(num):
        a, b = b, a + b
        yield a


# ---------- 3) 协程：生成器 + send，双向管道 ----------

def calc_avg():
    """流式计算平均值（原文 31 课的例子）。next 是开机，send 是喂数据。"""
    total, counter = 0, 0
    avg_value = None
    while True:
        value = yield avg_value        # send 进来的值落在这里
        total, counter = total + value, counter + 1
        avg_value = total / counter


def primes_stream(limit: int):
    """生成器表达式版筛法：无限数流 itertools.count 只被消费到够用为止。"""
    for n in range(2, limit + 1):
        if all(n % d for d in range(2, int(n ** 0.5) + 1)):
            yield n


# ---------- 4) itertools 工具箱 ----------

def demo_itertools():
    print("product(AB, 12)      :", list(product("AB", "12")))
    print("permutations('ABC',2):", list(__import__('itertools').permutations("ABC", 2)))
    print("combinations('ABCD',2):", list(__import__('itertools').combinations("ABCD", 2)))
    print("islice(cycle, 7)     :", list(islice(cycle([1, 2, 3]), 7)), "无限序列安全截断")
    print("chain 拼接           :", list(chain([1, 2], "ab", (3,))))
    print("accumulate 累加      :", list(accumulate([1, 3, 5, 7])))
    print("compress 掩码筛选    :", list(compress("abcdef", [1, 0, 1, 1, 0])))
    words = sorted(["pear", "fig", "apple", "pear", "fig", "pear"])
    grouped = {k: len(list(g)) for k, g in groupby(words)}
    print("groupby 计数         :", grouped, "(先排序才能把相同元素聚到一组)")


# ---------- 5) functools 三件套 ----------

def demo_functools():
    print("reduce(mul, 1..6)    :", reduce(mul, range(1, 7), 1), "== 6 的阶乘")

    @lru_cache(maxsize=None)
    def fib(n: int) -> int:
        return n if n < 2 else fib(n - 1) + fib(n - 2)

    print("lru_cache fib(100)   :", fib(100))
    print("缓存命中率信息       :", fib.cache_info())

    from functools import singledispatch

    @singledispatch
    def describe(x) -> str:                # 兜底分支 ≈ Java 的 Object 重载
        return f"未知类型 {type(x).__name__}: {x!r}"

    @describe.register
    def _(x: int) -> str:
        return f"整数 {x}"

    @describe.register
    def _(x: list) -> str:
        return f"长度 {len(x)} 的列表"

    print("singledispatch       :", describe(42), "/", describe([1, 2]), "/", describe(2.5))


if __name__ == "__main__":
    f = Fib(6)
    print("迭代器类 Fib(6)      :", list(f))
    print("再 list 同一个 f     :", list(f), "—— 迭代器是一次性的，游标不会自动回卷")
    print("对列表调两次 iter    :", [1, 2] == [1, 2],
          iter([1, 2]) is not iter([1, 2]), "—— 可迭代对象每次给新游标")

    g = fib_gen(6)
    print("生成器 fib_gen(6)    :", list(g))
    print("list 推导式对比      :", [x * x for x in range(5)], "vs 生成器表达式",
          tuple(x * x for x in range(5)), "—— 前者立刻算完占内存，后者按产")

    gen = calc_avg()
    next(gen)                              # priming：先推进到第一个 yield
    print("协程 send 10/20/30   :", gen.send(10), gen.send(20), gen.send(30))

    print("素数流(≤30)          :", list(primes_stream(30)))
    print("count 无限流取 5 个  :", list(islice((n for n in cycle(range(1, 100)) if True), 5)), "(示意)")

    demo_itertools()
    demo_functools()

    words = ["apple", "pear", "apple", "fig", "pear", "apple"]
    print("Counter.most_common  :", Counter(words).most_common(2), "—— 并列顺序别依赖，先排序再用")
