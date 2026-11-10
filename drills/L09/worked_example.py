# -*- coding: utf-8 -*-
"""L09 完整样例 —— 直接跑：py drills/L09/worked_example.py

演示"import 即执行"、模块搜索路径、__pycache__ 的真实路径、标准库判定、
requirements 解析与体检。全程纯内存，不联网、不建 venv（venv/pip 命令照讲义 ② 手动做一遍即可）。
"""
from __future__ import annotations

import importlib.util
import sys

# 下面这行 import 会在"导入的那一刻"往屏幕打印《Python 之禅》——
# 这就是 Java 里没有的现象：import 不是声明依赖，是【执行那个文件】。
import this  # noqa: F401,E402

REQUIREMENTS = """\
# 手工维护的直接依赖
flask==2.0.0
flask==2.0.1        # 写重了，后文取更高版本

rich==13.3.0
redis==5.0.0
"""
INSTALLED = {"flask": "2.0.1", "rich": "13.3.0"}   # 假装 pip list 的结果

IMPORT_LINES = [
    "import os",
    "import requests",
    "import myapp.db",
    "from os.path import join",
    "from collections.abc import Mapping",
    "import flask",
]


def top_of(line: str) -> str:
    return line.strip().split()[1].partition(".")[0]


def parse_requirements(text: str) -> list[tuple[str, str]]:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, sep, version = line.partition("==")
        if "#" in version:                        # 演示用：顺手去掉行尾注释
            version = version.partition("#")[0]
        if not sep or not name.strip() or not version.strip():
            raise ValueError(f"坏行: {line!r}")
        out.append((name.strip(), version.strip()))
    return out


def demo_import_is_execution():
    print("this 在 sys.modules 里吗:", "this" in sys.modules,
          "—— 导入过的模块缓存在这里，第二次 import 不再执行文件")
    print("本文件的 __name__ 是:", __name__,
          "—— 用 py 直接跑时为 '__main__'，被别人 import 时为模块名")


def demo_search_path():
    print("sys.path 前两项:", sys.path[:2], "—— 脚本目录/工作区优先，然后 stdlib，最后 site-packages")
    print("os 从哪里加载:", __import__("os").__file__)
    cache = importlib.util.cache_from_source(__file__)
    print("本文件对应的 .pyc 路径:", cache.split("Python-100-Days")[-1],
          "—— 源码没改就直接用字节码")


def demo_classify():
    unique = list(dict.fromkeys(top_of(line) for line in IMPORT_LINES))
    groups = {"standard": [], "third_party": [], "local": []}
    for name in unique:
        if name in {"myapp"}:
            groups["local"].append(name)
        elif name in sys.stdlib_module_names:
            groups["standard"].append(name)
        else:
            groups["third_party"].append(name)
    print("import 归组:", groups)
    print("'requests' 是标准库吗:", "requests" in sys.stdlib_module_names,
          "—— ModuleNotFoundError 通常是没 pip install，不是路径问题")


def demo_requirements():
    pairs = parse_requirements(REQUIREMENTS)
    print("解析结果（原顺序）:", pairs)
    best: dict[str, str] = {}
    for name, ver in pairs:
        key = tuple(int(p) for p in ver.split("."))
        if name not in best or key > tuple(int(p) for p in best[name].split(".")):
            best[name] = ver
    locked = [f"{n}=={best[n]}" for n in sorted(best)]
    print("去重取高、按名排序:", locked)
    for name, want in pairs:
        have = INSTALLED.get(name)
        status = "MISSING" if have is None else (
            "OUTDATED" if tuple(map(int, have.split("."))) < tuple(map(int, want.split(".")))
            else "OK")
        print(f"  {name:<8} 要求 {want:<8} 装了 {have or '-':<8} -> {status}")
    print("字符串比较的陷阱:", "1.9" > "1.10", "（True！所以版本号必须转 int 元组比）")


if __name__ == "__main__":
    demo_import_is_execution()
    demo_search_path()
    demo_classify()
    demo_requirements()
