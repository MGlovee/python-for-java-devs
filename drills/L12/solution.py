# -*- coding: utf-8 -*-
"""L12 参考答案。

别整篇抄 —— 它的价值在于卡住 15 分钟后对照思路。
验证题目本身有没有写错：py check.py L12 --solution
"""
from __future__ import annotations

import asyncio
import queue
import threading
from collections.abc import Callable


def map_in_threads(func: Callable[[int], int], items: list[int], workers: int) -> list[int]:
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max(workers, 1)) as pool:
        return list(pool.map(func, items))      # map 保序；as_completed 不保序


def increment_shared(workers: int, each: int) -> int:
    counter = {"value": 0}
    lock = threading.Lock()

    def work() -> None:
        for _ in range(each):
            with lock:                          # 读-改-写必须在同一把锁里
                counter["value"] += 1

    threads = [threading.Thread(target=work) for _ in range(max(workers, 1))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()                           # 不等 join 就 return 是经典 bug
    return counter["value"]


def sum_from_queue(items: list[int], workers: int) -> int:
    box: queue.Queue[int] = queue.Queue()
    for item in items:
        box.put(item)
    partials: dict[int, int] = {}
    lock = threading.Lock()

    def work(worker_id: int) -> None:
        local = 0
        while True:
            try:
                local += box.get_nowait()        # 队列自身线程安全，不用再上锁
            except queue.Empty:
                break
        with lock:                              # 这里才是需要锁的地方：写共享 dict
            partials[worker_id] = local

    threads = [threading.Thread(target=work, args=(i,)) for i in range(max(workers, 1))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return sum(partials.values())


def event_outcome(event: threading.Event, timeout: float) -> str:
    return "触发" if event.wait(timeout) else "超时"


def run_async_squares(nums: list[int]) -> list[int]:
    async def square(n: int) -> int:
        await asyncio.sleep(0)                  # 让出控制权，证明事件循环真的在转
        return n * n

    async def main() -> list[int]:
        return list(await asyncio.gather(*(square(n) for n in nums)))

    return asyncio.run(main())                  # 只有最外层该用 run，别在协程里嵌套


def async_lengths(names: list[str], delay: float) -> dict[str, int]:
    async def measure(name: str) -> int:
        await asyncio.sleep(delay)              # 模拟 I/O：阻塞时把 CPU 让给别的协程
        return len(name)

    async def main() -> dict[str, int]:
        results = await asyncio.gather(*(measure(n) for n in names))
        return dict(zip(names, results))

    return asyncio.run(main())


def recommend_concurrency(cpu_bound: bool, io_is_async: bool) -> str:
    if cpu_bound:
        return "process"                        # GIL：多线程帮不了 CPU 密集
    return "async" if io_is_async else "thread"


def chunk_items(items: list[int], workers: int) -> list[list[int]]:
    if workers <= 0:
        raise ValueError(f"workers 必须为正整数，收到 {workers}")
    size, remainder = divmod(len(items), workers)
    out: list[list[int]] = []
    start = 0
    for index in range(workers):
        take = size + (1 if index < remainder else 0)   # 靠前的多分 1 个
        out.append(items[start:start + take])
        start += take
    return out


def barrier_two_phases(values: list[int]) -> tuple[list[int], list[int]]:
    if not values:
        return [], []
    barrier = threading.Barrier(len(values))    # parties 必须等于参与线程数
    first: list[int] = [0] * len(values)
    second: list[int] = [0] * len(values)

    def work(index: int, value: int) -> None:
        first[index] = value * 2
        barrier.wait()                          # 卡在这里，直到所有线程都完成阶段一
        second[index] = first[index] ** 2

    threads = [threading.Thread(target=work, args=(i, v)) for i, v in enumerate(values)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return first, second


def divide_in_threads(nums: list[int], divisor: int) -> list[str]:
    from concurrent.futures import ThreadPoolExecutor

    def divide(n: int) -> float:
        return n / divisor                      # 这里抛的异常会在 result() 处重现

    with ThreadPoolExecutor(max_workers=max(min(len(nums), 8), 1)) as pool:
        futures = [pool.submit(divide, n) for n in nums]
        out: list[str] = []
        for future in futures:
            try:
                out.append(str(future.result()))
            except Exception:                   # noqa: BLE001 - 练习要求把错误收成 "error"
                out.append("error")
        return out
