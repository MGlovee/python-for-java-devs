# -*- coding: utf-8 -*-
"""L10 练习工作表 —— 把每个函数里的 `raise NotImplementedError` 删掉，写上你的实现。

本课全部离线：需要落盘的题，测试会用 `tempfile.mkdtemp()` 建临时目录并传绝对路径给你，
不要往仓库里写文件。所有文本读写一律显式 `encoding="utf-8"`。

判分：  py check.py L10 -v
看答案：py check.py L10 --solution   （建议卡住 15 分钟以上再看）
"""
from __future__ import annotations

from typing import Any


# ---------- 第一组：挖空题（有提示，照着填） ----------

def read_text_lines(path: str, encoding: str = "utf-8") -> list[str]:
    """读取文本文件，返回"每一行"的列表，行尾换行符要去掉，行内空格保留。

    提示：`with open(path, "r", encoding=encoding) as file:` + `file.read().splitlines()`
    >>> read_text_lines("x.txt")   # 内容为 "a\\nb\\n" 时
    ['a', 'b']
    """
    raise NotImplementedError


def split_path(path: str) -> tuple[str, str, str]:
    """用 `pathlib` 把路径拆成 (文件名, 主名, 扩展名)，扩展名**带点**，没有则为空串。

    提示：`from pathlib import PureWindowsPath`，它有 `.name` / `.stem` / `.suffix` 三个属性。
    **别用 `Path` / `PurePath`** —— 它们跟随当前操作系统，在 Linux 上会把
    `C:\\data\\scores.csv` 整串当成一个文件名。要处理 Windows 路径就显式用 `PureWindowsPath`。
    >>> split_path(r"C:\\data\\scores.csv")
    ('scores.csv', 'scores', '.csv')
    """
    raise NotImplementedError


def to_json_string(obj: Any) -> str:
    """把对象序列化成 JSON 字符串：中文保持原样（不要 `\\uXXXX`）、缩进 2 空格、键按字母序。

    提示：`json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)`
    """
    raise NotImplementedError


def to_json_with_default(obj: Any) -> str:
    """同 `to_json_string`，但要额外支持两种 json 模块不认的类型：

    - `set` / `frozenset` → 排序后的列表
    - `datetime.date`（含 `datetime.datetime`）→ ISO 字符串
    提示：`json.dumps(..., default=函数)`，default 只在遇到"认不出的对象"时被调用，
    它必须**返回一个可序列化的替身**，遇到连它也不认的对象就原样抛 TypeError。
    """
    raise NotImplementedError


def parse_csv_to_dicts(text: str) -> list[dict[str, str]]:
    """把一段 CSV **文本**（首行是表头）解析成 [{列名: 值}, ...]，值全是字符串。

    提示：标准库 `csv.DictReader` 吃的是"可迭代的行"，`io.StringIO(text)` 正好可以当文件用。
    带引号的字段（如 `"张三, Jr."`）必须按 CSV 规则解析，不许自己 split(",")。
    """
    raise NotImplementedError


def write_json_file(path: str, obj: Any) -> None:
    """把对象以 UTF-8 JSON 写入文件（中文原样、缩进 2），文件已存在则整个覆盖。

    提示：`with open(path, "w", encoding="utf-8") as file:` + `json.dump(...)`
    注意 `dump`（写文件）和 `dumps`（出字符串）只差一个字母。
    """
    raise NotImplementedError


# ---------- 第二组：只给需求（独立写） ----------

def read_json_file(path: str, encoding: str = "utf-8") -> Any:
    """按指定编码读一个 JSON 文件并反序列化成 Python 对象（dict / list / 标量都可能出现）。

    要求：文件不存在时让 `FileNotFoundError` 自然冒出去，不要自己吞掉。
    """
    raise NotImplementedError


def detect_bytes_encoding(raw: bytes) -> str:
    """猜一段字节串是什么编码，返回 `"utf-8"` / `"gbk"` / `"unknown"` 三者之一。

    规则（按顺序判，命中即返回）：
    1. 能按 utf-8 解码 → "utf-8"
    2. 否则能按 gbk 解码 → "gbk"
    3. 否则 → "unknown"
    要求：解码失败抛的是 `UnicodeDecodeError`，别用 try/except Exception 一把抓。
    """
    raise NotImplementedError


def copy_file_binary(src: str, dst: str, chunk_size: int = 4096) -> int:
    """二进制方式把 src 复制成 dst，返回复制的总字节数。

    要求：必须分块读写（一次最多 `chunk_size` 字节），不许 `read()` 一次性读进内存；
    任何字节序列（含非法 UTF-8）都要能原样复制过去。
    """
    raise NotImplementedError


def dict_rows_to_csv(fieldnames: list[str], rows: list[dict[str, str]]) -> str:
    """把 [{列名: 值}, ...] 渲染成 CSV 文本：首行表头，行之间用 \\n，末尾不要多余换行。

    要求：用 `csv.DictWriter`（写进 `io.StringIO`），行结束符指定成 `\\n`；
    字段里出现逗号或引号时交给 csv 模块自动加引号，值缺列时写空串。
    """
    raise NotImplementedError
