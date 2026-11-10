# -*- coding: utf-8 -*-
"""L03 参考答案。

别整篇抄 —— 它的价值在于卡住 15 分钟后对照思路。
验证题目本身有没有写错：py check.py L03 --solution
"""
from __future__ import annotations

import calendar
import re
from datetime import datetime, timedelta

PHONE_RE = re.compile(r'(?<!\d)1[3-9]\d{9}(?!\d)')


def slugify(text: str) -> str:
    return '-'.join(text.lower().split())


def align_columns(rows: list[list[str]], sep: str = ' | ') -> str:
    if not rows:
        return ''
    ncols = len(rows[0])
    for row in rows:
        if len(row) != ncols:
            raise ValueError(f'各行列数必须一致，第一行 {ncols} 列，收到 {len(row)} 列')
    widths = [max(len(row[i]) for row in rows) for i in range(ncols)]
    lines = []
    for row in rows:
        cells = [row[i].ljust(widths[i]) for i in range(ncols - 1)]
        cells.append(row[-1])          # 最后一列不补，行尾不留空白
        lines.append(sep.join(cells))
    return '\n'.join(lines)


def money_format(cents: int) -> str:
    if cents < 0:
        raise ValueError(f'金额不能为负，收到 {cents}')
    yuan, rest = divmod(cents, 100)
    return f'{yuan:,}.{rest:02d}'


def is_valid_username(name: str) -> bool:
    return re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{5,19}', name) is not None


def extract_phones(text: str) -> list[str]:
    return PHONE_RE.findall(text)


def days_between(start: str, end: str) -> int:
    fmt = '%Y-%m-%d'
    return (datetime.strptime(end, fmt) - datetime.strptime(start, fmt)).days


def mask_sensitive(text: str) -> str:
    return re.sub(r'(?<!\d)(1[3-9]\d)\d{4}(\d{4})(?!\d)', r'\1****\2', text)


def word_frequencies(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for word in re.findall(r'[A-Za-z]+', text):
        key = word.lower()
        counts[key] = counts.get(key, 0) + 1
    return counts


def month_last_day(year: int, month: int) -> str:
    if not 1 <= month <= 12:
        raise ValueError(f'月份必须在 1..12 之间，收到 {month}')
    last = calendar.monthrange(year, month)[1]
    return f'{year:04d}-{month:02d}-{last:02d}'


def count_business_days(start: str, end: str) -> int:
    fmt = '%Y-%m-%d'
    first = datetime.strptime(start, fmt).date()
    last = datetime.strptime(end, fmt).date()
    if first > last:
        return 0
    total = 0
    cursor = first
    while cursor <= last:                     # date 不可变，每次得到新对象
        if cursor.weekday() < 5:              # 周一=0 … 周五=4，周六周日跳过
            total += 1
        cursor += timedelta(days=1)
    return total
