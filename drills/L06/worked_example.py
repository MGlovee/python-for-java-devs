# -*- coding: utf-8 -*-
"""L06 完整样例 —— 直接跑：py drills/L06/worked_example.py

学习顺序：跑 → 看输出 → 改数字再跑 → 合上屏幕默写一遍。
全程不碰磁盘：假文件对象只存在于内存。
"""
from __future__ import annotations

import io
from contextlib import closing, contextmanager, suppress


# ---------- 1) 自定义异常层级：像 Java 一样按业务分层 ----------

class OrderError(Exception):
    """订单业务异常基类 —— 自定义异常继承 Exception，不是 BaseException。"""


class PaymentError(OrderError):
    def __init__(self, order_id: str, reason: str):
        super().__init__(f"订单 {order_id} 支付失败: {reason}")
        self.order_id = order_id


class InventoryError(OrderError):
    """库存不足。"""


def pay(order_id: str, balance: float, amount: float) -> str:
    if amount > balance:
        raise PaymentError(order_id, "余额不足")
    if amount <= 0:
        raise InventoryError(f"{order_id}/数量非法")
    return f"{order_id} 支付成功"


# ---------- 2) except 按书写顺序匹配，具体类型放前面 ----------

def classify(exc: Exception) -> str:
    try:
        raise exc
    except ValueError:
        return "value 家族"
    except (TypeError, LookupError):
        return "type/lookup 家族"
    except Exception as other:
        return f"其他: {type(other).__name__}"


# ---------- 3) else 与 finally：Java 里只有 finally ----------

audit_log: list[str] = []


def divide_with_audit(a, b) -> float:
    try:
        result = a / b
    except ZeroDivisionError as err:
        audit_log.append("error")
        raise ValueError("除数不能为 0") from err     # 异常链：cause 保留现场
    else:
        audit_log.append("ok")                        # 只有没抛异常才执行
        return result
    finally:
        audit_log.append("released")                  # 永远执行


# ---------- 4) with 协议：__enter__ / __exit__ ----------

class TaggedBlock:
    """手写上下文管理器，相当于 Java 实现 AutoCloseable，但还能决定是否吞异常。"""

    def __init__(self, name: str, log: list[str]):
        self.name = name
        self.log = log

    def __enter__(self):
        self.log.append(f"<{self.name}>")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.log.append(f"</{self.name}>")
        return False                                  # False = 异常继续向外传播


@contextmanager
def section(name: str, log: list[str]):
    """contextlib 版：一个生成器顶三个方法。"""
    log.append(f"[{name}]")
    try:
        yield
    finally:
        log.append(f"[/{name}]")


# ---------- 5) suppress 与 closing ----------

def parse_loose(text: str) -> int | None:
    with suppress(ValueError):            # 只在"明确允许失败"的小块里吞
        return int(text)
    return None


class FakeFile:
    """只有 read/close、没有 with 协议的对象 —— 用 contextlib.closing 兜住。"""

    def __init__(self, source: io.StringIO):
        self._source = source
        self.is_open = True

    def read(self) -> str:
        return self._source.read()

    def close(self) -> None:
        self.is_open = False


if __name__ == "__main__":
    # 1) 按业务基类 catch 一次捞到一族子类
    for order in (("A-1", 10.0, 20.0), ("A-2", 10.0, 5.0), ("A-3", 10.0, 0.0)):
        try:
            print(pay(*order))
        except OrderError as err:
            print(f"捕获 {type(err).__name__}: {err}  (是 PaymentError? {isinstance(err, PaymentError)})")

    # 2) except 顺序：ValueError 先命中，不会掉进后面的元组分支
    print(classify(ValueError()))
    print(classify(KeyError("k")))
    print(classify(RuntimeError("r")))

    # 3) else/finally + 异常链
    audit_log.clear()
    print(divide_with_audit(6, 3), "| audit:", audit_log)
    audit_log.clear()
    try:
        divide_with_audit(1, 0)
    except ValueError as err:
        print(f"拿到 ValueError，__cause__ 是 {type(err.__cause__).__name__}",
              "| audit:", audit_log)

    # 4) 两种 with 写法殊途同归
    log: list[str] = []
    with TaggedBlock("b", log):
        pass
    with section("s", log):
        pass
    print(" ".join(log))

    # 5) suppress / closing
    print(parse_loose("42"), parse_loose("x"))
    fake = FakeFile(io.StringIO("in-memory"))
    with closing(fake) as f:
        print(f.read(), end=" ")
    print("-> closing 之后 is_open =", fake.is_open)
