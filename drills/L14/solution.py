# -*- coding: utf-8 -*-
"""L14 参考答案 —— 测试与工程化（logging / pytest 心智 / CLI / timeit / 迷你 linter）。"""
from __future__ import annotations

import argparse
import ast
import contextlib
import io
import logging
import re
import timeit

# ---------- 第一组：挖空题 ----------

def level_name_to_no(name: str) -> int:
    """`"INFO"` → 20；认不出来时 `getLevelName` 返回**字符串**，要自己转成 ValueError。"""
    no = logging.getLevelName(name)
    if not isinstance(no, int):                      # "Level info" / "Level FOO"
        raise ValueError(f"不是有效的日志级别名：{name!r}")
    return no


def should_log(record_level: int, logger_level: int) -> bool:
    """级别是**阈值**：记录级别 >= logger 级别才输出，相等也输出。"""
    return record_level >= logger_level


def effective_level(logger_level: int | None, parent_level: int) -> int:
    """NOTSET(0) 和 None 都表示"没设"，于是向父级借；显式设过就用自己那份。"""
    if logger_level is None or logger_level == logging.NOTSET:
        return parent_level
    return logger_level


def parse_pytest_summary(text: str) -> dict[str, int]:
    """pytest 的摘要是**人读的自由文本**，只能一项一项正则抠；没出现就是 0。"""
    counts: dict[str, int] = {}
    for key, pattern in (("passed", r"(\d+) passed"),
                         ("failed", r"(\d+) failed"),
                         ("errors", r"(\d+) error"),      # 单数 error 也要吃下 "2 errors"
                         ("skipped", r"(\d+) skipped")):
        found = re.search(pattern, text)
        counts[key] = int(found.group(1)) if found else 0
    return counts


def format_log_record(name: str, level: int, message: str) -> str:
    """不经 handler，直接手工造 record + Formatter，验证"模板吃的是 record 的属性"。"""
    record = logging.LogRecord(name, level, __file__, 1, message, (), None)
    return logging.Formatter("%(levelname)s|%(name)s|%(message)s").format(record)


def parse_cli_args(argv: list[str]) -> dict[str, object]:
    """argparse 出错走 SystemExit（用法打到 stderr），不是 ValueError。"""
    parser = argparse.ArgumentParser(prog="demo", description="L14 命令行示例")
    parser.add_argument("-n", "--name", default="world", help="打招呼对象")
    parser.add_argument("-c", "--count", type=int, default=1, help="重复次数")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    return vars(parser.parse_args(argv))


# ---------- 第二组：只给需求 ----------

def expect_raises(func, expected_exc: type[BaseException]) -> str:
    """自己实现 pytest.raises：没抛 = 失败；抛错类型 = 让它冒出去。"""
    try:
        func()
    except expected_exc as exc:
        return str(exc)
    raise AssertionError(f"期望抛出 {expected_exc.__name__}，但 func() 正常返回了")


def capture_stdout(func, *args) -> tuple[str, object]:
    """redirect_stdout 是上下文管理器，异常路径也会还原 sys.stdout。"""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        result = func(*args)
    return buffer.getvalue(), result


def measure_runtime(stmt: str, number: int = 1000) -> float:
    """timeit 自动关 GC、只计 CPU 时间；这里返回单次平均秒数。"""
    if number <= 0:
        raise ValueError(f"number 必须是正整数，收到 {number}")
    total = timeit.Timer(stmt).timeit(number=number)
    return total / number


_SNAKE = re.compile(r"_*[a-z][a-z0-9_]*")            # fullmatch 用，不锚定


def find_bad_function_names(source: str) -> list[str]:
    """迷你 ruff：ast 遍历函数定义，行号升序报违规名。"""
    tree = ast.parse(source)                          # 语法错 → SyntaxError 原样抛出
    bad: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not _SNAKE.fullmatch(node.name):
                bad.append((node.lineno,
                            f"L{node.lineno}: N802 函数名应使用 snake_case: {node.name}"))
    return [message for _, message in sorted(bad, key=lambda item: item[0])]
