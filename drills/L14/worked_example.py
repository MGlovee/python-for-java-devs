# -*- coding: utf-8 -*-
"""L14 完整样例 —— 测试、日志、性能、静态检查，一个文件跑完。

跑法：
    py drills/L14/worked_example.py
    py drills/L14/worked_example.py --limit 2000 --verbose --profile

日志写进内存 + 临时目录里的文件（跑完连目录一起删），仓库里不留产物；
性能用 timeit 定量、cProfile+pstats 定位；测试用标准库手搓一个迷你 runner。
"""
from __future__ import annotations

import argparse
import ast
import cProfile
import contextlib
import io
import logging
import logging.config
import pstats
import re
import shutil
import sys
import tempfile
import timeit
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ==================================================================== 业务代码
def normalize_phone(raw: str) -> str:
    """把 '+86 138-0013-8000' 归一成 '13800138000'；非法输入抛 ValueError。"""
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("86") and len(digits) == 13:
        digits = digits[2:]
    if not re.fullmatch(r"1[3-9]\d{9}", digits):
        raise ValueError(f"不是有效的中国大陆手机号：{raw!r}")
    return digits


def total_price(prices: list[float], discount: float) -> float:
    """打折求和。discount 必须在 [0, 1]，越界抛 ValueError（好让测试去断言异常）。"""
    if not 0 <= discount <= 1:
        raise ValueError(f"折扣必须在 0~1 之间，收到 {discount}")
    return round(sum(p * discount for p in prices), 2)


# ==================================================================== 1. logging
def build_memory_logger(name: str, level: int, sink: io.StringIO) -> logging.Logger:
    """**不动全局配置**：私有 logger + propagate=False + 内存 handler。

    这样别的地方调过 logging.basicConfig 也不会影响这里的输出。
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    handler = logging.StreamHandler(sink)
    handler.setFormatter(logging.Formatter("%(levelname)-8s %(name)s - %(message)s"))
    logger.addHandler(handler)
    return logger


def demo_logging(verbose: bool) -> None:
    print("=== 1. logging：级别是阈值，模板吃的是 record 属性 ===")
    sink = io.StringIO()
    logger = build_memory_logger("L14.demo", logging.INFO, sink)
    log_dir = Path(tempfile.mkdtemp(prefix="l14_log_"))
    log_file = log_dir / "app.log"

    # dictConfig：等价于 Java 的 logback.xml，生产配置一律走这条路，不写代码里散 setLevel
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,            # 关键：否则上面建好的 logger 全被禁用
        "formatters": {"std": {"format": "%(asctime)s %(levelname)s %(message)s"}},
        "handlers": {"file": {"class": "logging.FileHandler", "filename": str(log_file),
                              "encoding": "utf-8", "formatter": "std"}},
        "root": {"level": "WARNING", "handlers": ["file"]},     # 只在这里配 root，跑完就撤
    })
    file_logger = logging.getLogger("L14.persist")             # 不在 L14.demo 子树里 → 冒到 root

    logger.debug("手机号长度校验完成")                          # 低于 INFO → 丢弃
    logger.info("导入完成，共 %d 条", 3)                        # 惰性格式化：参数交给 record 展开
    logger.warning("发现重复号码 +86 138-0013-8000")
    try:
        normalize_phone("123")
    except ValueError:
        logger.error("归一化失败", exc_info=verbose)            # 需要堆栈时才带 exc_info
    file_logger.info("这条是 INFO，低于 root 的 WARNING → 不会进文件")
    file_logger.error("这条 ERROR 会进临时日志文件")

    lines = sink.getvalue().splitlines()
    print(f"    内存 handler：level=INFO，共写出 {len(lines)} 行"
          f"（debug 被阈值挡掉；--verbose 时 error 还多带堆栈）")
    for line in lines[:4]:
        print(f"      {line[:100]}")
    on_disk = log_file.read_text(encoding="utf-8").splitlines() if log_file.exists() else []
    print(f"    文件 handler：root=WARNING，落盘 {len(on_disk)} 行"
          f"（注意：'L14.demo' 设了 propagate=False，它的日志不会冒到 root）")
    for line in on_disk:
        print(f"      {line[-60:]}")
    print(f"    级别名 ↔ 数字：getLevelName('WARNING')={logging.getLevelName('WARNING')}, "
          f"getLevelName(25)={logging.getLevelName(25)!r}（未注册的数字兜底成字符串，不报错）")

    child = logging.getLogger("L14.demo.parser")               # 没设级别 → 继承父级
    print(f"    子 logger 生效级别：{logging.getLevelName(child.getEffectiveLevel())}"
          f"（父级 L14.demo 是 INFO）")

    logging.getLogger().removeHandler(logging.getLogger().handlers[0])   # 撤掉文件 handler
    logging.shutdown()
    shutil.rmtree(log_dir, ignore_errors=True)
    print(f"    临时日志目录已删除：{log_dir.exists()=}\n")


# ==================================================================== 2. 迷你 runner
def run_cases(func, cases: list[tuple[tuple, object]], label: str) -> tuple[int, int]:
    """cases = [(入参元组, 期望结果 或 'RAISE:异常名'), ...]；返回 (通过数, 失败数)。"""
    passed = failed = 0
    for args, expected in cases:
        try:
            actual = func(*args)
        except Exception as exc:                       # noqa: BLE001 - runner 必须兜住被测码
            actual = f"RAISE:{type(exc).__name__}"
        if actual == expected:
            passed += 1
        else:
            failed += 1
            print(f"      FAIL {label}{args} 期望 {expected!r} 实际 {actual!r}")
    return passed, failed


def expect_raises(func, expected_exc: type[BaseException]) -> str:
    """pytest.raises 的手写版：没抛 = 断言失败，抛错类型 = 让它冒出去。"""
    try:
        func()
    except expected_exc as exc:
        return str(exc)
    raise AssertionError(f"期望抛出 {expected_exc.__name__}，但代码正常返回了")


def demo_testing(limit: int) -> None:
    print("=== 2. 测试：断言 = 直接写表达式，异常也能当期望结果 ===")
    p1, f1 = run_cases(normalize_phone, [
        (("+86 138-0013-8000",), "13800138000"),
        (("13800138000",), "13800138000"),
        (("12345678901",), "RAISE:ValueError"),
        (("138001380001",), "RAISE:ValueError"),
        (("+8613800138000",), "13800138000"),
    ], "normalize_phone")
    p2, f2 = run_cases(total_price, [
        (([10.0, 20.0], 1.0), 30.0),
        (([10.0, 20.0], 0.8), 24.0),
        (([], 0.5), 0.0),
        (([10.0], 1.5), "RAISE:ValueError"),
        ((list(range(limit)), 0.5), round(sum(i * 0.5 for i in range(limit)), 2)),
    ], "total_price")
    total_passed, total_failed = p1 + p2, f1 + f2
    print(f"      ==== {total_passed} passed, {total_failed} failed in mini-runner ====")
    print(f"      异常断言拿到消息：{expect_raises(lambda: total_price([1.0], 9), ValueError)!r}")
    with contextlib.suppress(AssertionError):
        expect_raises(lambda: normalize_phone("13800138000"), RuntimeError)
    print("      该抛没抛时 expect_raises 会抛 AssertionError（上面 suppress 掉，只演示语义）\n")


# ==================================================================== 3. timeit / cProfile
def demo_perf(limit: int, profile: bool) -> None:
    print("=== 3. 性能：先 timeit 定量，再 cProfile 定位 ===")
    candidates = {"生成器 + join": "'-'.join(str(i) for i in range(200))",
                  "列表推导 + join": "'-'.join([str(i) for i in range(200)])",
                  "map + join": "'-'.join(map(str, range(200)))"}
    for label, stmt in candidates.items():
        best = min(timeit.Timer(stmt).repeat(repeat=3, number=200)) / 200
        print(f"      {label:<16} 单次 {best * 1e6:7.2f} µs")
    print("      ↑ 取 repeat() 的最小值，比单次采样稳；timeit 还自动关了 GC")

    if profile:
        buf = io.StringIO()
        profiler = cProfile.Profile()
        with contextlib.redirect_stdout(buf):             # 别把 runner 的 FAIL 打印混进来
            profiler.runcall(run_cases, normalize_phone,
                             [(("+86 138-0013-8000",), "13800138000")] * limit,
                             "normalize_phone")
        stats = io.StringIO()
        pstats.Stats(profiler, stream=stats).sort_stats("cumulative").print_stats(6)
        rows = [line for line in stats.getvalue().splitlines() if line.strip()]
        print("      cProfile（按 cumulative 排序，找链路瓶颈；看函数自身耗时用 tottime）：")
        for line in rows[3:9]:
            print(f"        {line[:110]}")
    print("      ↑ Java 人的习惯是「先优化再说」，这里反过来：先量，再改，改完再量\n")


# ==================================================================== 4. 迷你 linter
_SNAKE = re.compile(r"_*[a-z][a-z0-9_]*")


def find_bad_function_names(source: str) -> list[str]:
    """ruff 的一条规则用 ast 就能写出来：不合规的函数名按行号报出来。"""
    tree = ast.parse(source)
    hits: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not _SNAKE.fullmatch(node.name):
                hits.append((node.lineno, f"L{node.lineno}: N802 snake_case: {node.name}"))
    return [msg for _, msg in sorted(hits)]


def demo_lint() -> None:
    print("=== 4. 静态检查：ruff/mypy 的定位（本机没装，自己写一条规则）===")
    source = ("def CalcTotal():\n    pass\n\ndef ok_name():\n    pass\n\n"
              "async def doIt():\n    pass\n\ndef _private_one():\n    pass\n")
    for report in find_bad_function_names(source):
        print(f"      {report}")
    print("      ruff = 快 + 规则多（风格/可疑写法），pylint = 严（噪音大），mypy = 管类型；")
    print("      新项目先 `ruff check` + `mypy`，CI 里各跑一遍，比人肉 review 便宜\n")


# ==================================================================== 5. argparse
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="worked_example.py", description="L14 四件套演示")
    parser.add_argument("--limit", type=int, default=800, help="用例重复次数 / 压测长度")
    parser.add_argument("-v", "--verbose", action="store_true", help="异常日志带堆栈")
    parser.add_argument("--profile", action="store_true", help="额外跑一次 cProfile")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)      # 非法参数会 SystemExit，不是 ValueError
    limit = max(int(args.limit), 1)
    demo_logging(bool(args.verbose))
    demo_testing(min(limit, 50))
    demo_perf(limit, bool(args.profile))
    demo_lint()
    print("全部跑完：日志没污染 root，测试自己报 passed/failed，性能是量出来的，不是猜的。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
