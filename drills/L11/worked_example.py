# -*- coding: utf-8 -*-
"""L11 完整样例 —— 直接跑：py drills/L11/worked_example.py

一个**离线**的"抓取 → 解析 → 结构化"最小闭环：页面 HTML 和 API JSON 都是内联假数据，
不联网也能把整条流水线的逻辑跑通。真上线时只需要把 fetch() 换成 requests/urllib。
"""
from __future__ import annotations

import json
import re
import sys
import time
from urllib.parse import urlencode, urljoin, urlparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 假装这是 GET https://movie.example.com/top?start=0 的响应体
PAGE_HTML = """
<div id="content">
  <ol>
    <li><div class="info"><div class="hd">
      <a href="/subject/1292052/"><span class="title">肖申克的救赎</span></a>
    </div><div class="bd"><span class="rating_num">9.7</span></div></div></li>
    <li><div class="info"><div class="hd">
      <a href="/subject/1291546/"><span class="title">霸王别姬</span></a>
    </div><div class="bd"><span class="rating_num">9.6</span></div></div></li>
    <!-- 这条是注释里的假数据 <span class="title">假货</span> -->
  </ol>
</div>
"""

# 假装这是某个开放 API 的 JSON 响应体
API_JSON = """{"code": 0, "data": {"items": [
  {"name": "北京时间", "value": "12:00"},
  {"name": "温度", "value": "21"}
]}}"""


def fake_fetch(url: str) -> str:
    """这里就是将来 requests.get(url).text 的位置 —— 现在返回假数据。"""
    return PAGE_HTML if "movie.example.com" in url else API_JSON


def extract_movies(html: str, base_url: str) -> list[dict[str, str]]:
    """正则提取：标题 + 评分 + 绝对链接。注意先清掉注释，否则"假货"也会被抓进来。"""
    cleaned = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    titles = re.findall(r'<span class="title">([^<]+)</span>', cleaned)
    scores = re.findall(r'<span class="rating_num">([^<]+)</span>', cleaned)
    hrefs = re.findall(r'<a href="([^"]+)"', cleaned)
    return [{"title": title, "score": score, "url": urljoin(base_url, href)}
            for title, score, href in zip(titles, scores, hrefs)]


def extract_api_items(text: str) -> dict[str, str]:
    return {item["name"]: item["value"] for item in json.loads(text)["data"]["items"]}


def build_next_page_url(base_url: str, page: int, size: int = 25) -> str:
    """翻页链接交给 urlencode，别自己拼 ? 和 &。"""
    return f"{base_url}?{urlencode(sorted({'start': str((page - 1) * size),
                                           'filter': 'false'}.items()))}"


def retry_plan(times: int = 4) -> list[float]:
    """指数退避序列（只算不睡），真实代码里再 random 加一点抖动。"""
    return [round(min(2 ** i, 30) + (i * 0.1), 2) for i in range(times)]


def main() -> None:
    base = "https://movie.example.com/top"
    url = build_next_page_url(base, page=2)
    print("请求 URL：", url)
    parts = urlparse(url)
    print(f"拆解：scheme={parts.scheme} host={parts.hostname} "
          f"path={parts.path} query={parts.query}")

    movies = extract_movies(fake_fetch(url), base)
    for movie in movies:
        print(f"  {movie['title']}  {movie['score']}  {movie['url']}")
    assert len(movies) == 2, "注释里的假数据不该被抓出来"

    print("API 数据：", extract_api_items(fake_fetch("https://api.example.com/t")))
    print("重试计划（秒）：", retry_plan())
    print("真实抓取时记得：设超时、带 User-Agent、遵守 robots.txt、控制频率。")
    t0 = time.time()
    print(f"整个离线流程耗时 {time.time() - t0:.6f} 秒")


if __name__ == "__main__":
    main()
