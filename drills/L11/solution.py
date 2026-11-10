# -*- coding: utf-8 -*-
"""L11 参考答案。

别整篇抄 —— 它的价值在于卡住 15 分钟后对照思路。
验证题目本身有没有写错：py check.py L11 --solution
"""
from __future__ import annotations

import html as html_module
import json
import re
from urllib.parse import parse_qs, parse_qsl, urlencode, urljoin, urlsplit


def split_url(url: str) -> dict[str, str]:
    parts = urlsplit(url)
    return {"scheme": parts.scheme, "netloc": parts.netloc, "path": parts.path,
            "query": parts.query, "fragment": parts.fragment}


def build_query_url(base: str, params: dict[str, str]) -> str:
    if not params:
        return base
    query = urlencode(sorted(params.items()))          # 排序让输出稳定
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}{query}"


def parse_query(query: str) -> dict[str, list[str]]:
    return parse_qs(query)                              # 重复键自动收集成列表


def extract_links(html: str) -> list[str]:
    cleaned = re.sub(r"<!--.*?-->", " ", html, flags=re.S)          # 注释里的假链接
    cleaned = re.sub(r"<script\b.*?</script>", " ", cleaned, flags=re.S | re.I)
    return re.findall(r"""<a[^>]*?href\s*=\s*['"]([^'"]+)['"]""", cleaned, re.I)


def strip_tags(html: str) -> str:
    text = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(html_module.unescape(text).split())


def parse_api_items(text: str, list_key: str, field: str) -> list[str]:
    payload = json.loads(text)                          # 解析失败让 JSONDecodeError 冒出去
    if not isinstance(payload, dict):
        raise KeyError(f"响应顶层不是 JSON 对象：{type(payload).__name__}")
    container = payload["data"] if isinstance(payload.get("data"), dict) else payload
    if list_key not in container:
        raise KeyError(f"响应里找不到 {list_key}")
    items = container[list_key]
    return [item[field] for item in items if isinstance(item, dict) and field in item]


def absolute_url(base_url: str, link: str) -> str:
    return urljoin(base_url, link)


def canonical_url(url: str) -> str:
    parts = urlsplit(url)
    path = parts.path or "/"
    pairs = sorted(parse_qsl(parts.query, keep_blank_values=True),
                   key=lambda kv: kv[0])               # 稳定排序：同键的值不乱
    query = urlencode(pairs)
    head = f"{parts.scheme.lower()}://{parts.netloc.lower()}{path}"
    return f"{head}?{query}" if query else head


def backoff_delays(attempts: int, base: float = 1.0, factor: float = 2.0,
                   cap: float | None = None) -> list[float]:
    delays: list[float] = []
    delay = float(base)
    for _ in range(max(attempts, 0)):
        delays.append(delay if cap is None else min(delay, cap))
        delay *= factor
    return delays


def robots_allows(robots_text: str, user_agent: str, path: str) -> bool:
    groups: list[tuple[str, list[str]]] = []
    for raw_line in robots_text.splitlines():
        line = raw_line.split("#", 1)[0].strip()      # 行内注释也算注释
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if key == "user-agent":
            groups.append((value, []))
        elif key == "disallow" and groups:
            groups[-1][1].append(value)               # Allow 行按简化规则忽略
    wanted = user_agent.lower()
    chosen = next((g for g in groups if g[0].lower() == wanted), None)
    if chosen is None:
        chosen = next((g for g in groups if g[0] == "*"), None)
    if chosen is None:
        return True
    return not any(rule and path.startswith(rule) for rule in chosen[1])
