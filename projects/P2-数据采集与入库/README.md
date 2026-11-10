# P2 · 数据采集与入库（离线可验收）

> 本项目的完整可运行参考实现见 example/app.py，卡住 20 分钟以上再看。

| 项 | 值 |
|---|---|
| 交付物 | 一个 `app.py`：本地 HTML/JSON 样本 → 解析 → 清洗去重（URL 规范化）→ 写入 SQLite → 查询报告 |
| 预计工时 | 4–6 小时 |
| 用到的课 | L10（文件与 JSON）、L11（HTTP/HTML 解析心智）、L13（数据库访问）、L02/L06 兜底 |
| 依赖 | 核心链路**纯标准库**（`json`、`html.parser`、`urllib.parse`、`sqlite3`）；联网抓取是可选增强 |
| 验收 | `py verify.py`（10 条探测全 `[通过]`，退出码 0；全程离线、临时文件测完即删） |

这个项目刻意做成**离线可验收**：判分器不联网，你也不需要联网。
真实抓取只是把 `extract_records` 的输入从"本地文件"换成"HTTP 响应正文"，管线其余部分不动——
这正是爬虫工程的分层方式。

---

## 1. 需求

- **解析**：`extract_records(source)` 接收一个**本地文件路径**，自动识别两种输入：
  - JSON：顶层是数组，或对象里第一个数组值（如 `{"items": [...]}`）；每条取
    `url`（或 `link`）、`title`、`date`、`views`，缺键给空串/0 兜底；
  - HTML：抽出所有 `<a href>`，链接文字作 `title`。
  - 两者都输出统一形态 `list[dict]`，键固定 `url/title/date/views`。
- **URL 规范化** `normalize_url`（去重的钥匙）：
  - 无协议补 `https://`；协议与主机名转小写；去掉默认端口（`:80`/`:443`）；
  - 去掉 `#fragment`；去掉 `utm_*` 跟踪参数；其余查询参数**按 key 排序**；
  - 去掉路径末尾多余的 `/`（根路径 `/` 保留）；主机名为空（相对路径）时原样返回。
- **清洗** `clean_records`：规范化 URL → 按规范化结果去重（保留第一条）→ 丢弃无 url 行 →
  `title` 去首尾空白 → 日期统一 `YYYY-MM-DD`（认 `%Y-%m-%d`、`%Y/%m/%d`、`%Y年%m月%d日`，
  认不出置 `""`）→ `views` 转 int（转不动置 0），**坏字段兜底而不是丢整行、不许抛异常**。
- **入库** `save_records`：`sqlite3`，表名**必须叫 `records`**，`url` 带 UNIQUE 约束；
  重复运行不产生重复行（`INSERT OR IGNORE`）；返回本次**新插入行数**；用完必须 `close`。
- **报告** `report(db_path, limit=20)`：按 `views` 降序（同分按 url 升序，保证结果确定）返回
  `list[dict]`，列 `url/title/date/views`。
- 边界要求：
  - 数据库文件放 `tempfile` 临时目录，**跑完仓库里不许留 `*.db`**（verify 会检查项目目录变化）；
  - 样本文件不存在 → 友好报错、`main` 返回非 0；
  - `requests` **只允许在函数体内 import**——顶层 import 第三方包会让离线判分整链崩溃。

## 2. 函数契约表（verify.py 按这个探测）

| 函数 | 签名 | 返回 | 异常 |
|---|---|---|---|
| `normalize_url` | `(url: str) -> str` | 规范化后的绝对 URL；输入空串得空串 | 不抛 |
| `extract_records` | `(source: str \| Path) -> list[dict]` | `[{url,title,date,views}, …]`，原始形态未清洗 | 文件不存在可抛 `FileNotFoundError` |
| `clean_records` | `(records: list[dict]) -> list[dict]` | 去重清洗后的记录，键同上，`views` 为 int、`date` 为 str | 不抛 |
| `save_records` | `(records, db_path: str \| Path) -> int` | 本次新插入行数；可重复调用（幂等） | 不抛 |
| `report` | `(db_path, limit: int = 20) -> list[dict]` | views 降序的 `[{url,title,date,views}, …]` | 不抛 |
| `main` | `(argv: list \| None = None) -> int` | 退出码；`main([])` 必须用内联样本全流程跑通 | — |
| `fetch`（可选） | `(url: str) -> list[dict]` | 联网抓取版解析结果 | requests 缺失时调用才报 `ModuleNotFoundError` |

表结构契约：`records(id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT UNIQUE NOT NULL, title TEXT, date TEXT, views INTEGER)`。

### 数据流一张图

```text
本地样本(.html/.json)      规范化+去重            幂等写入              降序查询
extract_records  ──▶  clean_records  ──▶  save_records(sqlite)  ──▶  report
   原始 list[dict]        干净 list[dict]         records 表            list[dict]
```

### 输入/输出样例（对着它核对）

输入 JSON（节选自 verify 用的样本）：

```json
[{"url": "HTTP://Shop.Example.com:80/item/7?utm_source=push&color=red",
  "title": " 商品7 ", "date": "2026/1/2", "views": "42"},
 {"url": "http://shop.example.com/item/7?color=red", "title": "商品7",
  "date": "2026-01-02", "views": 41}]
```

`clean_records` 之后必须只剩**一条**（两条是同一 URL 的变体）：

```python
{"url": "http://shop.example.com/item/7?color=red",
 "title": "商品7", "date": "2026-01-02", "views": 42}
```

`py example/app.py` 跑内联样本的成品输出（首行格式不必逐字一致，数字要一致）：

```text
原始 6 条 → 清洗后 4 条 → 新入库 4 条
   浏览数  日期          标题
    42  2026-01-02  商品7  <- http://shop.example.com/item/7?color=red
     0  -  文章A  <- https://blog.example.cn/post/a?a=1&b=2
     0  -  头条一  <- https://news.example.com/one
     0  -  头条二  <- https://www.news.example.com/two?x=1
```

## 3. 里程碑

| 阶段 | 目标 | 检查点 |
|---|---|---|
| M1 规范化 | `normalize_url` 五连改：大小写、默认端口、fragment、utm、参数排序 | 单独 `py -c "import app; print(app.normalize_url('HTTP://Example.COM:80/a/?utm_source=x#f'))"` 看到干净结果 |
| M2 解析+清洗 | 一个 JSON、一个 HTML 样本文件能 extract，clean 后条数符合手算 | verify 探测 2–5 绿 |
| M3 入库+报告 | sqlite3 建表、幂等插入、降序报告 | verify 探测 6–8 绿；用 `py -c` 手工开库 `SELECT` 核对一眼 |
| M4 全流程 | `main([])` 离线跑通、零残留 | verify 探测 9 绿；`git status` 干净 |

## 4. 验收标准（= verify.py 探测清单）

1. 模块可导入、五个契约函数齐全、无副作用。
2. `normalize_url` 四个标准用例逐字相等。
3. `extract_records` 解析 JSON 样本得 3 条、键齐全。
4. `extract_records` 解析 HTML 样本得 3 条 `<a>`。
5. `clean_records` 把同一 URL 的两种写法合成一条，坏字段兜底，无 url 行被丢弃。
6. `save_records` 建表 `records` 并返回新行数 3。
7. 重复 `save_records` 返回 0、总行数不变（幂等）。
8. `report` 降序、dict 行、`limit` 生效。
9. `main([])` 全流程返回 0 且在项目目录**零残留**。
10. （可选）`fetch` 存在且 requests 是延迟导入；未装 requests 时打印 `[缺依赖]` 不算失败。

**额外自拟一条**：给你的清洗函数加一条规则——标题为空时退化用 URL 最后一段路径充当标题，
并自己构造一条样本验证。

### 交卷前自查

| 问题 | 为什么要问 |
|---|---|
| `sqlite3.connect` 的连接在任何分支下都会 `close` 吗？ | Windows 上不关的 .db 文件删不掉，临时目录清理会失败（L06 try/finally） |
| `INSERT` 用了 `?` 占位符而不是 f-string 拼 SQL 吗？ | 标题里出现一个 `'` 你的入库就崩——这不只是注入问题，是健壮性问题（L13） |
| `requests` 只出现在 `fetch()` 函数体内部吗？ | 判分离线，顶层 import 会让 10 条探测全灭（L09/L11） |
| 同一批数据连跑两遍 `save_records`，行数不变吗？ | 幂等是采集工具的底线，断点续跑的前提（L13 UNIQUE） |

## 5. 参考实现提示（代码在 example/app.py）

| 里程碑 | 关键思路 | 该用的标准库 |
|---|---|---|
| M1 | `urlsplit` 拆五段 → 改 scheme/netloc → `parse_qsl` 过滤排序 → `urlencode` → `urlunsplit` 拼回 | `urllib.parse` |
| M2 | JSON 用 `json.loads` + `dict.get(k, 默认值)`；HTML 继承 `HTMLParser`，`handle_starttag` 记 href、`handle_endtag` 收文字 | `json`、`html.parser` |
| M3 | 去重用一个 `seen: set[str]`；每个 `int(...)`/`strptime(...)` 都包 `try/except ValueError` | L02 集合、L06 异常 |
| M3 | `conn.executemany("INSERT OR IGNORE ...")` + `conn.total_changes` 前后差 = 新插入行数 | `sqlite3` |
| M4 | 建库路径 = `tempfile.TemporaryDirectory()` 里，`with conn` 或 try/finally 里 close | `tempfile`、L06 上下文管理器 |

## 6. 常见错（Java 老手三连）

1. **JDBC 思维写 SQLite**：拼字符串 SQL、每条单独 execute 不开事务。Python 的 `sqlite3` 默认自动开事务，
   用 `executemany` + 一次 `commit`；参数一律 `?` 占位符，这是 L13 反复强调的防注入。
2. **忘了连接不关、文件留在临时目录外**。Windows 上没 close 的 sqlite 文件会锁住删不掉，
   下次判分直接报错。用 `with sqlite3.connect(...) as conn:` 只管事务，close 仍需显式（这是 Python 与 try-with-resources 的差异），或 try/finally。
3. **在顶层 `import requests`**。本机没装/判分离线时，verify 一 import 你的模块就全体阵亡。
   可选依赖永远延迟导入到函数体内，这是本项目的核心考点之一。

## 7. 进阶

- 装上 `requests` 后：实现 `fetch()`，加 User-Agent、超时、重试（指数退避），读 robots 常识（原文 Day61、番外篇反爬）。
- 把 SQLite 换 MySQL：`pip install pymysql`，表名/列名加反引号，`?` 占位符换成 `%s`——体会 L13 说的"接口在、方言在"。
- 断点续传：记录已见 URL 集合进一张 `seen_urls` 表，重启后先查再抓。
- 给清洗函数写 pytest 用例：`pip install pytest; py -m pytest`（L14）。
- 全部加类型注解并跑 `py -m mypy app.py`。

## 8. 回原文

| 想要 | 原文 |
|---|---|
| JSON 序列化/反序列化 | [Day21-30/22.对象的序列化和反序列化.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/22.%E5%AF%B9%E8%B1%A1%E7%9A%84%E5%BA%8F%E5%88%97%E5%8C%96%E5%92%8C%E5%8F%8D%E5%BA%8F%E5%88%97%E5%8C%96.md) |
| 读写文本文件与异常 | [Day21-30/21.文件读写和异常处理.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/21.%E6%96%87%E4%BB%B6%E8%AF%BB%E5%86%99%E5%92%8C%E5%BC%82%E5%B8%B8%E5%A4%84%E7%90%86.md) |
| 网络采集概述（含反爬礼仪） | [Day61-65/61.网络数据采集概述.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day61-65/61.%E7%BD%91%E7%BB%9C%E6%95%B0%E6%8D%AE%E9%87%87%E9%9B%86%E6%A6%82%E8%BF%B0.md) |
| requests 获取网络资源 | [Day61-65/62.用Python获取网络资源-1.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day61-65/62.%E7%94%A8Python%E8%8E%B7%E5%8F%96%E7%BD%91%E7%BB%9C%E8%B5%84%E6%BA%90-1.md) |
| HTML 解析 | [Day61-65/62.用Python解析HTML页面-2.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day61-65/62.%E7%94%A8Python%E8%A7%A3%E6%9E%90HTML%E9%A1%B5%E9%9D%A2-2.md) |
| Python 接数据库（MySQL 版） | [Day36-45/44.Python接入MySQL数据库.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day36-45/44.Python%E6%8E%A5%E5%85%A5MySQL%E6%95%B0%E6%8D%AE%E5%BA%93.md) |

主索引与判分机制见 [../../README.md](../../README.md)。
