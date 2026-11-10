# -*- coding: utf-8 -*-
"""L06 判分用例。别改这个文件 —— 它就是考官。

单独跑：py -m pytest drills/L06 -q    （装了 pytest 才有效）
推荐跑：py check.py L06 -v            （零依赖）
"""
import pytest
from exercises import (ParseError, call_safely, first_existing, ignore,
                       parse_config, read_and_close, safe_get, session,
                       sum_ints, to_int, try_divide)


class FakeStream:
    """只实现 read/close 的假文件对象，用来考 contextlib.closing。"""

    def __init__(self, text: str):
        self._buf = text
        self.closed = False

    def read(self) -> str:
        return self._buf

    def close(self) -> None:
        self.closed = True


def test_01_safe_get_in_range():
    assert safe_get([1, 2, 3], 0) == 1
    assert safe_get([1, 2, 3], 2) == 3


def test_02_safe_get_negative_index():
    # Python 原生支持负下标，EAFP 写法天然保留这个行为
    assert safe_get([1, 2, 3], -1) == 3, "负下标应按 Python 原生行为取末尾元素"


def test_03_safe_get_out_of_range():
    assert safe_get([1, 2, 3], 99) is None
    assert safe_get([], 0) is None, "空列表任何下标都该返回 None，不许抛 IndexError"


def test_04_to_int_ok():
    assert to_int("42") == 42
    assert to_int("-7") == -7


def test_05_to_int_raises_chained():
    assert issubclass(ParseError, ValueError), "ParseError 应继承自 ValueError"
    with pytest.raises(ParseError) as exc_info:
        to_int("abc")
    assert isinstance(exc_info.value.__cause__, ValueError), (
        "必须用 raise ParseError(...) from err 保留原始 ValueError 作为 __cause__")


def test_06_try_divide_ok_uses_else():
    audit: list[str] = []
    assert try_divide(6, 3, audit) == 2.0
    assert audit == ["ok", "end"], "成功走 else 记 ok，finally 记 end"


def test_07_try_divide_zero_and_type_error():
    audit1: list[str] = []
    assert try_divide(1, 0, audit1) is None
    assert audit1 == ["error", "end"], "除零被 except 捕获，finally 仍要执行"
    audit2: list[str] = []
    assert try_divide("a", 2, audit2) is None
    assert audit2 == ["error", "end"], "str/int 的 TypeError 同样要捕获"


def test_08_first_existing():
    assert first_existing({"b": 2, "c": 3}, ["a", "c"]) == 3
    assert first_existing({"b": 2, "c": 3}, ["b", "c"]) == 2, "按 keys 顺序，谁先出现取谁"
    assert first_existing({}, ["x"]) is None


def test_09_ignore_swallows_only_target():
    with ignore(KeyError):
        raise KeyError("miss")          # 应被吞掉，测试继续往下走
    with pytest.raises(ZeroDivisionError):
        with ignore(KeyError):
            1 / 0                       # 类型不匹配的异常必须放行


def test_10_read_and_close():
    stream = FakeStream("hello")
    assert read_and_close(stream) == "hello"
    assert stream.closed is True, "没有 with 协议的对象要用 contextlib.closing 保证关闭"


def test_11_sum_ints_skips_bad():
    assert sum_ints(["1", "2", "x", "3"]) == 6
    assert sum_ints([]) == 0
    assert sum_ints(["a", "b"]) == 0, "全部非法时和为 0，不许抛异常"


def test_12_call_safely_success_and_failure():
    result, err = call_safely(lambda: 7)
    assert (result, err) == (7, None)
    result, err = call_safely(lambda: int("x"))
    assert result is None
    assert isinstance(err, ValueError), "要把异常对象本身带回来，不是消息字符串"


def test_13_call_safely_does_not_swallow_base_exception():
    def interrupt():
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        call_safely(interrupt)


def test_14_parse_config_ok():
    got = parse_config(["host=127.0.0.1", "port=8080", "url=http://a/?k=1"])
    assert got == {"host": "127.0.0.1", "port": "8080",
                   "url": "http://a/?k=1"}, "只按第一个 = 分割，值里的 = 原样保留"


def test_15_parse_config_reports_line_number():
    with pytest.raises(ValueError) as exc_info:
        parse_config(["a=1", "garbage", "b=2"])
    assert "2" in str(exc_info.value), "异常消息必须包含出错行的 1 起始行号"
    with pytest.raises(ValueError):
        parse_config(["=novalue"])


def test_16_session_normal():
    log: list[str] = []
    with session(log):
        log.append("body")
    assert log == ["open", "body", "close"]


def test_17_session_still_closes_on_exception():
    log: list[str] = []
    # 注意用 ValueError 而不是 RuntimeError 测传播 —— NotImplementedError 继承自
    # RuntimeError，未做的空工作表会被 pytest.raises(RuntimeError) 误吞成"通过"。
    with pytest.raises(ValueError):
        with session(log):
            raise ValueError("boom")
    assert log == ["open", "close"], "块内抛异常时 close 仍要记录，且异常不许被吞"
