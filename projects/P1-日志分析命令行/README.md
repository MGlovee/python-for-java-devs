# P1 · 日志分析命令行工具

> 本项目的完整可运行参考实现见 example/app.py，卡住 20 分钟以上再看。

| 项 | 值 |
|---|---|
| 交付物 | 一个 `app.py`：给定 Nginx/access 日志文件，输出 PV/UV、状态码分布、Top-N URL、慢请求清单 |
| 预计工时 | 4–6 小时 |
| 用到的课 | L01–L09（正则与日期 L03、数据结构 L02、函数参数 L04、异常 L06、生成器 L07、模块与 argparse L09） |
| 依赖 | **零第三方依赖**，纯标准库 |
| 验收 | `py verify.py`（10 条探测全 `[通过]`，退出码 0） |

---

## 1. 需求

- 读取一个日志文件（位置参数），按行解析**共同日志格式（CLF）**：
  `IP - 用户 [时间] "方法 路径 协议" 状态码 字节数 [可选:耗时毫秒]`
  本项目在标准 CLF 之后扩展了**行尾可选的一个整数 = 请求耗时（毫秒）**，用于慢请求统计。
- 统计并输出：
  - `pv`：成功解析且未被过滤条件排除的行数；
  - `uv`：去重后的 IP 数；
  - `status_counts`：状态码分布；
  - `top_urls`：按出现次数降序的 URL，受 `--top` 截断；
  - `slow_requests` / `slow_count`：耗时 ≥ 阈值的请求（没有耗时字段的行不参与慢判定）；
  - `skipped`：解析失败被跳过的行数。
- 命令行参数（**必须用 `argparse`**）：

| 参数 | 默认 | 含义 |
|---|---|---|
| `logfile`（位置） | 必填 | 日志文件路径 |
| `--top N` | 10 | Top-N URL |
| `--min-status CODE` | 无 | 只统计状态码 ≥ CODE 的行 |
| `--since YYYY-MM-DD` | 无 | 只统计该日期（**按 UTC 零点解释**）及之后的行 |
| `--slow-ms MS` | 1000 | 慢请求阈值 |
| `--json` | 关 | 输出**单个 JSON 对象**到 stdout，供脚本消费 |

- 边界与异常处理要求：
  - 非法行（截断、乱码、`#` 注释）：**跳过并计入 skipped**，不许崩溃、不许打印堆栈；
  - 字节数为 `-` 时按 `0` 处理；
  - 文件不存在：stderr 打印一句中文错误，**退出码非 0**（建议 2），无 Traceback；
  - `--since` 格式错误：同样友好报错、非 0 退出；
  - 空文件：正常输出全 0 结果，退出码 0；
  - 默认人类可读输出；`--json` 时 stdout 只允许出现那一个 JSON 对象。

## 2. 函数契约表（verify.py 按这个探测）

### CLF 行 → 记录字段映射（`parse_line` 的契约细节）

| 日志片段 | 记录键 | 类型 | 约定 |
|---|---|---|---|
| `10.0.0.1`（第一个字段） | `ip` | `str` | UV 按它去重 |
| `-`（identd） | 不保留 | — | 直接丢弃 |
| `[01/Oct/2026:08:12:01 +0800]` | `time` | `datetime`（aware） | 格式 `%d/%b/%Y:%H:%M:%S %z`，保留原始偏移 |
| `"GET /path HTTP/1.1"` | `method` / `path` | `str` | path 含 query string，不去掉 |
| `200` | `status` | `int` | 三位数；字符串比较会错 |
| `6021` 或 `-` | `size` | `int` | `-` 归一化为 `0` |
| 行尾可选 `2680` | `latency_ms` | `int \| None` | 没有该字段就是 `None`，不参与慢判定 |

| 函数 | 签名 | 返回 | 异常 |
|---|---|---|---|
| `parse_line` | `(line: str) -> dict \| None` | 键：`ip`(str)、`time`(带日志原始时区的 aware `datetime`)、`method`、`path`(str)、`status`(int)、`size`(int，`-`→0)、`latency_ms`(int \| None) | 非法行返回 `None`，**不抛异常** |
| `analyze` | `(lines: Iterable[str], *, top=10, min_status=None, since=None, slow_ms=None) -> dict` | `{"pv","uv","skipped","status_counts","top_urls","slow_count","slow_requests"}`；`status_counts` 为 `{状态码字符串: 次数}`；`top_urls` 为 `[{"url","count"},…]` 降序；结果必须可直接 `json.dumps` | 不抛异常 |
| `build_parser` | `() -> argparse.ArgumentParser` | 定义上表全部参数 | — |
| `main` | `(argv=None) -> int` | 退出码；文件/参数错误返回非 0 | — |

入口必须是 `if __name__ == "__main__": sys.exit(main())`——**import 该模块时不得执行任何流程**
（verify 用 importlib 加载你的文件，import 副作用会污染所有探测）。

### 输出样例（对着它核对你的 CLI）

```text
$ py app.py example/sample_access.log --top 3
PV: 40  UV: 9  跳过的非法行: 1
状态码分布: 200×31  301×2  404×4  500×3
Top-3 URL:
    12  /api/orders
     8  /index.html
     6  /static/app.js
慢请求（>= 1000ms）: 4 条
    2680ms  10.0.0.5        /api/orders
    ...
```

`--json` 时 stdout 必须是**单个可 `json.loads` 的对象**，字段与契约表返回 dict 一致：

```json
{"pv": 40, "uv": 9, "skipped": 1, "status_counts": {"200": 31, "301": 2, "404": 4, "500": 3},
 "top_urls": [{"url": "/api/orders", "count": 12}], "slow_count": 4,
 "slow_requests": [{"ip": "10.0.0.5", "path": "/api/orders", "latency_ms": 2680}]}
```

## 3. 里程碑

| 阶段 | 目标 | 检查点（跑起来看到什么） |
|---|---|---|
| M1 解析器 | `parse_line` + `analyze` 只对 `example/sample_access.log` 算出 pv=40、uv=9、skipped=1 | `py verify.py example/app.py` 的第 2–8 条是绿的（先用你自己的 app.py 替换路径） |
| M2 过滤 | `min_status` / `since` / `slow_ms` 三个开关生效 | 探测 7、8 绿；对照本表手工核对一份 10 行的手抄小日志 |
| M3 CLI | argparse 全部参数 + `--json` + 错误处理 | `py verify.py` 的 9、10 绿 |
| M4 收尾 | 代码 100 行左右、有类型注解、无 Java 味 | `py ../../check.py` 里 L03/L04/L06 练习仍是绿的（没把旧知识还回去） |

## 4. 验收标准（= verify.py 的探测清单）

1. 模块可导入且无副作用。
2. `parse_line` 标准 CLF 行字段与类型正确（status 是 int、time 是 datetime）。
3. `parse_line` 非法行返回 `None` 不崩溃。
4. `analyze` 的 pv / uv / skipped 正确（8 行样本，3 个 IP，1 行坏数据）。
5. `status_counts` 分布正确。
6. `top_urls` 降序且受 `top` 参数截断。
7. `min_status=400` 只剩 5xx/4xx。
8. `since` 按 UTC 零点过滤。
9. CLI：`--json` 输出合法 JSON 且数字对、`--top` 生效、`--help` 列出四个选项。
10. CLI：文件不存在 → 非 0 退出码且无 Traceback。

**额外自拟一条**：从上面清单里挑一条，把它改写成 `drills/P1/test_app.py` 里的 pytest 风格断言
（本机可用 `py ../../check.py` 的判分机制跑），以后进阶到真 pytest 时直接复用。

### 交卷前自查（三条都答"是"再提交）

| 问题 | 为什么要问 |
|---|---|
| `analyze` 接收的是 `Iterable[str]` 而不是 `list[str]` 吗？ | 传文件句柄才能逐行流式处理，10GB 日志不爆内存（L07） |
| 所有可选参数都是关键字参数（签名里有 `*`）吗？ | `analyze(lines, 400)` 这种位置误传是静默 bug 的温床（L04） |
| 错误信息走 `sys.stderr`、结果走 `sys.stdout` 吗？ | 管道消费 `--json` 时，混在一起就没法 `json.loads` 了（L09/L14） |

## 5. 参考实现提示（不给完整代码，代码在 example/app.py）

| 里程碑 | 关键思路（1–3 行） | 该用的标准库 |
|---|---|---|
| M1 | 一条命名分组正则搞定整行：`(?P<ip>\S+) ... \[(?P<time>...)\] "(?P<method>...) (?P<path>...)..." (?P<status>\d{3}) (?P<size>\d+\|-)`，耗时字段做成可选分组 `(?:\s+(?P<latency>\d+))?` | `re`、`datetime.strptime(fmt="%d/%b/%Y:%H:%M:%S %z")` |
| M1 | `analyze` 收 `Iterable[str]`（文件句柄本身就是），一个 for 攒 records，坏行计数后 `continue` | `collections.Counter`、内置 `set` |
| M2 | 过滤条件全部在 `analyze` 循环内做，参数用 `*` 强制关键字，避免调用方传错位 | L04 的参数家族 |
| M3 | `--since` 解析成 `datetime` 后 `.replace(tzinfo=timezone.utc)`，才能和日志里的 aware datetime 比较——naive 与 aware 相比直接 `TypeError` | `argparse`、`datetime.timezone` |
| M3 | 错误路径统一 `print(..., file=sys.stderr)` + 返回非 0，别 raise 出去甩堆栈 | `sys.stderr` |

## 6. 常见错（Java 老手三连）

1. **正则里用 `.*` 一路吞**。`"(method) (path) [^"]*"` 的协议段用 `.*` 会把引号后内容吃进 path。
   用命名分组 + 精确 `\S+`，Java 里你习惯的 `Matcher.group(int)` 魔法数字在 Python 里就是给自己挖坑。
2. **把 status 留在字符串里比较**。`"404" >= "500"`？字符串比较按字典序，`min_status` 过滤会全错。
   `parse_line` 里就该 `int()`，Python 不会像 Java 那样在声明处帮你定型。
3. **在模块顶层读 `sys.argv` 或直接 open 文件**。被 importlib 加载时立刻炸/卡在 stdin。
   一切副作用收进 `main()`，用 `if __name__ == "__main__"` 守卫——等价于 Java 的 `public static void main`，
   但它是**运行时判断**，不是语言保证。

## 7. 进阶（做完再说）

- 把逐行 `for` 换成生成器管道：`records = (parse_line(l) for l in fh)`，再接 `filter`——大文件不爆内存（L07）。
- 加 `logging` 替代 print，`--verbose` 控制级别（L14 / 原文 Day51）。
- 写 `pyproject.toml` + console entry point，装成 `pipx` 可用的小命令（L09）。
- 全部函数补类型注解后跑 `pip install mypy; py -m mypy app.py`。
- 支持 gzip 日志：`gzip.open` 与 `Path.open` 同一接口，鸭子类型直接换（L05）。

## 8. 回原文（细节都在，按需查字典）

| 想要 | 原文 |
|---|---|
| 正则的完整啰嗦版 | [Day21-30/30.正则表达式的应用.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/30.%E6%AD%A3%E5%88%99%E8%A1%A8%E8%BE%BE%E5%BC%8F%E7%9A%84%E5%BA%94%E7%94%A8.md) |
| 字符串与日期方法全表 | [Day01-20/11.常用数据结构之字符串.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day01-20/11.%E5%B8%B8%E7%94%A8%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E4%B9%8B%E5%AD%97%E7%AC%A6%E4%B8%B2.md) |
| 函数参数家族 / 模块 | [Day01-20/14.函数和模块.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day01-20/14.%E5%87%BD%E6%95%B0%E5%92%8C%E6%A8%A1%E5%9D%97.md)、[16.函数使用进阶.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day01-20/16.%E5%87%BD%E6%95%B0%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6.md) |
| 异常处理与文件读写 | [Day21-30/21.文件读写和异常处理.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/21.%E6%96%87%E4%BB%B6%E8%AF%BB%E5%86%99%E5%92%8C%E5%BC%82%E5%B8%B8%E5%A4%84%E7%90%86.md) |
| 迭代器/生成器进阶 | [Day31-35/31.Python语言进阶.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day31-35/31.Python%E8%AF%AD%E8%A8%80%E8%BF%9B%E9%98%B6.md) |
| PEP8 风格自查 | [番外篇/PEP8风格指南.md](https://github.com/jackfrued/Python-100-Days/blob/master/%E7%95%AA%E5%A4%96%E7%AF%87/PEP8%E9%A3%8E%E6%A0%BC%E6%8C%87%E5%8D%97.md) |

判分机制与闪卡复习见 [../../README.md](../../README.md)；L01 讲义
[L01-语法差异地图.md](../../lessons/L01-语法差异地图.md) 是目前唯一已上线的课，其余课会陆续补齐。
