# -*- coding: utf-8 -*-
"""L05 练习工作表 —— Python 风格的面向对象。

判分：  py check.py L05 -v
看答案：py check.py L05 --solution   （建议卡住 15 分钟以上再看）

这一课的对象是"类"，所以工作表里是 10 个练习单元（9 个类 + 1 个工厂函数）。
每个方法体第一行都是 `raise NotImplementedError`，把整行删掉换成你的实现。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum


# ---------- 第一组：挖空题（有提示，照着填） ----------

class Vector:
    """不可变向量 —— 练 `__len__` / `__getitem__` / `__repr__` 三个魔术方法。"""

    def __init__(self, *components: int):
        """用可变参数收集分量，存成元组字段 `self.components`。
        >>> Vector(1, 2, 3).components
        (1, 2, 3)
        """
        raise NotImplementedError

    def __len__(self) -> int:
        """让 `len(v)` 能用 —— `len(v)` 实际调用的是 `v.__len__()`。"""
        raise NotImplementedError

    def __getitem__(self, index: int) -> int:
        """让 `v[0]`、`v[-1]` 能用。越界不用自己管：转交给元组，它自然抛 IndexError。"""
        raise NotImplementedError

    def __repr__(self) -> str:
        """可重建对象的形式：`Vector(1, 2, 3)`（逗号后有一个空格）。"""
        raise NotImplementedError


class Money:
    """金额 —— 练规范化、相等、哈希、加法。属性名固定 `self.yuan` / `self.cents`。"""

    def __init__(self, yuan: int, cents: int = 0):
        """满 100 的分要进位：`Money(1, 150)` 等价于 `Money(2, 50)`，且 `0 <= cents < 100`。
        提示：`divmod(yuan * 100 + cents, 100)` 一步搞定。
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        """形如 `'Money(2, 50)'`。"""
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        """只跟另一个 Money 比；类型不对时 `return NotImplemented`（不是 False，更不是抛异常）。"""
        raise NotImplementedError

    def __hash__(self) -> int:
        """定义了 `__eq__` 就必须定义 `__hash__`，否则 Money 进不了 set / dict。"""
        raise NotImplementedError

    def __add__(self, other: 'Money') -> 'Money':
        """返回新的 Money，不许改动两个操作数（像 BigDecimal 那样不可变）。"""
        raise NotImplementedError


class Rectangle:
    """矩形 —— 练 `@property`：用属性的语法调用方法的逻辑，顺便加校验。"""

    def __init__(self, width: float, height: float):
        """走 setter 赋值（`self.width = width`），校验就只写一遍。"""
        raise NotImplementedError

    @property
    def width(self) -> float:
        """返回私有字段 `self._width`。"""
        raise NotImplementedError

    @width.setter
    def width(self, value: float) -> None:
        """`value <= 0` 抛 ValueError，否则存进 `self._width`。"""
        raise NotImplementedError

    @property
    def height(self) -> float:
        """同上，读写 `self._height`。"""
        raise NotImplementedError

    @height.setter
    def height(self, value: float) -> None:
        """同上。"""
        raise NotImplementedError

    @property
    def area(self) -> float:
        """长乘宽。有了 @property，调用方写 `r.area` 而不是 `r.area()`。"""
        raise NotImplementedError


class Multiplier:
    """练 `__call__`：对象本身可以像函数一样被调用。"""

    def __init__(self, factor: int):
        """存进 `self.factor`。"""
        raise NotImplementedError

    def __call__(self, x: int) -> int:
        """`m(4)` 就是 `m.__call__(4)`。提示：Java 里得写 `m.apply(4)`。"""
        raise NotImplementedError


class Version:
    """三段版本号 —— 练 classmethod / staticmethod / 元组比较。字段名 `major`/`minor`/`patch`。"""

    def __init__(self, major: int, minor: int, patch: int):
        """三个字段按名字存好。"""
        raise NotImplementedError

    @classmethod
    def from_string(cls, text: str) -> 'Version':
        """把 `'2.10.3'` 解析成 `Version(2, 10, 3)`。

        提示：`map(int, text.split('.'))`；构造时用 `cls(...)` 而不是 `Version(...)`，
        子类调用才能拿到子类 —— 这就是 Java 里"静态方法不参与多态"的解药。
        """
        raise NotImplementedError

    @staticmethod
    def is_valid(text: str) -> bool:
        """是否形如"数字.数字.数字"。返回真正的 bool，别把 re 的匹配对象直接吐出去。"""
        raise NotImplementedError

    def __lt__(self, other: 'Version') -> bool:
        """按 `(major, minor, patch)` 元组比大小 —— 一行写完三级优先级。"""
        raise NotImplementedError


class Greeter:
    """`__str__` 与 `__repr__` 的分工。"""

    def __init__(self, message: str):
        """存进 `self.message`。"""
        raise NotImplementedError

    def __str__(self) -> str:
        """返回消息本身（给人看的）。"""
        raise NotImplementedError

    def __repr__(self) -> str:
        """返回 `'Greeter(\'你好\')'` 这种可重建形式。提示：内层用 `!r` 自动带引号。"""
        raise NotImplementedError


# ---------- 第二组：只给需求（独立写） ----------

class Suit(Enum):
    """花色枚举，四个成员的值依次是 0、1、2、3 —— 这一格已经写好，不用动。"""
    SPADE, HEART, CLUB, DIAMOND = range(4)


class Card:
    """一张牌：`Card(Suit.SPADE, 5)`。

    要求：字段 `self.suit`、`self.face`；suit 与 face 都相同的两张牌 `==`；
    可排序 —— 先比花色（用 `suit.value`，Enum 成员本身不支持 `<`），同花色再比点数；
    `__hash__` 要和 `__eq__` 配套（最省事：`(self.suit, self.face)` 元组）。
    可以手写 `__eq__`，也可以改用标准库的 `@dataclass` 让它替你生成。
    """

    def __init__(self, suit: Suit, face: int):
        raise NotImplementedError


class StrictPoint:
    """只有 x、y 两个字段，**禁止**再动态挂别的属性。

    要求：`p = StrictPoint(1, 2)` 后 `p.x`、`p.y` 正常；`p.z = 3` 必须 AttributeError。
    提示：`__slots__`。想想 Java 里靠 `final` + 私有字段做到的事，Python 是从结构上封死的。
    """

    def __init__(self, x: int, y: int):
        raise NotImplementedError


class Shape(ABC):
    """抽象基类 + 一个子类，一起写。

    要求：
    - `Shape` 继承 `ABC`，`__init__(self, name)` 存 `self.name`，`area()` 用 `@abstractmethod`
      标记且没有实现 —— `Shape('x')` 必须 TypeError；
    - `Square(Shape)`：`Square(3).area() == 9.0`、`Square(3).name == 'square'`，
      `__init__` 里用 `super().__init__('square')` 把公共字段的活儿交回父类。
    """

    def __init__(self, name: str):
        raise NotImplementedError

    @abstractmethod
    def area(self) -> float:
        raise NotImplementedError


class Square(Shape):
    """和上面的 Shape 一起写：`Square(3).area() == 9.0`、`Square(3).name == 'square'`。

    `__init__` 里用 `super().__init__('square')` 把公共字段交回父类，别自己赋值。
    """

    def __init__(self, side: float):
        raise NotImplementedError

    def area(self) -> float:
        raise NotImplementedError


def diamond_mro() -> list[str]:
    """函数内部定义菱形继承，返回 `D` 的 MRO 类名列表。

    结构：`class A`；`class B(A)`；`class C(A)`；`class D(C, B)`（注意基类顺序是 C 在前）。
    返回 `[cls.__name__ for cls in D.__mro__]`。
    >>> diamond_mro()
    ['D', 'C', 'B', 'A', 'object']
    """
    raise NotImplementedError
