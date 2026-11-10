# -*- coding: utf-8 -*-
"""L13 判分用例。别改这个文件 —— 它就是考官。

全部用 `sqlite3.connect(":memory:")`，零落盘、零三方包。
推荐跑：py check.py L13 -v
"""
from __future__ import annotations

import sqlite3

import pytest
from exercises import (add_student, avg_score, build_in_clause, count_students,
                       enable_dict_rows, find_by_name, load_csv_into_db, rows_to_dicts,
                       transfer_score, upsert_student)

SCHEMA = ("CREATE TABLE student (id INTEGER PRIMARY KEY AUTOINCREMENT, "
          "name TEXT NOT NULL UNIQUE, score REAL NOT NULL)")


def new_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def seed(conn: sqlite3.Connection) -> None:
    add_student(conn, "关羽", 90.0)
    add_student(conn, "张飞", 50.0)


def scores_of(conn: sqlite3.Connection) -> dict[str, float]:
    return {row["name"]: row["score"] for row in
            rows_to_dicts(conn, "SELECT name, score FROM student")}


def test_01_add_student_returns_new_id():
    conn = new_db()
    try:
        first = add_student(conn, "关羽", 88.5)
        second = add_student(conn, "张飞", 70.0)
        assert (first, second) == (1, 2), "AUTOINCREMENT 的 id 要回传给调用方"
        assert count_students(conn) == 2, "不 commit 的话事务语义就丢了"
    finally:
        conn.close()


def test_02_add_student_rejects_duplicate_name():
    conn = new_db()
    try:
        add_student(conn, "赵云", 95.0)
        with pytest.raises(sqlite3.IntegrityError):
            add_student(conn, "赵云", 60.0), "name 上有 UNIQUE，重复要报错而不是悄悄再来一行"
    finally:
        conn.close()


def test_03_find_by_name_returns_dict_or_none():
    conn = new_db()
    try:
        add_student(conn, "马超", 77.0)
        got = find_by_name(conn, "马超")
        assert isinstance(got, dict), "要返回字典，不是元组"
        assert got["id"] == 1 and got["name"] == "马超"
        assert got["score"] == pytest.approx(77.0)
        assert find_by_name(conn, "不存在") is None, "查不到给 None，不许抛 IndexError"
    finally:
        conn.close()


def test_04_parameterized_query_blocks_injection():
    conn = new_db()
    try:
        seed(conn)
        assert find_by_name(conn, "' OR '1'='1") is None, (
            "参数是**值**不是 SQL 片段，注入串只会当成一个查不到的姓名")
        assert count_students(conn) == 2, "表没被删、没被多塞"
        assert rows_to_dicts(conn, "SELECT name FROM student WHERE name = ?", ("关羽",)) == [
            {"name": "关羽"}]
    finally:
        conn.close()


def test_05_rows_to_dicts_uses_column_names():
    conn = new_db()
    try:
        seed(conn)
        rows = rows_to_dicts(conn, "SELECT name, score FROM student WHERE score >= ?", (60.0,))
        assert rows == [{"name": "关羽", "score": pytest.approx(90.0)}], "参数化过滤要生效"
        assert all(isinstance(row, dict) for row in rows)
        assert rows_to_dicts(conn, "SELECT name FROM student WHERE id = ?", (999,)) == []
    finally:
        conn.close()


def test_06_count_students():
    conn = new_db()
    try:
        assert count_students(conn) == 0, "空表是 0，不是 None"
        seed(conn)
        assert count_students(conn) == 2
    finally:
        conn.close()


def test_07_avg_score_none_when_empty():
    conn = new_db()
    try:
        assert avg_score(conn) is None, "AVG() 在 0 行时是 NULL → None，不能编造成 0.0"
        seed(conn)
        assert avg_score(conn) == pytest.approx(70.0), "(90 + 50) / 2"
    finally:
        conn.close()


def test_08_enable_dict_rows_changes_fetch_shape():
    conn = new_db()
    try:
        seed(conn)
        enable_dict_rows(conn)
        row = conn.execute("SELECT id, name FROM student WHERE id = ?", (1,)).fetchone()
        assert isinstance(row, dict), "装了行工厂以后 fetchone 直接给字典"
        assert row == {"id": 1, "name": "关羽"}
    finally:
        conn.close()


def test_09_build_in_clause_placeholders_match_values():
    sql, params = build_in_clause("id", [1, 2, 3])
    assert sql == "WHERE id IN (?, ?, ?)", "一个值一个占位符，值绝不进字符串"
    assert params == (1, 2, 3)
    assert sql.count("?") == len(params), "占位符个数必须等于参数个数"


def test_10_build_in_clause_empty_values():
    sql, params = build_in_clause("name", [])
    assert sql == "WHERE 1 = 0" and params == (), "`IN ()` 是语法错误，用恒假条件代替"


def test_11_build_in_clause_validates_identifier():
    for bad in ("id; DROP TABLE student", "1id", "na me", "id--"):
        with pytest.raises(ValueError):
            build_in_clause(bad, [1]), f"列名不能参数化，只能白名单校验：{bad!r}"


def test_12_build_in_clause_works_as_where():
    conn = new_db()
    try:
        seed(conn)
        sql, params = build_in_clause("id", [2])
        names = [row["name"] for row in
                 rows_to_dicts(conn, f"SELECT name FROM student {sql}", params)]
        assert names == ["张飞"]
    finally:
        conn.close()


def test_13_transfer_score_moves_atomically():
    conn = new_db()
    try:
        seed(conn)                       # 关羽 90 / 张飞 50
        transfer_score(conn, 1, 2, 30.0)
        assert scores_of(conn)["关羽"] == pytest.approx(60.0)
        assert scores_of(conn)["张飞"] == pytest.approx(80.0)
    finally:
        conn.close()


def test_14_transfer_score_rolls_back_and_rejects_bad_input():
    conn = new_db()
    try:
        seed(conn)
        with pytest.raises(ValueError):
            transfer_score(conn, 1, 2, 1000.0), "余额不足必须抛，且两边都不变"
        assert scores_of(conn) == {"关羽": pytest.approx(90.0),
                                   "张飞": pytest.approx(50.0)}, "第一条 UPDATE 生效就说明没回滚"
        for bad in ((1, 2, 0), (1, 2, -5.0), (1, 99, 10.0)):
            with pytest.raises(ValueError):
                transfer_score(conn, *bad), "非正数金额 / 接收方不存在都要抛"
        assert count_students(conn) == 2
        assert scores_of(conn) == {"关羽": pytest.approx(90.0), "张飞": pytest.approx(50.0)}
    finally:
        conn.close()


def test_15_upsert_inserts_then_updates_same_row():
    conn = new_db()
    try:
        created = upsert_student(conn, "黄忠", 60.0)
        again = upsert_student(conn, "黄忠", 92.0)
        assert created == again == 1, "同名必须回到同一行，不能新增第二行"
        assert count_students(conn) == 1
        assert find_by_name(conn, "黄忠")["score"] == pytest.approx(92.0), (
            "DO UPDATE 分支要真的生效")
    finally:
        conn.close()


def test_16_load_csv_into_db_counts_new_rows_only():
    conn = new_db()
    try:
        add_student(conn, "关羽", 10.0)
        text = "name,score\n马超,88\n黄忠,77\n关羽,99\n"
        assert load_csv_into_db(conn, text) == 2, "已存在的关羽要跳过而不是报错"
        assert count_students(conn) == 3
        assert find_by_name(conn, "马超")["score"] == pytest.approx(88.0), "score 要转成 float"
    finally:
        conn.close()


def test_17_load_csv_into_db_rejects_bad_rows():
    conn = new_db()
    try:
        with pytest.raises(ValueError):
            load_csv_into_db(conn, "name\n关羽\n"), "缺 score 列就是脏数据，明确报错"
        with pytest.raises(ValueError):
            load_csv_into_db(conn, "name,score\n张飞,高分\n"), "score 不是数字也要报错"
    finally:
        conn.close()
