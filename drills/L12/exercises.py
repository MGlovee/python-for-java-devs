# -*- coding: utf-8 -*-
"""L12 练习工作表 —— 把每个函数里的 `raise NotImplementedError` 删掉，写上你的实现。

判分纪律（本课特有）：
- 测试**只看可验证的结果**（计数、总和、返回值），不断言线程顺序、不测墙钟时间收益；
- 所以你的实现里不许出现"靠 sleep 碰运气"的逻辑，线程该等的一律用 `Event` / `Barrier` / `join` 等；
- 每个测试 10 秒超时，别把 `workers` 开得没边，也别起真进程（Windows 要 spawn，见讲义 ⑤-3）。

判分：  py check.py L12 -v
看答案：py check.py L12 --solution
"""
from __future__ import annotations

import threading
from collections.abc import Callable


# ---------- 第一组：挖空题（有提示，照着填） ----------

def map_in_threads(func: Callable[[int], int], items: list[int], workers: int) -> list[int]:
    """在线程池里对每个 item 调用 func，返回**与输入同序**的结果列表。

    提示：`with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:`
          + `list(pool.map(func, items))` —— 用 `as_completed` 就变成"谁先完谁在前"了。
    """
    raise NotImplementedError


def increment_shared(workers: int, each: int) -> int:
    """开 `workers` 个线程，每个线程把同一个共享计数器加 `each` 次，返回最终计数。

    要求：必须用 `threading.Lock` 保护"读-改-写"，最后 `join` 全部线程再返回；
    结果恒等于 `workers * each` —— 少一个锁就一定会丢更新。
    """
    raise NotImplementedError


def sum_from_queue(items: list[int], workers: int) -> int:
    """把 items 放进 `queue.Queue`，`workers` 个线程并发取数求和，返回总和。

    要求：线程从同一个队列 `get`，取不到就退出（`queue.Empty` + `break` 最省事）；
    队列是线程安全的，**不要**再加锁，也不要按下标切分数据。
    """
    raise NotImplementedError


def event_outcome(event: threading.Event, timeout: float) -> str:
    """等这个事件，等到返回 `"触发"`，超时返回 `"超时"`。

    提示：`threading.Event.wait(timeout)` 的返回值就是"有没有等到"的布尔值，别再 `is_set()` 猜。
    """
    raise NotImplementedError


def run_async_squares(nums: list[int]) -> list[int]:
    """用 asyncio 并发计算每个数的平方，返回与输入同序的列表。

    要求：`async def` 里 `await asyncio.sleep(0)` 让出一次控制权（模拟 I/O），
    用 `asyncio.gather(*coros)` 收集，最外层 `asyncio.run(...)` 启动事件循环。
    """
    raise NotImplementedError


def async_lengths(names: list[str], delay: float) -> dict[str, int]:
    """每个名字一个协程：`await asyncio.sleep(delay)` 之后返回它的长度，汇总成 dict。

    要求：所有协程并发跑（`gather`），返回 `{名字: 长度}`；名字列表里有重复时同一个键只留一份即可。
    提示：`asyncio.run(main())`，main 里 `dict(zip(names, await asyncio.gather(*tasks)))`。
    """
    raise NotImplementedError


# ---------- 第二组：只给需求（独立写） ----------

def recommend_concurrency(cpu_bound: bool, io_is_async: bool) -> str:
    """并发选型：返回 `"process"` / `"async"` / `"thread"` 之一。

    规则（照这个决策表，不要加自己的判断）：
    1. `cpu_bound` 为真 → `"process"`（GIL 挡着，多线程加不了速）；
    2. 否则 `io_is_async` 为真 → `"async"`（协程，省掉线程切换与连接池开销）；
    3. 否则 → `"thread"`（第三方阻塞库 / 老代码只能开线程）。
    """
    raise NotImplementedError


def chunk_items(items: list[int], workers: int) -> list[list[int]]:
    """把任务切成 `workers` 份连续分片（多进程分片前要先做这一步，练习里不起进程）。

    要求：返回列表长度**恰好**是 `workers`；数量除不尽时靠前的分片多分 1 个；
    任务少于 workers 时多余的分片是空列表；`workers <= 0` 抛 `ValueError`。
    例：`chunk_items([1, 2, 3, 4, 5], 2) == [[1, 2, 3], [4, 5]]`
    """
    raise NotImplementedError


def barrier_two_phases(values: list[int]) -> tuple[list[int], list[int]]:
    """每个值一个线程，跑两阶段：阶段一算 `v * 2`，**所有线程都完成阶段一**后才进阶段二算平方。

    要求：用 `threading.Barrier(parties=len(values))` 做分阶段同步，
    返回 `(阶段一结果, 阶段二结果)`，两个列表都按输入顺序摆放；
    `values` 为空时直接返回 `([], [])`（`Barrier(0)` 会报错）。
    """
    raise NotImplementedError


def divide_in_threads(nums: list[int], divisor: int) -> list[str]:
    """线程池里并发算 `n / divisor`（真除法），返回与输入同序的字符串列表。

    要求：成功项返回 `str(结果)`；抛异常的项（比如 `divisor == 0` 的 `ZeroDivisionError`）
    返回 `"error"`，不要让整个函数崩掉。
    提示：`executor.submit` 拿 Future，`future.result()` 会把子线程里的异常**在当前线程重新抛出**，
    所以 try/except 要包在取结果的地方。
    """
    raise NotImplementedError
