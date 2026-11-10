#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P1 验收脚本 —— 只用标准库。

用法（在任意目录）：
    py projects/P1-日志分析命令行/verify.py              # 验收项目根下的 app.py
    py projects/P1-日志分析命令行/verify.py example/app.py   # 先验参考实现

探测项按 README「函数契约表」调用你的 parse_line / analyze，并用 subprocess 跑 CLI。
退出码：0 = 没有红色项；1 = 有未过项或还没写 app.py。
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
TIMEOUT = 5
stats = {"通过": 0, "未过": 0, "缺依赖": 0}
# importlib 加载被测模块时不写 __pycache__，判分不留产物
sys.dont_write_bytecode = True


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
        raise TimeoutError(f"单条探测超过 {TIMEOUT}s，检查有没有死循环或阻塞 IO")
    if "exc" in box:
        raise box["exc"]


def _probe(title: str, guide: str, func):
    try:
        _call_with_timeout(func)
        stats["通过"] += 1
        print(f"[通过] {title}")
    except MissingDep as exc:
        stats["缺依赖"] += 1
        print(f"[缺依赖] {title} — {exc}（不计失败，装上后重跑）")
    except AssertionError as exc:
        stats["未过"] += 1
        print(f"[未过] {title} — {exc or '断言失败'}。{guide}")
    except Exception as exc:  # noqa: BLE001
        stats["未过"] += 1
        print(f"[未过] {title} — 抛了 {type(exc).__name__}: {exc}。{guide}")


# ---- 构造一份数字可手工核算的小日志（8 条合法 + 1 条坏行） ----
TEST_LOG = """\
10.0.0.1 - - [01/Oct/2026:10:00:00 +0800] "GET /index.html HTTP/1.1" 200 1000 120
10.0.0.2 - - [01/Oct/2026:10:00:01 +0800] "GET /api/orders HTTP/1.1" 200 900 300
10.0.0.1 - - [01/Oct/2026:10:00:02 +0800] "GET /api/orders HTTP/1.1" 200 900 2400
10.0.0.3 - - [02/Oct/2026:09:00:00 +0800] "GET /api/orders HTTP/1.1" 500 12 30
10.0.0.2 - - [02/Oct/2026:09:00:01 +0800] "GET /login HTTP/1.1" 404 0 40
10.0.0.3 - - [02/Oct/2026:09:00:02 +0800] "GET /old-page HTTP/1.1" 301 - 20
10.0.0.1 - - [03/Oct/2026:23:59:59 +0800] "GET /static/app.js HTTP/1.1" 200 5000 15
10.0.0.2 - - [03/Oct/2026:23:59:58 +0800] "GET /index.html HTTP/1.1" 200 1000 90
这一行坏得彻底 [[[
"""

GOOD_LINE = ('127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] '
             '"GET /apache_pb.gif HTTP/1.0" 200 2326')


def _load(app_path: Path):
    name = "p1_target_app"
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


def _run_cli(app_path: Path, *args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run([sys.executable, str(app_path), *args],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=TIMEOUT, env=env)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # ---- 定位被测文件 ----
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

    # ---- 探测 1：可导入且无副作用 ----
    holder: dict = {}

    def load():
        holder["mod"] = _load(target)
        for fname in ("parse_line", "analyze"):
            if not callable(getattr(holder["mod"], fname, None)):
                raise AssertionError(f"缺少约定函数 {fname}()，见 README 函数契约表")

    _probe("1. 模块可导入，且 import 时不执行主流程（无副作用）",
           "回到 L09：入口代码要收进 if __name__ == '__main__'。", load)
    if "mod" not in holder:
        print("-" * 60)
        print("模块加载失败，其余探测无法进行。")
        return 1
    mod = holder["mod"]

    # ---- 探测 2：parse_line 合法行 ----
    def p2():
        d = mod.parse_line(GOOD_LINE)
        assert isinstance(d, dict), f"应返回 dict，返回了 {type(d).__name__}"
        assert d.get("ip") == "127.0.0.1", f"ip 错：{d.get('ip')!r}"
        assert d.get("status") == 200 and isinstance(d.get("status"), int), \
            f"status 应为 int 200：{d.get('status')!r}"
        assert isinstance(d.get("time"), datetime), \
            f"time 应为 datetime，得到 {type(d.get('time')).__name__}"
        assert d["time"].strftime("%H:%M:%S") == "13:55:36", "time 解析成了别的时间"
        assert d.get("size") == 2326, f"size 错：{d.get('size')!r}"
        assert d.get("path") == "/apache_pb.gif", f"path 错：{d.get('path')!r}"
    _probe("2. parse_line 解析标准 CLF 行（字段与类型正确）",
           "回到 L03：正则命名分组 + datetime.strptime。", p2)

    # ---- 探测 3：parse_line 非法行 ----
    def p3():
        for bad in ("", "这不是日志 [[[", '10.0.0.1 - - [坏时间] "GET / HTTP/1.1"'):
            got = mod.parse_line(bad)
            assert got is None, f"非法行应返回 None，得到 {got!r}"
    _probe("3. parse_line 遇到非法行返回 None，不崩溃",
           "回到 L06：解析失败是预期分支，返回 None 而不是抛裸异常。", p3)

    # ---- 探测 4：analyze 的 PV/UV/跳过数 ----
    with tempfile.TemporaryDirectory() as td:
        log_path = Path(td) / "access.log"
        log_path.write_text(TEST_LOG, encoding="utf-8")
        lines = log_path.read_text(encoding="utf-8").splitlines()

        def p4():
            r = mod.analyze(lines)
            assert r.get("pv") == 8, f"pv 应为 8，得到 {r.get('pv')!r}"
            assert r.get("uv") == 3, f"uv 应为 3（IP 去重），得到 {r.get('uv')!r}"
            assert r.get("skipped") == 1, f"skipped 应为 1，得到 {r.get('skipped')!r}"
        _probe("4. analyze 统计 PV / UV / 跳过行数正确",
               "回到 L02：set 去重算 UV。", p4)

        # ---- 探测 5：状态码分布 ----
        def p5():
            r = mod.analyze(lines)
            sc = r.get("status_counts", {})
            assert {str(k): int(v) for k, v in sc.items()} == \
                {"200": 5, "500": 1, "404": 1, "301": 1}, f"分布错：{sc}"
        _probe("5. analyze 的状态码分布 status_counts 正确",
               "回到 L02：collections.Counter 或 dict 累加。", p5)

        # ---- 探测 6：Top-N URL ----
        def p6():
            r = mod.analyze(lines, top=2)
            top_urls = r.get("top_urls")
            assert isinstance(top_urls, list) and len(top_urls) <= 2, \
                f"top_urls 应为长度 <= 2 的列表：{top_urls!r}"
            first = top_urls[0]
            url = first.get("url") if isinstance(first, dict) else first[0]
            count = first.get("count") if isinstance(first, dict) else first[1]
            assert url == "/api/orders" and count == 3, \
                f"第一名应为 /api/orders×3，得到 {first!r}"
        _probe("6. analyze 的 Top-N URL 排序正确且受 top 参数截断",
               "回到 L02/L04：Counter.most_common(top)，参数要真的生效。", p6)

        # ---- 探测 7：min_status 过滤 ----
        def p7():
            r = mod.analyze(lines, min_status=400)
            assert r.get("pv") == 2, f"状态码>=400 应剩 2 条（500 和 404），得到 {r.get('pv')!r}"
            codes = {int(k) for k in r.get("status_counts", {})}
            assert codes and all(c >= 400 for c in codes), f"混入了低状态码：{codes}"
        _probe("7. analyze(min_status=400) 过滤正确",
               "回到 L04：关键字参数 + 过滤循环。", p7)

        # ---- 探测 8：since 过滤 ----
        def p8():
            since = datetime(2026, 10, 2, tzinfo=timezone.utc)
            r = mod.analyze(lines, since=since)
            assert r.get("pv") == 5, \
                f"since=2026-10-02(UTC) 应剩 5 条，得到 {r.get('pv')!r}"
        _probe("8. analyze(since=...) 只保留该时刻之后的请求",
               "回到 L03：datetime 比较；日志时间是带时区的，比较前先统一。", p8)

        # ---- 探测 9：CLI --json ----
        def p9():
            proc = _run_cli(target, str(log_path), "--json", "--top", "2")
            assert proc.returncode == 0, f"退出码应为 0，得到 {proc.returncode}"
            data = json.loads(proc.stdout)
            assert data["pv"] == 8 and data["uv"] == 3, f"JSON 数字不对：{data}"
            assert len(data["top_urls"]) <= 2, f"--top 2 未生效：{data['top_urls']}"
            help_out = _run_cli(target, "--help").stdout
            for opt in ("--top", "--min-status", "--since", "--json"):
                assert opt in help_out, f"帮助里看不到 {opt}，argparse 没配全"
        _probe("9. CLI 跑通：--json 输出合法 JSON，--top 生效，--help 列出全部选项",
               "回到 L09：argparse 子命令参数 + if __name__ 入口。", p9)

        # ---- 探测 10：CLI 错误处理 ----
        def p10():
            proc = _run_cli(target, str(Path(td) / "不存在的.log"))
            assert proc.returncode != 0, "文件不存在时应以非 0 退出码结束"
            combined = proc.stdout + proc.stderr
            assert "Traceback" not in combined, "把异常堆栈直接甩给用户了，用 try/except 包住"
        _probe("10. CLI 文件不存在：非 0 退出码且无 Traceback",
               "回到 L06：捕获 FileNotFoundError，打印友好信息后 sys.exit(非0)。", p10)

    print("=" * 60)
    print(f"结果：通过 {stats['通过']}，未过 {stats['未过']}，缺依赖 {stats['缺依赖']}")
    return 0 if stats["未过"] == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n已中断。")
        sys.exit(130)
