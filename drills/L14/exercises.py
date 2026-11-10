# -*- coding: utf-8 -*-
"""L14 练习工作表 —— 把每个函数里的 `raise NotImplementedError` 删掉，写上你的实现。

这一课的四件工具，`pytest` / `ruff` / `mypy` 都没装，所以练习**不导入它们**，
而是让你用标准库把它们做的事各写一遍，跑完就懂原理：

| 函数 | 对应真实工具 | 用的标准库 |
|---|---|---|
| 1-5 | `logging` 的分级与继承 | `logging` |
| 4 | pytest 结尾那行摘要 | `re` |
| 6 | 命令行入口 | `argparse` |
| 7-8 | 自己写断言与"抓输出" | `io` / `contextlib` |
| 9 | 性能基线 | `timeit` |
| 10 | `ruff` 的一条命名规则 | `ast` + `re` |

纪律：**不许改全局日志配置**（`basicConfig` / `root.setLevel` 都不许动），
所有函数纯进纯出，测试才好断言。
"""
from __future__ import annotations

import logging

# ---------- 第一组：挖空题（有提示，照着填） ----------

def level_name_to_no(name: str) -> int:
    """把级别名转成数字：`"INFO"` → 20，`"WARNING"` → 30。

    提示：`logging.getLevelName("INFO")` 直接给 20。
    坑：传进去它认不出的名字（小写 `"info"`、乱写的 `"FOO"`）时，它**不抛异常**，
    而是回一个形如 `"Level info"` 的**字符串** —— 所以要自己判类型并抛 `ValueError`。
    """
    raise NotImplementedError


def should_log(record_level: int, logger_level: int) -> bool:
    """这条日志会不会被输出？（记录级别 >=  logger 级别 才输出）

    提示：一条 `>=` 就够。注意边界：logger 是 `WARNING`(30)，
    `WARNING`(30) 的记录**会**输出，`INFO`(20) 不会 —— Java 里习惯反了的人常写错。
    """
    raise NotImplementedError


def effective_level(logger_level: int | None, parent_level: int) -> int:
    """算出这条 logger 真正生效的级别（模拟日志的**继承**）。

    要求：`logger_level` 是 `None` 或 `logging.NOTSET`(0) → 用父级 `parent_level`；
    否则用自己的，**即使比自己低**（子 logger 显式设了就得听它的）。
    """
    raise NotImplementedError


def parse_pytest_summary(text: str) -> dict[str, int]:
    """把 pytest 结尾那行摘要解析成计数：结果固定四个键。

    输入形如 `"==== 5 passed, 2 failed, 1 error, 4 skipped in 0.12s ===="`。
    要求：返回 `{"passed": …, "failed": …, "errors": …, "skipped": …}`；
    摘要里没出现的键给 `0`；`"no tests ran"` 这种一行数字都没有 → 四个键全 0。
    提示：`re.search(r"(\\d+) passed", text)` 一项一项取，别指望一次性切干净。
    """
    raise NotImplementedError


def format_log_record(name: str, level: int, message: str) -> str:
    """手工造一条日志记录，用模板 `"%(levelname)s|%(name)s|%(message)s"` 渲染成文本。

    提示：
        record = logging.LogRecord(name, level, __file__, 1, message, (), None)
        return logging.Formatter("%(levelname)s|%(name)s|%(message)s").format(record)
    坑：`levelname` 不是你自己写的字符串，它由**级别数字**换算而来；
    传一个没注册过的数字（如 25）时，`logging.getLevelName(25)` 回 `"Level 25"`，
    所以输出是 `"Level 25|app|boom"` 而不是报错。
    """
    raise NotImplementedError


def parse_cli_args(argv: list[str]) -> dict[str, object]:
    """用 `argparse` 解析命令行，返回 `vars(args)` 那个字典。

    要求（三个选项，参数名就是这个三个键）：
        -n / --name   str，默认 "world"
        -c / --count  int，默认 1
        -v / --verbose 开关（`action="store_true"`），默认 False
    坑：非法参数（`--count abc`、`--nope`）时 argparse 自己 **打印用法并 `SystemExit`**，
    不会抛 ValueError —— 这一点跟 Java 的 CLI 库很不一样，别去 catch ValueError。
    """
    raise NotImplementedError


# ---------- 第二组：只给需求（独立写） ----------

def expect_raises(func, expected_exc: type[BaseException]) -> str:
    """自己实现 `pytest.raises` 的语义：调用 `func()`，必须抛出 `expected_exc`。

    要求：1) 抛出（或 `expected_exc` 的子类）→ 返回异常的字符串形式 `str(exc)`；
          2) **什么都没抛** → 抛 `AssertionError`，消息里带上期望的异常名；
          3) 抛了别的类型 → 原样让它往上冒，不要吞掉也不要转成 AssertionError。
    """
    raise NotImplementedError


def capture_stdout(func, *args) -> tuple[str, object]:
    """抓函数打印的内容：返回 `(stdout 文本, 函数返回值)`。

    要求：1) 用 `io.StringIO()` + `contextlib.redirect_stdout`，不许手动换 `sys.stdout`
             （手动换的话异常路径容易忘了还原，测试会串味）；
          2) 函数抛异常时异常照常往上走，但 `sys.stdout` 必须已经恢复原样；
          3) 只抓这一次调用的输出，别把全局状态改了。
    """
    raise NotImplementedError


def measure_runtime(stmt: str, number: int = 1000) -> float:
    """用 `timeit` 量一段代码：返回**单次执行**平均秒数（总耗时 / number）。

    要求：1) `number <= 0` → 抛 `ValueError`（别把 0 传给 timeit，它返回 0 秒，
             于是你算出个"0 纳秒"的漂亮结论）；
          2) 语法错误的 `stmt` 让 `SyntaxError` 原样抛出；
          3) `timeit` 默认用 `time.perf_counter()`（**挂钟时间**，不是 CPU 时间），
             并在计时期间自动关 GC，这正是它比手写循环靠谱的地方，别退回手写。
    """
    raise NotImplementedError


def find_bad_function_names(source: str) -> list[str]:
    """迷你 linter：找出不符合 snake_case 的函数名，按行号报出来（就是 `ruff` 的一条规则）。

    要求：1) 用 `ast.parse(source)` + `ast.walk`，`def` 和 `async def` 都要查；
          2) 合法名 = 任意个前导下划线 + 小写字母开头 + 之后只有小写字母/数字/下划线，
             即 `re.fullmatch(r"_*[a-z][a-z0-9_]*", name)`；
          3) 每条消息格式**固定**：`f"L{node.lineno}: N802 函数名应使用 snake_case: {node.name}"`；
          4) 结果按行号升序（`ast.walk` 是层序遍历，不保证行号顺序，要自己排）；
          5) 源码本身语法错 → 让 `SyntaxError` 抛出，不要返回空列表糊弄过去。
    """
    raise NotImplementedError
