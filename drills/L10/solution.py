# -*- coding: utf-8 -*-
"""L10 参考答案。

别整篇抄 —— 它的价值在于卡住 15 分钟后对照思路。
验证题目本身有没有写错：py check.py L10 --solution
"""
from __future__ import annotations

import csv
import datetime
import io
import json
from pathlib import Path, PurePath
from typing import Any


def read_text_lines(path: str, encoding: str = "utf-8") -> list[str]:
    # 文本模式 + 显式 encoding；splitlines() 顺手把 \r\n / \n / \r 全吃掉
    with open(path, "r", encoding=encoding) as file:
        return file.read().splitlines()


def split_path(path: str) -> tuple[str, str, str]:
    pure = PurePath(path)
    return pure.name, pure.stem, pure.suffix


def to_json_string(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)


def _json_default(value: Any) -> Any:
    """json 只认识 dict/list/str/int/float/bool/None，其余都得在这里翻译成它们。"""
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    raise TypeError(f"无法序列化 {type(value).__name__} 对象")


def to_json_with_default(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True,
                      default=_json_default)


def parse_csv_to_dicts(text: str) -> list[dict[str, str]]:
    with io.StringIO(text, newline="") as buffer:
        return [dict(row) for row in csv.DictReader(buffer)]


def write_json_file(path: str, obj: Any) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as file:
        json.dump(obj, file, ensure_ascii=False, indent=2, default=_json_default)


def read_json_file(path: str, encoding: str = "utf-8") -> Any:
    with open(path, "r", encoding=encoding) as file:
        return json.load(file)


def detect_bytes_encoding(raw: bytes) -> str:
    for name in ("utf-8", "gbk"):
        try:
            raw.decode(name)
        except UnicodeDecodeError:
            continue
        return name
    return "unknown"


def copy_file_binary(src: str, dst: str, chunk_size: int = 4096) -> int:
    total = 0
    with open(src, "rb") as reader, open(dst, "wb") as writer:
        while True:
            chunk = reader.read(chunk_size)
            if not chunk:                      # 读到空字节串就是文件尾
                break
            writer.write(chunk)
            total += len(chunk)
    return total


def dict_rows_to_csv(fieldnames: list[str], rows: list[dict[str, str]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames,
                            lineterminator="\n", restval="")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().rstrip("\n")
