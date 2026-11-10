# -*- coding: utf-8 -*-
"""L03 练习工作表 —— 字符串方法 / f-string 格式化 / 正则 / 日期。

判分：  py check.py L03 -v
看答案：py check.py L03 --solution   （建议卡住 15 分钟以上再看）

模块已经替你 import 好了，缺什么自己加（只许用标准库）。
"""
from __future__ import annotations

import re  # noqa: F401  正则
from datetime import date, datetime  # noqa: F401  日期时间


# ---------- 第一组：挖空题（有提示，照着填） ----------

def slugify(text: str) -> str:
    """把标题转成 URL slug：全小写、忽略首尾空白、把中间连续的空白压成一个 '-'。

    提示：`lower()` → `split()`（不传参数时按**任意空白**切，且自动丢掉空串）→ `'-'.join(...)`
    >>> slugify('  HelLO   WorLD  ')
    'hello-world'
    """
    raise NotImplementedError


def align_columns(rows: list[list[str]], sep: str = ' | ') -> str:
    """把二维列表排成一张文本表，返回字符串（行与行之间用 '\n'）。

    规则：每列宽度 = 该列所有单元格的最长长度；除**最后一列**外都用空格右对齐补齐
    （最后一列不补，免得行尾留一串看不见的空格）。
    行与行列数不一致时抛 ValueError。
    >>> align_columns([['a', 'bb'], ['ccc', 'd']])
    'a   | bb\nccc | d'
    """
    raise NotImplementedError


def money_format(cents: int) -> str:
    """把"分"转成带千分位的金额字符串：123456 -> '1,234.56'。

    cents 为负数时抛 ValueError。
    提示：先 `divmod(cents, 100)` 拿到 (元, 零头)，再用 f-string 的 `:,` 和 `:02d`。
    >>> money_format(123456)
    '1,234.56'
    """
    raise NotImplementedError


def is_valid_username(name: str) -> bool:
    """校验用户名：首字符必须是字母，总长 6~20，只允许字母、数字、下划线。

    提示：`re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{5,19}', name)` 再取真假。
    >>> is_valid_username('jackfrued'), is_valid_username('1jackfrued')
    (True, False)
    """
    raise NotImplementedError


def extract_phones(text: str) -> list[str]:
    r"""从任意文本里抽出所有中国大陆手机号（11 位、1 开头、第二位 3~9）。

    要求：**前后不能紧挨着数字** —— 一串 12 位数字里不许抽出 11 位手机号。
    返回按出现顺序排列的列表。
    提示：`re.findall(r'(?<!\d)1[3-9]\d{9}(?!\d)', text)`，前后都别用 `\b`。
    >>> extract_phones('拨110，或打 13512346789 找我')
    ['13512346789']
    """
    raise NotImplementedError


def days_between(start: str, end: str) -> int:
    """两个 'YYYY-MM-DD' 日期相差几天（end - start，可以为负，同一天为 0）。

    提示：`datetime.strptime(s, '%Y-%m-%d')` 解析成 datetime，两个 datetime 相减得
    timedelta，取它的 `.days`。格式符和 Java 的 `yyyy-MM-dd` 完全不是一套字母。
    >>> days_between('2024-01-01', '2024-01-31')
    30
    """
    raise NotImplementedError


# ---------- 第二组：只给需求（独立写） ----------

def mask_sensitive(text: str) -> str:
    """把文本里的手机号打成掩码：保留前 3 位和后 4 位，中间 4 位换成 '****'。

    例：'客服 13800138000' -> '客服 138****8000'
    要求：不是 11 位的数字串（如 12 位订单号）必须原样保留，不能误伤。
    提示：`re.sub` 用捕获组 + `r'\1****\2'` 引用；别写成 findall 再拼回去。
    """
    raise NotImplementedError


def word_frequencies(text: str) -> dict[str, int]:
    """统计英文单词词频：只认连续的字母串（`[A-Za-z]+`），统一转小写后计数。

    数字、中文、标点都不是单词，它们只起分隔作用。
    例：word_frequencies('Cat, dog! cat') == {'cat': 2, 'dog': 1}
    要求：不许用 collections.Counter（先手写 dict 版本）。
    """
    raise NotImplementedError


def month_last_day(year: int, month: int) -> str:
    """返回该年该月最后一天的 'YYYY-MM-DD' 字符串。

    month 不在 1~12 内抛 ValueError。闰年 2 月必须是 '29'。
    提示：标准库 `calendar.monthrange(year, month)[1]` 直接给天数；
    或 `date(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1)`。
    要求：不许手写闰年判断。
    """
    raise NotImplementedError


def count_business_days(start: str, end: str) -> int:
    """统计 [start, end] 闭区间内的工作日（周一到周五）天数。

    start 晚于 end 时返回 0。两个参数都是 'YYYY-MM-DD'。
    提示：`date.weekday()` 周一是 0、周日是 6；用 `timedelta(days=1)` 一天天往前走。
    例：2024-01-01 是周一，2024-01-06/07 是周六周日，
        count_business_days('2024-01-01', '2024-01-07') == 5
    """
    raise NotImplementedError
