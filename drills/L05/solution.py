# -*- coding: utf-8 -*-
"""L05 参考答案。

别整篇抄 —— 它的价值在于卡住 15 分钟后对照思路。
验证题目本身有没有写错：py check.py L05 --solution
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class Vector:

    def __init__(self, *components: int):
        self.components: tuple[int, ...] = components

    def __len__(self) -> int:
        return len(self.components)

    def __getitem__(self, index: int) -> int:
        return self.components[index]        # 元组替我们做越界检查

    def __repr__(self) -> str:
        return f'Vector({", ".join(map(str, self.components))})'


class Money:

    def __init__(self, yuan: int, cents: int = 0):
        self.yuan, self.cents = divmod(yuan * 100 + cents, 100)

    def __repr__(self) -> str:
        return f'Money({self.yuan}, {self.cents})'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented            # 交回 Python，它自己会得出 False
        return (self.yuan, self.cents) == (other.yuan, other.cents)

    def __hash__(self) -> int:
        return hash((self.yuan, self.cents))  # 与 __eq__ 用同一组字段，才不会进 set 出鬼

    def __add__(self, other: 'Money') -> 'Money':
        return Money(self.yuan + other.yuan, self.cents + other.cents)


class Rectangle:

    def __init__(self, width: float, height: float):
        self.width = width                   # 没有 @property 时这行是直接建字段
        self.height = height                 # 有了 setter，这行变成"走校验"

    @property
    def width(self) -> float:
        return self._width

    @width.setter
    def width(self, value: float) -> None:
        if value <= 0:
            raise ValueError(f'宽度必须为正数，收到 {value}')
        self._width = value

    @property
    def height(self) -> float:
        return self._height

    @height.setter
    def height(self, value: float) -> None:
        if value <= 0:
            raise ValueError(f'高度必须为正数，收到 {value}')
        self._height = value

    @property
    def area(self) -> float:
        return self._width * self._height


class Multiplier:

    def __init__(self, factor: int):
        self.factor = factor

    def __call__(self, x: int) -> int:
        return self.factor * x


class Version:

    def __init__(self, major: int, minor: int, patch: int):
        self.major, self.minor, self.patch = major, minor, patch

    @classmethod
    def from_string(cls, text: str) -> 'Version':
        parts = [int(p) for p in text.split('.')]
        return cls(*parts)                   # cls 而不是 Version：子类调用时拿到子类

    @staticmethod
    def is_valid(text: str) -> bool:
        return re.fullmatch(r'\d+\.\d+\.\d+', text) is not None

    def __lt__(self, other: 'Version') -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)


class Greeter:

    def __init__(self, message: str):
        self.message = message

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f'Greeter({self.message!r})'          # !r 自动补引号


class Suit(Enum):
    SPADE, HEART, CLUB, DIAMOND = range(4)


@dataclass(frozen=True)                       # 一行顶掉 __init__/__eq__/__repr__/__hash__
class Card:
    suit: Suit
    face: int

    def __lt__(self, other: 'Card') -> bool:
        if self.suit is not other.suit:
            return self.suit.value < other.suit.value   # Enum 成员本身不能 < 比较
        return self.face < other.face


class StrictPoint:
    __slots__ = ('x', 'y')                    # 没有 __dict__，也就挂不上别的属性

    def __init__(self, x: int, y: int):
        self.x, self.y = x, y


class Shape(ABC):

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def area(self) -> float:
        """只有声明没有实现 —— 子类不重写就实例化不了。"""


class Square(Shape):

    def __init__(self, side: float):
        super().__init__('square')            # 公共字段让父类初始化（Proxy 模式那套）
        self.side = side

    def area(self) -> float:
        return float(self.side) ** 2


def diamond_mro() -> list[str]:
    class A:
        pass

    class B(A):
        pass

    class C(A):
        pass

    class D(C, B):                            # 基类顺序 (C, B) 决定线性化结果
        pass

    return [cls.__name__ for cls in D.__mro__]
