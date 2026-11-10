# -*- coding: utf-8 -*-
"""L03 判分用例。别改这个文件 —— 它就是考官。

单独跑：py -m pytest drills/L03 -q    （装了 pytest 才有效）
推荐跑：py check.py L03 -v            （零依赖）
"""
import pytest
from exercises import (align_columns, count_business_days, days_between,
                       extract_phones, is_valid_username, mask_sensitive,
                       money_format, month_last_day, slugify, word_frequencies)


def test_01_slugify_basic():
    assert slugify('  HelLO   WorLD  ') == 'hello-world', (
        "小写 + 去首尾空白 + 连续空白压成一个 '-'")
    assert slugify('Python 3.14 release notes') == 'python-3.14-release-notes'


def test_02_slugify_tabs_and_empty():
    assert slugify('a\tb\nc  d') == 'a-b-c-d', (
        "split() 不带参数按任意空白切，Tab 和换行一样是分隔符")
    assert slugify('') == '', "空串切出来是空列表，join 得空串"
    assert slugify('     ') == '', "全是空白也不能留下 '-' 这种脏字符"


def test_03_align_columns_table():
    rows = [['name', 'score'], ['tom', '9'], ['jerry', '10']]
    assert align_columns(rows) == (
        'name  | score\n'
        'tom   | 9\n'
        'jerry | 10'), "第一列宽 5，最后一列不补空格"


def test_04_align_columns_custom_sep_and_ragged():
    assert align_columns([['a', 'bb'], ['ccc', 'd']], sep=' / ') == (
        'a   / bb\nccc / d')
    with pytest.raises(ValueError):
        align_columns([['a', 'b'], ['c']])


def test_05_money_format_thousands():
    assert money_format(123456) == '1,234.56'
    assert money_format(5) == '0.05', "零头要补成两位"
    assert money_format(0) == '0.00'
    assert money_format(100000000) == '1,000,000.00', "千分位是每三位一个逗号"


def test_06_money_format_rejects_negative():
    for bad in (-1, -100):
        with pytest.raises(ValueError):
            money_format(bad)


def test_07_username_valid():
    assert is_valid_username('jackfrued')
    assert is_valid_username('ab12_3'), "6 位刚好压线，合法"
    assert is_valid_username('a' * 20), "20 位是上限"


def test_08_username_invalid():
    assert not is_valid_username('abc12'), "5 位太短"
    assert not is_valid_username('1abcde'), "首位必须是字母"
    assert not is_valid_username('a' * 21), "21 位超长"
    assert not is_valid_username('a-b_cdef'), "连字符不在允许字符集里"
    assert not is_valid_username(''), "空串不合法"


def test_09_extract_phones_order():
    text = '联系 13512345678 或 15600001111，座机不是手机号'
    assert extract_phones(text) == ['13512345678', '15600001111'], (
        "按出现顺序返回，findall 给的就是这个顺序")


def test_10_extract_phones_digit_boundary():
    text = '12345678901 和 8135123456789 都不是手机号，但 13800138000 是'
    assert extract_phones(text) == ['13800138000'], (
        "必须用 (?<!\\d) 和 (?!\\d) 卡住两侧，\\b 在数字边界上不好使")
    assert extract_phones('没有号码') == []


def test_11_days_between_all_signs():
    assert days_between('2024-01-01', '2024-01-31') == 30
    assert days_between('2024-03-01', '2024-03-01') == 0
    assert days_between('2023-12-31', '2024-01-01') == 1
    assert days_between('2024-12-31', '2024-01-01') == -365, (
        "2024 是闰年，共 366 天，首尾相差 365 天；倒着传得负数")


def test_12_mask_sensitive_phones():
    assert mask_sensitive('客服 13800138000，备用 13911112222。') == (
        '客服 138****8000，备用 139****2222。'), "留前 3 后 4，中间 4 位变 ****"


def test_13_mask_sensitive_keeps_other_digits():
    text = '订单号 138001380000 与手机号 13800138000 共存'
    assert mask_sensitive(text) == '订单号 138001380000 与手机号 138****8000 共存', (
        "12 位数字整串不许被改动")
    assert mask_sensitive('纯中文没有数字') == '纯中文没有数字'


def test_14_word_frequencies_basic():
    assert word_frequencies('Cat, dog! cat; CAT') == {'cat': 3, 'dog': 1}
    assert word_frequencies('') == {}, "没有单词就是空字典"


def test_15_word_frequencies_splits_on_nonletters():
    assert word_frequencies('hello123world hello') == {'hello': 2, 'world': 1}, (
        "数字不是单词的一部分，它把 hello 和 world 切开了")
    assert word_frequencies('你好 hello 你好') == {'hello': 1}, "中文不算单词"


def test_16_month_last_day():
    assert month_last_day(2024, 2) == '2024-02-29', "闰年 2 月 29 天"
    assert month_last_day(2023, 2) == '2023-02-28'
    assert month_last_day(1900, 2) == '1900-02-28', "能被 100 整除但不能被 400 整除不算闰年"
    assert month_last_day(2024, 1) == '2024-01-31'
    assert month_last_day(2024, 12) == '2024-12-31'
    for bad in (0, 13, -1):
        with pytest.raises(ValueError):
            month_last_day(2024, bad)


def test_17_count_business_days_one_week():
    assert count_business_days('2024-01-01', '2024-01-05') == 5, "周一到周五"
    assert count_business_days('2024-01-01', '2024-01-07') == 5, "周六周日不算"
    assert count_business_days('2024-01-06', '2024-01-07') == 0, "整个周末都不算"
    assert count_business_days('2024-01-03', '2024-01-03') == 1, "闭区间含端点"


def test_18_count_business_days_edges():
    assert count_business_days('2024-01-10', '2024-01-01') == 0, "start 晚于 end 返回 0"
    assert count_business_days('2024-01-01', '2024-01-31') == 23, "2024 年 1 月有 23 个工作日"
