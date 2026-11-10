# -*- coding: utf-8 -*-
"""L03 完整样例 —— 直接跑：py drills/L03/worked_example.py

一条正则拆 access log，f-string 出报表，datetime 算跨度。
学习顺序：跑 → 看输出 → 改日志行再跑 → 合上屏幕默写 LINE_RE。
"""
from __future__ import annotations

import re
import sys
from datetime import datetime

# 命名分组 (?P<name>...) 让后面的代码能按名字取值，比 group(3) 好读得多
LINE_RE = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] '
    r'"(?P<method>[A-Z]+) (?P<path>\S+) [^"]*" '
    r'(?P<status>\d{3}) (?P<size>\d+) (?P<cost>\d+\.\d+)'
)
TIME_FMT = '%Y-%m-%d %H:%M:%S'

LOGS = [
    '10.0.0.7 - - [2024-03-15 09:23:41] "GET /api/orders?page=2 HTTP/1.1" 200 5120 0.043',
    '10.0.0.8 - - [2024-03-15 09:23:58] "POST /api/orders HTTP/1.1" 500 812 1.204',
    '10.0.0.7 - - [2024-03-16 10:01:02] "GET /api/orders?page=3 HTTP/1.1" 200 6144 0.038',
    '10.0.0.9 - - [2024-03-16 10:07:19] "GET /health HTTP/1.1" 200 15 0.001',
]


def parse_line(line: str) -> dict | None:
    """一行日志 → 字典；格式不对就返回 None（match 只从行首开始试）。"""
    m = LINE_RE.match(line)
    if m is None:
        return None
    row = m.groupdict()                          # 一次拿到所有命名分组
    row['time'] = datetime.strptime(row['time'], TIME_FMT)
    row['status'] = int(row['status'])
    row['size'] = int(row['size'])
    row['cost'] = float(row['cost'])
    row['route'] = row['path'].split('?')[0]     # 查询串丢掉：/api/orders?page=2 -> /api/orders
    return row


def summarize(rows: list[dict]) -> list[list[str]]:
    """按路由聚合：请求数、错误数、总流量、平均耗时。"""
    stats: dict[str, list[int]] = {}
    for r in rows:
        s = stats.setdefault(r['route'], [0, 0, 0, 0])
        s[0] += 1
        s[1] += r['status'] >= 500               # bool 当 1 用，但结果仍是 int
        s[2] += r['size']
        s[3] += round(r['cost'] * 1000)          # 用毫秒整数累加，避开浮点误差
    table = [['route', 'req', 'err', 'traffic', 'avg_ms']]
    for route in sorted(stats):
        req, err, size, ms = stats[route]
        table.append([route, str(req), str(err), f'{size:,}', f'{ms / req:.1f}'])
    return table


def render(rows: list[list[str]]) -> str:
    """对齐列宽 —— 最后一列不补空格，行尾不留脏字符。"""
    if not rows:
        return ''
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    out = []
    for r in rows:
        cells = [r[i].ljust(widths[i]) for i in range(len(r) - 1)]
        cells.append(r[-1])
        out.append(' | '.join(cells))
    head = out[0]
    return '\n'.join([head, '-' * len(head)] + out[1:])


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):        # Windows 控制台默认 GBK，中文会糊
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    parsed = [p for p in (parse_line(line) for line in LOGS) if p]
    print(f'解析成功 {len(parsed)}/{len(LOGS)} 行\n')

    for row in parsed:
        print(f'{row["ip"]} {row["time"]:%m-%d %H:%M} '          # f-string 里直接塞格式符
              f'{row["method"]} {row["route"]} '
              f'{row["status"]} {row["cost"] * 1000:>6.0f}ms')
    print()
    print(render(summarize(parsed)))

    first, last = min(r['time'] for r in parsed), max(r['time'] for r in parsed)
    span = last - first                       # 两个 datetime 相减得 timedelta
    print(f'\n时间跨度：{span.days} 天 {span.seconds // 3600} 小时'
          f'（{span.total_seconds():,.0f} 秒）')
    print(f'错误率：{sum(r["status"] >= 500 for r in parsed) / len(parsed):.2%}')
