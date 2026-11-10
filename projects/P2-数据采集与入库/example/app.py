#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P2 参考实现 —— 采集(离线样本)→清洗→SQLite 入库→查询报告（纯标准库）。

用法：
    py example/app.py                      # 用内联样本文件跑完整管线（临时目录，不留产物）
    py example/app.py 某页.html 某接口.json  # 对指定样本文件跑管线

网络抓取是可选增强：fetch() 内部才 import requests，未安装也不影响上面任何流程。
"""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Union
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from html.parser import HTMLParser

TABLE = "records"

# ---------------- URL 规范化 ----------------

def normalize_url(url: str) -> str:
    """小写协议/域名、补默认协议、去 fragment、去默认端口、去 utm_* 参数、查询参数排序、去尾部斜杠。"""
    url = (url or "").strip()
    if not url:
        return ""
    if "://" not in url:
        url = "https://" + url
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    host = parts.netloc.lower()
    if host.endswith(":80") and scheme == "http":
        host = host[:-3]
    if host.endswith(":443") and scheme == "https":
        host = host[:-4]
    if not host:                      # 相对路径之类，没有主机名，原样返回
        return url
    pairs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_")]
    query = urlencode(sorted(pairs))
    path = parts.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return urlunsplit((scheme, host, path, query, ""))


# ---------------- 解析（JSON / HTML 两路） ----------------

class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.records: list[dict] = []
        self._href: Optional[str] = None
        self._buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._buf = []

    def handle_data(self, data):
        if self._href is not None:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.records.append({"url": self._href,
                                 "title": "".join(self._buf).strip(),
                                 "date": "", "views": 0})
            self._href = None


def _record_from_dict(item: dict) -> dict:
    return {"url": item.get("url") or item.get("link") or "",
            "title": item.get("title") or "",
            "date": item.get("date") or "",
            "views": item.get("views", 0)}


def extract_records(source: Union[str, Path]) -> list[dict]:
    """从本地 JSON 或 HTML 文件提取原始记录。source 必须是存在的文件路径。"""
    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(f"样本文件不存在：{path}")
    text = path.read_text(encoding="utf-8", errors="replace")

    stripped = text.lstrip()
    if stripped.startswith(("[", "{")):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = None                   # 长得像 JSON 但坏了，掉到 HTML 分支
        if data is not None:
            if isinstance(data, dict):    # {"items": [...]} 之类
                data = next((v for v in data.values() if isinstance(v, list)), [])
            return [_record_from_dict(x) for x in data if isinstance(x, dict)]

    parser = _LinkParser()
    parser.feed(text)
    return parser.records


# ---------------- 清洗去重 ----------------

_DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日")


def _norm_date(raw) -> str:
    s = str(raw or "").strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


def clean_records(records: list[dict]) -> list[dict]:
    """规范化 URL、去重（同一规范化 URL 保留第一条）、统一日期/浏览数；无 url 的记录丢弃。"""
    seen: set[str] = set()
    out: list[dict] = []
    for rec in records:
        url = normalize_url(str(rec.get("url") or ""))
        if not url or url in seen:
            continue
        seen.add(url)
        try:
            views = int(str(rec.get("views", 0)).strip())
        except (TypeError, ValueError):
            views = 0
        out.append({"url": url,
                    "title": str(rec.get("title") or "").strip(),
                    "date": _norm_date(rec.get("date")),
                    "views": views})
    return out


# ---------------- SQLite 入库 ----------------

def save_records(records: list[dict], db_path: Union[str, Path]) -> int:
    """写入 SQLite（表名固定 records，url 唯一）。返回新插入的行数，重复运行不产生重复数据。"""
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS {TABLE} ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "url TEXT UNIQUE NOT NULL, title TEXT DEFAULT '', "
            "date TEXT DEFAULT '', views INTEGER DEFAULT 0)")
        before = conn.total_changes
        conn.executemany(
            f"INSERT OR IGNORE INTO {TABLE} (url, title, date, views) VALUES (?,?,?,?)",
            [(r["url"], r["title"], r["date"], r["views"]) for r in records])
        conn.commit()
        return conn.total_changes - before
    finally:
        conn.close()


def report(db_path: Union[str, Path], limit: int = 20) -> list[dict]:
    """按浏览数降序返回报告行：[{url,title,date,views}, …]。"""
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"SELECT url, title, date, views FROM {TABLE} "
            "ORDER BY views DESC, url ASC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------- 可选增强：联网抓取（缺 requests 也能整体跑） ----------------

def fetch(url: str, timeout: float = 5.0) -> list[dict]:
    """真·抓取入口。requests 只在函数内部 import——顶层 import 会拖垮离线判分。"""
    import requests                      # noqa: 延迟导入是本项目的设计点
    resp = requests.get(url, timeout=timeout,
                        headers={"User-Agent": "P2-learner/1.0"})
    resp.raise_for_status()
    return extract_records_from_text(resp.text)


def extract_records_from_text(text: str) -> list[dict]:
    stripped = text.lstrip()
    if stripped.startswith(("[", "{")):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return []
        if isinstance(data, dict):
            data = next((v for v in data.values() if isinstance(v, list)), [])
        return [_record_from_dict(x) for x in data if isinstance(x, dict)]
    parser = _LinkParser()
    parser.feed(text)
    return parser.records


# ---------------- 内联样本与入口 ----------------

INLINE_HTML = """\
<html><body>
  <a href="https://news.example.com/one">头条一</a>
  <p>与链接无关的正文</p>
  <a href="https://www.news.example.com/two?x=1&utm_source=rss">  头条二  </a>
  <a href="https://news.example.com/one#frag">头条一（重复，带锚点）</a>
</body></html>
"""

INLINE_JSON = """\
[
  {"url": "HTTP://Shop.Example.com:80/item/7?utm_source=push&color=red",
   "title": " 商品7 ", "date": "2026/1/2", "views": "42"},
  {"url": "http://shop.example.com/item/7?color=red",
   "title": "商品7", "date": "2026-01-02", "views": 41},
  {"url": "https://blog.example.cn/post/a?b=2&a=1#frag",
   "title": "文章A", "date": "坏日期", "views": "很多"}
]
"""


def build_sample_files(tmpdir: Path) -> list[Path]:
    html, js = tmpdir / "sample.html", tmpdir / "sample.json"
    html.write_text(INLINE_HTML, encoding="utf-8")
    js.write_text(INLINE_JSON, encoding="utf-8")
    return [html, js]


def main(argv: Optional[list[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = [str(a) for a in (argv if argv is not None else sys.argv[1:])]
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        sources = [Path(a) for a in args] or build_sample_files(tmp)
        raw: list[dict] = []
        for src in sources:
            try:
                raw.extend(extract_records(src))
            except FileNotFoundError as exc:
                print(f"错误：{exc}", file=sys.stderr)
                return 2
        cleaned = clean_records(raw)
        db = tmp / "p2.db"                # 临时目录里的库，进程退出即焚
        inserted = save_records(cleaned, db)
        inserted += 0                     # 演示幂等：再存一次也不会变
        save_records(cleaned, db)
        print(f"原始 {len(raw)} 条 → 清洗后 {len(cleaned)} 条 → 新入库 {inserted} 条")
        print(f"{'浏览数':>6}  日期          标题")
        for row in report(db):
            print(f"{row['views']:>6}  {row['date'] or '-'}  {row['title']}  <- {row['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
