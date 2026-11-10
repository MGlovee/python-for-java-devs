#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P1 参考实现 —— Nginx/access 日志分析 CLI（纯标准库）。

用法：
    py example/app.py example/sample_access.log --top 3
    py example/app.py example/sample_access.log --min-status 400 --json
    py example/app.py example/sample_access.log --since 2026-10-02 --slow-ms 2000

格式约定：标准共同日志格式（CLF），行尾可选追加一个数字字段 = 请求耗时（毫秒）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

LINE_RE = re.compile(
    r"(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "
    r'"(?P<method>\S+) (?P<path>\S+)[^"]*"\s+'
    r'(?P<status>\d{3}) (?P<size>\d+|-)(?:\s+(?P<latency>\d+))?\s*$'
)
TIME_FMT = "%d/%b/%Y:%H:%M:%S %z"


def parse_line(line: str) -> Optional[dict]:
    """解析一行日志。非法行返回 None，绝不抛异常。"""
    m = LINE_RE.match(line.strip())
    if m is None:
        return None
    try:
        when = datetime.strptime(m["time"], TIME_FMT)
    except ValueError:
        return None
    return {
        "ip": m["ip"],
        "time": when,                              # 带日志原始时区的 aware datetime
        "method": m["method"],
        "path": m["path"],
        "status": int(m["status"]),
        "size": 0 if m["size"] == "-" else int(m["size"]),
        "latency_ms": None if m["latency"] is None else int(m["latency"]),
    }


def analyze(lines: Iterable[str], *, top: int = 10,
            min_status: Optional[int] = None,
            since: Optional[datetime] = None,
            slow_ms: Optional[int] = None) -> dict:
    """统计 PV/UV/状态码分布/Top-N URL/慢请求。结果可直接 json.dumps。"""
    records: list[dict] = []
    skipped = 0
    for line in lines:
        if not line.strip():
            continue
        rec = parse_line(line)
        if rec is None:
            skipped += 1
            continue
        if min_status is not None and rec["status"] < min_status:
            continue
        if since is not None:
            if rec["time"] < since:
                continue
        records.append(rec)

    slow = [r for r in records
            if slow_ms is not None and r["latency_ms"] is not None
            and r["latency_ms"] >= slow_ms]
    return {
        "pv": len(records),
        "uv": len({r["ip"] for r in records}),
        "skipped": skipped,
        "status_counts": {str(k): v
                          for k, v in Counter(r["status"] for r in records).items()},
        "top_urls": [{"url": u, "count": c}
                     for u, c in Counter(r["path"] for r in records).most_common(top)],
        "slow_count": len(slow),
        "slow_requests": [{"ip": r["ip"], "path": r["path"],
                           "latency_ms": r["latency_ms"]} for r in slow],
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="分析 Nginx/access 日志（CLF 格式，行尾可选耗时毫秒）")
    p.add_argument("logfile", help="日志文件路径")
    p.add_argument("--top", type=int, default=10, help="Top-N URL，默认 10")
    p.add_argument("--min-status", type=int, default=None, metavar="CODE",
                   help="只统计状态码 >= CODE 的请求")
    p.add_argument("--since", default=None, metavar="YYYY-MM-DD",
                   help="只统计该日期（按 UTC 零点）之后的请求")
    p.add_argument("--slow-ms", type=int, default=1000,
                   help="慢请求阈值（毫秒），默认 1000")
    p.add_argument("--json", action="store_true", help="输出单个 JSON 对象")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)

    path = Path(args.logfile)
    if not path.is_file():
        print(f"错误：日志文件不存在：{path}", file=sys.stderr)
        return 2

    since = None
    if args.since is not None:
        try:
            since = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"错误：--since 需要 YYYY-MM-DD 格式，收到：{args.since}",
                  file=sys.stderr)
            return 2

    with path.open(encoding="utf-8", errors="replace") as fh:
        result = analyze(fh, top=args.top, min_status=args.min_status,
                         since=since, slow_ms=args.slow_ms)

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
        return 0

    print(f"PV: {result['pv']}  UV: {result['uv']}"
          f"  跳过的非法行: {result['skipped']}")
    dist = "  ".join(f"{k}×{v}" for k, v in sorted(result["status_counts"].items()))
    print(f"状态码分布: {dist or '（无）'}")
    print(f"Top-{args.top} URL:")
    for item in result["top_urls"]:
        print(f"  {item['count']:>4}  {item['url']}")
    print(f"慢请求（>= {args.slow_ms}ms）: {result['slow_count']} 条")
    for r in result["slow_requests"]:
        print(f"  {r['latency_ms']:>6}ms  {r['ip']:<15} {r['path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
