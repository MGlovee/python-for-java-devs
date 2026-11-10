# -*- coding: utf-8 -*-
"""L10 完整样例 —— 直接跑：py drills/L10/worked_example.py

一个 20 行的"读 CSV → 清洗 → 写 JSON"小流程，把本课的六个知识点全串起来：
文本模式读、显式 encoding、pathlib、csv.DictReader、json.dump/ensure_ascii、二进制写。
所有文件写在临时目录里，跑完自动删除，仓库不会留产物。
"""
from __future__ import annotations

import csv
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):        # 和 check.py 保持一致，中文不乱码
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CSV_TEXT = """姓名,语文,数学,英语
关羽,98,86,61
张飞,86,58,80
赵云,95,73,70
"""


def parse_scores(text: str) -> list[dict[str, object]]:
    """csv.DictReader 读出来全是字符串，数值要自己转 —— 它不会猜。"""
    rows: list[dict[str, object]] = []
    with io.StringIO(text, newline="") as buffer:
        for raw in csv.DictReader(buffer):
            record: dict[str, object] = {"name": raw["姓名"]}
            for subject in ("语文", "数学", "英语"):
                record[subject] = int(raw[subject])
            record["avg"] = round(
                (record["语文"] + record["数学"] + record["英语"]) / 3, 2)  # type: ignore[operator]
            rows.append(record)
    return rows


def top_student(rows: list[dict[str, object]]) -> dict[str, object]:
    """按平均分最高的那个 —— max(key=...) 比排序省事。"""
    return max(rows, key=lambda row: row["avg"])


def write_report(folder: Path, rows: list[dict[str, object]]) -> Path:
    """写 JSON 报表：ensure_ascii=False 才能让人看懂中文。"""
    target = folder / "成绩单.json"
    with open(target, "w", encoding="utf-8", newline="\n") as file:
        json.dump({"count": len(rows), "rows": rows}, file,
                  ensure_ascii=False, indent=2)
    return target


def read_report_briefly(target: Path) -> tuple[int, int]:
    """同一个文件：文本模式读回 JSON，二进制模式看它真实占了多少字节。"""
    with open(target, "r", encoding="utf-8") as file:
        payload = json.load(file)
    size = target.stat().st_size            # pathlib 拿文件大小，不用 os.path.getsize
    return len(payload["rows"]), size


def main() -> None:
    folder = Path(tempfile.mkdtemp(prefix="l10_example_"))
    try:
        source = folder / "scores.csv"
        source.write_text(CSV_TEXT, encoding="utf-8")   # pathlib 一行写文本
        print("路径拆解：", source.name, "|", source.stem, "|", source.suffix)

        rows = parse_scores(source.read_text(encoding="utf-8"))
        print(f"读到 {len(rows)} 行，最高平均分：{top_student(rows)}")

        report = write_report(folder, rows)
        count, size = read_report_briefly(report)
        print(f"报表 {report.name}：{count} 条记录，{size} 字节")
        print("文件前 60 个字符：", report.read_text(encoding="utf-8")[:60].replace("\n", " "))
    finally:
        shutil.rmtree(folder, ignore_errors=True)


if __name__ == "__main__":
    main()
