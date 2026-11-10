# -*- coding: utf-8 -*-
"""L11 判分用例。别改这个文件 —— 它就是考官。

零网络：所有 HTML / JSON 都是内联的假数据，跑得快也跑得稳。
推荐跑：py check.py L11 -v            （零依赖）
"""
from __future__ import annotations

import pytest
from exercises import (absolute_url, backoff_delays, build_query_url, canonical_url,
                       extract_links, parse_api_items, parse_query, robots_allows,
                       split_url, strip_tags)

FAKE_HTML = """
<html><body>
<!-- 顶部广告位 <a href="/ad">别点</a> -->
<ul class="list">
  <li><a href="/top250?start=25" title="下一页">2</a></li>
  <li><a href='detail/1.html'>肖申克的救赎</a></li>
  <li><a href="https://movie.douban.com/subject/2/">教父</a></li>
</ul>
<script>var a = "<a href='/fake'>脚本里的不算</a>";</script>
</body></html>
"""

FAKE_API = """
{"code": 1, "msg": "ok",
 "data": {"newslist": [
   {"title": "标题一", "url": "http://a.com/1"},
   {"title": "标题二", "url": "http://a.com/2"},
   {"url": "http://a.com/3"}
 ]}}
"""

ROBOTS = """# 注释行
User-agent: *
Disallow: /search
Disallow: /group/search
Allow: /search/public

User-agent: Baiduspider
Disallow:

User-agent: MyLittleCrawler
Disallow: /private
"""


def test_01_split_url_all_parts():
    got = split_url("https://movie.douban.com/top250?start=25&filter=#item3")
    assert got == {"scheme": "https", "netloc": "movie.douban.com",
                   "path": "/top250", "query": "start=25&filter=",
                   "fragment": "item3"}
    missing = split_url("http://x.com/")
    assert missing["query"] == "" and missing["fragment"] == "", "缺的键给空串不是 None"
    assert missing["netloc"] == "x.com"


def test_02_build_query_url_sorts_and_escapes():
    url = build_query_url("https://api.tianapi.com/guonei", {"num": "10", "key": "a b"})
    assert url == "https://api.tianapi.com/guonei?key=a+b&num=10", (
        "键按字母序，转义交给 urlencode，不许手拼 k=v")


def test_03_build_query_url_appends_to_existing_query():
    assert build_query_url("https://x.com/a?id=1", {"p": "2"}) == "https://x.com/a?id=1&p=2"
    assert build_query_url("https://x.com/a", {}) == "https://x.com/a", "空参数不要留个光秃秃的 ?"


def test_04_build_query_url_escapes_reserved_chars():
    url = build_query_url("https://x.com/s", {"q": "中文&符号=1"})
    query = url.split("?", 1)[1]
    assert query.startswith("q=") and query.count("&") == 0, (
        "值里的 & 必须被转义，否则参数被切开")
    assert "%E4%B8%AD" in query, "中文要百分号编码"


def test_05_parse_query_repeated_keys():
    assert parse_query("a=1&b=x+y&b=%E4%B8%AD") == {"a": ["1"], "b": ["x y", "中"]}
    assert parse_query("") == {}


def test_06_extract_links_in_order():
    assert extract_links(FAKE_HTML) == ["/top250?start=25", "detail/1.html",
                                        "https://movie.douban.com/subject/2/"], (
        "按出现顺序返回；注释里的和 <a> 之外的都不算")
    assert extract_links("<p>没有链接</p>") == []
    assert extract_links('<A HREF="x.html">大写标签</A>') == ["x.html"], "标签名不分大小写"


def test_07_strip_tags_removes_entities_and_whitespace():
    text = "<p>第一行\n  缩进</p>\n<!-- 注释 <b>粗</b> --> <a href='#'>O&#39;Neil &amp; Sons</a>"
    assert strip_tags(text) == "第一行 缩进 O'Neil & Sons", "实体要还原，空白要压扁"
    assert strip_tags("<div></div>") == ""
    assert strip_tags("没有标签的纯文本") == "没有标签的纯文本"


def test_08_parse_api_items_basic():
    assert parse_api_items(FAKE_API, "newslist", "title") == ["标题一", "标题二"], (
        "缺字段的那一项要跳过，不是报错")


def test_09_parse_api_items_missing_or_broken():
    with pytest.raises(KeyError):
        parse_api_items(FAKE_API, "unknown_list", "title")
    with pytest.raises(KeyError):
        parse_api_items('["不是对象"]', "newslist", "title")
    with pytest.raises(ValueError):       # json.JSONDecodeError 是 ValueError 的子类
        parse_api_items("<html>不是 JSON</html>", "newslist", "title")


def test_10_absolute_url_relative_forms():
    base = "https://movie.douban.com/list/top250?start=0"
    assert absolute_url(base, "/subject/1/") == "https://movie.douban.com/subject/1/", (
        "以 / 开头的是站根绝对路径，不带 base 的目录")
    assert absolute_url(base, "detail/1.html") == "https://movie.douban.com/list/detail/1.html"
    assert absolute_url("https://h/dir/page.html", "../a") == "https://h/a"


def test_11_absolute_url_protocol_relative_and_absolute():
    base = "https://movie.douban.com/top250"
    assert absolute_url(base, "//cdn.x.com/a.js") == "https://cdn.x.com/a.js", "继承 base 的协议"
    assert absolute_url(base, "http://other.com/x") == "http://other.com/x", "绝对地址原样给回"


def test_12_canonical_url_dedups():
    assert canonical_url("HTTPS://API.X.COM?b=2&a=1#frag") == "https://api.x.com/?a=1&b=2"
    assert canonical_url("http://A.COM:8080/Pages?x=1") == "http://a.com:8080/Pages?x=1", (
        "路径大小写敏感不能压，端口要留")
    assert canonical_url("http://a.com") == "http://a.com/", "空路径补成 /"
    assert canonical_url("https://api.x.com/?a=1&b=2") == canonical_url("https://API.x.com/?b=2&a=1")


def test_13_backoff_delays_growth_and_cap():
    assert backoff_delays(5, 1, 2, 10) == [1.0, 2.0, 4.0, 8.0, 10.0], "最后一档被 cap 削平"
    assert backoff_delays(3, 0.5, 3) == [0.5, 1.5, 4.5]
    assert backoff_delays(0) == [] and backoff_delays(-2) == [], "非正数 attempts 给空列表"


def test_14_robots_allows_uses_star_group():
    assert robots_allows(ROBOTS, "SomeUnknownBot", "/search") is False
    assert robots_allows(ROBOTS, "SomeUnknownBot", "/subject/2/") is True, (
        "本课的简化规则里 Allow 被忽略，不在 Disallow 前缀下就允许")


def test_15_robots_allows_named_group_and_empty_disallow():
    assert robots_allows(ROBOTS, "MyLittleCrawler", "/private/a") is False
    assert robots_allows(ROBOTS, "MyLittleCrawler", "/public") is True
    assert robots_allows(ROBOTS, "baiduspider", "/anything") is True, (
        "Disallow 值为空 = 全放开，且 UA 匹配不分大小写")


def test_16_robots_allows_no_matching_group():
    assert robots_allows("User-agent: Googlebot\nDisallow: /\n", "Other", "/x") is True, (
        "没有自己也没有 * 的组时按允许处理")
