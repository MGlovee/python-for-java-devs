# -*- coding: utf-8 -*-
"""L14 判分用例。别改这个文件 —— 它就是考官。

只用标准库，不联网、不依赖 pytest/ruff/mypy（本机没装）。
推荐跑：py check.py L14 -v
"""
from __future__ import annotations

import contextlib
import io
import logging
import sys

import pytest
from exercises import (capture_stdout, effective_level, expect_raises,
                       find_bad_function_names, format_log_record, level_name_to_no,
                       measure_runtime, parse_cli_args, parse_pytest_summary,
                       should_log)

SUMMARY = "============ 5 passed, 2 failed, 1 error, 4 skipped in 0.31s ============"


def _greet(who: str = "world") -> None:
    print(f"你好, {who}")


def _boom() -> None:
    raise RuntimeError("炸了")


def _print_then_boom(text: str) -> None:
    print(text)
    raise RuntimeError("打印完还是炸")


def _wrong_type() -> None:
    raise TypeError("类型不对")


def _mixed_source() -> str:
    return (
        "def CalcSum(a, b):\n"        # 1 大写开头 → 违规
        "    return a + b\n"
        "\n"
        "def _helper():\n"            # 4 一个前导下划线 → 合法
        "    pass\n"
        "\n"
        "async def doThing():\n"      # 7 async 也要查 → 违规
        "    pass\n"
        "\n"
        "def ok_2_name():\n"          # 10 数字和下划线都合法
        "    pass\n"
    )


# ---------- 级别名与阈值 ----------

def test_01_level_name_to_no_known_names():
    got = {name: level_name_to_no(name) for name in
           ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")}
    assert got == {"DEBUG": 10, "INFO": 20, "WARNING": 30,
                   "ERROR": 40, "CRITICAL": 50}, "五个内置级别名要逐个对上数字"
    assert level_name_to_no("NOTSET") == 0


def test_02_level_name_to_no_rejects_unrecognized_names():
    for bad in ("info", "Warning", "FOO", ""):
        with pytest.raises(ValueError):
            level_name_to_no(bad), f"getLevelName 认不出来时返回**字符串**，必须转成 ValueError：{bad!r}"


def test_03_should_log_uses_greater_or_equal():
    assert should_log(logging.WARNING, logging.WARNING) is True, "等于阈值也要输出"
    assert should_log(logging.ERROR, logging.WARNING) is True
    assert should_log(logging.INFO, logging.WARNING) is False, "低于阈值才丢弃"
    assert should_log(logging.DEBUG, logging.NOTSET) is True, "logger 是 NOTSET(0) 时全放行"


def test_04_effective_level_follows_inheritance():
    assert effective_level(None, logging.ERROR) == logging.ERROR, "没设就继承父级"
    assert effective_level(logging.NOTSET, logging.ERROR) == logging.ERROR, "NOTSET 等于没设"
    assert effective_level(logging.DEBUG, logging.ERROR) == logging.DEBUG, (
        "子 logger 显式设了就用自己那份，即使比父级更低")
    assert effective_level(logging.CRITICAL, logging.ERROR) == logging.CRITICAL


# ---------- pytest 摘要 ----------

def test_05_parse_pytest_summary_reads_all_four_counts():
    assert parse_pytest_summary(SUMMARY) == {
        "passed": 5, "failed": 2, "errors": 1, "skipped": 4}, "四个键一个都不能少"


def test_06_parse_pytest_summary_defaults_missing_to_zero():
    assert parse_pytest_summary("============ 3 passed in 0.01s ============") == {
        "passed": 3, "failed": 0, "errors": 0, "skipped": 0}, "摘要里没写的就是 0，不是缺键"
    assert parse_pytest_summary("no tests ran in 0.00s") == {
        "passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    assert parse_pytest_summary("=== 12 failed, 1 error in 2.5s ===")["failed"] == 12, (
        "两位数也要读对")


# ---------- 日志渲染 ----------

def test_07_format_log_record_matches_template():
    assert format_log_record("app", logging.WARNING, "磁盘不足") == "WARNING|app|磁盘不足"
    assert format_log_record("my.module", logging.INFO, "启动完成") == "INFO|my.module|启动完成", (
        "levelname 由级别数字换算，name 原样带上")


def test_08_format_log_record_with_unregistered_level_number():
    assert format_log_record("app", 25, "boom") == "Level 25|app|boom", (
        "没注册过的数字不报错，getLevelName 兜底成 'Level 25'")


# ---------- argparse ----------

def test_09_parse_cli_args_uses_defaults():
    assert parse_cli_args([]) == {"name": "world", "count": 1, "verbose": False}, (
        "不给参数时三个默认值要齐")


def test_10_parse_cli_args_accepts_long_and_short_flags():
    got = parse_cli_args(["--name", "Python", "-c", "3", "--verbose"])
    assert got == {"name": "Python", "count": 3, "verbose": True}
    assert isinstance(got["count"], int), "count 必须被 type=int 转换过，不是字符串 '3'"
    again = parse_cli_args(["-n", "Go", "-v"])
    assert again["name"] == "Go" and again["verbose"] is True and again["count"] == 1


def test_11_parse_cli_args_exits_on_bad_input():
    for argv in (["--count", "abc"], ["--nope"], ["extra-positional"]):
        buffer = io.StringIO()
        with pytest.raises(SystemExit), contextlib.redirect_stderr(buffer):
            parse_cli_args(argv), f"argparse 报错走 SystemExit，不是 ValueError：{argv}"
        assert buffer.getvalue(), "argparse 会把用法说明打到 stderr"


# ---------- 自己实现 raises ----------

def test_12_expect_raises_returns_exception_message():
    assert expect_raises(_boom, RuntimeError) == "炸了", "把异常消息交还给调用方断言"
    assert expect_raises(_boom, Exception) == "炸了", "父类也应接住子类异常"


def test_13_expect_raises_fails_when_nothing_raised():
    with pytest.raises(AssertionError):
        expect_raises(lambda: None, RuntimeError), "没抛异常就是测试失败，不能静默返回 None"


def test_14_expect_raises_lets_other_exceptions_escape():
    message = expect_raises(lambda: int("x"), ValueError)
    assert "invalid literal" in message, "类型对得上时返回异常消息，不再往外抛"
    with pytest.raises(TypeError):
        expect_raises(_wrong_type, ValueError)      # 抛错类型 → 原样冒出去，不许吞


# ---------- 抓 stdout ----------

def test_15_capture_stdout_returns_text_and_result():
    text, result = capture_stdout(_greet, "关羽")
    assert text == "你好, 关羽\n", "print 的换行要留着"
    assert result is None, "返回值也要带出来（_greet 没有 return）"


def test_16_capture_stdout_restores_stream_on_error():
    before = sys.stdout
    with pytest.raises(RuntimeError):
        capture_stdout(_print_then_boom, "一半输出")
    assert sys.stdout is before, "异常路径也必须把 stdout 还回去，否则后面所有测试串味"
    text, _ = capture_stdout(print, "完整一行")
    assert text == "完整一行\n", "上一次失败后函数还能正常用"


# ---------- timeit ----------

def test_17_measure_runtime_returns_per_call_seconds_and_validates():
    cost = measure_runtime("x = 1 + 1", 20)
    assert isinstance(cost, float) and cost >= 0.0
    assert cost < 1.0, "单次赋值不可能慢到一秒，多半是忘了除以 number"
    with pytest.raises(ValueError):
        measure_runtime("x = 1", 0), "number<=0 要拦住，别算出 0 秒的假结论"
    with pytest.raises(ValueError):
        measure_runtime("x = 1", -5)
    with pytest.raises(SyntaxError):
        measure_runtime("def f(:", 10), "语法错误原样抛出"


# ---------- 迷你 linter ----------

def test_18_find_bad_function_names_reports_line_numbers_in_order():
    assert find_bad_function_names(_mixed_source()) == [
        "L1: N802 函数名应使用 snake_case: CalcSum",
        "L7: N802 函数名应使用 snake_case: doThing",
    ], "只报违规的，按行号升序，async def 也要查"
    assert find_bad_function_names("def __init__(self):\n    pass\n") == [], (
        "多个前导下划线仍算合法")
    assert find_bad_function_names("x = 1\n") == [], "没有函数就是空列表"
    with pytest.raises(SyntaxError):
        find_bad_function_names("def broken("), "源码本身语法错要抛，不许返回空列表糊弄"
