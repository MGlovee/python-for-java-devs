#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查仓库内 Markdown 的本地链接是否可解析（相对路径 + 锚点）。

用法:
    python tools/linkcheck.py            # 检查全部 .md
    python tools/linkcheck.py -v         # 额外打印每个被检查的链接

只校验仓库内链接；http(s) 外链不联网验证。
退出码：0 全部可解析；1 存在断链。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
LINK_RE = re.compile(r"\[[^\]]*\]\((?P<url>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
SKIP_PREFIX = ("http://", "https://", "mailto:", "file://", "tel:")


def slugify(heading: str) -> str:
    """近似 GitHub 的标题锚点规则（够用于本仓库的中英文标题）。"""
    text = heading.strip().lower()
    text = re.sub(r"[`*_~]", "", text)
    text = re.sub(r"[^\w\u4e00-\u9fff\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text


def anchors_of(path: Path) -> set[str]:
    out: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            out.add(slugify(m.group(2)))
    return out


def main() -> int:
    verbose = "-v" in sys.argv
    broken: list[str] = []
    checked = 0

    for md in sorted(ROOT.rglob("*.md")):
        if any(part in {".git", "node_modules", ".idea"} for part in md.parts):
            continue
        text = md.read_text(encoding="utf-8")
        for m in LINK_RE.finditer(text):
            url = m.group("url").strip()
            if url.startswith(SKIP_PREFIX) or not url:
                continue
            checked += 1
            target, _, anchor = url.partition("#")
            target = unquote(target)

            if target:
                resolved = (md.parent / target).resolve()
                if not resolved.exists():
                    broken.append(f"{md.relative_to(ROOT)} -> {url}  (文件不存在)")
                    continue
                if anchor and resolved.suffix == ".md":
                    if slugify(anchor) not in anchors_of(resolved):
                        broken.append(f"{md.relative_to(ROOT)} -> {url}  (锚点不存在)")
            elif anchor and slugify(anchor) not in anchors_of(md):
                broken.append(f"{md.relative_to(ROOT)} -> #{anchor}  (锚点不存在)")

            if verbose:
                print(f"  ok  {md.relative_to(ROOT)} -> {url}")

    print(f"检查了 {checked} 条本地链接，断链 {len(broken)} 条")
    for item in broken:
        print("  BROKEN " + item)
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
