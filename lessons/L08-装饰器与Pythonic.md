# L08 · 装饰器与 Pythonic

> 读 40 分钟 · 练 50 分钟
> 对应原文：`Day01-20/17`、`Day31-35/31` 与番外篇 5 篇（7 篇、共 2313 行）→ 压缩成这一页
> 判分：`py check.py L08` ｜ 卡片：[cards/l08.md](../cards/l08.md)

装饰器 = 你早就会的东西换了层皮：高阶函数 + 闭包 + 语法糖。Java 里它的近亲是
AOP 代理和 Lombok 注解——但 Python 的装饰器**就在语言表面**，不需要容器、不需要编译期魔法。
这一课另一半篇幅给"类型注解 + Pythonic 惯例 + 经典坑"，这三样决定你写的代码
像不像本地人写的。

---

## ① 开课先答 3 题（先答后读，答错才对）

1. 堆两个装饰器 `@a` 在上、`@b` 在下，调用 `f()` 时**哪个 wrapper 先执行**（离原函数更近）？
2. 装饰器忘了写 `@functools.wraps(func)`，`f.__name__` 会变成什么？怎么拿回未装饰的原函数？
3. `def score(x: int) -> str: return 1` —— Python 运行时报错吗？mypy 报错吗？

答案在 ⑥。先看地图。

---

## ② 差异地图（只列你缺的那 20%）

| 主题 | Java | Python | 一句话提醒 |
|---|---|---|---|
| 装饰器本质 | AOP 代理 / 动态代理 | `f = dec(f)`，def 时执行 | 就是赋值，没有任何运行时魔法 |
| `@Override` | 编译期校验 | **没有等价物** | 方法名拼错只有调用时才 AttributeError |
| 注解(annotation) | 元数据 + 框架扫描 | 装饰器是**可执行代码**，同名不同物 | `@property`、`@lru_cache` 都真的替换了你的定义 |
| 带参装饰器 | 注解元素 `@Retry(times=3)` | 三层：工厂→装饰器→wrapper | 用语法糖时 `@retry(3)` 括号必写 |
| 类装饰器 | — | `@dataclass`、`@singleton` | 参数是类，返回改造后的类 ≈ Lombok |
| 类型注解 | 静态强类型，编译器强制执行 | **纯提示**，运行时零强制 | 别把 Java 的信任感带过来 |
| 泛型 | `List<? extends T>`、通配符满天飞 | `list[str]`、`TypeVar`、`X | None` | 3.9+ 内置容器可直接下标 |
| 接口 | 名义子类型，必须 implements | `Protocol` 结构化子类型：像就行 | 鸭子类型拿到静态检查版 |
| 类型检查器 | javac 内置 | 另跑 `mypy`（或 pyright） | 不进运行时，CI 里当一道门 |
| 命名 | camelCase / PascalCase / CONSTANT | snake_case / CapWords / CONSTANT | PEP8：函数和变量小写下划线 |
| 空安全 | `Optional<String>` / @Nullable | `str | None` | 语义≈可空类型注解，不是容器 |

### 装饰器：从闭包到 @ 只需三步

```python
def counted(func):                      # ① 高阶函数：参数是函数
    @wraps(func)                        # ② 必写：保住 __name__/__doc__/__wrapped__
    def wrapper(*args, **kwargs):       # ③ 闭包持有 func；参数照单全收再转交
        CALLS[func.__name__] = CALLS.get(func.__name__, 0) + 1
        return func(*args, **kwargs)
    return wrapper

@counted                                # 等价于 fetch_user = counted(fetch_user)
def fetch_user(user_id): ...
```

带参数就多包一层工厂（原文 31 课的 `record(output)`、`lru_cache(maxsize)` 都是它）：

```python
from functools import wraps

def repeat(times):                      # 工厂：收装饰器参数
    def decorate(func):                 # 真正的装饰器
        @wraps(func)
        def wrapper(*args, **kwargs):
            return [func(*args, **kwargs) for _ in range(times)]
        return wrapper
    return decorate

@repeat(3)                              # repeat(3) 先执行，返回 decorate 再来装饰
def shout(text):
    return text.upper()

print(shout("hi"))                      # ['HI', 'HI', 'HI'] —— 返回值已被 wrapper 换掉
```

栈顺序：**自下而上应用，自上而下执行**。`@a @b def f` = `a(b(f))`，b 的 wrapper 离原函数最近。

类装饰器（Day31 的 `@singleton` 就是）：输入类、返回类/替换物。写 `__call__` 的类
也能当装饰器用。

### 类型注解速成（给 Java 人的 10 行版）

```python
from typing import Protocol, TypeVar
T = TypeVar("T")

def top(names: list[str], n: int) -> str | None: ...   # 可空写成联合，不是 Optional
def first(xs: list[T]) -> T: ...                       # 同一次调用内 T 一致
class Sized(Protocol):                                  # 结构化子类型
    def __len__(self) -> int: ...
def show(x: Sized) -> int: return len(x)                # list/str/任意有 __len__ 的都行
```

规则就三条：**注解不强制运行时**（`sum([1, "2"])` 照样炸）；`mypy 文件.py` 离线按注解检查；
泛型参数写在小写内置类型里（`dict[str, int]`，Java 的 `Map<String, Integer>` 心智直接平移）。
`bool` 是 `int` 的子类——`isinstance(True, int) is True`，严格判类型用 `type(x) is int`。

### Pythonic 惯例（番外篇《Python编程惯例》十条压缩版）

| 别写 | 写 |
|---|---|
| `if len(items) > 0:` | `if items:` |
| `if name.find('L') != -1:` | `if 'L' in name:` |
| `for i in range(len(xs)):` | `for i, x in enumerate(xs):` |
| `for i in range(len(keys)): d[keys[i]] = vals[i]` | `for k, v in zip(keys, vals):` 或 `d = dict(zip(keys, vals))` |
| `s = ''; for p in parts: s += p` | `s = ''.join(parts)` |
| `if k in d: v = d[k]` (LBYL) | `try: v = d[k] / except KeyError:` (EAFP，L06) |
| 一行嵌套三元的"炫技表达式" | 辅助函数拆开（《用函数还是用复杂的表达式》） |
| `import this 风格自由发挥` | import 三段排：标准库→第三方→本地，段内字母序，放文件头 |

PEP8 硬指标：4 空格缩进不用 Tab、行宽 79、函数/类前后两空行、方法间一空行、
`from math import sqrt` 优于到处 `math.sqrt`、内外都要 `is not b` 而不是 `not a is b`。

---

## ③ 完整样例：读 → 跑 → 改

跑 [drills/L08/worked_example.py](../drills/L08/worked_example.py)：
`py drills/L08/worked_example.py`

五段：计数装饰器（计时器换计数器，输出确定）、带参装饰器与嵌套顺序、类装饰器、
注解运行时不强制 + Protocol/TypeVar、经典坑巡礼（`[[0]*3]*5`）。
改一处再看：把 `@tag` 两层顺序调换，输出从 `<i><b>hello</b></i>` 变成什么？
把 `@wraps` 注释掉，`fetch_user.__name__` 和调用还正常吗？

---

## ④ 补全题

打开 [drills/L08/exercises.py](../drills/L08/exercises.py)，10 个函数，前 6 个挖空后 4 个只给需求。
第 4 题先写下你对装饰器栈顺序的预测再动手。

```powershell
py check.py L08 -v
```

---

## ⑤ 三个 Java 老手必踩的坑

1. **忘写 `@wraps`**。函数名字、docstring、`__wrapped__` 全丢，日志和堆栈里满屏 "wrapper"。
   习惯：写装饰器第一段代码就是 `from functools import wraps`。
2. **带参装饰器少写括号 / 栈顺序脑补反**。`@repeat` 和 `@repeat(3)` 是两个世界（前者把
   被装饰函数当成 times 参数，行为离谱）；顺序记死：**离 def 近的先生效（在内层）**。
3. **信了类型注解**。`: int` 不会拦下 str；`isinstance(True, int)` 是 True；`is` 比 int
   在 [-5,256] 内碰巧能过、出界就翻车（CPython small_ints 缓存，番外篇《坑》原文）。
   要边界校验就手写 `type(x) is int` / `raise TypeError`，要静态保障就进 CI 跑 mypy。

---

## ⑥ 现在回看开头 3 题

1. **`@b` 的 wrapper 先执行**——b 包在最里层（`a(b(f))`），调用链是 a→b→f。
2. 变成 **`"wrapper"`**；`f.__wrapped__` 可以拿到原函数，但前提是写了 wraps。
3. **运行时什么都不报**（注解零强制）；**mypy 会报** `返回类型 str 与实际 int 不符`。

答错的题，去 [cards/l08.md](../cards/l08.md) 找对应卡片过一遍。

---

## ⑦ 通关标准

- `py check.py L08` 输出 `18/18 通过`。
- 不看资料，手写出带参数装饰器三层结构，并解释 `@a @b` 的执行顺序。
- 达成后：`py progress.py done L08`。

## ⑧ 还要细节？回原文

| 想要 | 原文 |
|---|---|
| 装饰器的"下载上传计时"完整故事 | [Day01-20/17.函数高级应用.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day01-20/17.%E5%87%BD%E6%95%B0%E9%AB%98%E7%BA%A7%E5%BA%94%E7%94%A8.md) |
| 带参装饰器 / 类装饰器 / @singleton 单例 | [Day31-35/31.Python语言进阶.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day31-35/31.Python%E8%AF%AD%E8%A8%80%E8%BF%9B%E9%98%B6.md) 的"函数的使用方式"小节 |
| 十条编程惯用法原文 | [番外篇/Python编程惯例.md](https://github.com/jackfrued/Python-100-Days/blob/master/%E7%95%AA%E5%A4%96%E7%AF%87/Python%E7%BC%96%E7%A8%8B%E6%83%AF%E4%BE%8B.md) |
| PEP8 空格/命名/import 三节 | [番外篇/PEP8风格指南.md](https://github.com/jackfrued/Python-100-Days/blob/master/%E7%95%AA%E5%A4%96%E7%AF%87/PEP8%E9%A3%8E%E6%A0%BC%E6%8C%87%E5%8D%97.md) |
| 容器使用技巧（zip_longest/转置/取最大键） | [番外篇/Python容器使用小技巧.md](https://github.com/jackfrued/Python-100-Days/blob/master/%E7%95%AA%E5%A4%96%E7%AF%87/Python%E5%AE%B9%E5%99%A8%E4%BD%BF%E7%94%A8%E5%B0%8F%E6%8A%80%E5%B7%A7.md) |
| is 比较 / 嵌套列表 / 私有命名三大坑 | [番外篇/那些年我们踩过的那些坑.md](https://github.com/jackfrued/Python-100-Days/blob/master/%E7%95%AA%E5%A4%96%E7%AF%87/%E9%82%A3%E4%BA%9B%E5%B9%B4%E6%88%91%E4%BB%AC%E8%B8%A9%E8%BF%87%E7%9A%84%E9%82%A3%E4%BA%9B%E5%9D%91.md) |
| 复杂表达式 vs 辅助函数之辩 | [番外篇/用函数还是用复杂的表达式.md](https://github.com/jackfrued/Python-100-Days/blob/master/%E7%95%AA%E5%A4%96%E7%AF%87/%E7%94%A8%E5%87%BD%E6%95%B0%E8%BF%98%E6%98%AF%E7%94%A8%E5%A4%8D%E6%9D%82%E7%9A%84%E8%A1%A8%E8%BE%BE%E5%BC%8F.md) |
