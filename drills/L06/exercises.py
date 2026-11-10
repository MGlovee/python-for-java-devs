# -*- coding: utf-8 -*-
"""L06 练习工作表 —— 把每个函数里的 `raise NotImplementedError` 删掉，写上你的实现。

判分：  py check.py L06 -v
看答案：py check.py L06 --solution   （建议卡住 15 分钟以上再看）

本文件已给出自定义异常 ParseError（继承 ValueError），第 2 题要用。
所有题目不碰磁盘：文件类对象一律用 io.StringIO 或测试里的假对象。
"""
from __future__ import annotations

from collections.abc import Callable


class ParseError(ValueError):
    """L06 提供的自定义异常：转换失败时抛它，并用 from 保留原始异常。"""


# ---------- 第一组：挖空题（有提示，照着填） ----------

def safe_get(items: list, index: int):
    """返回 items[index]；下标越界返回 None。负下标按 Python 原生行为（-1 是末尾）。

    提示：EAFP —— 直接取，越界时 except IndexError 返回 None。
    不许写 `if 0 <= index < len(items)` 这种 LBYL 预检查。
    >>> safe_get([1, 2, 3], 0)
    1
    >>> safe_get([1, 2, 3], 99) is None
    True
    """
    raise NotImplementedError


def to_int(text: str) -> int:
    """把字符串转成 int；失败时抛 ParseError，并且必须用 raise ... from 保留原始 ValueError。

    提示：try: return int(text)
          except ValueError as err: raise ParseError(f"无法转换: {text}") from err
    >>> to_int("42")
    42
    """
    raise NotImplementedError


def try_divide(a, b, audit: list[str]) -> float | None:
    """执行 a / b。异常（ZeroDivisionError 或 TypeError）时返回 None 并向 audit 追加 "error"；
    成功时在 else 分支返回商并向 audit 追加 "ok"；无论哪种情况，finally 都要向 audit 追加 "end"。

    提示：try / except / else / finally 四段都要用到。
    else 只在 try 没抛异常时执行；finally 总是执行。
    >>> audit = []; try_divide(6, 3, audit)
    2.0
    >>> audit
    ['ok', 'end']
    """
    raise NotImplementedError


def first_existing(mapping: dict, keys: list) -> object | None:
    """按 keys 顺序查找，返回第一个存在的键对应的值；一个都不存在返回 None。

    提示：对每个 k 直接 `return mapping[k]`，except KeyError 就 continue。
    不要写 `if k in mapping`（那是 LBYL，字典大/键是惰性算的时会亏）。
    >>> first_existing({"b": 2, "c": 3}, ["a", "c"])
    3
    """
    raise NotImplementedError


def ignore(exception_type: type[Exception]):
    """返回一个上下文管理器：with 块里抛出的指定类型异常被吞掉，其他异常照常向外传播。

    提示：标准库现成的 —— `from contextlib import suppress`，
    return suppress(exception_type)。本函数自己不是 with 语句，是"造一个能用的对象"。
    >>> with ignore(KeyError):
    ...     raise KeyError("miss")     # 到这里什么都没发生
    """
    raise NotImplementedError


def read_and_close(stream) -> str:
    """读取 stream 的全部内容并返回；无论中途是否出错，都必须调用 stream.close()。

    提示：stream 不是真正的文件对象，不能用 `with stream:`。
    用 `from contextlib import closing`：with closing(stream) as s: return s.read()
    """
    raise NotImplementedError


# ---------- 第二组：只给需求（独立写） ----------

def sum_ints(tokens: list[str]) -> int:
    """把 tokens 里能转成 int 的项求和；转换失败（ValueError）的项直接跳过。
    空列表返回 0。
    """
    raise NotImplementedError


def call_safely(func: Callable[[], object]) -> tuple[object | None, Exception | None]:
    """无参调用 func：
    - 正常返回 (返回值, None)；
    - 抛出 Exception 家族的任何异常时，返回 (None, 异常对象本身)（不要返回消息字符串）；
    - 但 KeyboardInterrupt / SystemExit 这类 BaseException 不在捕获范围，必须向外传播。
    """
    raise NotImplementedError


def parse_config(lines: list[str]) -> dict[str, str]:
    """把 ["key=value", ...] 解析成字典。按第一个 "=" 分割（值里可以再有 "="）。

    任何一行不合法就抛 ValueError，异常消息里必须包含该行的 1 起始行号；不合法的行指：
    - 不含 "="；
    - "=" 前的键为空（如 "=abc"）。
    键和值都不需要 strip。
    """
    raise NotImplementedError


def session(log: list[str]):
    """做成一个上下文管理器，用法：with session(log): ...
    进入时向 log 追加 "open"，退出时追加 "close"；with 块里抛的异常不吞，继续向外传播，
    但 "close" 仍然要记录。

    要求：用 `@contextlib.contextmanager` 装饰一个生成器函数来实现（try/finally 放生成器里）。
    """
    raise NotImplementedError
