#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P3 验收脚本 —— 只用标准库（被测 app.py 自己用 pandas）。

用法：
    py projects/P3-数据报表/verify.py               # 验收项目根下的 app.py
    py projects/P3-数据报表/verify.py example/app.py # 先验参考实现

退出码：0 = 没有红色项；1 = 有未过项或还没写 app.py。
"""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
TIMEOUT = 5
stats = {"通过": 0, "未过": 0, "缺依赖": 0}
sys.dont_write_bytecode = True  # 判分不在仓库留 __pycache__

SAMPLE_CSV = """\
部门,姓名,销售额
研发,张三,100
研发,李四,120
研发,王五,
销售,赵六,200
销售,赵六,200
销售,孙七,150
财务,周八,130
财务,吴九,999999
财务,郑十,110
"""


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
        raise TimeoutError(f"单条探测超过 {TIMEOUT}s，检查有没有卡在 IO 或死循环")
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


def _load(app_path: Path):
    name = "p3_target_app"
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


def _close(got, want, tol=1e-6):
    return abs(float(got) - float(want)) < tol


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
        missing = [f for f in ("load_data", "data_check", "summarize", "write_outputs")
                   if not callable(getattr(holder["mod"], f, None))]
        assert not missing, f"缺少契约函数：{missing}，见 README 函数契约表"

    _probe("1. 模块可导入（pandas 可用），四个契约函数齐全，无副作用",
           "回到 L15：DataFrame 最小可用集；L09：入口守卫。", load)
    if "mod" not in holder:
        print("-" * 60)
        print("模块加载失败（多半是没装 pandas：pip install pandas），其余探测无法进行。")
        return 1
    mod = holder["mod"]

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        csv_file = tdp / "data.csv"
        csv_file.write_text(SAMPLE_CSV, encoding="utf-8")

        # ---- 2. load_data ----
        df_holder: dict = {}

        def p2():
            df_holder["df"] = mod.load_data(csv_file)
            df = df_holder["df"]
            assert tuple(df.shape) == (9, 3), f"shape 应为 (9,3)，得到 {tuple(df.shape)}"
            assert list(df.columns) == ["部门", "姓名", "销售额"], \
                f"列名不对：{list(df.columns)}"
        _probe("2. load_data 读出 9 行 3 列的 DataFrame",
               "回到 L15：pd.read_csv；L10：utf-8-sig 与 BOM。", p2)
        df = df_holder.get("df")
        if df is None:
            print("-" * 60)
            print("load_data 失败，后续探测依赖它的返回值，先修第 2 条。")
            return 1

        # ---- 3. data_check：缺失 ----
        def p3():
            chk = mod.data_check(df)
            assert chk["missing"]["销售额"] == 1, f"销售额缺失应为 1：{chk['missing']}"
            assert chk["missing"]["部门"] == 0, f"部门缺失应为 0：{chk['missing']}"
            json.dumps(chk)  # 契约：纯 Python 类型，可直接序列化
        _probe("3. data_check 缺失计数正确，且结果是 JSON 可序列化的纯 Python 类型",
               "回到 L15：df[col].isna().sum()；numpy 标量记得 int()/float() 转纯类型。", p3)

        # ---- 4. data_check：重复 ----
        def p4():
            chk = mod.data_check(df)
            assert chk["duplicate_rows"] == 1, \
                f"重复行应为 1（第二条 赵六），得到 {chk.get('duplicate_rows')!r}"
        _probe("4. data_check 重复行数正确（整行完全相同的多余副本）",
               "回到 L15：df.duplicated().sum()。", p4)

        # ---- 5. data_check：异常值 ----
        def p5():
            chk = mod.data_check(df)
            out = chk["outliers"].get("销售额", [])
            assert 7 in out, f"行下标 7（999999）应被标为异常：{out}"
            assert 0 not in out and 3 not in out, f"正常值被误报：{out}"
        _probe("5. data_check 用 IQR 1.5 法则揪出异常值（且不误伤正常值）",
               "回到 L15：quantile(0.25/0.75) 求上下界。", p5)

        # ---- 6. summarize ----
        def p6():
            rows = mod.summarize(df, "部门", "销售额")
            assert isinstance(rows, list) and len(rows) == 3, f"应 3 组：{rows!r}"
            by = {r["部门"]: r for r in rows}
            rd = by["研发"]
            assert rd["count"] == 2, f"研发非空计数应为 2（NaN 不计数）：{rd}"
            assert _close(rd["sum"], 220) and _close(rd["mean"], 110), f"研发数字错：{rd}"
            assert _close(by["销售"]["sum"], 550), f"销售合计应为 550：{by['销售']}"
            sums = [r["sum"] for r in rows]
            assert sums == sorted(sums, reverse=True), f"未按 sum 降序：{sums}"
            assert rows[0]["部门"] == "财务", "降序首位应是财务"
        _probe("6. summarize 分组聚合：count/sum/mean 正确且按 sum 降序",
               "回到 L15：groupby(col)[val].agg(['count','sum','mean'])。", p6)

        # ---- 7. write_outputs（进程内） ----
        out1 = tdp / "out1"

        def p7():
            files = mod.write_outputs(df, out1, "部门", "销售额")
            names = {Path(f).name for f in files}
            assert "summary.csv" in names and "stats.txt" in names, f"产出文件不对：{names}"
            with (out1 / "summary.csv").open(encoding="utf-8-sig", newline="") as fh:
                rows = list(csv.reader(fh))
            assert rows[0] == ["部门", "count", "sum", "mean"], f"表头契约不符：{rows[0]}"
            assert len(rows) == 4, f"summary.csv 应 3 行数据+1 表头，得到 {len(rows)}"
            assert (out1 / "stats.txt").stat().st_size > 0, "stats.txt 是空的"
        _probe("7. write_outputs 产出 summary.csv（表头=分组列,count,sum,mean）与 stats.txt",
               "回到 L15/L10：DataFrame.to_csv(..., index=False)；文本用 write_text。", p7)

        # ---- 8. CLI 全流程 ----
        def p8():
            out2 = tdp / "out2"
            proc = _run_cli(target, str(csv_file), "--group-by", "部门",
                            "--value", "销售额", "--out-dir", str(out2))
            assert proc.returncode == 0, \
                f"退出码应为 0，得到 {proc.returncode}：{(proc.stderr or '')[:200]}"
            assert "Traceback" not in (proc.stdout + proc.stderr), "把堆栈甩给用户了"
            assert (out2 / "summary.csv").is_file(), "CLI 没写出 summary.csv"
            assert (out2 / "stats.txt").is_file() and \
                (out2 / "stats.txt").read_text(encoding="utf-8"), "stats.txt 缺失或为空"
        _probe("8. CLI：py app.py data.csv --group-by 部门 --value 销售额 --out-dir DIR 跑通",
               "回到 L09：argparse 入口；L06：列名写错要友好报错而不是 KeyError 堆栈。", p8)

        # ---- 9. Excel 可选导出 ----
        def p9():
            have = importlib.util.find_spec("openpyxl") is not None
            if have:
                assert (out1 / "report.xlsx").is_file(), \
                    "本机装了 openpyxl，应额外产出 report.xlsx"
            # 没装 openpyxl 时：write_outputs/CLI 不抛 ImportError 即为正解（第 7、8 条已证明）
        _probe("9. Excel 导出：装了 openpyxl 就出 report.xlsx，没装则优雅跳过不崩",
               "回到 L10：to_excel 需要 engine；缺依赖走 try/except 提示而不是 ImportError 裸奔。", p9)

    print("=" * 60)
    print(f"结果：通过 {stats['通过']}，未过 {stats['未过']}，缺依赖 {stats['缺依赖']}"
          "（本机未装 openpyxl 时第 9 条按『优雅跳过』判通过）")
    return 0 if stats["未过"] == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n已中断。")
        sys.exit(130)
