# Java → Python 对照速查表

> **这是一张查的表，不是读的教程。** 忘了就 Ctrl-F 搜关键词，两边代码对着抄。环境：Windows + Python 3.14，命令一律 `py`（`py -3.14` 指定版本）。
> 基础语法差异（缩进 / 动态类型 / `/` `//` `%` / 真值 / `None` / `match-case` / `range` `enumerate` `zip` / `for-else`）见 [L01](../lessons/L01-语法差异地图.md)，不重复。

| 我要…… | 去 |
|---|---|
| 写类 / 接口 / 抽象类 / record / 干掉 Lombok | [1. 类型系统与面向对象](#1-类型系统与面向对象) |
| 把泛型签名翻成类型注解 | [2. 泛型与类型注解](#2-泛型与类型注解) |
| 找 `HashMap` / `PriorityQueue` / Stream 的对应物 | [3. 集合与流](#3-集合与流) |
| 处理异常、写 try-with-resources | [4. 异常](#4-异常) |
| 决定用线程 / 进程 / 协程 | [5. 并发模型](#5-并发模型) |
| 装依赖、建虚拟环境、配 pyproject | [6. 构建与依赖](#6-构建与依赖) |
| 写测试、跑静态检查、写文档字符串 | [7. 测试与质量](#7-测试与质量) |
| 拼字符串 / 正则 / 中文乱码 | [8. 字符串与文本](#8-字符串与文本) |
| 找 `java.time`、Jackson、OkHttp 的对应模块 | [9. 常用标准库](#9-常用标准库) |
| 检查自己写的有没有 Java 味 | [10. 12 个反模式](#10-java-老手写-python-的-12-个反模式) |

## 1. 类型系统与面向对象

Java 静态强类型（类型在变量上）；Python **动态强类型**（类型在对象上，变量只是标签）。两边都不自动转 `int`→`str`：`1 + "1"` 都报错。`int` 任意精度，无溢出，不需要 `BigInteger`。

### interface：名义子类型 vs 结构化子类型

```java
public interface PaymentGateway {
    Result charge(Order order);
    default boolean supports(Channel c) { return true; }
}
```

```python
# A：abc.ABC —— 名义子类型，必须显式继承；漏实现抽象方法 -> 实例化时 TypeError
from abc import ABC, abstractmethod

class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, order: Order) -> Result: ...     # 方法体用 ... 占位
    def supports(self, channel: Channel) -> bool: ...  # 相当于 default 方法
```

```python
# B：typing.Protocol —— 结构化子类型，不继承也算实现（鸭子类型 + 静态检查）
from typing import Protocol, runtime_checkable

@runtime_checkable
class Priced(Protocol):
    @property
    def price(self) -> float: ...
    def discount(self, rate: float) -> float: ...

def total(items: list[Priced]) -> float:   # 任何"长得像"的对象都能传，包括第三方库的类
    return sum(i.price - i.discount(0.1) for i in items)
```

要共享默认实现、要用 `isinstance` 挡人 → `ABC`；只声明契约、允许白嫖 → `Protocol`（Java 做不到，这是纯增量）。`@runtime_checkable` 的 `isinstance` 只查方法名不查签名。

### 类相关映射

| Java | Python | 备注 |
|---|---|---|
| `abstract class` + 字段 | `ABC` + `@abstractmethod`，共享状态写 `__init__` | 抽象属性：`@property` + `@abstractmethod` |
| 方法重载（同名不同参） | **不存在**，后写的 `def` 覆盖前一个 | 90% 用默认参数 + 关键字参数；`@typing.overload` 只给检查器看，运行时只有一个函数；要运行时分派用 `@functools.singledispatch`（按第一个参数类型） |
| `@Override` / `final` / `private` | `@typing.override`（3.12+）/ `@typing.final` / `_单下划线`（约定）、`__双下划线`（改名防冲突） | 都不强制；真不可变靠 `@dataclass(frozen=True)`，常量靠全大写约定；Python 没有真 private，别硬拦 |
| 静态内部类 / 内部类 | **同模块的顶层类**，模块即命名空间 | `Order.Item` → `Item`，靠文件名分层 |
| `static` 方法 / 静态工厂 / 构造重载 `new Order(a)` / `(a,b)` | `@staticmethod` / `@classmethod def now(cls) -> Self` / 默认参数 + `@classmethod from_json(...)` | 前者不拿 self，后者能返回子类；工具类常直接写成模块级函数 |
| Lombok `@Data` / `@Value` / `@Builder` / `@AllArgsConstructor` / `@Slf4j` | `@dataclass` / `@dataclass(frozen=True)` / 关键字参数+默认值 / 自动生成 / `logger = logging.getLogger(__name__)` | 字段默认值是可变容器时写 `field(default_factory=list)` |

### getter/setter → property；Object 方法对照

先用公开属性，需要校验时再换成 property，调用方一行不改 —— 这就是 Java 那套 getter/setter 样板在 Python 里不存在的原因。

```python
class Temperature:
    def __init__(self, celsius: float): self.celsius = celsius   # 走下面的 setter
    @property
    def fahrenheit(self) -> float:                                # 只读派生属性，像字段一样访问
        return self.celsius * 9 / 5 + 32
    @celsius.setter
    def celsius(self, value: float) -> None:
        if value < -273.15: raise ValueError("低于绝对零度")
        self._celsius = value
```

| Java | Python | 备注 |
|---|---|---|
| `equals(Object)` / 引用相等 `a == b` / `instanceof` | `__eq__`（`==` 调它，`!=` 自动取反）/ `a is b` / `isinstance(x, A \| B)` | 判 `None` 只用 `is None`；`type(x) == A` 是反模式（不认子类） |
| `hashCode()` | `__hash__` | **定义了 `__eq__` 不写 `__hash__`，对象自动不可哈希**，进不了 `set`、当不了 `dict` 键 |
| `toString()` | `__str__`（print）+ `__repr__`（调试、容器内显示） | 只写一个就写 `__repr__`；`dataclass` 自动生成 |
| `Comparable.compareTo` | `__lt__` + `@functools.total_ordering` | 排序只要 `<`；`(self.x, self.y) < (o.x, o.y)` 顶多个 Comparator |
| `record` | `@dataclass(frozen=True, slots=True)` / `NamedTuple` | `frozen=True` 才生成 `__hash__` |

```java
public record Point(int x, int y) implements Comparable<Point> { }
```

```python
@dataclass(frozen=True, slots=True)     # = record：不可变 + 自动 eq/hash/repr
class Point:
    x: int
    y: int
    def __lt__(self, other: "Point") -> bool: return (self.x, self.y) < (other.x, other.y)
```

## 2. 泛型与类型注解

**类型注解 3.5+ 才有，运行时完全不强制**：写错、传错都不报错，它只服务 mypy/pyright/IDE，运行时唯一痕迹是 `__annotations__`。mypy 一句话：`py -m mypy --strict src/` —— 不执行你代码的静态类型检查器，相当于把 javac 的类型检查单独拎出来跑。

| Java | Python 3.14 | 备注 |
|---|---|---|
| `List<String>` / `Map<K,V>` / `Set<T>` | `names: list[str]` / `dict[K, V]` / `set[T]`、`frozenset[T]` | 小写内建泛型（3.9+），别写 `typing.List`；只读参数用 `Mapping[K, V]` |
| `T[]` | `list[T]`；定长 `tuple[float, float]`，变长 `tuple[T, ...]` | |
| `Optional<String>` | `str \| None` | 不是容器，只是"可能没值" |
| `Function<A,B>` / `Supplier<T>` / `Class<T>` / `Comparator<? super T>` | `Callable[[A], B]` / `Callable[[], T]` / `type[T]` / `Callable[[T], Any]`（`sorted` 的 `key=`） | Python 无 comparator，只有 key |
| `? extends Number`（协变读） | `Sequence[int]` / `Iterable[int]` | `list` 是**不变的**；只有只读接口协变 |
| `<T> T first(List<T> xs)` / `interface Foo<T>` | `def first[T](xs: list[T]) -> T:` / `class Box[T]: ...`（PEP 695，3.12+） | 旧写法 `TypeVar` + `Generic[T]`；上界 `[T: Number]`；Protocol 同样支持泛型 |
| 裸类型 / 反射 | `Any`（**关掉检查**，尽量少用） vs `object`（强制你检查） | |
| 强转 `(Order) x` / `@SuppressWarnings` | `cast(Order, x)`（运行时什么都不做）/ `# type: ignore[code]` | 真校验用 `isinstance` + `assert` |
| 只为类型存在的 import | `if TYPE_CHECKING:` | 防循环导入 |

## 3. 集合与流

### 容器对照

| Java | Python 等价的类 | 复杂度 / 提醒 |
|---|---|---|
| `ArrayList` | `list`（动态数组） | `append` 均摊 O(1)；`insert(0,x)` O(n)；`x in xs` O(n) |
| `LinkedList` | `collections.deque`（块链表） | 两端 O(1)，**下标访问 O(n)**，别当列表用 |
| `Stack` / `Queue`(FIFO) | `list` 的 `append`+`pop` / `deque` 的 `append`+`popleft`；跨线程 `queue.Queue` | `list.pop(0)` 是 O(n) |
| `HashMap` / `LinkedHashMap` | `dict` | O(1)；3.7+ **就是插入序**；要访问序 LRU 才用 `OrderedDict`（有 `move_to_end`） |
| `TreeMap` / `TreeSet` / `HashSet` | 有序无内置：`sorted(d)` 取有序键 / `bisect.insort` 维护有序 `list` / 第三方 `sortedcontainers`；`set` | 别自己造红黑树；`set` 元素必须可哈希（见 §1 的 `__hash__`） |
| `PriorityQueue` | `heapq`（**是模块不是类**，直接操作 `list`） | 最小堆；大顶堆取负数；无 comparator |
| Guava `Multimap` / `Collections.frequency` | `collections.defaultdict(list)` / `collections.Counter` | `d[k].append(v)` 免初始化；`Counter(ws).most_common(5)` |
| `Collections.unmodifiableList` / `Arrays.asList` / `EnumMap` | `tuple` / `frozenset`（真不可变）/ `list(...)` / 以 `Enum` 成员为键的 `dict` | |
| `ConcurrentHashMap` | `dict` + `threading.Lock` | GIL 只保证单条字节码原子，`if k not in d:` 照样竞态 |

### Stream API 逐行对应

| Java | Python |
|---|---|
| `.filter(x -> x > 0).toList()` | `[x for x in xs if x > 0]` |
| `.map(String::toUpperCase).toList()` | `[x.upper() for x in xs]`；不建中间列表用生成器 `(f(x) for x in xs)` |
| `.flatMap(List::stream)` / `.distinct()` | `[y for x in xs for y in x]` / `list(dict.fromkeys(xs))`（保序） |
| `.sorted(Comparator.comparing(User::getAge))` | `sorted(users, key=lambda u: u.age)`（原列表不动；原地是 `xs.sort(...)`） |
| `.comparing(A::getX).thenComparing(B::getY)` | `key=lambda x: (x.a, x.b)`；一升一降 `(x.a, -x.b)` 或**分两趟排** |
| `.collect(toList())` / `toSet()` / `.limit(5)` / `.skip(5)` | `list(...)` / `set(...)` / `xs[:5]` / `xs[5:]` |
| `.collect(joining(", "))` | `", ".join(str(x) for x in xs)` |
| `.collect(groupingBy(User::getCity))` | `{k: list(g) for k, g in groupby(sorted(xs, key=f), key=f)}` —— **必须先按同一 key 排序**；日常更常见 `defaultdict(list)` 循环 |
| `.collect(partitioningBy(x -> x > 0))` | 两个推导式，或按条件塞进 `defaultdict` |
| `.reduce(BigDecimal::add).orElse(ZERO)` | `sum(xs)`（空集合也不报错）；乘积 `math.prod(xs)` |
| `.mapToDouble().max(comparator)` / `.average()` | `max(xs, key=...)` / `min(...)`；均值 `statistics.fmean(xs)` |
| `.anyMatch(p)` / `.allMatch(p)` / `.noneMatch(p)` / `.count()` | `any(p(x) for x in xs)` / `all(...)` / `not any(...)` / `sum(1 for x in xs if cond)`（无过滤用 `len(xs)`，O(1)） |
| `.findFirst().orElse(null)` / `IntStream.range(0,10)` | `next((x for x in xs if cond), None)` / `range(10)` |

要点：① `sorted`/`list.sort` **永远稳定**（TimSort），相等元素保持原序，所以多键排序可以放心分趟做；② 只收 `key=` 和 `reverse=`，**不收 comparator** —— 复杂比较给元素加 `__lt__` 或压进 key 元组；③ 推导式急切、Stream 惰性，大文件流要写生成器（L07）；④ `.peek(副作用)` 没有干净对应物，老实写 for 循环。

## 4. 异常

**没有 checked exception**：不声明、不强制捕获，运行时才炸；代价是 `throws` 的信息只能进文档字符串。

```java
try (BufferedReader in = Files.newBufferedReader(path)) {
    return in.readLine();
} catch (IOException e) { throw new IllegalStateException("读取配置失败", e); }
finally { audit.log(); }
```

```python
try:
    with open(path, encoding="utf-8") as f:        # 相当于 try-with-resources，自动关闭
        line = f.readline()
except OSError as e:                               # IOException 的父类级等价物
    raise RuntimeError("读取配置失败") from e        # from = 保留 cause 链
else:                                              # Java 没有：try 体没抛异常才执行
    logger.info("读到了首行")
finally:
    audit.log()                                    # 和 Java 一样，一定执行
```

| Java | Python |
|---|---|
| 多个 `catch` 块 / `catch (IOException \| RetryException e)` | `except A as e:` / `except B as e:`（**从具体到宽泛**，顺序错了后面永远进不去）/ `except (OSError, RetryError) as e:` |
| `throw e;` 重抛 / `new RuntimeException(e)` | `raise`（裸写，保留原 traceback）/ `raise RuntimeError(...) from e` |
| `catch (Exception)` / `catch (Throwable)` | `except Exception:` / `except BaseException:` —— `KeyboardInterrupt`、`SystemExit` 继承 `BaseException`，前者抓不到（好事，别去抓后者） |
| 空的 `catch` / `finally` 里 `return` | `with contextlib.suppress(FileNotFoundError): ...` / 同样吞异常，别写 |
| `AutoCloseable.close()` | `__enter__`/`__exit__` 或 `@contextlib.contextmanager`（L06） |
| `throws IOException` + 自定义异常 | docstring 的 `Raises:` 段（唯一契约，工具不校验）；异常类继承 `Exception`，模块内定义一个 `AppError` 基类，业务异常继承它 |

```python
try:                                    # EAFP（Python 习惯）：先做，错了补 —— 也避开 check-then-act 竞态
    value = d[key]
except KeyError:
    value = default
value = d.get(key, default)             # 一行内置能解决的别写 try；LBYL（Java 习惯）就是 `if key in d:`
```

## 5. 并发模型

CPython 有 **GIL**：同一时刻只有一个线程执行 Python 字节码。**I/O 密集**（socket/文件/`sleep`）会释放 GIL → 多线程有效；**纯 CPU 的 Python 循环**多线程不加速 → 上进程，或把热点交给 C 实现（NumPy）。官方 Windows 安装包 3.14 仍带 GIL（3.13+ 有实验性 free-threading 构建，别依赖）。

| Java | Python | 备注 |
|---|---|---|
| `Thread` / `Runnable` | `threading.Thread(target=fn, args=(...), daemon=True)` | `start()`/`join()` 同名 |
| `ExecutorService` / `ThreadPool` | `ThreadPoolExecutor(max_workers=n)`（`concurrent.futures`） | `with` 块自动 shutdown，免 `close()` |
| `ForkJoinPool` 跑 CPU | `ProcessPoolExecutor` | Windows 是 spawn，**必须**写在 `if __name__ == "__main__":` 里；参数走 pickle |
| `Future.get()` / `isDone` / `CompletionService` | `future.result(timeout=…)` / `.done()` / `as_completed(fs)` | 异常只在 `.result()` 时抛；`executor.map` 保序 |
| `CompletableFuture` 链 / 虚拟线程 | `asyncio`（`async def` + `await`） | 单线程事件循环，可挂几万协程 |
| `synchronized` / `ReentrantLock` / `Semaphore` / `CountDownLatch` / `CyclicBarrier` / `wait-notify` | `with threading.Lock():` / `RLock`（可重入）/ `threading.Semaphore` / `Event` / `Barrier` / `Condition` | 无公平锁、无读写锁；队列场景别手写 wait/notify，直接用 `queue.Queue` |
| `AtomicInteger` / `LongAdder` / `ThreadLocal` / `Timer` | 无原子类：`with lock: n += 1`；纯递增 `next(itertools.count())`；`contextvars.ContextVar`（协程安全的 ThreadLocal）；`threading.Timer`、`loop.call_later()` | |
| `volatile` | **没有对应物**：CPython 里单次读/写因 GIL 不会撕裂，可见性问题比 Java 小；但 `x += 1`、`if cache is None: cache = build()` 这类读-改-写仍是竞态 | **GIL ≠ 线程安全** |

```java
try (var pool = Executors.newFixedThreadPool(8)) {
    var futures = urls.stream().map(u -> pool.submit(() -> fetch(u))).toList();
    for (var f : futures) results.add(f.get(5, SECONDS));
}
```

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=8) as pool:          # 退出即 shutdown
    futures = {pool.submit(fetch, u): u for u in urls}
    for fut in as_completed(futures, timeout=5):         # 谁先好谁先用；要保序用 pool.map
        results[futures[fut]] = fut.result()
```

```python
import asyncio

async def main(urls: list[str]) -> list[str]:            # ≈ CompletableFuture 编排
    async with asyncio.timeout(5):                       # ≈ orTimeout(...)，3.11+
        async with asyncio.TaskGroup() as tg:            # 任一失败 -> 取消其余，异常打包成 ExceptionGroup
            tasks = [tg.create_task(fetch(u)) for u in urls]
        return [t.result() for t in tasks]
# 失败也算一个结果：await asyncio.gather(*map(fetch, urls), return_exceptions=True)
# 阻塞库别卡事件循环：await asyncio.to_thread(blocking_sync_call, arg)
```

### 什么场景选线程 / 进程 / 协程

| 场景 | 选 | 为什么 |
|---|---|---|
| CPU 密集：压缩、图像、大量纯 Python 计算 | `ProcessPoolExecutor` / NumPy 向量化 | 绕开 GIL，多核真并行 |
| I/O 密集、并发几十~几百 | `ThreadPoolExecutor` | 阻塞库（`requests`、`pymysql`）不用改代码 |
| I/O 密集、并发几千+（爬虫、网关、WebSocket） | `asyncio` + `aiohttp`/`httpx` | 单线程，切换成本远低于线程 |
| 主流程异步但有阻塞调用 | `asyncio.to_thread` 包一层 | 别在协程里直接跑同步 I/O |
| 生产者/消费者跨线程传数据 | `queue.Queue` | 自带阻塞与锁 |
| 跨进程共享状态 / 真原子计数 | `multiprocessing.Value`、Redis | 内存变量不跨进程 |

## 6. 构建与依赖

心智模型：**没有全局仓库**。Maven 靠 `~/.m2` 全机器共享，Python 靠**每个项目一个虚拟环境**（`.venv`），环境就是隔离单位，`site-packages` 相当于该项目的专属本地仓库。

```toml
# pyproject.toml —— 取代 pom.xml / build.gradle
[project]
name = "app"
requires-python = ">=3.14"              # 相当于 <maven.compiler.release>
dependencies = ["requests>=2.32", "pydantic>=2.7"]                    # compile scope
[project.optional-dependencies]         # 相当于 <scope>test</scope>
dev = ["pytest>=8", "ruff", "mypy"]
[project.scripts]                       # 相当于 <mainClass>
app = "app.cli:main"
[build-system]                          # 相当于 <build><plugins>
requires = ["setuptools>=68"]; build-backend = "setuptools.build_meta"
```

| 我想干 | Maven | Python（Windows） |
|---|---|---|
| 建工程 / 装依赖 / 装当前项目 | 手写 pom / `mvn install` | `py -m venv .venv` → `.venv\Scripts\activate`；`py -m pip install -r requirements.txt`（**永远 `py -m pip`**，保证装进当前解释器）；`py -m pip install -e ".[dev]"` |
| 依赖树 / 查可升级 / 清理 | `mvn dependency:tree`、`versions:display-dependency-updates`、`mvn clean` | `py -m pipdeptree` / `py -m pip list --outdated` / 无统一命令：删 `build/ dist/ *.egg-info __pycache__`，或 `git clean -xfd` |
| 打包 / 运行 / 测试 | `mvn package` / `java -jar app.jar` / Surefire | `py -m build`（wheel+sdist）/ `py -m app` 或激活后的 `app` / `py -m pytest` |
| 私服 + `settings.xml` | `<repositories>` + mirror | `py -m pip install --index-url <内网源> …` |
| lockfile | `mvn dependency:lock` | `py -m pip freeze > requirements.txt`；正式用 `pip-tools`（`py -m piptools compile requirements.in` → `pip sync`）或 `uv`（`uv lock` / `uv sync` / `uv run pytest`） |

镜像源（国内网络慢时用；**是第三方镜像，可能滞后或抽风，能直连官方源就别换**）：

```powershell
py -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple requests          # 临时一次
py -m pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/   # 永久（阿里源）
py -m pip config unset global.index-url                                        # 回到官方 pypi.org
```

## 7. 测试与质量

```java
@Test
@DisplayName("金额为负应当抛异常")
void rejectsNegativeAmount() {
    var ex = assertThrows(IllegalArgumentException.class, () -> new Order(-1));
    assertThat(ex).hasMessageContaining("amount");
    assertThat(cart.items()).hasSize(3).extracting(Item::price).containsExactly(9.9, 20.0);
}
```

```python
import pytest

def test_rejects_negative_amount():                      # 不用建测试类
    with pytest.raises(ValueError, match="amount"):      # = assertThrows，match 是正则
        Order(-1)
    assert len(cart.items) == 3
    assert [i.price for i in cart.items] == [9.9, 20.0]  # 失败时 pytest 展开表达式里每个值
```

| JUnit5 / Mockito | pytest |
|---|---|
| `assertEquals` / `assertSame` / `assertThrows` | 内置 `assert a == b` / `assert a is b` / `with pytest.raises(E)`（不需要 AssertJ） |
| `@BeforeEach` + `@AfterEach` | `@pytest.fixture`：`yield` 前=前置，后=后置（失败也执行）；`@InjectMocks` = 参数按名字注入 |
| `@ParameterizedTest` + `@CsvSource` | `@pytest.mark.parametrize(("n", "ok"), [(1, False), (2, True)])` |
| `@Mock` + `when(x.y()).thenReturn(z)` + `verify(x, times(1))` | `MagicMock(y=Mock(return_value=z))` + `mock.assert_called_once_with(...)`；改模块属性用 `monkeypatch.setattr(mod, "y", fake)` |
| `@TempDir` / 捕获 stdout / `@Disabled`、`@Tag` / `junit-platform.properties` | `tmp_path` / `capsys` / `@pytest.mark.skip`、`skipif`、`-k` 选择 / `[tool.pytest.ini_options]` 写进 `pyproject.toml`，共享 fixture 放 `conftest.py` |

```python
@pytest.fixture
def db(tmp_path):                                  # 一个 fixture 顶一对 Before/After
    conn = sqlite3.connect(tmp_path / "t.db")
    yield conn
    conn.close()
```

| 工具 | Java | Python |
|---|---|---|
| 覆盖率 / 静态类型 / 安全扫描 / 风格 / 格式化 / 深度 lint | JaCoCo / javac / SpotBugs / Checkstyle / Google Java Format / — | `py -m pytest --cov=src --cov-report=term-missing` / `py -m mypy --strict`（或 pyright）/ `py -m bandit -r src` / `py -m ruff check --fix .` / `py -m ruff format` / `py -m pylint`（重）；Sonar 也吃 Python，前端换成上面几个 |

文档字符串替代 Javadoc（`pydoc 模块名` 可查，IDE 也认）。**Google 风格，本项目就用这种**（短、后端够用）：

```python
def ship(order: Order, *, express: bool = False) -> Tracking:
    """把订单交给承运商并返回运单。

    Args:
        order: 待发货订单，状态必须是 PAID。
        express: 是否走次日达。
    Returns:
        承运商返回的运单。
    Raises:
        ValueError: 订单状态不是 PAID。
    """
```

**NumPy 风格**（数据科学社区默认，读 pandas 源码会碰到）：同样内容写成 `Parameters` / `Returns` / `Raises` 三段，每段名下一条 `----` 下划线，参数行写 `order : Order` 再缩进四格写说明。共同规则：首行是一句祈使句摘要，空一行再写正文。

**跑测试**：Java 有 Surefire 兜底；这里**默认没装 pytest**，所以课程配了零依赖判分器。`check.py` 把 [\_pytest_shim.py](../_pytest_shim.py) 冒充成 `pytest` 注册进 `sys.modules`，所以 `import pytest`、`pytest.raises(...)`、`@pytest.mark.parametrize` 在未装 pytest 时也能跑（只实现练习用到的子集，单条超时 10 秒），测试文件写法与真 pytest 完全一致。

```powershell
py check.py L01                    # 全绿才算过；-v 逐条看，--solution 看参考答案成绩
py -m pytest drills/L01 -q         # 装了 pytest 之后这样跑（没装时用上面那行即可）
```

## 8. 字符串与文本

| Java | Python |
|---|---|
| `String.format("%s 今年 %d 岁", n, a)` / `"%,.2f"` / 对齐 / 老式 `%s` | `f"{name} 今年 {age} 岁"`（表达式直接进 `{}`）/ `f"{price:,.2f}"` / `f"{n:>8d}"`、`f"{s:^20}"` / `"%s" % v` 只在老代码里读，别新写 |
| 调试打印 | `f"{value=}"` → 输出 `value=42`（Python 独有）；`f"{s!r}"` 取 repr；`f"{n:03d}"` 补零 |
| `DateTimeFormatter` / `MessageFormat` / 多行文本 | `f"{now:%Y-%m-%d}"` / `"总价 {total}".format(total=…)`（模板可存配置，运行时填）/ 三引号 `"""…"""` + `textwrap.dedent`、`string.Template` |
| `StringBuilder` / `StringJoiner(", ","[","]")` | `parts.append(...)` 再 `"".join(parts)`（**别用 `+=`**，见 §10）/ `f"[{', '.join(items)}]"` |
| `String.repeat` / 补齐 / `trim` / `split` / `startsWith` / `StringUtils.isBlank` | `"ab" * 3`、`s.ljust(10, "-")`、`s.zfill(8)` / `s.strip()` / `s.split(",")`（返回 `list[str]`）/ `s.startswith(("a","b"))` / `if not s.strip():` |

### 正则：Pattern/Matcher → re

```java
Pattern p = Pattern.compile("(?<year>\\d{4})-(\\d{2})");
Matcher m = p.matcher(s);
if (m.find()) { m.group("year"); m.group(1); }
String out = p.matcher(s).replaceAll("-*-$1");
Pattern.compile("\\d+", Pattern.CASE_INSENSITIVE | Pattern.MULTILINE);
```

```python
import re
pat = re.compile(r"(?P<year>\d{4})-(\d{2})")    # 原始字符串 r""：写 \d，不要 \\d
if (m := pat.search(s)):                         # find() -> search()；具名组 (?P<name>...)
    m.group("year"); m.group(1); m.span(); m.start("year")
out = pat.sub(r"-\g<year>", s)                   # replaceAll -> sub；$1 -> \g<1>
pat2 = re.compile(r"\d+", re.IGNORECASE | re.MULTILINE)
pat3.fullmatch(s)                                # Java 的 matches() 等价 fullmatch
pat.findall(s)                                   # 坑：有分组时返回分组而不是整段 —— 用 (?:…) 或 finditer
for m in pat.finditer(s): ...                    # 惰性遍历；还有 re.split(r"[,;\s]+", s)、re.escape(用户输入)
```

### 编码（Windows 最容易踩，重点）

| | Java | Python |
|---|---|---|
| 文本类型 | `String`，内部 UTF-16（emoji 占 2 个 `char`） | `str` = **Unicode 码点序列**（`len("😀") == 1`，切片按码点，不撕裂） |
| 字节类型 / 何时关心编码 | `byte[]`；只在 IO 边界操心 | `bytes`，与 `str` **永不隐式转换**（`b"a" + "a"` 直接 `TypeError`）；同样只在边界：`s.encode("utf-8")` / `b.decode("utf-8")` |

```python
open("x.txt")                      # 简体中文 Windows 默认 cp936/GBK —— 读 UTF-8 文件直接 UnicodeDecodeError
open("x.txt", encoding="utf-8")    # 正确：encoding 永远写死
Path("x.txt").read_text(encoding="utf-8")
```

兜底与配套：`py -X utf8 script.py` 或环境变量 `PYTHONUTF8=1`（全局 UTF-8 模式）；`json.dumps(..., ensure_ascii=False)` 才输出中文而不是 `\uXXXX`；`requests` 的 `.text` 按响应头猜编码，猜错用 `r.content.decode("utf-8")`；控制台乱码多半是代码页问题，`chcp 65001`，别去改文件编码。

## 9. 常用标准库

| Java | Python 模块 | 最短用法 |
|---|---|---|
| `LocalDate`/`Duration`/`ZonedDateTime`/`DateTimeFormatter` | `datetime` + `zoneinfo` | `datetime.now(UTC)`、`d + timedelta(days=1)`、`(b-a).total_seconds()`、`ZoneInfo("Asia/Shanghai")`（Windows 需 `pip install tzdata`）、`strptime(s, "%Y-%m-%d")`、`fromisoformat` |
| `Files`/`Path`/`Paths.get` | `pathlib` + `shutil` | `Path(p).read_text(encoding="utf-8")`、`write_text`、`Path.cwd()/"a.csv"`、`mkdir(parents=True, exist_ok=True)`、`shutil.copy2` |
| Jackson / Gson（Map 进出） | `json` | `json.loads(s)` → `dict`；`json.dumps(obj, ensure_ascii=False, indent=2)` |
| CSV / Jackson + record（强类型 JSON） | `csv`；`pydantic`（第三方） | `csv.DictReader(f)` 迭代出 `dict`；`class Order(BaseModel): id: int` → `Order.model_validate(data)` |
| `HttpClient` / OkHttp / RestTemplate | `urllib.request`（stdlib）/ `requests`（事实标准，第三方） | `requests.get(url, timeout=5).raise_for_status().json()` |
| `WebClient`（异步）/ Jsoup | `aiohttp` / `httpx`；`bs4`（第三方） | `async with httpx.AsyncClient() as c: r = await c.get(u)`；`BeautifulSoup(html, "html.parser").select("a.title")` |
| `java.sql` / JDBC / HikariCP | `sqlite3`（stdlib）/ `pymysql` + 连接池 | `with closing(pymysql.connect(**cfg)) as db:`，游标 `execute(sql, params)` 防注入（L13、Day44） |
| `Executors` | `concurrent.futures` | `with ThreadPoolExecutor(8) as pool: pool.map(f, xs)` |
| `Arrays.sort` / `parallelSort` / `Math.*` / `BigInteger` | 内置 `sorted`；`math`（`int` 本身任意精度） | `sorted(xs, key=…)`（要并行上进程池或 NumPy）；`math.ceil/isclose/gcd/isqrt/inf` |
| SLF4J / Log4j | `logging` | `logging.basicConfig(level=logging.INFO)`；模块内 `logger = logging.getLogger(__name__)` |
| `Random`/`SecureRandom`/`UUID`/`MessageDigest`/`Base64` | `random`/`secrets`/`uuid`/`hashlib`/`base64` | `random.choice(xs)`、`secrets.token_urlsafe(32)`、`uuid.uuid4()`、`hashlib.sha256(b).hexdigest()`、`base64.b64encode(s.encode())` |
| `URLEncoder`/`URI`/`ProcessBuilder`/`ZipInputStream`/GZIP/`Properties`/`System.getenv` | `urllib.parse`、`subprocess`、`zipfile`/`gzip`/`shutil`、`os.environ`、`tomllib` | `urlencode(qs)`、`urlsplit`；`subprocess.run(["git","status"], text=True, capture_output=True, check=True)`；`ZipFile(p).namelist()`、`shutil.unpack_archive`；`os.getenv("HOME","")`；`tomllib.loads(...)`（3.11+） |
| `@Transactional` 边界 / Guava `Cache` / `Thread.sleep` | `contextlib` / `functools` / `time` | `@contextmanager def tx(): … yield … conn.commit()`；`@functools.lru_cache(maxsize=None)` 一行本地缓存；`time.sleep(0.2)`、异步 `await asyncio.sleep(0.2)` |

## 10. Java 老手写 Python 的 12 个反模式

| # | 错误写法 | 为什么不好 | 地道写法 |
|---|---|---|---|
| 1 | `class XxxUtils` 只装静态方法 | **模块就是命名空间**，不用给函数找容器 | 模块级函数：`from tools import count_words` |
| 2 | 全量生成 `getName()/setName()` | Java 式无意义样板 | 直接 `obj.name`；要校验再 `@property` / `@dataclass` |
| 3 | `for i in range(len(xs)):` | 多一次下标查找，易错位 | `for x in xs:`；要下标用 `enumerate(xs)` |
| 4 | `if x == None:` | 不严谨，自定义 `__eq__` 的对象会误判 | `if x is None:`；判空集合是另一回事：`if not x:` |
| 5 | `if type(x) == str:` | 不认子类、不认多态 | `isinstance(x, str)`；结构判断交给 Protocol + mypy |
| 6 | `def f(x=[])` / `def f(now=datetime.now())` | **默认值只创建一次**，所有调用共享同一对象 → 经典 bug | `def f(x: list \| None = None): x = x if x is not None else []` |
| 7 | `for k in list(d.keys()):` | 白包一层、多份内存 | `for k in d:`；只有"边遍历边删"才需要 `list(d)` |
| 8 | 模块顶层直接跑逻辑 | 别人 import 你就被执行一遍；Windows 多进程直接报错 | 包进 `if __name__ == "__main__":` |
| 9 | `try: … except: pass` | 裸 `except` 连 `KeyboardInterrupt`/`SystemExit` 都吞，bug 从此隐形 | 抓具体异常，或 `except Exception as e: logger.exception(...)`；真想忽略用 `contextlib.suppress(KeyError)` |
| 10 | 循环里 `s += line` | `str` 不可变 → O(n²) | 收进 `parts`，最后 `"".join(parts)` |
| 11 | `q.append(x); q.pop(0)` 当队列 | `list.pop(0)` 是 O(n)，整体 O(n²) | `collections.deque`；线程间用 `queue.Queue` |
| 12 | 静态内部类 / `__new__` 手写单例 | Python 的**模块只导入一次**，本身就是单例 | 模块级变量 + `import config`；要工厂就 `functools.cache` |

命名也换一套：函数/变量 `snake_case`、类 `PascalCase`、常量 `UPPER_SNAKE`（Java 的 `mUserName` 前缀没人看）；推导式套到第二层就别硬塞，写回 for 循环 —— 见 [用函数还是用复杂的表达式](https://github.com/jackfrued/Python-100-Days/blob/master/%E7%95%AA%E5%A4%96%E7%AF%87/%E7%94%A8%E5%87%BD%E6%95%B0%E8%BF%98%E6%98%AF%E7%94%A8%E5%A4%8D%E6%9D%82%E7%9A%84%E8%A1%A8%E8%BE%BE%E5%BC%8F.md)。

## 这套对照的出处

本表 Python 侧的写法与坑取自原仓库这些讲义（路径均已确认存在）：

| 章节 | 原文出处 |
|---|---|
| §1 OOP / property / ABC / 魔术方法 | [18.面向对象编程入门](https://github.com/jackfrued/Python-100-Days/blob/master/Day01-20/18.%E9%9D%A2%E5%90%91%E5%AF%B9%E8%B1%A1%E7%BC%96%E7%A8%8B%E5%85%A5%E9%97%A8.md)、[19.面向对象编程进阶](https://github.com/jackfrued/Python-100-Days/blob/master/Day01-20/19.%E9%9D%A2%E5%90%91%E5%AF%B9%E8%B1%A1%E7%BC%96%E7%A8%8B%E8%BF%9B%E9%98%B6.md)、[20.面向对象编程应用](https://github.com/jackfrued/Python-100-Days/blob/master/Day01-20/20.%E9%9D%A2%E5%90%91%E5%AF%B9%E8%B1%A1%E7%BC%96%E7%A8%8B%E5%BA%94%E7%94%A8.md) |
| §2 类型注解、一等对象、装饰器 | [31.Python语言进阶](https://github.com/jackfrued/Python-100-Days/blob/master/Day31-35/31.Python%E8%AF%AD%E8%A8%80%E8%BF%9B%E9%98%B6.md)、[17.函数高级应用](https://github.com/jackfrued/Python-100-Days/blob/master/Day01-20/17.%E5%87%BD%E6%95%B0%E9%AB%98%E7%BA%A7%E5%BA%94%E7%94%A8.md) |
| §3 容器、`Counter`/`deque`、推导式 | [12.常用数据结构之集合](https://github.com/jackfrued/Python-100-Days/blob/master/Day01-20/12.%E5%B8%B8%E7%94%A8%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E4%B9%8B%E9%9B%86%E5%90%88.md)、[13.常用数据结构之字典](https://github.com/jackfrued/Python-100-Days/blob/master/Day01-20/13.%E5%B8%B8%E7%94%A8%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E4%B9%8B%E5%AD%97%E5%85%B8.md)、[Python容器使用小技巧](https://github.com/jackfrued/Python-100-Days/blob/master/%E7%95%AA%E5%A4%96%E7%AF%87/Python%E5%AE%B9%E5%99%A8%E4%BD%BF%E7%94%A8%E5%B0%8F%E6%8A%80%E5%B7%A7.md) |
| §4 异常与 `with` | [21.文件读写和异常处理](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/21.%E6%96%87%E4%BB%B6%E8%AF%BB%E5%86%99%E5%92%8C%E5%BC%82%E5%B8%B8%E5%A4%84%E7%90%86.md) |
| §5 GIL / 线程 / 进程 / 协程 | [63.并发编程-1](https://github.com/jackfrued/Python-100-Days/blob/master/Day61-65/63.Python%E4%B8%AD%E7%9A%84%E5%B9%B6%E5%8F%91%E7%BC%96%E7%A8%8B-1.md)、[-2](https://github.com/jackfrued/Python-100-Days/blob/master/Day61-65/63.Python%E4%B8%AD%E7%9A%84%E5%B9%B6%E5%8F%91%E7%BC%96%E7%A8%8B-2.md)、[-3](https://github.com/jackfrued/Python-100-Days/blob/master/Day61-65/63.Python%E4%B8%AD%E7%9A%84%E5%B9%B6%E5%8F%91%E7%BC%96%E7%A8%8B-3.md)、[一个小例子助你彻底理解协程](https://github.com/jackfrued/Python-100-Days/blob/master/%E7%95%AA%E5%A4%96%E7%AF%87/%E4%B8%80%E4%B8%AA%E5%B0%8F%E4%BE%8B%E5%AD%90%E5%8A%A9%E4%BD%A0%E5%BD%BB%E5%BA%95%E7%90%86%E8%A7%A3%E5%8D%8F%E7%A8%8B.md) |
| §6 模块、虚拟环境、依赖 | [14.函数和模块](https://github.com/jackfrued/Python-100-Days/blob/master/Day01-20/14.%E5%87%BD%E6%95%B0%E5%92%8C%E6%A8%A1%E5%9D%97.md)、[91.团队项目开发的问题和解决方案](https://github.com/jackfrued/Python-100-Days/blob/master/Day91-100/91.%E5%9B%A2%E9%98%9F%E9%A1%B9%E7%9B%AE%E5%BC%80%E5%8F%91%E7%9A%84%E9%97%AE%E9%A2%98%E5%92%8C%E8%A7%A3%E5%86%B3%E6%96%B9%E6%A1%88.md) |
| §7 测试与工程化 | [96.软件测试和自动化测试](https://github.com/jackfrued/Python-100-Days/blob/master/Day91-100/96.%E8%BD%AF%E4%BB%B6%E6%B5%8B%E8%AF%95%E5%92%8C%E8%87%AA%E5%8A%A8%E5%8C%96%E6%B5%8B%E8%AF%95.md)、[check.py](../check.py)、[\_pytest_shim.py](../_pytest_shim.py) |
| §8–§9 字符串、正则、编码、数据库 / HTTP / CSV | [11.常用数据结构之字符串](https://github.com/jackfrued/Python-100-Days/blob/master/Day01-20/11.%E5%B8%B8%E7%94%A8%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E4%B9%8B%E5%AD%97%E7%AC%A6%E4%B8%B2.md)、[30.正则表达式的应用](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/30.%E6%AD%A3%E5%88%99%E8%A1%A8%E8%BE%BE%E5%BC%8F%E7%9A%84%E5%BA%94%E7%94%A8.md)、[22.对象的序列化和反序列化](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/22.%E5%AF%B9%E8%B1%A1%E7%9A%84%E5%BA%8F%E5%88%97%E5%8C%96%E5%92%8C%E5%8F%8D%E5%BA%8F%E5%88%97%E5%8C%96.md)、[44.Python接入MySQL数据库](https://github.com/jackfrued/Python-100-Days/blob/master/Day36-45/44.Python%E6%8E%A5%E5%85%A5MySQL%E6%95%B0%E6%8D%AE%E5%BA%93.md)、[62.用Python获取网络资源-1](https://github.com/jackfrued/Python-100-Days/blob/master/Day61-65/62.%E7%94%A8Python%E8%8E%B7%E5%8F%96%E7%BD%91%E7%BB%9C%E8%B5%84%E6%BA%90-1.md)、[23.Python读写CSV文件](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/23.Python%E8%AF%BB%E5%86%99CSV%E6%96%87%E4%BB%B6.md) |
| §10 反模式、惯例、踩坑 | [Python编程惯例](https://github.com/jackfrued/Python-100-Days/blob/master/%E7%95%AA%E5%A4%96%E7%AF%87/Python%E7%BC%96%E7%A8%8B%E6%83%AF%E4%BE%8B.md)、[PEP8风格指南](https://github.com/jackfrued/Python-100-Days/blob/master/%E7%95%AA%E5%A4%96%E7%AF%87/PEP8%E9%A3%8E%E6%A0%BC%E6%8C%87%E5%8D%97.md)、[那些年我们踩过的那些坑](https://github.com/jackfrued/Python-100-Days/blob/master/%E7%95%AA%E5%A4%96%E7%AF%87/%E9%82%A3%E4%BA%9B%E5%B9%B4%E6%88%91%E4%BB%AC%E8%B8%A9%E8%BF%87%E7%9A%84%E9%82%A3%E4%BA%9B%E5%9D%91.md) |
