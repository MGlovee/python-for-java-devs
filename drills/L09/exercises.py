# -*- coding: utf-8 -*-
"""L09 练习工作表 —— 把每个函数里的 `raise NotImplementedError` 删掉，写上你的实现。

判分：  py check.py L09 -v
看答案：py check.py L09 --solution   （建议卡住 15 分钟以上再看）

本课讲义要建 venv、跑 pip，但**练习全部是纯函数**：解析文本、比较版本、给 import 分类，
不联网、不建环境、不碰仓库外的文件。
"""
from __future__ import annotations


# ---------- 第一组：挖空题（有提示，照着填） ----------

def top_level_package(import_line: str) -> str:
    """从一条 import 语句里取"顶层包名"（第一个点号之前的部分）。

    输入保证是三种形态之一（可能有首尾空白）：
    - "import NAME" 或 "import NAME as ALIAS" 或 "import NAME.sub"
    - "from NAME import ..." 或 "from NAME.sub import ..."
    提示：先 strip，split() 拿词，取 "import"/"from" 之后的那个词，再 partition('.') 取头段。
    >>> top_level_package("from collections.abc import Mapping")
    'collections'
    >>> top_level_package("import os.path as p")
    'os'
    """
    raise NotImplementedError


def version_key(version: str) -> tuple[int, ...]:
    """把 "1.2.10" 转成 (1, 2, 10) —— 元组比较天然满足 1.10 > 1.9，字符串比较则会输。

    提示：tuple(int(part) for part in version.split("."))；非数字段会自己抛 ValueError，不用管。
    >>> version_key("3.14.0")
    (3, 14, 0)
    """
    raise NotImplementedError


def parse_requirements(text: str) -> list[tuple[str, str]]:
    """解析 requirements.txt 的文本内容，返回 [(包名, 版本), ...]（保持原顺序）。

    规则：每行先 strip；空行和以 "#" 开头的注释行跳过；
    其余行必须是 "name==version"（按**第一个** == 分割，两侧再 strip 一次）。
    不符合格式的行抛 ValueError（消息里带上该行内容）。
    提示：splitlines() 遍历；partition("==") 分割。
    >>> parse_requirements("# c\\n\\nflask==2.0.1\\n")
    [('flask', '2.0.1')]
    """
    raise NotImplementedError


def dedupe_imports(lines: list[str]) -> list[str]:
    """给一组 import 语句去重：同一个**顶层包**只保留第一次出现的整行，顺序不变。

    提示：seen 集合 + "取顶层包名"的判断逻辑（第 1 题同款语义，就地重写即可）。
    返回的是原样的整行字符串（已 strip）。
    >>> dedupe_imports(["import os", "import os.path", "import sys"])
    ['import os', 'import sys']
    """
    raise NotImplementedError


def is_stdlib(name: str) -> bool:
    """判断顶层模块名是否属于标准库（不查三方库、不查本地文件）。

    提示：Python 3.10+ 标准答案就在 `sys.stdlib_module_names`（一个 frozenset）。
    >>> is_stdlib("json"), is_stdlib("requests")
    (True, False)
    """
    raise NotImplementedError


def max_version(candidates: list[str]) -> str:
    """返回候选版本号里最大的那个（按数字段比较："1.10" > "1.9"）。
    候选列表为空时抛 ValueError。

    提示：max(candidates, key=version_key 的等价实现)。第 2 题的语义可参考。
    >>> max_version(["1.9", "1.10", "1.2"])
    '1.10'
    """
    raise NotImplementedError


# ---------- 第二组：只给需求（独立写） ----------

def compare_versions(a: str, b: str) -> int:
    """比较两个点分版本号：a 小返回 -1，相等返回 0，a 大返回 1。

    要求：
    - 按数字段逐位比较；
    - 段数不同时短的**右侧补 0**："1.2" 与 "1.2.0" 相等；
    - 任何一段不是纯数字时抛 ValueError。
    """
    raise NotImplementedError


def requirements_report(text: str, installed: dict[str, str]) -> list[str]:
    """对照"已安装表"给出体检报告，输入顺序、每包一行：
    - 未安装：            f"{name} MISSING"
    - 装低了：            f"{name} OUTDATED (installed {have}, need {want})"
    - 版本恰好或更高：    f"{name} OK"

    解析规则同 parse_requirements（注释/空行跳过，坏行 ValueError）；
    版本高低用 compare_versions 的语义（段数不同补零、数字段比较）。
    示例（installed={"flask": "2.0.0", "rich": "13.3.0"}）：
    "flask==2.0.1\\nredis==5.0.0\\nrich==13.3.0\\n"
    -> ["flask OUTDATED (installed 2.0.0, need 2.0.1)", "redis MISSING", "rich OK"]
    """
    raise NotImplementedError


def classify_imports(lines: list[str], local: set[str]) -> dict[str, list[str]]:
    """把一批 import 语句按顶层包归入三类，返回固定三键的字典：
    {"standard": [...], "third_party": [...], "local": [...]}

    规则：
    - 先按语句出现顺序取每个顶层包的第一次出现（重复的顶层包只算一次）；
    - 顶层包在 local 集合里 -> "local"；否则在 sys.stdlib_module_names 里 -> "standard"；
      否则 -> "third_party"；
    - 每个列表内部保持首次出现顺序。
    示例：classify_imports(["import os", "import requests", "import myapp.db"],
    {"myapp"}) == {"standard": ["os"], "third_party": ["requests"], "local": ["myapp"]}
    """
    raise NotImplementedError


def unique_sorted_requirements(text: str) -> list[str]:
    """把 requirements 文本整理成"干净的锁定行列表"：
    - 解析规则同 parse_requirements；
    - 同一个包出现多次时保留**更高**版本（用 compare_versions 的语义判断高低）；
    - 返回形如 ["flask==2.0.1", "rich==13.3.0"] 的列表，按包名字典序升序排列。
    """
    raise NotImplementedError
