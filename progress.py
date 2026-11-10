#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""learn 进度与复习排期 —— 只依赖标准库。

用法：
    py progress.py                 # 看进度面板
    py progress.py start L03       # 标记开始第 3 课
    py progress.py done  L03       # 手动标记完成（check.py 全绿时会自动标）
    py progress.py review          # 今天该复习哪些课的闪卡
    py progress.py read L03        # 打过一次闪卡，推进复习进度
    py progress.py reset L03       # 清空某课记录
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

LEARN = Path(__file__).resolve().parent
STATE_FILE = LEARN / "progress.json"
LESSONS_DIR = LEARN / "lessons"

# 间隔重复：完成当天算 D0，之后 D+1、D+2、D+4、D+7 各复习一次闪卡
# 14 天冲刺方案（PLAN-14-DAYS.md）用这组短间隔，保证四轮都落在窗口内。
# 回到 README 的 4 周方案时改回 [1, 3, 7, 21]。
INTERVALS = [1, 2, 4, 7]
DAY = 86400
FMT = "%Y-%m-%d"


def load() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def save(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                          encoding="utf-8")


def lesson_titles() -> list[tuple[str, str]]:
    out = []
    if LESSONS_DIR.exists():
        for path in sorted(LESSONS_DIR.glob("L*.md")):
            first = next((line for line in
                          path.read_text(encoding="utf-8").splitlines()
                          if line.startswith("# ")), path.stem)
            out.append((path.stem.split("-")[0], first.lstrip("# ").strip()))
    return out


def _entry(state: dict, lesson: str) -> dict:
    return state.setdefault(lesson, {"status": "未开始", "score": "",
                                     "done_at": "", "reviews": 0})


def _mark_done(entry: dict) -> None:
    entry["status"] = "已完成"
    entry["done_at"] = time.strftime(FMT)
    entry.setdefault("reviews", 0)


def cmd_start(state: dict, lesson: str) -> None:
    entry = _entry(state, lesson)
    entry["status"] = "在读"
    entry["started_at"] = time.strftime(FMT)
    save(state)
    print(f"{lesson} -> 在读")


def cmd_done(state: dict, lesson: str) -> None:
    entry = _entry(state, lesson)
    _mark_done(entry)
    save(state)
    days = [time.strftime("%m-%d", time.localtime(time.time() + i * DAY))
            for i in INTERVALS]
    print(f"{lesson} -> 已完成。闪卡复习日：{', '.join(days)}")


def cmd_read(state: dict, lesson: str) -> None:
    entry = _entry(state, lesson)
    if not entry.get("done_at"):
        _mark_done(entry)
    entry["reviews"] = int(entry.get("reviews", 0)) + 1
    save(state)
    total = len(INTERVALS)
    print(f"{lesson} 复习进度 {entry['reviews']}/{total}"
          + ("  — 间隔重复走完，可以放手了。" if entry["reviews"] >= total else ""))


def cmd_reset(state: dict, lesson: str) -> None:
    state.pop(lesson, None)
    save(state)
    print(f"{lesson} 记录已清空")


def due_for_review(state: dict) -> list[str]:
    """今天到复习日、且间隔还没走完的课程。"""
    now = time.time()
    out = []
    for lesson, entry in sorted(state.items()):
        done_at = entry.get("done_at")
        if not done_at:
            continue
        try:
            start = time.mktime(time.strptime(done_at, FMT))
        except ValueError:
            continue
        arrived = sum(1 for i in INTERVALS if start + i * DAY <= now)
        done_reviews = int(entry.get("reviews", 0))
        if arrived > done_reviews:
            left = len(INTERVALS) - done_reviews
            out.append(f"{lesson}  第 {arrived}/{len(INTERVALS)} 次，"
                       f"剩 {left} 次（看 cards/{lesson.lower()}.md）")
    return out


def cmd_show(state: dict) -> None:
    titles = lesson_titles()
    if not titles:
        print("lessons/ 目录还是空的。")
        return
    print("=" * 64)
    print(f"{'课程':<5} {'状态':<7} {'判分':<7} 标题")
    print("-" * 64)
    finished = 0
    for num, title in titles:
        entry = state.get(num, {})
        status = entry.get("status", "未开始")
        if status == "已完成":
            finished += 1
        print(f"{num:<6} {status:<8} {entry.get('score', ''):<7} {title}")
    print("-" * 64)
    print(f"完成 {finished}/{len(titles)} 课。（L15 为选做，按需学。）")
    due = due_for_review(state)
    if due:
        print("\n今天要复习的闪卡（复习完用 `py progress.py read LXX` 打卡）：")
        for item in due:
            print(f"  - {item}")
    else:
        print("\n今天没有到期的闪卡复习。完成一课后这里会自动排上。")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    state = load()
    args = sys.argv[1:]
    if not args:
        cmd_show(state)
        return 0
    action = args[0]
    lesson = args[1].upper() if len(args) > 1 else ""
    if lesson and not lesson.startswith("L"):
        lesson = f"L{int(lesson):02d}"

    if action == "review":
        due = due_for_review(state)
        print("今天要复习：" if due else "没有到期的复习。")
        for item in due:
            print(f"  - {item}")
        return 0
    handlers = {"start": cmd_start, "done": cmd_done,
                "read": cmd_read, "reset": cmd_reset}
    if action in handlers:
        if not lesson:
            print(f"用法：py progress.py {action} L03")
            return 1
        handlers[action](state, lesson)
        return 0
    print(f"不认识的动作：{action}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
