#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P2 验收脚本 —— 只用标准库，全程离线，临时文件测完即删。

用法：
    py projects/P2-数据采集与入库/verify.py               # 验收项目根下的 app.py
    py projects/P2-数据采集与入库/verify.py example/app.py # 先验参考实现

退出码：0 = 没有红色项；1 = 有未过项或还没写 app.py。
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import sqlite3
import sys
import tempfile
import threading
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
TIMEOUT = 5
stats = {"通过": 0, "未过": 0, "缺依赖": 0}
sys.dont_write_bytecode = True  # 判分不在仓库留 __pycache__


class MissingDep(Exception):
    pass


def _call_with_timeout(func):
    box: dict = {}

    def target():
        try:
            func()
        except BaseException as exc:  # noqa: BLE001
            box["exc"] = exc

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(TIMEOUT)
    if t.is_alive():
        raise TimeoutError(f"单条探测超过 {TIMEOUT}s，检查有没有偷偷联网或死循环")
    if "exc" in box:
        raise box["exc"]


def _probe(title: str, guide: str, func):
    try:
        _call_with_timeout(func)
        stats["通过"] += 1
        print(f"[通过] {title}")
    except MissingDep as exc:
        stats["缺依赖"] += 1
        print(f"[缺依赖] {title} — {exc}（不计失败；若是第三方包在模块顶层被 import，"
              f"把它挪进函数体才是本项目的正解，见 README 需求）")
    except AssertionError as exc:
        stats["未过"] += 1
        print(f"[未过] {title} — {exc or '断言失败'}。{guide}")
    except Exception as exc:  # noqa: BLE001
        stats["未过"] += 1
        print(f"[未过] {title} — 抛了 {type(exc).__name__}: {exc}。{guide}")


def _load(app_path: Path):
    name = "p2_target_app"
    sys.path.insert(0, str(app_path.parent))
    try:
        spec = importlib.util.spec_from_file_location(name, app_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"无法加载 {app_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    except ModuleNotFoundError as exc:
        raise MissingDep(f"pip install {exc.name}") from exc


SAMPLE_JSON = """\
[
  {"url": "HTTP://Shop.Example.com:80/item/7?utm_source=push&color=red",
   "title": " 商品7 ", "date": "2026/1/2", "views": "42"},
  {"url": "http://shop.example.com/item/7?color=red",
   "title": "商品7", "date": "2026-01-02", "views": 41},
  {"url": "https://blog.example.cn/post/a?b=2&a=1#frag",
   "title": "文章A", "date": "坏日期", "views": "很多"}
]
"""

SAMPLE_HTML = """\
<html><body>
  <a href="https://news.example.com/one">头条一</a>
  <p>与链接无关的正文</p>
  <a href="https://www.news.example.com/two?x=1&utm_source=rss">  头条二  </a>
  <a href="https://news.example.com/one#frag">头条一（重复，带锚点）</a>
</body></html>
"""


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) > 1:
        raw = Path(sys.argv[1])
        candidates = [raw]
        if not raw.is_absolute():
            candidates += [PROJECT / raw, Path.cwd() / raw]
        target = next((c for c in candidates if c.is_file()), None)
    else:
        target = PROJECT / "app.py" if (PROJECT / "app.py").is_file() else None
        if target is None and (Path.cwd() / "app.py").is_file():
            target = Path.cwd() / "app.py"

    if target is None:
        print("还没有 app.py。先从 example/ 参考实现看起：")
        print(f"    py {Path(__file__)} example/app.py   # 确认验收脚本本身是绿的")
        return 1
    target = target.resolve()
    print(f"验收对象：{target}")
    print("=" * 60)

    holder: dict = {}

    def load():
        holder["mod"] = _load(target)
        missing = [f for f in ("normalize_url", "extract_records", "clean_records",
                               "save_records", "report")
                   if not callable(getattr(holder["mod"], f, None))]
        assert not missing, f"缺少契约函数：{missing}，见 README 函数契约表"

    _probe("1. 模块可导入，五个契约函数齐全，import 时无副作用",
           "回到 L09：入口收进 __main__ 守卫；回到 L10：读文件不要发生在顶层。", load)
    if "mod" not in holder:
        print("-" * 60)
        print("模块加载失败，其余探测无法进行。")
        return 1
    mod = holder["mod"]

    # ---- 2. normalize_url ----
    def p2():
        cases = {
            "HTTP://Example.COM:80/a/?utm_source=x&b=2&a=1#frag":
                "http://example.com/a?a=1&b=2",
            "www.site.cn": "https://www.site.cn/",
            "https://Example.com:443/x/": "https://example.com/x",
            "http://example.com": "http://example.com/",
        }
        for src, want in cases.items():
            got = mod.normalize_url(src)
            assert got == want, f"normalize_url({src!r}) = {got!r}，期望 {want!r}"
    _probe("2. normalize_url：小写主机/去默认端口/去 utm_*/参数排序/去锚点/补协议",
           "回到 L03/L10：urllib.parse 的 urlsplit + parse_qsl + urlunsplit。", p2)

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        json_file, html_file = tdp / "s.json", tdp / "s.html"
        json_file.write_text(SAMPLE_JSON, encoding="utf-8")
        html_file.write_text(SAMPLE_HTML, encoding="utf-8")

        # ---- 3. extract_records（JSON） ----
        def p3():
            recs = mod.extract_records(json_file)
            assert isinstance(recs, list) and len(recs) == 3, f"应得 3 条，得到 {len(recs)}"
            for r in recs:
                assert isinstance(r, dict), f"元素应为 dict：{r!r}"
                assert {"url", "title", "date", "views"} <= set(r), f"键不全：{r!r}"
        _probe("3. extract_records 解析本地 JSON 样本，统一成 url/title/date/views 记录",
               "回到 L10：json.loads + dict.get 兜底，别让缺键炸 KeyError。", p3)

        # ---- 4. extract_records（HTML） ----
        def p4():
            recs = mod.extract_records(html_file)
            assert len(recs) == 3, f"3 个 <a> 应得 3 条，得到 {len(recs)}：{recs!r}"
            titles = {str(r.get("title", "")).strip() for r in recs}
            assert "头条一" in titles and "头条二" in titles, f"标题没抓到：{titles}"
        _probe("4. extract_records 解析本地 HTML，抽取全部 <a href> 及链接文字",
               "回到 L10/L11：标准库 html.parser 即可，不必上 bs4。", p4)

        # ---- 5. clean_records ----
        def p5():
            cleaned = mod.clean_records(mod.extract_records(json_file))
            assert len(cleaned) == 2, \
                f"前两条是同一 URL 的变体，去重后应剩 2 条，得到 {len(cleaned)}：{cleaned!r}"
            first = cleaned[0]
            assert first["url"] == "http://shop.example.com/item/7?color=red", \
                f"url 应已规范化：{first['url']!r}"
            assert first["title"] == "商品7", f"title 应去空白：{first['title']!r}"
            assert first["date"] == "2026-01-02", f"2026/1/2 应转成 ISO：{first['date']!r}"
            assert first["views"] == 42 and isinstance(first["views"], int), \
                f"views 应转 int：{first['views']!r}"
            assert cleaned[1]["date"] == "" and cleaned[1]["views"] == 0, \
                f"坏日期/坏数字应兜底为 ''/0 而不是丢整条：{cleaned[1]!r}"
            dropped = mod.clean_records([{"url": "", "title": "无链接"},
                                         {"url": "https://ok.cn/x", "title": "ok"}])
            assert len(dropped) == 1, f"空 url 记录应被丢弃：{dropped!r}"
        _probe("5. clean_records：按规范化 URL 去重、字段兜底、丢弃无 url 行",
               "回到 L02：set 记忆已见 URL；L06：try/except 包住 int()/strptime()。", p5)

        # ---- 6. save_records 落库 ----
        recs3 = [{"url": "https://x.com/a", "title": "A", "date": "2026-01-01", "views": 5},
                 {"url": "https://x.com/b", "title": "B", "date": "", "views": 100},
                 {"url": "https://x.com/c", "title": "C", "date": "2026-01-02", "views": 7}]
        db = tdp / "p2.db"

        def p6():
            n = mod.save_records(recs3, db)
            assert isinstance(n, int) and n == 3, f"应返回新插入行数 3，得到 {n!r}"
            conn = sqlite3.connect(str(db))
            try:
                names = [r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")]
                assert "records" in names, f"表名必须是 records（契约），实际：{names}"
                cnt = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
                assert cnt == 3, f"应有 3 行，得到 {cnt}"
            finally:
                conn.close()
        _probe("6. save_records：建表 records、插入并返回新行数（url 唯一）",
               "回到 L13：sqlite3 建表/占位符 executemany；参数化查询防注入。", p6)

        # ---- 7. save_records 幂等 ----
        def p7():
            n = mod.save_records(recs3, db)
            assert n == 0, f"重复入库应新插入 0 行，得到 {n!r}"
            conn = sqlite3.connect(str(db))
            try:
                cnt = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
                assert cnt == 3, f"重复运行后仍是 3 行才对，得到 {cnt}"
            finally:
                conn.close()
        _probe("7. save_records 幂等：同一批数据跑两遍不产生重复行",
               "回到 L13：UNIQUE 约束 + INSERT OR IGNORE（或 ON CONFLICT DO NOTHING）。", p7)

        # ---- 8. report ----
        def p8():
            rows = mod.report(db)
            assert isinstance(rows, list) and rows, "report 应返回非空 list[dict]"
            assert all(isinstance(r, dict) for r in rows), "元素必须是 dict"
            views = [int(r["views"]) for r in rows]
            assert views == sorted(views, reverse=True), f"未按浏览数降序：{views}"
            assert rows[0]["title"] == "B", f"榜首应是 views=100 的 B：{rows[0]!r}"
            assert len(mod.report(db, limit=2)) == 2, "limit 参数未生效"
        _probe("8. report：降序查询、dict 行、limit 生效",
               "回到 L13：ORDER BY ... LIMIT ?；sqlite3.Row 转 dict。", p8)

        # ---- 9. main 离线跑通且不留产物 ----
        def p9():
            fn = getattr(mod, "main", None)
            assert callable(fn), "缺少 main(argv=None)，见契约表"
            before = {p.name for p in PROJECT.iterdir()}
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = fn([])
            assert rc == 0, f"main([]) 应返回 0，得到 {rc!r}"
            out = buf.getvalue()
            assert "条" in out or "record" in out.lower(), f"stdout 看不到管线结果：{out[:120]!r}"
            after = {p.name for p in PROJECT.iterdir()}
            assert after == before, f"跑完在项目目录留下了产物：{after - before}"
        _probe("9. main([]) 离线全流程跑通，且不在仓库目录留下任何文件",
               "回到 L06/L10：临时库用 tempfile，退出前清理；用 with 管连接。", p9)

    # ---- 10. 可选网络抓取 ----
    def p10():
        try:
            import requests  # noqa: F401
        except ModuleNotFoundError as exc:
            raise MissingDep("pip install requests") from exc
        fetch = getattr(mod, "fetch", None)
        assert callable(fetch), "requests 已装：应按契约提供 fetch(url) 函数（不强制调用，避免联网）"
    _probe("10.（可选增强）fetch() 存在且 requests 是延迟导入",
           "回到 L11：requests 只在函数体 import，离线判分才不会全军覆没。", p10)

    print("=" * 60)
    print(f"结果：通过 {stats['通过']}，未过 {stats['未过']}，缺依赖 {stats['缺依赖']}")
    return 0 if stats["未过"] == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n已中断。")
        sys.exit(130)
