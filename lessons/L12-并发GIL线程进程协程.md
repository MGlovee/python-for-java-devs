# L12 · 并发：GIL、线程、进程、协程

> 读 40 分钟 · 练 50 分钟
> 对应原文：`Day61-65/63`（4 篇）+ `番外篇/一个小例子助你彻底理解协程.md`（5 篇、1088 行）
> 判分：`py check.py L12` ｜ 卡片：[cards/l12.md](../cards/l12.md)

Java 人的心智是"线程池 + 锁 + `CompletableFuture`"。Python 的 API 你都认得，
真正要重装的是两个认知：**GIL 让多线程加不了 CPU 的速**，以及**协程是同一线程内的主动让位**。

---

## ① 开课先答 3 题（先答后读，答错才对）

1. 4 核机器上用 4 个 Python 线程跑纯计算（求大素数），CPU 占用率大约是多少？
2. `threading.Lock` 能防住 GIL 吗？GIL 保护的是什么，锁保护的又是什么？
3. `async def f()` 之后直接写 `f()`，函数体执行了吗？

答案在 ⑥。

---

## ② 差异地图（Java → Python）

| 主题 | Java | Python | 一句话提醒 |
|---|---|---|---|
| 执行单元 | Thread / 虚拟线程 | `threading.Thread` / 协程 | 没有 `ExecutorService` 那种一等公民感，靠 `concurrent.futures` |
| 共享内存 | 同进程线程共享堆 | 同进程线程共享对象 | 进程之间**不共享**，要靠 `Queue` / `Pipe` / `Manager` |
| 锁 | `synchronized` / `ReentrantLock` | `threading.Lock` / `RLock` / `Condition` | `with lock:` 就是 try-finally；**没有偏向锁/锁升级这些概念** |
| 原子性 | `volatile` / `AtomicInteger` | 没有对应关键字 | `x += 1` 在 Python 里也**不是**原子操作 |
| 计数闩 | `CountDownLatch(1)` | `threading.Event` | `event.wait(t)` 返回 bool，超时不抛异常 |
| 栅栏 | `CyclicBarrier` | `threading.Barrier(parties)` | 一次性的用 `Event` 更轻；`parties` 必须等于参与线程数 |
| 线程池 | `Executors.newFixedThreadPool` | `ThreadPoolExecutor(max_workers=)` | 返回 `Future`，`result()` 会**重新抛出**子任务异常 |
| 进程池 | 无（另起 JVM） | `ProcessPoolExecutor` / `multiprocessing.Pool` | CPU 密集的唯一解 |
| 阻塞队列 | `BlockingQueue` | `queue.Queue`（线程安全） | 多进程要换成 `multiprocessing.Queue` |
| 异步 | CompletableFuture / Reactor | `asyncio` + `async/await` | 单线程事件循环，**没有回调地狱**但有"别调阻塞函数"铁律 |
| 取消 | `Future.cancel` | `Task.cancel()` 抛 `CancelledError`（继承 BaseException） | `except Exception` 抓不到它，这是故意的 |
| 并行流 | `parallelStream()` | 无 | 自己 `chunk` + 进程池，见练习 `chunk_items` |

### GIL 到底锁什么

CPython 的全局解释器锁保护的是**解释器内部状态**（对象引用计数、内存分配），
所以：**任意时刻只有一个线程在执行 Python 字节码**。

| 事实 | 结论 |
|---|---|
| I/O 等待时线程会**释放** GIL | 多线程对网络/磁盘并发**有效** |
| 纯 Python 计算不释放 GIL | 多线程对 CPU 密集**无效**（还多付切换成本） |
| `numpy` / `pandas` 的 C 内核自己会释放 GIL | 向量化运算能真并行（见 L15） |
| 每个进程有自己的一份解释器和 GIL | 多进程 = 多个 GIL，这才是 CPU 并行的解法 |
| 3.13+ 有实验性 free-threaded 构建、3.12 有 `interpreter` 模块 | 别在课程里赌它，生产上仍按上面的规则选型 |

有了 GIL 也别高兴太早：**GIL 不等于线程安全**。`balance += 1` 是"读-改-写"三步，
GIL 只保证一步之内不被打断，切换发生在步与步之间 → 照样丢失更新。该上锁还得锁。

### 三件套 API 速记

```python
import threading, queue
from concurrent.futures import ThreadPoolExecutor, as_completed, Future

lock = threading.Lock()          # with lock: ... —— 不可重入；重入用 RLock
ready = threading.Event()        # set() / clear() / wait(timeout)->bool
gate = threading.Barrier(3)      # wait() —— 3 个线程都到了一起走
box = queue.Queue()              # put/get/get_nowait、qsize()、join() + task_done()
box.put(item); item = box.get()  # 空队列时 get() 阻塞，get_nowait() 抛 queue.Empty
```

`concurrent.futures` 把线程池和进程池做成同一个接口 —— **换实现只换类名**：

| | `ThreadPoolExecutor` | `ProcessPoolExecutor` |
|---|---|---|
| 加速对象 | 阻塞 I/O | CPU 密集 |
| 参数传递 | 引用共享 | **序列化（pickle）拷贝**，别指望改对象能带回来 |
| 返回值 | 任意对象 | 也必须可 pickle |
| 开销 | 线程切换 | 进程创建 + 序列化，起得慢得多 |
| `map` / `submit` / `as_completed` | 完全一样 | 完全一样 |

### `multiprocessing` 与 Windows 的硬要求

```python
from multiprocessing import Process, Queue   # 这里的 Queue 才是跨进程的

def worker(box):                 # 顶层函数，不能是闭包/局部函数/lambda
    box.put(1)

if __name__ == "__main__":       # Windows/macOS 用 spawn：子进程重新 import 本文件
    box = Queue()
    proc = Process(target=worker, args=(box,))
    proc.start(); proc.join()
    print(box.get())
```

| 要点 | 说明 |
|---|---|
| 为什么必须 `if __name__ == "__main__"` | Windows 默认 `spawn`（Linux 默认 `fork`）。spawn 会**重新 import 主模块**，没有这层保护 → 子进程又起子进程 → 递归爆炸 |
| 冻结库（打包 exe） | 还要在 `freeze_support()` 之后才启动进程，PyInstaller 场景下必写 |
| 目标函数 | 必须是模块顶层可 pickle 的对象，参数返回值都要可 pickle |
| 共享状态 | 子进程**复制**父进程内存，全局计数器各自加各自的（原文那个 Ping/Pong 各 50 的例子就是这坑） |
| 通信 | `multiprocessing.Queue` / `Pipe` / `Value`/`Array` / `Manager()` |

### `asyncio` 的最小正确姿势

```python
import asyncio

async def one(name: str) -> str:
    await asyncio.sleep(0.02)          # 让出控制权；真实代码 await 网络
    return name

async def main() -> list[str]:
    results = await asyncio.gather(*(one(n) for n in "abc"))     # 并发，保序返回
    async with asyncio.TaskGroup() as tg:                        # 3.11+：任一失败自动取消其余
        tasks = [tg.create_task(one(n)) for n in "abc"]
    return [t.result() for t in tasks]

asyncio.run(main())                    # 只在程序入口调用一次，别在协程里嵌套 run
```

| API | 语义 | 注意 |
|---|---|---|
| `async def` | 定义协程函数 | 调用它**只得到协程对象，不执行** |
| `await x` | 让出控制权，等 x 完成 | 只能在协程里用 |
| `asyncio.run(coro)` | 建循环 + 跑到完成 + 关循环 | 阻塞调用，程序入口用一次 |
| `gather(*coros)` | 并发，返回**按传入顺序**的结果列表 | 默认第一个异常会向上冒 |
| `TaskGroup` (3.11+) | 结构化并发，异常/取消处理更干净 | 新项目优先它 |
| `to_thread(func)` | 把阻塞函数丢进线程池 | 老库（`requests`、`pymysql`）就靠它 |
| `asyncio.sleep` | 协程版睡眠 | `time.sleep` 会**卡死整个循环**，禁止 |

### 选型决策表（背下来，面试和评审都用得上）

| 任务长相 | 选 | 典型例子 |
|---|---|---|
| CPU 密集、纯 Python 计算 | 进程池 `ProcessPoolExecutor` | 判断大素数、图像批处理、压缩 |
| 大量 I/O，库支持 async | `asyncio` + `aiohttp`/`httpx` | 上千个 URL 抓取、网关转发 |
| I/O 密集，库是阻塞的 | `ThreadPoolExecutor` | `requests` + `pymysql` 并发跑 |
| CPU 密集但计算在 C 扩展里 | 线程也行 | `numpy` 大矩阵、`pandas` 部分算子 |
| 要共享内存对象、又不能吃 GIL | 先想清楚能不能改成消息传递 | 生产者-消费者 → `Queue` |
| 定时/后台任务 | `asyncio` 或任务队列（Celery/APScheduler） | 别拿裸线程当调度器 |

---

## ③ 完整样例：读 → 跑 → 改

[drills/L12/worked_example.py](../drills/L12/worked_example.py) 直接跑：
`py drills/L12/worked_example.py`。它把"无锁 vs 有锁的丢失更新计数""Event 当开关"
"线程池 `map` 保序""三个协程并发"四件事压缩进一个文件，**结果每次都确定**（不测墙钟、不赌顺序）。

跑完回答：把 `bank_with_lock` 里的 `with lock:` 去掉，两次运行结果会一样吗？这说明了并发 bug 的什么特征？

---

## ④ 补全题

打开 [drills/L12/exercises.py](../drills/L12/exercises.py)，10 个函数：前 6 挖空、后 4 只给需求。
判分器单条测试 10 秒超时，本课不起真进程池（原因见 ⑤-3）。

```powershell
py check.py L12 -v
```

---

## ⑤ 三个 Java 老手必踩的坑

1. **以为 GIL 让程序"天然线程安全"，或以为 `Lock` 能替代 GIL。**
   两个方向都错：有 GIL 照样丢更新（练习 `increment_shared`），有锁也照样只有一个核在跑 Python 字节码。
2. **在协程里调阻塞函数。** `time.sleep` / `requests.get` 放进 `async def` 会把**整个事件循环**卡住，
   看起来"异步没加速"。要么换异步库，要么 `await asyncio.to_thread(blocking_call)`。
   另一个反向坑是 `async def` 忘了 `await` —— 得到的是协程对象，什么都没发生。
3. **在 Windows 上直接 `ProcessPoolExecutor()` 裸调。** 脚本顶层没有 `if __name__ == "__main__":`
   就起进程池，spawn 会无限递归创建子进程（表现为"程序疯狂吃 CPU 且永不输出"）；
   传给进程池的函数若是闭包或 lambda，会直接 `PicklingError`。
   所以**本课练习一律不真起进程池**：讲清 spawn/`freeze_support()` 的机制，把分片逻辑（`chunk_items`）
   写成可单测的纯函数，真上线时再把它交给 `ProcessPoolExecutor`。

---

## ⑥ 现在回看开头 3 题

1. **≈100%**（一个核跑满）。GIL 让 Python 字节码同时只有一个线程在跑，CPU 密集要换进程池。
2. **不能。** GIL 保护解释器内部状态，`Lock` 保护**你的**共享数据；两回事，`x += 1` 仍要自己加锁。
3. **没执行**，只得到一个协程对象。要 `await f()`，并由 `asyncio.run(main())` 驱动。

答错的那题，去 [cards/l12.md](../cards/l12.md) 找对应卡片。

---

## ⑦ 通关标准

- `py check.py L12` 输出 `10/10 通过`（判分器显示 `18/18`）。
- 白板写出：给 1000 个 URL 并发抓取的两种写法（线程池 / asyncio），并说出各自前提。
- 达成后：`py progress.py done L12`。

## ⑧ 还要细节？回原文

| 想要 | 原文 |
|---|---|
| 进程/线程概念、下载例子对比、守护线程、锁与 GIL | [63.Python中的并发编程-1.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day61-65/63.Python%E4%B8%AD%E7%9A%84%E5%B9%B6%E5%8F%91%E7%BC%96%E7%A8%8B-1.md)（382 行） |
| `Process`、多进程 vs 多线程实测、`multiprocessing.Queue` | [63.Python中的并发编程-2.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day61-65/63.Python%E4%B8%AD%E7%9A%84%E5%B9%B6%E5%8F%91%E7%BC%96%E7%A8%8B-2.md)（254 行） |
| 阻塞/同步概念、生成器协程、`async/await`、`aiohttp` | [63.Python中的并发编程-3.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day61-65/63.Python%E4%B8%AD%E7%9A%84%E5%B9%B6%E5%8F%91%E7%BC%96%E7%A8%8B-3.md)（215 行） |
| 并发在爬虫里怎么落地（含 `concurrent.futures`） | [63.并发编程在爬虫中的应用.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day61-65/63.%E5%B9%B6%E5%8F%91%E7%BC%96%E7%A8%8B%E5%9C%A8%E7%88%AC%E8%99%AB%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8.md)（185 行） |
| 协程直觉：为什么 10 个各睡 1 秒的协程只花 1 秒 | [番外篇/一个小例子助你彻底理解协程.md](https://github.com/jackfrued/Python-100-Days/blob/master/%E7%95%AA%E5%A4%96%E7%AF%87/%E4%B8%80%E4%B8%AA%E5%B0%8F%E4%BE%8B%E5%AD%90%E5%8A%A9%E4%BD%A0%E5%BD%BB%E5%BA%95%E7%90%86%E8%A7%A3%E5%8D%8F%E7%A8%8B.md)（52 行） |
