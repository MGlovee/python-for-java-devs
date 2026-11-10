# -*- coding: utf-8 -*-
"""L13 完整样例 —— 直接跑：py drills/L13/worked_example.py

一条最小 ETL：CSV 文本 → 参数化批量入库 → 查询（行工厂出字典）→ 事务转账 → 落盘验证。
数据库文件写在 tempfile.mkdtemp() 里，跑完删掉，仓库不留 .db。
"""
from __future__ import annotations

import csv
import io
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CSV_TEXT = """name,score
关羽,90
张飞,50
赵云,95
马超,88
"""

SCHEMA = """
CREATE TABLE student (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL UNIQUE,
    score REAL NOT NULL
);
"""


def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    """行工厂：让 fetchone/fetchall 直接给你字典，而不是靠下标猜列。"""
    return {column[0]: value for column, value in zip(cursor.description, row)}


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = dict_factory
    conn.execute("PRAGMA foreign_keys = ON")     # sqlite 默认不开外键，要手动打开
    return conn


def load_students(conn: sqlite3.Connection, text: str) -> int:
    """批量插入用 executemany；同名重复用 OR IGNORE 跳过。"""
    rows = []
    with io.StringIO(text, newline="") as buffer:
        for record in csv.DictReader(buffer):
            rows.append((record["name"], float(record["score"])))
    before = conn.total_changes
    cursor = conn.cursor()
    cursor.executemany("INSERT OR IGNORE INTO student (name, score) VALUES (?, ?)", rows)
    conn.commit()                                # 忘了 commit，数据不会落盘
    return conn.total_changes - before


def top_students(conn: sqlite3.Connection, threshold: float) -> list[dict]:
    """参数化查询：值走 ?，永远不要把值拼进 SQL 字符串。"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, score FROM student WHERE score >= ? "
        "ORDER BY score DESC LIMIT ?", (threshold, 3))
    return cursor.fetchall()


def transfer(conn: sqlite3.Connection, src: str, dst: str, amount: float) -> None:
    """`with conn:` = 正常结束提交、抛异常回滚，等价于 Java 的 @Transactional。"""
    with conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE student SET score = score - ? "
                       "WHERE name = ? AND score >= ?", (amount, src, amount))
        if cursor.rowcount != 1:
            raise ValueError(f"{src} 分数不足 {amount}，整笔回滚")
        cursor.execute("UPDATE student SET score = score + ? WHERE name = ?",
                       (amount, dst))


def build_in_clause(column: str, values: list[int]) -> tuple[str, tuple]:
    """IN 的占位符个数要跟值的个数一致；列名不能参数化，只能白名单校验。"""
    if not column.isidentifier():
        raise ValueError(f"非法列名 {column!r}")
    return f"WHERE {column} IN ({', '.join('?' * len(values))})", tuple(values)


def main() -> None:
    folder = Path(tempfile.mkdtemp(prefix="l13_"))
    db_file = folder / "school.db"
    conn = connect(db_file)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
        print(f"新建库 {db_file.name}，导入 {load_students(conn, CSV_TEXT)} 行")

        print("85 分以上：", [(row["name"], row["score"]) for row in top_students(conn, 85)])

        sql, params = build_in_clause("id", [1, 3])
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM student {sql}", params)
        print("IN 查询：", [row["name"] for row in cursor.fetchall()])

        transfer(conn, "关羽", "张飞", 20.0)
        cursor.execute("SELECT name, score FROM student WHERE name IN ('关羽', '张飞')")
        print("转账后：", [(row["name"], row["score"]) for row in cursor.fetchall()])

        try:
            transfer(conn, "赵云", "马超", 1000.0)
        except ValueError as err:
            print("预期失败：", err)
        cursor.execute("SELECT score FROM student WHERE name = '赵云'")
        print("回滚验证，赵云仍是：", cursor.fetchone()["score"])

        # 注入尝试：这串东西只会被当成一个"查不到的姓名"，不会改变 SQL 结构
        cursor.execute("SELECT COUNT(*) AS total FROM student WHERE name = ?",
                       ("' OR '1'='1",))
        print("注入串当值处理，命中行数：", cursor.fetchone()["total"])
        print("落盘文件大小：", db_file.stat().st_size, "字节")
    finally:
        conn.close()
        shutil.rmtree(folder, ignore_errors=True)


if __name__ == "__main__":
    main()
