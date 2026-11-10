# -*- coding: utf-8 -*-
"""L09 判分用例。别改这个文件 —— 它就是考官。

单独跑：py -m pytest drills/L09 -q    （装了 pytest 才有效）
推荐跑：py check.py L09 -v            （零依赖）
"""
import pytest
from exercises import (classify_imports, compare_versions, dedupe_imports,
                       is_stdlib, max_version, parse_requirements,
                       requirements_report, top_level_package,
                       unique_sorted_requirements, version_key)


def test_01_top_level_plain_import():
    assert top_level_package("import os") == "os"
    assert top_level_package("import os.path") == "os", "只取第一个点号前的顶层包"


def test_02_top_level_variants():
    assert top_level_package("from collections.abc import Mapping") == "collections"
    assert top_level_package("import pydantic as pd") == "pydantic", "as 别名不影响顶层名"
    assert top_level_package("  from myproj.db import connect  ") == "myproj", "容忍首尾空白"


def test_03_version_key():
    assert version_key("1.2.10") == (1, 2, 10)
    assert version_key("3") == (3,)


def test_04_max_version_numeric():
    # 字符串比较会得出 "1.9" > "1.10" 的错果 —— 必须按数字段
    assert max_version(["1.9", "1.10", "1.2"]) == "1.10"
    assert max_version(["2.0.1"]) == "2.0.1"


def test_05_max_version_empty():
    with pytest.raises(ValueError):
        max_version([])


def test_06_parse_requirements_skips_noise():
    text = "# comment\n\n  flask==2.0.1  \nrich==13.3.0\n# another\n"
    assert parse_requirements(text) == [("flask", "2.0.1"), ("rich", "13.3.0")]


def test_07_parse_requirements_keeps_order_and_rejects_bad():
    assert parse_requirements("b==1\na==2") == [("b", "1"), ("a", "2")], "保持原顺序"
    with pytest.raises(ValueError):
        parse_requirements("flask")            # 没有 ==
    with pytest.raises(ValueError):
        parse_requirements("==2.0")            # 包名为空
    with pytest.raises(ValueError):
        parse_requirements("rich==")           # 版本为空


def test_08_dedupe_imports_first_wins():
    lines = ["import os", "import os.path", "from os import getcwd", "import sys"]
    assert dedupe_imports(lines) == ["import os", "import sys"], "同顶层包留第一次出现的整行"


def test_09_dedupe_imports_edges():
    assert dedupe_imports([]) == []
    assert dedupe_imports(["import requests", "import rich"]) == ["import requests", "import rich"]


def test_10_is_stdlib_true_cases():
    for name in ("os", "sys", "json", "contextlib", "itertools"):
        assert is_stdlib(name), f"{name} 是标准库"


def test_11_is_stdlib_false_cases():
    for name in ("requests", "flask", "numpy", "myapp"):
        assert not is_stdlib(name), f"{name} 不是标准库"


def test_12_compare_versions_basic_and_padding():
    assert compare_versions("1.9", "1.10") == -1
    assert compare_versions("2.1", "2.0") == 1
    assert compare_versions("1.2", "1.2.0") == 0, "短的右侧补零：1.2 == 1.2.0"
    assert compare_versions("1.2.0.1", "1.2") == 1


def test_13_compare_versions_rejects_garbage():
    with pytest.raises(ValueError):
        compare_versions("1.x", "1.0")
    with pytest.raises(ValueError):
        compare_versions("1.0", "2-beta")


def test_14_requirements_report_three_states():
    installed = {"flask": "2.0.0", "rich": "13.3.0"}
    text = "flask==2.0.1\nredis==5.0.0\nrich==13.3.0\n"
    assert requirements_report(text, installed) == [
        "flask OUTDATED (installed 2.0.0, need 2.0.1)",
        "redis MISSING",
        "rich OK",
    ], "三种状态各一行，顺序同输入"


def test_15_requirements_report_empty_and_newer():
    assert requirements_report("", {}) == []
    assert requirements_report("# nothing\n", {"a": "1"}) == []
    # 装得比要求新也算 OK
    assert requirements_report("a==1.0", {"a": "1.10"}) == ["a OK"]


def test_16_classify_imports_groups():
    lines = ["import os", "import requests", "import myapp.db", "from os import getcwd",
             "import rich"]
    got = classify_imports(lines, {"myapp"})
    assert got == {"standard": ["os"], "third_party": ["requests", "rich"], "local": ["myapp"]}, (
        "重复顶层包只计一次；三键齐全；组内保持首现顺序")


def test_17_classify_imports_empty():
    assert classify_imports([], {"x"}) == {"standard": [], "third_party": [], "local": []}


def test_18_unique_sorted_requirements():
    text = "rich==13.3.0\n# c\nflask==2.0.0\n\nflask==2.0.1\nrich==13.2.0\n"
    assert unique_sorted_requirements(text) == ["flask==2.0.1", "rich==13.3.0"], (
        "同包取更高版本，行按包名字典序")
    assert unique_sorted_requirements("") == []
