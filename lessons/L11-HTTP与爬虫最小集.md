# L11 · HTTP 与爬虫最小集

> 读 40 分钟 · 练 50 分钟
> 对应原文：`Day61-65/61`、`62`（两篇）、`64`、`65` + `番外篇/常见反爬策略及应对方案.md`（6 篇、1094 行）
> 判分：`py check.py L11` ｜ 卡片：[cards/l11.md](../cards/l11.md)
> **本课练习零网络**：抓取环节全部换成"解析内联的假 HTML / JSON 字符串"，逻辑一样。

HTTP 这层你太熟了：请求行、请求头、响应状态码、`Set-Cookie`。这一课的真正增量只有两块——
① Python 里**怎么发请求**（标准库很啰嗦，`requests` 很爽，但你机器上没装）；
② **怎么从 HTML 里取数据**（正则 / XPath / CSS 选择器三选一）。

---

## ① 开课先答 3 题（先答后读，答错才对）

1. `urllib.request.urlopen("https://x.com")` 返回的对象，`.read()` 给的是 `str` 还是 `bytes`？
2. 页面里有 `<a href="../b.html">`，你只有 base URL，想要绝对地址——该用什么？（不许手写字符串替换）
3. 服务器返回 `429`，最该做的第一件事是什么？

答案在 ⑥。

---

## ② 差异地图（Java → Python）

| 主题 | Java | Python | 一句话提醒 |
|---|---|---|---|
| 发请求 | `HttpClient.newBuilder()` | `urllib.request.urlopen` / `requests.get` | 标准库要自己拼 Request、自己处理重定向细节 |
| 响应体 | `HttpResponse.body()` | `.read()` → **bytes** | 文本要 `.decode(resp.headers.get_content_charset() or "utf-8")` |
| 状态码 | `response.statusCode()` | `resp.status`（requests）/ HTTPError 异常（urllib） | **`urllib` 对 4xx/5xx 直接抛 `HTTPError`**，不像 Java 那样"正常返回" |
| 超时 | `.connectTimeout(...)` | `urlopen(url, timeout=5)` / `requests.get(url, timeout=(3, 7))` | 没有超时的爬虫 = 定时卡死的进程 |
| 请求头 | `.header(k, v)` | `Request(url, headers={...})` | 爬虫必带 `User-Agent`，否则很多站直接拒 |
| JSON 响应 | Jackson/Gson | `resp.json()`（requests）/ `json.loads(resp.read())` | 见 L10 |
| URL 编解码 | `URLEncoder.encode` | `urllib.parse.urlencode / quote / unquote` | `urlencode` 吃 dict 直接出 `a=1&b=2` |
| URL 拼接 | 手搓 / `URI.resolve` | `urljoin(base, link)` | 相对路径、`//cdn/`、`../` 它全包了 |
| HTML 解析 | Jsoup | `re` / `lxml`(XPath) / `beautifulsoup4`(CSS) | 本机都没装，练习一律用正则或手写解析 |
| 重试 | Spring Retry / Resilience4j | 无标准库装饰器；`urllib3.Retry`（requests 系）或自己写循环 | 原则：**指数退避 + 抖动 + 只重试幂等请求** |
| 并发抓取 | 线程池 / WebFlux | `asyncio` + `aiohttp`，或 `ThreadPoolExecutor` + `requests` | 见 L12 |

### `urllib.request`：标准库唯一能跑的做法

```python
from urllib.parse import urlencode
import json, urllib.request, urllib.error

def fetch(url: str, timeout: float = 5.0) -> dict:
    request = urllib.request.Request(
        url + "?" + urlencode({"num": 10, "key": "APIKey"}),
        headers={"User-Agent": "Mozilla/5.0 (learn-demo)", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # 4xx/5xx 会抛
            charset = response.headers.get_content_charset() or "utf-8"
            return json.loads(response.read().decode(charset))
    except urllib.error.HTTPError as err:       # 有响应：状态码 + err.read()
        raise RuntimeError(f"HTTP {err.code}") from err
    except urllib.error.URLError as err:        # 无响应：DNS/连接/超时，err.reason
        raise RuntimeError(f"网络失败：{err.reason}") from err
```

`with` 用在响应对象上会自动关闭连接 —— 这是 `urllib` 里最容易漏的一步。

### `requests`（三方）为什么人人都装

```python
import requests
resp = requests.get(url, params={"num": 10}, headers={"User-Agent": "…"}, timeout=(3, 7))
resp.raise_for_status()          # 4xx/5xx 主动抛，别写 if status_code != 200
data = resp.json()               # 自动按编码解码 + 解析
```

| 差别 | `urllib.request` | `requests` |
|---|---|---|
| 非 2xx | 抛 `HTTPError`（默认不返回响应对象） | 正常返回，自己 `raise_for_status()` |
| 编码 | 手动 `decode` | 看 `Content-Type`/BOM，还有 `apparent_encoding` |
| 参数、表单、文件、Cookie、代理、连接池 | 自己写 | 一个函数参数搞定 |
| Session | 要自己管 opener | `requests.Session()` 复用连接 + 自动带 Cookie |
| 依赖 | 零 | 需要 `pip install requests`（练习本身不需要，讲义代码照做可用） |

**结论**：脚本能装库就用 `requests`；不能装库（运维机、考试环境）就用上面那段 `urllib`。

### HTML 取数据三选一

| 方式 | 依赖 | 速度 | 难度 | 什么时候用 |
|---|---|---|---|---|
| 正则 `re` | 标准库 | 快 | 写对很难 | 结构极规整、或环境装不了库（本课练习） |
| XPath `lxml` | `pip install lxml` | 快 | 中 | 层级深、要按属性过滤；浏览器 F12 能直接复制 XPath |
| CSS 选择器 `beautifulsoup4` | `pip install beautifulsoup4` | 一般 | 低 | 首选。`soup.select("div.info > a > span")[0].get_text()` |

标准库还有一个被低估的选项：`html.parser.HTMLParser`（写子类）和 `html.unescape`（还原实体）。
真要处理脏 HTML，别硬扛正则 —— 装 `bs4`，它会修复未闭合标签。

```python
from html.parser import HTMLParser          # 零依赖的结构化解析（比正则稳）
class LinkGrabber(HTMLParser):
    def __init__(self): super().__init__(); self.hrefs = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.hrefs += [v for k, v in attrs if k == "href" and v]
```

### 抓取之外的规矩（原 61 篇和反爬番外篇的要点）

| 主题 | 要点 |
|---|---|
| 合法性 | 只取前端公开数据；尊重 `robots.txt`（君子协议但法官会看）；尊重知识产权；别公开爬虫源码 |
| `robots.txt` | `User-agent` 分组 + `Disallow` 前缀；`Disallow:` 空值＝全放开；淘宝直接 `Disallow: /` 禁百度 |
| 频率 | 加延时（原文用 `time.sleep(random.random() * 4 + 1)`），单 IP 并发别超过个位数 |
| 身份 | 合理请求头（UA/Referer/Accept-Language）；`Referer` 常防盗链；商业 IP 代理只用于隐匿，不用于绕过付费墙 |
| 动态页面 | HTML 里没有的数据 → 先查 Network 面板找 XHR 接口（能拿 JSON 就别啃 HTML），实在不行才上 Selenium（原文 64） |
| 反爬进阶 | 验证码（OCR/打码平台，商业项目慎用）、蜜罐链接（可见性判断）、JS 混淆、指纹 |
| 框架 | 上百个站点、要断点续传和调度时再谈 Scrapy（原文 65），单站脚本别上 |

---

## ③ 完整样例：读 → 跑 → 改

[drills/L11/worked_example.py](../drills/L11/worked_example.py) 直接跑：
`py drills/L11/worked_example.py`。它用内联假 HTML 演示"清注释 → 正则提取 → `urljoin` 补全绝对链接 →
翻页 URL 用 `urlencode` → 重试退避序列"，全程离线。

跑完回答：把 `extract_movies` 里删注释那一行去掉，输出会多几条？为什么？

---

## ④ 补全题

打开 [drills/L11/exercises.py](../drills/L11/exercises.py)，10 个函数：前 6 挖空、后 4 只给需求。
测试用的是内联假 HTML/JSON，**不联网、不装三方包**。

```powershell
py check.py L11 -v
```

---

## ⑤ 三个 Java 老手必踩的坑

1. **`urllib` 对 4xx/5xx 抛异常，`requests` 不抛。** 从 Java 的 `HttpClient` 过来的人默认"状态码是返回值"，
   用 `requests` 时忘了 `raise_for_status()`，于是 500 的错误页被当正常数据解析，报错报在十万八千里外。
2. **`.read()` 是 bytes，不是 str。** 忘记 decode 会把 `b'{"code":0}'` 一路传下去；
   decode 时不指定编码，Windows 上又回到 GBK 坑（见 L10）。`requests` 的 `.text` 帮你解码，但猜错编码时
   仍以 `resp.encoding` 为准，手动设成 `utf-8` 最保险。
3. **相对链接和查询串不能手拼。** `"https://a.com/dir/page.html" + "?x=1"` 会丢掉原有参数；
   `base + href` 处理不了 `../`、`//cdn/`。一律 `urljoin` + `urlencode`。爬虫去重还要先做 URL 规范化
   （本练习的 `canonical_url`）——否则同一个页面会因为参数顺序被当成两个 URL 抓两遍。

---

## ⑥ 现在回看开头 3 题

1. **`bytes`**。要 `.decode(charset)` 才是 `str`。
2. **`urllib.parse.urljoin(base, link)`**（`//` 会继承 base 的协议，`/x` 回到站点根）。
3. **停止轰炸，按 `Retry-After` 或指数退避等待**，并降低并发。换 IP/换 UA 硬闯是另一种 429。

答错的那题，去 [cards/l11.md](../cards/l11.md) 找对应卡片。

---

## ⑦ 通关标准

- `py check.py L11` 输出 `10/10 通过`（判分器显示 `16/16`）。
- 白板写出：带 UA 和超时的 `urllib` GET + JSON 解析 + 一次重试（退避）——不查资料。
- 达成后：`py progress.py done L11`。

## ⑧ 还要细节？回原文

| 想要 | 原文 |
|---|---|
| 爬虫概念、合法性讨论、robots.txt 实例 | [61.网络数据采集概述.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day61-65/61.%E7%BD%91%E7%BB%9C%E6%95%B0%E6%8D%AE%E9%87%87%E9%9B%86%E6%A6%82%E8%BF%B0.md)（200 行） |
| requests 用法、豆瓣 Top250 正则版、IP 代理 | [62.用Python获取网络资源-1.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day61-65/62.%E7%94%A8Python%E8%8E%B7%E5%8F%96%E7%BD%91%E7%BB%9C%E8%B5%84%E6%BA%90-1.md)（133 行） |
| HTML 结构、XPath 语法表、bs4 CSS 选择器版 | [62.用Python解析HTML页面-2.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day61-65/62.%E7%94%A8Python%E8%A7%A3%E6%9E%90HTML%E9%A1%B5%E9%9D%A2-2.md)（149 行） |
| 动态内容：Selenium + WebDriver | [64.使用Selenium抓取网页动态内容.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day61-65/64.%E4%BD%BF%E7%94%A8Selenium%E6%8A%93%E5%8F%96%E7%BD%91%E9%A1%B5%E5%8A%A8%E6%80%81%E5%86%85%E5%AE%B9.md)（281 行） |
| 什么时候上 Scrapy | [65.爬虫框架Scrapy简介.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day61-65/65.%E7%88%AC%E8%99%AB%E6%A1%86%E6%9E%B6Scrapy%E7%AE%80%E4%BB%8B.md)（250 行） |
| 反爬手段清单（请求头/Cookie/验证码/蜜罐/代理） | [番外篇/常见反爬策略及应对方案.md](https://github.com/jackfrued/Python-100-Days/blob/master/%E7%95%AA%E5%A4%96%E7%AF%87/%E5%B8%B8%E8%A7%81%E5%8F%8D%E7%88%AC%E7%AD%96%E7%95%A5%E5%8F%8A%E5%BA%94%E5%AF%B9%E6%96%B9%E6%A1%88.md)（81 行） |
