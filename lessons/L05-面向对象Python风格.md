# L05 · 面向对象：Python 风格

> 读 40 分钟 · 练 50 分钟
> 对应原文：`Day01-20/18`（207 行）+ `19`（191 行）+ `20`（228 行）→ 3 篇约 626 行压成这一页
> 参考：`Day31-35/31.Python语言进阶.md` 的"面向对象相关知识"小节
> 判分：`py check.py L05` ｜ 卡片：[cards/l05.md](../cards/l05.md)

封装继承多态你都懂，不用重学。这一页只解决一件事：**Java 那套 OOP 直觉在 Python 里哪几条是错的**。
Python 的类是运行时可改的对象，没有编译期契约，所以语言把"接口、getter、值对象、枚举"全都变成了
**约定 + 魔术方法 + 装饰器**三件套。

---

## ① 开课先答 3 题（先答后读，答错才对）

1. `p = Point(1, 2)` —— `__init__` 是构造器吗？它应该 `return` 什么？
2. 一个类只写了 `__eq__`，没写 `__hash__`。把它的实例放进 `set()` 会发生什么？
3. `class Square(Shape)` 里的 `super().__init__('square')`，这个 `super()` 和 Java 的 `super` 有什么区别？

答案在 ⑥。先看地图。

---

## ② 差异地图

### 类的骨架：Java → Python

| 主题 | Java | Python | 提醒 |
|---|---|---|---|
| 定义 | `class A { }` | `class A:` + 缩进 | 类体是**运行时执行**的代码，可以往里塞函数、改属性 |
| 构造 | `A()` 构造器，名字必须同类 | `__init__(self, ...)` 只是**初始化**；真正造对象的是 `__new__` | `__init__` 必须返回 None，写了返回值直接 `TypeError` |
| 接收者 | 隐式 `this` | **显式 `self`**，每个实例方法第一个参数 | 漏写 `self` 就是普通函数；`obj.f(x)` 其实是 `A.f(obj, x)` |
| 字段声明 | 类体里声明 `private int x;` | 没有声明，在 `__init__` 里 `self.x = ...` 才存在 | 类体里写的 `x = 5` 是**类属性**，所有实例共享 |
| 私有 | `private` 关键字 | `__name` 名称改写（`_ClassName__name`），`_name` 只是约定 | 一句名言：*We are all consenting adults here* |
| 动态加属性 | 不行 | 默认随便加（对象有 `__dict__`） | 想封死用 `__slots__` |
| `static` 方法 | `static` | `@staticmethod`（不接 self 也不接 cls） | 常常不如直接写模块级函数 |
| 类方法 | 无对应物 | `@classmethod`，第一个参数是 `cls` | 工厂方法的标准姿势，子类调用时 `cls` 是子类 |
| getter/setter | `getX()` / `setX()` | `@property` / `@x.setter`，调用方写 `obj.x` | 想加校验随时升级成 property，**不用改调用方代码** |
| 接口 | `interface` + `implements` | `abc.ABC`（名义类型，要继承）或 `typing.Protocol`（结构类型，不用继承） | Protocol 才是 Python 的默认味道：鸭子类型有类型检查 |
| 值对象 | `record` / Lombok `@Data` | `@dataclass` | 一行生成 `__init__/__repr__/__eq__`；`frozen=True` 才给 `__hash__`，`order=True` 才给比较 |
| 枚举 | `enum` 关键字 | `class Color(Enum)` | 成员**不能**直接 `<` 比较，要比 `.value` |
| 重载/覆盖 | 编译期 `@Override` 检查 | 子类方法名撞上就覆盖，没有任何提示 | 靠 `@override`（3.12+）或测试兜住 |

### 魔术方法速查（"运算符/内置函数"其实是这些方法）

| 你想支持 | 实现 | 谁调用它 |
|---|---|---|
| `print(obj)` / `f'{obj}'` | `__str__(self) -> str` | `str(obj)`、`format(obj)` |
| 调试输出 / 列表里显示 | `__repr__(self) -> str` | `repr(obj)`；**`__str__` 没写时 `print` 退用它** |
| `a == b` / 进 `set`、当 `dict` 键 | `__eq__` + `__hash__`（成对写） | `==`、`hash()`、容器 |
| `a < b`、`sorted()` | `__lt__`（必要时 `__gt__/__le__/__ge__`） | 排序、堆、`min/max` |
| `a + b` | `__add__`；就地版 `__iadd__` | 运算符 |
| `len(obj)` | `__len__` | `len()`，注意空容器因此是 falsy |
| `obj[i]`、`for x in obj` | `__getitem__`（+ `__setitem__`/`__delitem__`） | 下标、迭代、解包 |
| `obj(...)` 像函数一样调用 | `__call__` | 装饰器、策略对象 |
| `with obj:` | `__enter__` / `__exit__` | L06 主讲 |
| `bool(obj)` | `__bool__`（没写则退到 `__len__`） | `if obj:` |

> 只写 `__lt__` 就够 `sorted()` 用；`list.sort()` 只需要 `<`。别七个比较全手写，用 `functools.total_ordering` 或 `@dataclass(order=True)`。

### 继承、MRO、`super()`

```python
class A: pass
class B(A): pass
class C(A): pass
class D(C, B): pass

D.__mro__   # (D, C, B, A, object)  ← C3 线性化，Python 3 统一用新式类
```

| 点 | Java | Python |
|---|---|---|
| 多重继承 | 类不允许（只能多接口） | **允许**，冲突由 MRO 定顺序；构造不了的多继承图会直接 `TypeError` |
| `super` | 编译期确定的"父类" | **函数** `super()`，返回 MRO 里**下一个**类，不是"爸爸" |
| Mixin | 没有 | 靠协作式 `super().__init__(*args, **kwargs)` 串成一链 |
| 找类型 | `instanceof` | `isinstance(x, C)`（认继承和 ABC/Protocol 注册）；`type(x) is C` 只认精确类型 |

---

## ③ 完整样例：读 → 跑 → 改

[drills/L05/worked_example.py](../drills/L05/worked_example.py) 是一个工单小模型，
七段分别演示：`@dataclass(frozen=True, order=True)` 值对象、`ABC` 拦裸实例、
`@classmethod`/`@staticmethod`、`@property`、魔术方法、`Protocol` 不继承也算实现、
以及 `Order(Timestamped, Traced, Task)` 的 MRO 与协作式 `super()` 链、`__slots__` 封死动态属性。

```powershell
py drills/L05/worked_example.py
```

跑出来最该盯的两行：

```
Order 的 MRO： Order -> Timestamped -> Traced -> Task -> WorkItem -> ABC -> object
一路 super() 走完后： True True 双十一大促 4 12
```

改两处再看：① 把 `class Order(Timestamped, Traced, Task)` 改成 `(Task, Timestamped, Traced)`，
`stamped`/`traced` 还能被赋上吗？② 删掉 `Point` 的 `__slots__`，第 ⑤ 段的报错就没了。

---

## ④ 补全题

打开 [drills/L05/exercises.py](../drills/L05/exercises.py)：10 个单元（9 个类 + 1 个函数），
前 6 个挖空（docstring 里有提示和一个 `>>>` 示例），后 4 个只给需求。

```powershell
py check.py L05 -v
```

---

## ⑤ 三个 Java 老手必踩的坑

1. **类体里直接写 `items = []` 是类属性，所有实例共享**。
   `a.items.append(1)` 之后 `b.items` 也有 1 —— 这就是 Java 里 `static List` 的灾难复刻。
   实例字段必须在 `__init__` 里 `self.items = []`。
2. **写了 `__eq__` 就等于把 `__hash__` 设成 `None`**，实例立刻不可哈希：
   `TypeError: unhashable type`。值对象要么两个都写（用同一组字段），要么直接
   `@dataclass(frozen=True)` 让工具成对生成。
3. **`super()` 是"MRO 的下一个"，不是"父类"**。多继承里把 Mixin 顺序写反，就会出现
   `object.__init__() takes exactly one argument` —— 因为链条走到 `object` 才停，
   中间有人没把 `*args, **kwargs` 往下传。Java 里不可能的错，Python 里人人会碰到一次。

---

## ⑥ 现在回看开头 3 题

1. **不是构造器**。`Point(1, 2)` 先由 `__new__` 造出实例，再自动调 `__init__(self, 1, 2)` 做初始化；
   `__init__` 只能返回 `None`（返回别的会 `TypeError`）。要控制"造出来的是什么"（单例、缓存）才动 `__new__`。
2. **`TypeError: unhashable type`**。Python 规定"相等的对象必须有相同哈希"，所以只要自定义了
   `__eq__`，就自动把 `__hash__` 置空，逼你显式补上。
3. Java 的 `super` 编译期绑死直接父类；Python 的 `super()` 返回的是**当前类 MRO 上下一个类**的代理。
   多继承时 `super()` 可能跳到 Mixin 而不是你写的那个基类 —— 这正是 Mixin 机制能成立的原因。

答错的那题，去 [cards/l05.md](../cards/l05.md) 找对应卡片，那张卡今天必须过一遍。

---

## ⑦ 通关标准

- `py check.py L05` 输出 `18/18 通过`。
- 不看资料，写一个 `@dataclass(frozen=True)` 的 `Money` + 一个 `ABC` 计价策略 + 一个能 `sorted()` 的类，10 分钟内跑对。
- 达成后：`py progress.py read L05`。

## ⑧ 还要细节？回原文

| 想要 | 原文 |
|---|---|
| `self`、`__init__`、构造对象、时钟与点的例子 | [Day01-20/18.面向对象编程入门.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day01-20/18.%E9%9D%A2%E5%90%91%E5%AF%B9%E8%B1%A1%E7%BC%96%E7%A8%8B%E5%85%A5%E9%97%A8.md) |
| 访问可见性、动态属性与 `__slots__`、静态/类方法、继承多态 | [Day01-20/19.面向对象编程进阶.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day01-20/19.%E9%9D%A2%E5%90%91%E5%AF%B9%E8%B1%A1%E7%BC%96%E7%A8%8B%E8%BF%9B%E9%98%B6.md) |
| `Enum`、`__repr__`/`__lt__` 运算符重载、`ABCMeta` 工资结算系统 | [Day01-20/20.面向对象编程应用.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day01-20/20.%E9%9D%A2%E5%90%91%E5%AF%B9%E8%B1%A1%E7%BC%96%E7%A8%8B%E5%BA%94%E7%94%A8.md) |
| 工厂模式、单例（`__new__` 用法）与 OOP 复习 | [Day31-35/31.Python语言进阶.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day31-35/31.Python%E8%AF%AD%E8%A8%80%E8%BF%9B%E9%98%B6.md) |
| 装饰器与 `@property` 背后的机制 | [Day01-20/17.函数高级应用.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day01-20/17.%E5%87%BD%E6%95%B0%E9%AB%98%E7%BA%A7%E5%BA%94%E7%94%A8.md) |

原文用的是 `metaclass=ABCMeta` 的老写法；现在直接 `class Shape(ABC)` 就行，效果一样。
