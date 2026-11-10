# -*- coding: utf-8 -*-
"""L12 完整样例 —— 直接跑：py drills/L12/worked_example.py

四段小演示：① 没锁 vs 有锁的丢失更新  ② Event 当开关  ③ 线程池保序 map
④ 协程并发（模拟 I/O）。全程不起进程、不靠 sleep 竞争，结果每次都一样。
"""
from __future__ import annotations

import asyncio
import sys
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROUNDS = 20_000


def bank_without_lock(workers: int) -> int:
    """丢失更新演示：`balance += 1` 不是原子操作，读-改-写之间有窗口。"""
    state = {"balance": 0}

    def deposit() -> None:
        for _ in range(ROUNDS):
            current = state["balance"]          # 读
            state["balance"] = current + 1      # 改 + 写：中间随时可能被打断

    run_threads(deposit, workers)
    return state["balance"]


def bank_with_lock(workers: int) -> int:
    state = {"balance": 0}
    lock = threading.Lock()

    def deposit() -> None:
        for _ in range(ROUNDS):
            with lock:                          # 同一时刻只有一个线程在改
                state["balance"] += 1

    run_threads(deposit, workers)
    return state["balance"]


def run_threads(target: Callable[[], None], workers: int) -> None:
    threads = [threading.Thread(target=target) for _ in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()                           # 忘了 join 就会读到半截结果


def gated_by_event() -> tuple[bool, bool]:
    ready = threading.Event()
    print("  Event 初始状态：", ready.is_set())
    timed_out = not ready.wait(0.01)            # 没人 set → 等一会儿就走
    ready.set()                                 # 相当于 Java 的 CountDownLatch(1)
    return timed_out, ready.wait(0.01)


def thread_pool_ordered(items: list[int]) -> list[int]:
    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(lambda n: n * n, items))   # map 保序


async def one_job(name: str, fake_seconds: float) -> str:
    await asyncio.sleep(fake_seconds)           # 真正的协程在这里 await 网络/磁盘
    return f"{name} 完成"


async def coroutine_demo() -> list[str]:
    jobs = [one_job(n, 0.02) for n in ("取列表", "取详情", "写数据库")]
    return list(await asyncio.gather(*jobs))    # 三个 0.02s 的活儿一起等 ≈ 0.02s


def main() -> None:
    expected = 4 * ROUNDS
    print(f"目标计数（4 线程 × {ROUNDS} 次）= {expected}")
    lost = expected - bank_without_lock(4)
    print(f"  无锁少了 {lost} 次 ← 只要不是 0 就是丢失更新；为 0 也不代表安全，多跑几次")
    print(f"  有锁少了 {expected - bank_with_lock(4)} 次 ← 恒为 0，这才是可依赖的正确性")
    print("Event：", gated_by_event())
    print("线程池（保序）：", thread_pool_ordered([1, 2, 3, 4]))
    print("协程：", asyncio.run(coroutine_demo()))
    print()
    print("选型：CPU 密集 → 进程池（绕开 GIL）；阻塞 I/O 且库不支持异步 → 线程池；"
          "高并发 I/O 且能全链路 async → 协程。")
    print("Windows 起进程池必须在 if __name__ == '__main__': 里，且子进程会重新 import 本文件。")


if __name__ == "__main__":
    main()
