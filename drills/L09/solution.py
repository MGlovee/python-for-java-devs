# -*- coding: utf-8 -*-
"""L09 参考答案。

别整篇抄 —— 它的价值在于卡住 15 分钟后对照思路。
验证题目本身有没有写错：py check.py L09 --solution
"""
from __future__ import annotations

import sys


def _top(line: str) -> str:
    """内部小工具：取 import 语句的顶层包名（同第 1 题语义，供后面几题复用）。"""
    return line.strip().split()[1].partition(".")[0]


def top_level_package(import_line: str) -> str:
    line = import_line.strip()
    token = line.split()[1]              # "import X..." 和 "from X import ..." 都在第 2 个词
    return token.partition(".")[0]


def version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))   # 非数字段 int() 自己抛 ValueError


def parse_requirements(text: str) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, sep, version = line.partition("==")            # 只按第一个 == 分割
        name, version = name.strip(), version.strip()
        if not sep or not name or not version:
            raise ValueError(f"不是 name==version 格式: {line!r}")
        result.append((name, version))
    return result


def dedupe_imports(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for line in lines:
        stripped = line.strip()
        top = _top(stripped)
        if top not in seen:
            seen.add(top)
            result.append(stripped)
    return result


def is_stdlib(name: str) -> bool:
    return name in sys.stdlib_module_names       # 3.10+ 官方给出的 frozenset，约 300 个


def max_version(candidates: list[str]) -> str:
    if not candidates:
        raise ValueError("候选版本列表为空")
    return max(candidates, key=version_key)


def compare_versions(a: str, b: str) -> int:
    pa, pb = version_key(a), version_key(b)
    width = max(len(pa), len(pb))
    pa += (0,) * (width - len(pa))                # 右侧补零：1.2 == 1.2.0
    pb += (0,) * (width - len(pb))
    return (pa > pb) - (pa < pb)                 # -1 / 0 / 1


def requirements_report(text: str, installed: dict[str, str]) -> list[str]:
    report: list[str] = []
    for name, want in parse_requirements(text):
        have = installed.get(name)
        if have is None:
            report.append(f"{name} MISSING")
        elif compare_versions(have, want) < 0:
            report.append(f"{name} OUTDATED (installed {have}, need {want})")
        else:
            report.append(f"{name} OK")
    return report


def classify_imports(lines: list[str], local: set[str]) -> dict[str, list[str]]:
    groups = {"standard": [], "third_party": [], "local": []}
    seen: set[str] = set()
    for line in lines:
        top = _top(line)
        if top in seen:
            continue
        seen.add(top)
        if top in local:                          # 先本地，再标准库，剩下归三方
            groups["local"].append(top)
        elif is_stdlib(top):
            groups["standard"].append(top)
        else:
            groups["third_party"].append(top)
    return groups


def unique_sorted_requirements(text: str) -> list[str]:
    best: dict[str, str] = {}
    for name, version in parse_requirements(text):
        old = best.get(name)
        if old is None or compare_versions(version, old) > 0:
            best[name] = version
    return [f"{name}=={best[name]}" for name in sorted(best)]
