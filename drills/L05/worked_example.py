# -*- coding: utf-8 -*-
"""L05 完整样例 —— 直接跑：py drills/L05/worked_example.py

一个工单小模型，七段分别演示：self 与 __init__、类属性 vs 实例属性、@property、
魔术方法、classmethod 工厂、Enum + dataclass、ABC 与 Protocol、__slots__、MRO 与 super()。
学习顺序：跑 → 对着输出读代码 → 把 Ticket 的 frozen=True 改成 False 再跑 → 默写 Order 的 MRO。
"""
from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable


class Priority(Enum):
    """枚举：成员可比可迭代，成员本身不支持 `<`，要比 `.value`。"""
    LOW, NORMAL, URGENT = range(3)


@dataclass(frozen=True, order=True)
class Ticket:
    """值对象：@dataclass 一行生成 __init__/__repr__/__eq__/__hash__，order=True 再加比较。

    frozen=True → 字段只读、可哈希；这就是 Java 里 record 或 Lombok @Value 的位置。
    """
    key: str
    priority: Priority
    points: int

    def __str__(self) -> str:                      # 给人看的那份，和 __repr__ 分工
        return f'{self.key}[{self.priority.name}] {self.points}分'


class WorkItem(ABC):
    """抽象基类：`is-a` 关系 + 强制子类实现。Java 的 abstract class。"""

    registry: list[str] = []                       # 类属性：所有实例共享，相当于 static 字段

    def __init__(self, title: str) -> None:
        self.title = title                         # 实例属性：写在 self 上才算
        WorkItem.registry.append(title)

    @abstractmethod
    def estimate(self) -> int:
        """只有声明没有实现；子类不重写就实例化不了。"""

    @classmethod
    def from_ticket(cls, ticket: Ticket) -> 'WorkItem':
        """工厂方法：用 cls(...) 才能被子类正确继承（Java 静态方法做不到）。"""
        return cls(f'{ticket.key}-{ticket.priority.name}')

    @staticmethod
    def rank(ticket: Ticket) -> int:
        """静态方法：不需要 self 也不需要 cls，纯粹挂在类名下的工具函数。"""
        return -ticket.points * Priority[ticket.priority.name].value

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.title!r})'      # type(self) 让子类自动带上自己的名字


@runtime_checkable
class Reportable(Protocol):
    """结构化子类型：只要你有 report_line()，你就"是" Reportable —— 不用继承。Java 的 interface 要显式 implements。"""

    def report_line(self) -> str: ...


class Task(WorkItem):
    def __init__(self, title: str, hours: int = 1) -> None:
        super().__init__(title)                    # 把公共字段的初始化交回父类
        self.hours = hours

    def estimate(self) -> int:
        return self.hours * 3

    @property
    def label(self) -> str:                        # @property：调用方写 t.label，不加括号
        return self.title.upper()

    def report_line(self) -> str:                  # 有了这个方法，Task 就"长得像" Reportable
        return f'task: {self.title} 预估 {self.estimate()} 人日'


class AuditLog:
    """没继承 Reportable，但因为长得像，Protocol 就认它（Python 版的鸭子类型）。"""

    def report_line(self) -> str:
        return 'audit: 3 条变更已归档'


class Timestamped:
    """Mixin：只提供一个切面能力，靠协作式 super() 把链条接上。"""

    def __init__(self, *args, **kwargs) -> None:
        self.stamped = True
        super().__init__(*args, **kwargs)


class Traced:
    def __init__(self, *args, **kwargs) -> None:
        self.traced = True
        super().__init__(*args, **kwargs)


class Order(Timestamped, Traced, Task):
    """把两个 mixin 排在 Task 前面：MRO 就是 Order → Timestamped → Traced → Task → WorkItem。

    注意整条链上只有 Order 的 `__init__` 被真正调用，它一路 `super()` 把参数往下传，
    最后由 Task/WorkItem 完成 title、hours 的赋值 —— 这叫协作式多继承。
    """

    def __init__(self, title: str, hours: int = 1) -> None:
        super().__init__(title, hours)             # 这里不碰 self.hours，赋值交给链尾的 Task


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    t = Ticket('ORD-1', Priority.URGENT, 5)
    print('① Ticket  ', repr(t), '|', str(t))
    print('   同一内容两个对象相等：', t == Ticket('ORD-1', Priority.URGENT, 5),
          '| 能进 set：', len({t, Ticket('ORD-1', Priority.URGENT, 5)}))

    print('\n② 抽象基类')
    try:
        WorkItem('裸的')                     # TypeError：抽象方法没实现
    except TypeError as exc:
        print('   实例化 WorkItem 失败 ->', exc)
    task = Task('重构支付模块', hours=2)
    print('   ', repr(task), '| estimate =', task.estimate(), '| label =', task.label)
    print('   类工厂 Task.from_ticket（cls 就是 Task，抽象类 WorkItem 自己调会炸）：',
          repr(Task.from_ticket(t)))
    print('   类属性 registry（共享）：', WorkItem.registry)

    print('\n③ Protocol（不用继承也算实现）')
    print('    isinstance(AuditLog(), Reportable) =', isinstance(AuditLog(), Reportable))
    for item in (AuditLog(), task):
        print('   ', item.report_line())

    print('\n④ MRO 与协作式 super()')
    print('    Order 的 MRO：', ' -> '.join(c.__name__ for c in Order.__mro__))
    o = Order('双十一大促', 4)
    print('    一路 super() 走完后：', o.stamped, o.traced, o.title, o.hours, o.estimate())

    print('\n⑤ __slots__ 关掉动态挂属性')

    class Point:
        __slots__ = ('x', 'y')

        def __init__(self, x: int, y: int) -> None:
            self.x, self.y = x, y

    p = Point(1, 2)
    try:
        p.z = 3                          # AttributeError
    except AttributeError as exc:
        print('   给 Point 挂 z 失败 ->', exc)
    print('   普通类对象想挂就挂：')
    plain = type('Plain', (), {})()
    plain.anything = 42
    print('   plain.anything =', plain.anything)
