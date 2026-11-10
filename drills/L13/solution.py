# -*- coding: utf-8 -*-
"""L13 参考答案。

别整篇抄 —— 它的价值在于卡住 15 分钟后对照思路。
验证题目本身有没有写错：py check.py L13 --solution

注意：`sqlite3.Cursor` **不支持** `with conn.cursor() as ...`（pymysql 支持，别混用），
这里直接 `conn.cursor()`，连接关闭时游标自然回收。
"""
from __future__ import annotations

import csv
import io
import re
import sqlite3
from typing import Any

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def add_student(conn: sqlite3.Connection, name: str, score: float) -> int:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO student (name, score) VALUES (?, ?)", (name, score))
    new_id = cursor.lastrowid
    conn.commit()                       # 不提交 = 事务没结束，别人看不见
    return int(new_id)


def find_by_name(conn: sqlite3.Connection, name: str) -> dict[str, Any] | None:
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, score FROM student WHERE name = ?", (name,))
    row = cursor.fetchone()             # 没匹配时是 None，不是 IndexError
    if row is None:
        return None
    columns = [meta[0] for meta in cursor.description]
    return dict(zip(columns, row))


def rows_to_dicts(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(sql, params)
    columns = [meta[0] for meta in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def count_students(conn: sqlite3.Connection) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM student")
    return int(cursor.fetchone()[0])


def avg_score(conn: sqlite3.Connection) -> float | None:
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(score) FROM student")
    value = cursor.fetchone()[0]        # 0 行时 SQL NULL → Python None
    return None if value is None else float(value)


def enable_dict_rows(conn: sqlite3.Connection) -> None:
    def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict[str, Any]:
        return {column[0]: value for column, value in zip(cursor.description, row)}

    conn.row_factory = dict_factory     # 连接级设置，之后每条语句都走它


def build_in_clause(column: str, values: list[Any]) -> tuple[str, tuple]:
    if not _IDENTIFIER.match(column):
        raise ValueError(f"非法列名：{column!r}")   # 标识符不能参数化，只能白名单
    if not values:
        return "WHERE 1 = 0", ()
    placeholders = ", ".join("?" * len(values))
    return f"WHERE {column} IN ({placeholders})", tuple(values)


def transfer_score(conn: sqlite3.Connection, src_id: int, dst_id: int, amount: float) -> None:
    if amount <= 0:
        raise ValueError(f"转账金额必须为正数，收到 {amount}")
    with conn:                          # 正常结束提交，抛异常自动回滚
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE student SET score = score - ? WHERE id = ? AND score >= ?",
            (amount, src_id, amount))
        if cursor.rowcount != 1:        # 余额判断交给 SQL，别"先查再改"
            raise ValueError(f"{src_id} 不存在或余额不足")
        cursor.execute("UPDATE student SET score = score + ? WHERE id = ?",
                       (amount, dst_id))
        if cursor.rowcount != 1:
            raise ValueError(f"{dst_id} 不存在")


def upsert_student(conn: sqlite3.Connection, name: str, score: float) -> int:
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO student (name, score) VALUES (?, ?) "
        "ON CONFLICT(name) DO UPDATE SET score = excluded.score",
        (name, score))
    cursor.execute("SELECT id FROM student WHERE name = ?", (name,))
    row_id = int(cursor.fetchone()[0])
    conn.commit()
    return row_id


def load_csv_into_db(conn: sqlite3.Connection, csv_text: str) -> int:
    records: list[tuple[str, float]] = []
    with io.StringIO(csv_text, newline="") as buffer:
        for row in csv.DictReader(buffer):
            if not row.get("name") or row.get("score") in (None, ""):
                raise ValueError(f"脏数据，缺 name/score：{row}")
            try:
                score = float(row["score"])
            except ValueError as err:
                raise ValueError(f"score 不是数字：{row['score']!r}") from err
            records.append((str(row["name"]), score))
    before = conn.total_changes
    cursor = conn.cursor()
    cursor.executemany(                 # 批量：一次把参数序列喂进去
        "INSERT OR IGNORE INTO student (name, score) VALUES (?, ?)", records)
    conn.commit()
    return conn.total_changes - before  # 被 IGNORE 跳过的不算新增
