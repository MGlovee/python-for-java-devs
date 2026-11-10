# -*- coding: utf-8 -*-
"""L05 判分用例。别改这个文件 —— 它就是考官。

单独跑：py -m pytest drills/L05 -q    （装了 pytest 才有效）
推荐跑：py check.py L05 -v            （零依赖）
"""
import pytest
from exercises import (Card, Greeter, Money, Multiplier, Rectangle, Shape,
                       Square, StrictPoint, Suit, Vector, Version, diamond_mro)


def test_01_vector_container_protocol():
    v = Vector(10, 20, 30)
    assert len(v) == 3, "len() 走 __len__"
    assert v[0] == 10 and v[-1] == 30, "负下标由元组白送"
    assert [v[i] for i in range(len(v))] == [10, 20, 30]
    assert v.components == (10, 20, 30), "分量存成元组，所以 Vector 天生不可变"


def test_02_vector_repr():
    assert repr(Vector(1, 2, 3)) == 'Vector(1, 2, 3)'
    assert repr(Vector()) == 'Vector()', "空向量也不能多一个逗号或空格"
    assert f'{Vector(4, 5)}' == 'Vector(4, 5)', "没有 __str__ 时 print 和 f-string 都退到 __repr__"


def test_03_vector_out_of_range():
    with pytest.raises(IndexError):
        Vector(1, 2)[2]


def test_04_money_normalizes_on_construct():
    m = Money(1, 150)
    assert (m.yuan, m.cents) == (2, 50), "分满 100 要进位"
    assert repr(m) == 'Money(2, 50)'
    assert Money(0, 0).cents == 0


def test_05_money_equality_by_value():
    assert Money(1, 150) == Money(2, 50), "按值比较，不是按身份"
    assert Money(2, 30) != Money(2, 31)
    assert (Money(1, 0) == '1 元') is False, (
        "__eq__ 收到别的类型要返回 NotImplemented，让 Python 得出 False，别抛异常")


def test_06_money_add_is_immutable():
    a, b = Money(1, 20), Money(0, 90)
    assert a + b == Money(2, 10)
    assert repr(a) == 'Money(1, 20)' and repr(b) == 'Money(0, 90)', "不许改动操作数"
    assert (a + b) + Money(0, 1) == Money(2, 11)


def test_07_money_is_hashable():
    assert len({Money(1, 20), Money(1, 20), Money(1, 21)}) == 2, (
        "没有 __hash__ 的话这里直接 TypeError：定义了 __eq__ 就等于把 __hash__ 设为 None")
    assert hash(Money(3, 4)) == hash(Money(3, 4))
    assert {Money(1, 0): 'x'}[Money(1, 0)] == 'x'


def test_08_rectangle_area_is_property():
    r = Rectangle(2, 3)
    assert r.area == 6, "property：不加括号"
    assert not callable(r.area), "area 必须是值，不是方法"
    r.width = 4
    assert r.area == 12, "area 得跟着 width 变，不能是构造时算死的"


def test_09_rectangle_rejects_bad_sizes():
    r = Rectangle(2, 3)
    with pytest.raises(ValueError):
        r.width = -1
    with pytest.raises(ValueError):
        r.height = 0
    with pytest.raises(ValueError):          # 构造也要校验，前提是 __init__ 走了 setter
        Rectangle(0, 5)


def test_10_multiplier_is_callable():
    m = Multiplier(3)
    assert callable(m)
    assert m(4) == 12
    assert [m(x) for x in range(3)] == [0, 3, 6]
    assert Multiplier(2)(10) == 20


def test_11_version_from_string():
    v = Version.from_string('2.10.3')
    assert isinstance(v, Version), "classmethod 的第一个参数是类本身，要返回实例"
    assert (v.major, v.minor, v.patch) == (2, 10, 3)


def test_12_version_is_valid_returns_bool():
    assert Version.is_valid('1.2.3') is True
    assert Version.is_valid('1.2') is False
    assert Version.is_valid('a.b.c') is False
    assert Version.is_valid('1.2.3.4') is False


def test_13_version_compares_numerically():
    assert Version(2, 9, 9) < Version(2, 10, 0), "按数值比：字符串比的话 '9' > '10'"
    ordered = sorted([Version(1, 0, 0), Version(0, 9, 9), Version(1, 0, 1)])
    assert [(v.major, v.minor, v.patch) for v in ordered] == [(0, 9, 9), (1, 0, 0), (1, 0, 1)]


def test_14_card_equality_by_fields():
    a, b = Card(Suit.SPADE, 5), Card(Suit.SPADE, 5)
    assert a == b, "默认按身份比较，所以必须自己实现 __eq__（或上 @dataclass）"
    assert a != Card(Suit.HEART, 5)
    assert a != Card(Suit.SPADE, 6)
    assert (a.suit, a.face) == (Suit.SPADE, 5)


def test_15_card_sorting():
    hand = [Card(Suit.HEART, 2), Card(Suit.SPADE, 13),
            Card(Suit.CLUB, 1), Card(Suit.SPADE, 1)]
    assert sorted(hand) == [Card(Suit.SPADE, 1), Card(Suit.SPADE, 13),
                            Card(Suit.HEART, 2), Card(Suit.CLUB, 1)], (
        "先按 Suit 定义顺序（SPADE<HEART<CLUB<DIAMOND），同花色按点数升序")
    assert len({Card(Suit.SPADE, 5), Card(Suit.SPADE, 5)}) == 1, "__eq__ 写了就得写 __hash__"


def test_16_slots_blocks_new_attributes():
    p = StrictPoint(1, 2)
    assert (p.x, p.y) == (1, 2)
    with pytest.raises(AttributeError):      # 默认对象有 __dict__，随便挂属性也不报错
        p.z = 3


def test_17_abstract_shape_cannot_instantiate():
    with pytest.raises(TypeError):
        Shape('any')
    s = Square(3)
    assert s.area() == 9
    assert s.name == 'square', "Square 要把构造交给 super().__init__"
    assert isinstance(s, Shape) and issubclass(Square, Shape)


def test_18_diamond_mro():
    assert diamond_mro() == ['D', 'C', 'B', 'A', 'object'], (
        "C3 线性化：D -> C -> B -> A -> object，不是 Java 那种根本没有的多重继承")
