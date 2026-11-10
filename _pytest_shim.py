# -*- coding: utf-8 -*-
"""pytest 的标准库替身。

没装 pytest 时，check.py 会把本模块注册成 sys.modules["pytest"]，
于是练习题里写的 `import pytest` / `pytest.raises(ValueError)` 照样能跑；
装了 pytest 之后，测试文件走的仍是真正的 pytest，两边语法完全一致。

只实现这套练习用得到的极小子集，不是要复刻 pytest。
"""
from __future__ import annotations

from contextlib import suppress as _suppress  # noqa: F401 - 万一哪天要标"允许异常"


class _Raises:
    """用法：with pytest.raises(ValueError): ...

    和 pytest.raises 的差别只有一处：这里不检查 match 正则之外的细节，
    且 `except` 参数必须是一个异常类或异常类元组。
    """

    def __init__(self, expected, match=None):
        self.expected = expected
        self.match = match
        self.value = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            name = getattr(self.expected, "__name__", str(self.expected))
            raise AssertionError(f"期望抛出 {name}，但代码正常返回了")
        if not issubclass(exc_type, self.expected):
            return False  # 让异常原样冒出去，报错信息更诚实
        self.value = exc_val
        if self.match is not None:
            import re
            if not re.search(self.match, str(exc_val)):
                raise AssertionError(
                    f"异常消息 {exc_val!r} 不匹配 {self.match!r}")
        return True


def raises(expected, match=None):
    return _Raises(expected, match)


class _Approx:
    """pytest.approx 的最小版：pytest.approx(3.5, rel=1e-9)"""

    def __init__(self, expected, rel=None, abs=None):  # noqa: A002
        self.expected = expected
        self.rel = rel if rel is not None else 1e-6
        self.abs = abs if abs is not None else 1e-12

    def __eq__(self, other):
        try:
            diff = abs(float(other) - float(self.expected))
        except (TypeError, ValueError):
            return NotImplemented
        tolerance = max(self.abs, self.rel * abs(float(self.expected)))
        return diff <= tolerance

    def __repr__(self):
        return f"approx({self.expected})"


def approx(expected, rel=None, abs=None):  # noqa: A002
    return _Approx(expected, rel, abs)


def skip(reason=""):
    raise _Skipped(reason)


class _Skipped(Exception):
    pass


class mark:  # noqa: N801 - 与 pytest.mark 同名，保持写法一致
    @staticmethod
    def skipif(condition, reason=""):
        if condition:
            raise _Skipped(reason)

    @staticmethod
    def parametrize(argnames, argvalues):  # 本替身不支持参数化，明确告知
        raise NotImplementedError(
            "这个替身不支持 parametrize；请 pip install pytest 后再跑该文件")
