# -*- coding: utf-8 -*-
"""L13 练习工作表 —— 把每个函数里的 `raise NotImplementedError` 删掉，写上你的实现。

本课主力是标准库 `sqlite3`（零安装），核心心智只有一条 DB-API 2.0 流水线：
    连接 Connection → 游标 Cursor → execute → fetch* → commit
判分用的表结构（测试已经建好，你只管读写）：

    CREATE TABLE student (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        name  TEXT NOT NULL UNIQUE,
        score REAL NOT NULL
    )

铁律：**值永远走参数占位符 `?`，一次都不许把值拼进 SQL 字符串。**
"""
from __future__ import annotations

import sqlite3
from typing import Any


# ---------- 第一组：挖空题（有提示，照着填） ----------

def add_student(conn: sqlite3.Connection, name: str, score: float) -> int:
    """插入一名学生并提交，返回新行的 `id`。

    提示：`cursor.execute("INSERT INTO student (name, score) VALUES (?, ?)", (name, score))`
          → `cursor.lastrowid`；别忘了 `conn.commit()`（不提交，别的连接看不到）。
    """
    raise NotImplementedError


def find_by_name(conn: sqlite3.Connection, name: str) -> dict[str, Any] | None:
    """按姓名精确查一个人，返回 `{"id":…, "name":…, "score":…}`，查不到返回 None。

    提示：参数化 `WHERE name = ?` + `fetchone()`；`fetchone()` 拿到的是元组，
    要自己按列名组装成 dict（或者用 `cursor.description`）。
    """
    raise NotImplementedError


def rows_to_dicts(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """执行任意 SELECT，把结果行变成 `[{列名: 值}, ...]`（列名来自 `cursor.description`）。

    提示：`cursor.description` 是每列的元组，第 0 项是列名；
          `[dict(zip(names, row)) for row in cursor.fetchall()]`。
          这就是"行工厂"要解决的问题 —— 下一题你会把它做成连接级别的默认行为。
    """
    raise NotImplementedError


def count_students(conn: sqlite3.Connection) -> int:
    """返回学生总数。

    提示：`SELECT COUNT(*) FROM student` 之后 `fetchone()[0]`。别把整表 fetchall 再 len。
    """
    raise NotImplementedError


def avg_score(conn: sqlite3.Connection) -> float | None:
    """返回平均分；**表为空时返回 None**（不要返回 0.0）。

    提示：`SELECT AVG(score) FROM student` 在 0 行时返回 SQL 的 NULL，sqlite3 把它变成 Python 的 None。
    """
    raise NotImplementedError


def enable_dict_rows(conn: sqlite3.Connection) -> None:
    """给连接装上行工厂，让之后所有查询直接返回 dict（键是列名）。

    提示：`conn.row_factory = lambda cursor, row: dict(zip(
              [d[0] for d in cursor.description], row))`
          —— 标准库还有个现成的 `sqlite3.Row`，但那是只读序列，不是 dict，这里要求返回真 dict。
    """
    raise NotImplementedError


# ---------- 第二组：只给需求（独立写） ----------

def build_in_clause(column: str, values: list[Any]) -> tuple[str, tuple]:
    """为 `IN (...)` 生成 (SQL 片段, 参数元组)，永远不把值拼进字符串。

    要求：1) 占位符数量等于值的个数，形如 `WHERE id IN (?, ?)`（列名由调用方给，占位符用 `?`）；
          2) `values` 为空 → 返回 `("WHERE 1 = 0", ())`，让上层查询直接空手而归而不是拼出 `IN ()`；
          3) `column` 只能是合法标识符（字母/数字/下划线，且不以数字开头），否则抛 `ValueError`
             —— 因为**列名没法参数化**，它必须走白名单校验，这是防注入的另一半。
    """
    raise NotImplementedError


def transfer_score(conn: sqlite3.Connection, src_id: int, dst_id: int, amount: float) -> None:
    """把 `amount` 分从 src 转给 dst，两条 UPDATE 必须**原子**生效。

    要求：1) 用 `with conn:`（进去自动开事务，正常结束提交，抛异常自动回滚）；
          2) `amount <= 0`、转出方不存在或余额不足、接收方不存在 → 抛 `ValueError`，
             并且两边分数都不许变化；
          3) 余额判断交给 SQL 做（`WHERE id = ? AND score >= ?` 再看 `rowcount`），
             不要"先 SELECT 再判断再 UPDATE"——那中间有并发窗口。
    """
    raise NotImplementedError


def upsert_student(conn: sqlite3.Connection, name: str, score: float) -> int:
    """有则改、无则增（`name` 上有 UNIQUE 约束），返回该学生的 `id`。

    要求：只用一条写语句完成 upsert（SQLite 3.24+ 支持 `ON CONFLICT(name) DO UPDATE SET …`），
    不许"先查再决定 insert 还是 update"；提交后返回 id。
    """
    raise NotImplementedError


def load_csv_into_db(conn: sqlite3.Connection, csv_text: str) -> int:
    """ETL 最小一步：把 CSV 文本（表头含 `name,score`）批量写进 student 表，返回**新增**行数。

    要求：1) 用标准库 `csv.DictReader` 解析（见 L10），`score` 转成 `float`；
          2) 批量插入用 `executemany`，不要循环 execute 一条条发；
          3) 同名学生重复出现时**跳过而不是报错**（想想 `INSERT OR IGNORE`）；
          4) 行里缺 `name` 或 `score` 时抛 `ValueError`，消息内容随便写；
          5) 提交事务。
    """
    raise NotImplementedError
