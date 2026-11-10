#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""learn 判分器 —— 只依赖 Python 标准库，测试文件同时兼容 pytest。

用法（在项目根目录或 anywhere 都行）：
    py check.py                # 跑全部课程，输出成绩单
    py check.py L03            # 只跑第 3 课
    py check.py L03 -v         # 逐条列出每个测试
    py check.py P1             # 跑项目验收（转给该项目的 verify.py）
    py check.py --list         # 列出所有课程和项目

判分结果会写进 progress.json，供 progress.py 统计进度。

以后装了 pytest（pip install pytest），同一批测试文件可以直接：
    py -m pytest drills/L03 -q
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

LEARN = Path(__file__).resolve().parent
DRILLS = LEARN / "drills"
PROJECTS = LEARN / "projects"
STATE_FILE = LEARN / "progress.json"
# 判分器每次都重新加载源码，留下 __pycache__ 只会让仓库变脏
sys.dont_write_bytecode = True

# 单个测试最长跑这么久，防止死循环把整个判分器一起卡住
TIMEOUT_SECONDS = 10

# 状态 -> 展示符号（Windows 控制台避免用 emoji）
PASS, FAIL, ERROR, TODO, MISSING, TIMEOUT = (
    "通过", "失败", "报错", "未做", "缺依赖", "超时")
NON_PASS = (TODO, FAIL, ERROR, MISSING, TIMEOUT)


class _Timeout(Exception):
    pass


def _call_with_timeout(func) -> None:
    """在后台线程执行 func，等 TIMEOUT_SECONDS 未果则判定超时。

    Python 无法强杀线程，超时的线程会留在后台继续空转；这里只求判分器本身
    不被一个死循环卡死，进程结束时自然回收。
    """
    box: dict[str, BaseException | None] = {"exc": None}

    def target() -> None:
        try:
            func()
        except BaseException as exc:  # noqa: BLE001 - 原样带回主线程再判定
            box["exc"] = exc

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(TIMEOUT_SECONDS)
    if thread.is_alive():
        raise _Timeout(f"超过 {TIMEOUT_SECONDS}s 未结束，检查有没有死循环")
    if box["exc"] is not None:
        raise box["exc"]


def _run_one(func) -> tuple[str, str]:
    """跑单个测试函数，返回 (状态, 说明)。"""
    try:
        _call_with_timeout(func)
        return PASS, ""
    except _Timeout as exc:
        return TIMEOUT, str(exc)
    except NotImplementedError:
        return TODO, "还没写"
    except AssertionError as exc:
        return FAIL, str(exc) or "断言失败"
    except ModuleNotFoundError as exc:
        return MISSING, f"需要 pip install {exc.name}"
    except Exception:  # noqa: BLE001 - 练习题里任何异常都算报错，直接摊开给用户看
        last = traceback.format_exc().strip().splitlines()[-1]
        return ERROR, last


def _import_as(path: Path, unique_name: str):
    """按文件路径加载模块，用唯一名字避免各课程间同名模块互相污染。"""
    spec = importlib.util.spec_from_file_location(unique_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载 {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[unique_name] = module
    spec.loader.exec_module(module)
    return module


def _load_pair(lesson_dir: Path, use_solution: bool = False):
    """加载某课的 exercises.py 与 test_*.py。

    测试文件里写的是 `from exercises import xxx`，所以先把 exercises 注册进
    sys.modules，再让测试模块去 import；同时把课程目录放进 sys.path。
    use_solution=True 时改成把 solution.py 注册成 exercises，用来验收参考答案。
    """
    test_files = sorted(lesson_dir.glob("test_*.py"))
    if not test_files:
        raise RuntimeError(f"{lesson_dir.name} 缺少 test_*.py")
    answers = lesson_dir / "solution.py" if use_solution else lesson_dir / "exercises.py"
    if not answers.exists():
        if use_solution:
            raise RuntimeError(f"{lesson_dir.name} 没有参考答案 solution.py")
        raise RuntimeError(f"{lesson_dir.name} 缺少 exercises.py")

    sys.path.insert(0, str(lesson_dir))
    try:
        _ensure_pytest()
        answers_mod = _import_as(answers, f"{lesson_dir.name}_answers")
        sys.modules["exercises"] = answers_mod
        test_mod = _import_as(test_files[0], f"{lesson_dir.name}_tests")
    finally:
        if sys.path and sys.path[0] == str(lesson_dir):
            sys.path.pop(0)
    return test_mod


def _ensure_pytest() -> None:
    """装了 pytest 就用真的；没装就把 _pytest_shim.py 冒充成 pytest。

    这样练习文件只有一种写法，不用为"有没有装 pytest"分叉。
    """
    if "pytest" in sys.modules:
        return
    try:
        import pytest  # noqa: F401
    except ModuleNotFoundError:
        shim = _import_as(LEARN / "_pytest_shim.py", "learn_pytest_shim")
        sys.modules["pytest"] = shim


def run_lesson(lesson_dir: Path, verbose: bool = False,
               use_solution: bool = False) -> dict:
    started = time.time()
    counts = {k: 0 for k in (PASS, FAIL, ERROR, TODO, MISSING, TIMEOUT)}
    details: list[tuple[str, str, str]] = []
    tag = "参考答案" if use_solution else "你的答案"

    try:
        test_mod = _load_pair(lesson_dir, use_solution)
    except ModuleNotFoundError as exc:
        return {"lesson": lesson_dir.name, "counts": {MISSING: 1},
                "details": [(lesson_dir.name, MISSING, f"需要 pip install {exc.name}")],
                "seconds": 0.0}
    except Exception as exc:  # noqa: BLE001
        return {"lesson": lesson_dir.name, "counts": {ERROR: 1},
                "details": [(lesson_dir.name, ERROR, str(exc))], "seconds": 0.0}

    tests = [(n, f) for n, f in vars(test_mod).items()
             if n.startswith("test_") and callable(f)]
    for name, func in sorted(tests, key=lambda p: p[0]):
        status, note = _run_one(func)
        counts[status] += 1
        details.append((name, status, note))

    result = {"lesson": lesson_dir.name, "label": f"{lesson_dir.name}〈{tag}〉",
              "counts": counts, "details": details,
              "seconds": round(time.time() - started, 2)}
    if not use_solution:
        _record(result)
    _print(result, verbose)
    return result


def _print(result: dict, verbose: bool) -> None:
    counts = result["counts"]
    total = sum(counts.values())
    passed = counts.get(PASS, 0)
    line = f"{result['label']:<9} {passed:>2}/{total:<2} 通过"
    for key in NON_PASS:
        if counts.get(key):
            line += f"  | {key} {counts[key]}"
    print(line)
    if verbose:
        for name, status, note in result["details"]:
            if status == PASS:
                print(f"      ok    {name}")
            else:
                print(f"      {status:<5} {name}  {note[:90]}")
    else:
        for name, status, note in result["details"]:
            if status in (FAIL, ERROR, MISSING, TIMEOUT):
                print(f"      {status:<5} {name}  {note[:90]}")


def _record(result: dict) -> None:
    state = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - 状态文件坏了就重建，不值得为练习工具报错
            state = {}
    counts = result["counts"]
    total = sum(counts.values())
    entry = state.get(result["lesson"], {})
    entry["score"] = f"{counts.get(PASS, 0)}/{total}"
    entry["passed"] = counts.get(PASS, 0) == total and total > 0
    entry["last_check"] = time.strftime("%Y-%m-%d %H:%M:%S")
    entry.setdefault("status", "未开始")
    if entry["passed"]:
        # 全绿就自动记完成日，复习排期由 progress.py 按完成日推算，不用手动 done
        if entry["status"] != "已完成":
            entry["status"] = "已完成"
            entry["done_at"] = time.strftime("%Y-%m-%d")
            entry.setdefault("reviews", 0)
    state[result["lesson"]] = entry
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                          encoding="utf-8")


def lessons() -> list[Path]:
    if not DRILLS.exists():
        return []
    return sorted(p for p in DRILLS.iterdir() if (p / "exercises.py").exists())


def projects() -> list[Path]:
    if not PROJECTS.exists():
        return []
    return sorted(p for p in PROJECTS.iterdir() if (p / "verify.py").exists())


def run_project(want: str, use_solution: bool) -> int:
    """把 P1/P2/P3/P4 转给项目自己的 verify.py，输出原样透传。

    项目验收是"跑一个程序看结果"，跟 drills 的函数级判分不是一回事，
    所以不进 progress.json，复习排期只管课程。
    """
    matched = [p for p in projects() if p.name.upper().startswith(want)]
    if not matched:
        print(f"找不到项目 {want}。可用：{', '.join(p.name for p in projects()) or '（还没有）'}")
        return 1
    if len(matched) > 1:
        print("项目名有歧义：" + ", ".join(p.name for p in matched))
        return 1
    target = matched[0]
    script = target / "verify.py"
    args = [sys.executable, str(script)]
    if use_solution:
        example = target / "example" / "app.py"
        if not example.exists():
            print(f"{target.name} 没有 example/app.py，无法用 --solution 跑。")
            return 1
        args.append(str(example))
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    print(f"--- {target.name} 验收 ---", flush=True)
    return subprocess.run(args, env=env).returncode


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="learn 练习判分器")
    parser.add_argument("lesson", nargs="?", help="课程号 L03 或项目号 P1；省略则跑全部课程")
    parser.add_argument("-v", "--verbose", action="store_true", help="逐条显示")
    parser.add_argument("--solution", action="store_true",
                        help="跑 solution.py 的参考答案，用来验证题目本身有没有写错")
    parser.add_argument("--list", action="store_true", help="列出课程和项目")
    args = parser.parse_args()

    available = lessons()
    if args.list:
        for p in available:
            print(f"{p.name}  练习")
        for p in projects():
            print(f"{p.name}  项目")
        return 0

    want = (args.lesson or "").upper()
    if want.startswith("P"):
        return run_project(want, args.solution)

    if not available:
        print("还没有 drills 目录，先完成 L01。")
        return 1

    targets = available
    if want:
        if want.startswith("L") and len(want) > 1 and not want[1:].isdigit():
            print(f"看不懂「{args.lesson}」。课程用 L03 这样写，项目用 P1。")
            return 1
        if not want.startswith("L"):
            if not want.isdigit():
                print(f"看不懂「{args.lesson}」。课程用 L03 这样写，项目用 P1。")
                return 1
            want = f"L{int(want):02d}"
        targets = [p for p in available if p.name.upper() == want]
        if not targets:
            print(f"找不到课程 {want}。可用：{', '.join(p.name for p in available)}")
            return 1

    print("=" * 46)
    print("判分结果（未做 = 还没填答案，失败 = 答案不对）")
    print("=" * 46)
    results = [run_lesson(p, args.verbose, args.solution) for p in targets]
    total = sum(sum(r["counts"].values()) for r in results)
    passed = sum(r["counts"].get(PASS, 0) for r in results)
    slowest = max(results, key=lambda r: r["seconds"])
    print("-" * 46)
    print(f"合计 {passed}/{total} 通过   最慢一课 {slowest['seconds']:.2f}s"
          f"（{slowest['lesson']}）")
    if args.solution:
        print("提示：这是参考答案的成绩，不代表你已经会了。")
    return 0 if passed == total else 2


if __name__ == "__main__":
    sys.exit(main())
