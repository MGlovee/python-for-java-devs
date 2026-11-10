# -*- coding: utf-8 -*-
"""L06 参考答案。

别整篇抄 —— 它的价值在于卡住 15 分钟后对照思路。
验证题目本身有没有写错：py check.py L06 --solution
"""
from __future__ import annotations

from collections.abc import Callable
from contextlib import closing, contextmanager, suppress


class ParseError(ValueError):
    """L06 提供的自定义异常：转换失败时抛它，并用 from 保留原始异常。"""


def safe_get(items: list, index: int):
    try:
        return items[index]
    except IndexError:
        return None


def to_int(text: str) -> int:
    try:
        return int(text)
    except ValueError as err:
        raise ParseError(f"无法转换: {text}") from err


def try_divide(a, b, audit: list[str]) -> float | None:
    try:
        result = a / b
    except (ZeroDivisionError, TypeError):
        audit.append("error")
        return None
    else:
        audit.append("ok")          # else：只有 try 没抛异常才走到这里
        return result
    finally:
        audit.append("end")         # finally：无论如何都执行（正常 / 异常 / return 之后）


def first_existing(mapping: dict, keys: list) -> object | None:
    for key in keys:
        try:
            return mapping[key]
        except KeyError:
            continue
    return None


def ignore(exception_type: type[Exception]):
    return suppress(exception_type)


def read_and_close(stream) -> str:
    with closing(stream) as s:      # closing 给"没有 with 协议但有 close()"的对象补上协议
        return s.read()


def sum_ints(tokens: list[str]) -> int:
    total = 0
    for token in tokens:
        try:
            total += int(token)
        except ValueError:
            continue                # EAFP：解析失败跳过，而不是先 isdigit 预检查
    return total


def call_safely(func: Callable[[], object]) -> tuple[object | None, Exception | None]:
    try:
        return func(), None
    except Exception as err:        # 只兜 Exception 家族；KeyboardInterrupt 等继续外传
        return None, err


def parse_config(lines: list[str]) -> dict[str, str]:
    config: dict[str, str] = {}
    for number, line in enumerate(lines, start=1):
        key, sep, value = line.partition("=")
        if not sep or not key:
            raise ValueError(f"第 {number} 行不是 key=value 格式: {line!r}")
        config[key] = value
    return config


@contextmanager
def session(log: list[str]):
    log.append("open")
    try:
        yield                       # with 块的主体在 yield 处执行
    finally:
        log.append("close")         # 主体抛异常也要收尾，且不在这里吞
