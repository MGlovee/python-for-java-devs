# -*- coding: utf-8 -*-
"""L11 练习工作表 —— 把每个函数里的 `raise NotImplementedError` 删掉，写上你的实现。

**本课练习完全离线**：没有网络，也没有 requests/bs4/lxml。
所有"抓取"都改成一端字符串或字节串：HTML 片段、API 的 JSON 文本、URL 本身，
你在测试里会看到它们长什么样。判分只看你的解析/拼接结果。

判分：  py check.py L11 -v
看答案：py check.py L11 --solution
"""
from __future__ import annotations


# ---------- 第一组：挖空题（有提示，照着填） ----------

def split_url(url: str) -> dict[str, str]:
    """把 URL 拆成 `scheme / netloc / path / query / fragment` 五个键的字典，缺的给空串。

    提示：`urllib.parse.urlsplit(url)` 返回 5 元组，字段名就是 `.scheme` `.netloc` …
    >>> split_url("https://a.com/x?y=1#z")["path"]
    '/x'
    """
    raise NotImplementedError


def build_query_url(base: str, params: dict[str, str]) -> str:
    """把参数字典拼到 URL 上，返回完整链接。

    要求：1) 键按字母序排（同样输入永远同样输出，方便做缓存键）；
          2) 用 `urlencode` 转义，不许手拼 `k=v`；
          3) `base` 已经自带 `?` 时用 `&` 续接，否则用 `?`。
    提示：`urllib.parse.urlencode(sorted(params.items()))`
    """
    raise NotImplementedError


def parse_query(query: str) -> dict[str, list[str]]:
    """把查询串解析成 `{键: [值, ...]}`，同一个键出现多次要全收，`%20` 要还原成空格。

    提示：`urllib.parse.parse_qs(query)` 本身就是这个结构。
    >>> parse_query("a=1&b=x+y&b=%E4%B8%AD")
    {'a': ['1'], 'b': ['x y', '中']}
    """
    raise NotImplementedError


def extract_links(html: str) -> list[str]:
    """用正则抓出页面里所有 `<a>` 标签的 `href` 值，单引号和双引号都要认，按出现顺序返回。

    要求：HTML 注释 `<!-- ... -->` 和 `<script>...</script>` 里的假链接不算（它们也长得像标签）。
    提示：先 `re.sub` 把注释和 script 块删掉（`flags=re.S` 让 `.` 吃换行），再
          `re.findall(r"<a[^>]*?href=['\"]([^'\"]+)['\"]", html, re.I)` —— `[^>]*?` 防止跨过标签边界。
    """
    raise NotImplementedError


def strip_tags(html: str) -> str:
    """把 HTML 变成纯文本：先删注释再删标签，还原 `&amp;` `&#39;` 这类实体，
    连续空白压成一个空格，最后 strip。

    提示：`re.sub(r"<!--.*?-->", " ", html, flags=re.S)` →
          `re.sub(r"<[^>]+>", " ", ...)` → `html.unescape(...)` → `split()` 后 `" ".join(...)`
    """
    raise NotImplementedError


def parse_api_items(text: str, list_key: str, field: str) -> list[str]:
    """解析一段 API 返回的 JSON 文本，取出列表 `payload["data"][list_key]` 里每一项的 `field`。

    要求：1) 顶层是 `{"code":…, "data": {"newslist": […]}}` 这种结构，先去 `data` 里找 `list_key`；
          顶层没有 `data` 时，直接在顶层找 `list_key`；
          2) 两处都找不到、或顶层不是 JSON 对象 → 抛 `KeyError`；
          3) 某一项没有 `field` 这个键 → 跳过它，不要报错；
          4) 值原样返回（这里都是字符串，不用转类型）。
    提示：`json.loads` 完就是一堆 dict / list，按 Java 里 Jackson 的 treeNode 思路取字段即可。
    """
    raise NotImplementedError


# ---------- 第二组：只给需求（独立写） ----------

def absolute_url(base_url: str, link: str) -> str:
    """把页面里的相对链接换成绝对链接。

    要求：`/top250?start=25` 接在 base 的站点根上；`detail.html` 接在 base 所在目录下；
    `//cdn.x.com/a.js` 继承 base 的协议；已经是 `http(s)://` 的原样返回。
    标准库有一个函数能一次做完这四件事，别自己拼字符串。
    """
    raise NotImplementedError


def canonical_url(url: str) -> str:
    """URL 规范化，用于爬虫去重。

    要求：1) 丢掉 `#fragment`；2) 主机名转小写（含端口保留），scheme 也转小写；
          3) path 为空时补成 `/`，path 本身的大小写不动；
          4) query 参数按**键**排序（用稳定排序，同键的值保持原顺序）。
    提示：`urlsplit` + `parse_qsl` + `sorted(..., key=lambda kv: kv[0])` + `urlencode` 三件套。
    """
    raise NotImplementedError


def backoff_delays(attempts: int, base: float = 1.0, factor: float = 2.0,
                   cap: float | None = None) -> list[float]:
    """返回每次**重试前**该等多少秒的指数退避序列（不含随机抖动）。

    要求：第 i 次（从 0 开始）等 `base * factor ** i`；给了 `cap` 就取 min(算出来的, cap)；
    `attempts <= 0` 返回空列表；本函数只做纯计算，不许 `time.sleep`。
    例：`backoff_delays(5, 1, 2, 10)` → `[1.0, 2.0, 4.0, 8.0, 10.0]`
    """
    raise NotImplementedError


def robots_allows(robots_text: str, user_agent: str, path: str) -> bool:
    """按 robots.txt 文本判断某个 UA 能否抓某个路径，True 表示允许。

    解析规则（简化版，按这个来）：
    1. `User-agent: X` 开一个新组，后面直到下一个 `User-agent` 之间的 `Disallow: P` 都归属该组；
    2. 选组：先取与 `user_agent` **不区分大小写完全相等**的组，没有就取 `*` 组，两个都没有 → 允许；
    3. 组内 `Disallow:` 值为空串表示"什么都不禁止"，忽略它；
    4. `path` 以组内任一非空 Disallow 值**开头** → 不允许（False），否则 True。
    其余行（`Allow:`、空行、注释）一律忽略。
    """
    raise NotImplementedError
