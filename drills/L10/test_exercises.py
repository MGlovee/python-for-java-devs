# -*- coding: utf-8 -*-
"""L10 判分用例。别改这个文件 —— 它就是考官。

全部离线，落盘的文件都写在 `tempfile.mkdtemp()` 里，测完立刻删。
单独跑：py -m pytest drills/L10 -q    （装了 pytest 才有效）
推荐跑：py check.py L10 -v            （零依赖）
"""
from __future__ import annotations

import datetime
import json
import shutil
import tempfile
from contextlib import contextmanager

import pytest
from exercises import (copy_file_binary, detect_bytes_encoding, dict_rows_to_csv,
                       parse_csv_to_dicts, read_json_file, read_text_lines,
                       split_path, to_json_string, to_json_with_default,
                       write_json_file)


@contextmanager
def temp_dir():
    """临时目录，出了 with 就删干净 —— 仓库里不许留下任何产物。"""
    path = tempfile.mkdtemp(prefix="l10_")
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def write_text(path: str, text: str, encoding: str = "utf-8") -> None:
    with open(path, "w", encoding=encoding, newline="\n") as file:
        file.write(text)


def test_01_read_text_lines_strips_newlines():
    with temp_dir() as folder:
        path = folder + "/poem.txt"
        write_text(path, "第一行\n第二行\n")
        assert read_text_lines(path) == ["第一行", "第二行"], "行尾换行符要去掉"
        blank = folder + "/blank.txt"
        write_text(blank, "a\n\nb\n")
        assert read_text_lines(blank) == ["a", "", "b"], "空行要占一个元素，不能顺手 strip 掉"


def test_02_read_text_lines_crlf():
    with temp_dir() as folder:
        path = folder + "/crlf.txt"
        with open(path, "wb") as file:
            file.write("a\r\nb\r\n".encode("utf-8"))
        assert read_text_lines(path) == ["a", "b"], "Windows 的 \\r\\n 也不该留下 \\r"


def test_03_split_path_windows():
    assert split_path(r"C:\data\scores.csv") == ("scores.csv", "scores", ".csv")
    assert split_path("notes.md") == ("notes.md", "notes", ".md")


def test_04_split_path_edges():
    assert split_path("archive.tar.gz") == ("archive.tar.gz", "archive.tar", ".gz"), (
        "suffix 只取最后一段")
    assert split_path("README") == ("README", "README", ""), "没有扩展名给空串"


def test_05_to_json_string_keeps_chinese():
    text = to_json_string({"姓名": "骆昊"})
    assert "骆昊" in text, "ensure_ascii=False 才能输出中文原样"
    assert "\\u" not in text, "不许出现 \\uXXXX 转义"
    assert text == '{\n  "姓名": "骆昊"\n}'


def test_06_to_json_string_sorts_keys_and_indents():
    assert to_json_string({"b": 1, "a": 2}) == '{\n  "a": 2,\n  "b": 1\n}', "键按字母序"
    assert to_json_string({"cars": [{"brand": "BMW"}]}) == (
        '{\n  "cars": [\n    {\n      "brand": "BMW"\n    }\n  ]\n}')


def test_07_to_json_with_default_handles_set():
    text = to_json_with_default({"tags": {"c", "a", "b"}})
    assert json.loads(text) == {"tags": ["a", "b", "c"]}, "set 要变成排序后的列表"


def test_08_to_json_with_default_handles_dates():
    payload = {"day": datetime.date(2024, 5, 6),
               "at": datetime.datetime(2024, 5, 6, 7, 8, 9)}
    assert json.loads(to_json_with_default(payload)) == {
        "day": "2024-05-06", "at": "2024-05-06T07:08:09"}


def test_09_to_json_with_default_rejects_unknown():
    with pytest.raises(TypeError):
        to_json_with_default({"bad": object()})


def test_10_parse_csv_to_dicts_basic():
    rows = parse_csv_to_dicts("姓名,语文\n关羽,98\n张飞,86\n")
    assert rows == [{"姓名": "关羽", "语文": "98"}, {"姓名": "张飞", "语文": "86"}]
    assert all(isinstance(v, str) for v in rows[0].values()), "csv 读出来全是字符串"
    assert parse_csv_to_dicts("a,b\n") == [], "只有表头时是空列表"


def test_11_parse_csv_to_dicts_quoted():
    rows = parse_csv_to_dicts('name,note\n"张三, Jr.","他说""很好"""\n')
    assert len(rows) == 1, "引号里的逗号不是分隔符"
    assert rows[0]["name"] == "张三, Jr."
    assert rows[0]["note"] == '他说"很好"', "两个连续引号是一个引号"


def test_12_json_round_trip_in_temp_file():
    data = {"姓名": "骆昊", "cars": [{"brand": "BMW", "max_speed": 240}]}
    with temp_dir() as folder:
        path = folder + "/data.json"
        write_json_file(path, data)
        assert read_json_file(path) == data, "写出去再读回来必须完全相等"
        with open(path, "rb") as file:
            assert "骆昊" in file.read().decode("utf-8"), "文件本身应是 UTF-8 中文"
        write_json_file(path, {"v": 2})
        assert read_json_file(path) == {"v": 2}, "重复写是覆盖不是追加"


def test_13_read_json_file_missing_raises():
    with temp_dir() as folder:
        with pytest.raises(FileNotFoundError):
            read_json_file(folder + "/not_here.json")


def test_14_detect_bytes_encoding():
    assert detect_bytes_encoding("中文测试".encode("utf-8")) == "utf-8"
    assert detect_bytes_encoding("成绩表".encode("gbk")) == "gbk", "Windows 默认编码就是它"
    assert detect_bytes_encoding(b"\xff\xff\xff\xff") == "unknown"
    assert detect_bytes_encoding(b"plain ascii") == "utf-8", "纯 ASCII 也是合法 UTF-8"


def test_15_read_gbk_file_needs_explicit_encoding():
    with temp_dir() as folder:
        path = folder + "/gbk.txt"
        write_text(path, "成绩\n语文\n", encoding="gbk")
        assert read_text_lines(path, encoding="gbk") == ["成绩", "语文"]
        with pytest.raises(UnicodeDecodeError):
            read_text_lines(path), "按 utf-8 读 GBK 文件必然炸 —— 永远显式写 encoding"


def test_16_copy_file_binary_is_byte_exact():
    payload = bytes(range(256)) * 40          # 含一堆非法 UTF-8 字节
    with temp_dir() as folder:
        src, dst = folder + "/src.bin", folder + "/dst.bin"
        with open(src, "wb") as file:
            file.write(payload)
        written = copy_file_binary(src, dst, chunk_size=100)
        assert written == len(payload), "返回值是复制的总字节数"
        with open(dst, "rb") as file:
            assert file.read() == payload, "二进制复制不许改动任何字节"


def test_17_copy_file_binary_replaces_target():
    with temp_dir() as folder:
        src, dst = folder + "/a.txt", folder + "/b.txt"
        write_text(src, "hello\n")
        with open(dst, "wb") as file:
            file.write(b"old content that is longer")
        assert copy_file_binary(src, dst) == 6, "目标文件已存在时要整体覆盖"
        with open(dst, "rb") as file:
            assert file.read() == b"hello\n"


def test_18_dict_rows_to_csv():
    text = dict_rows_to_csv(["姓名", "备注"],
                            [{"姓名": "张三, Jr.", "备注": '他说"好"'},
                             {"姓名": "李四", "备注": ""}])
    lines = text.split("\n")
    assert lines[0] == "姓名,备注"
    assert lines[1] == '"张三, Jr.","他说""好"""', "该加引号时要加，且引号要翻倍转义"
    assert lines[2] == "李四,", "空串直接留空，不要写成 None"
    assert not text.endswith("\n"), "末尾不要多余换行"
    round_trip = [{"a": "1", "b": "x,y"}, {"a": "2", "b": '"z"'}]
    assert parse_csv_to_dicts(dict_rows_to_csv(["a", "b"], round_trip) + "\n") == round_trip

