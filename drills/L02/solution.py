# -*- coding: utf-8 -*-
"""L02 参考答案。卡住 15 分钟以上再看，别整篇抄。

py check.py L02 --solution
"""
from __future__ import annotations

from collections import Counter, defaultdict


def slice_tail(seq: list, n: int) -> list:
    # 关键：把起点算成 len(seq)-n，n=0 时得到 len(seq) → 空；n 超界时得到负数 → 整段返回
    return seq[len(seq) - n:]


def dedup_keep_order(items: list) -> list:
    return list(dict.fromkeys(items))


def word_frequencies(words: list[str]) -> dict[str, int]:
    return Counter(words)


def group_by_first_letter(words: list[str]) -> dict[str, list[str]]:
    groups = defaultdict(list)
    for word in words:
        groups[word[0]].append(word)
    return dict(groups)


def squares_of_evens(n: int) -> list[int]:
    return [x * x for x in range(1, n + 1) if x % 2 == 0]


def invert_index(docs: dict[str, list[str]]) -> dict[str, set[str]]:
    vocabulary = {word for words in docs.values() for word in words}   # 嵌套推导式做并集
    return {word: {doc_id for doc_id, words in docs.items() if word in words}
            for word in vocabulary}


def top_k_words(words: list[str], k: int) -> list[str]:
    counts = Counter(words)
    ranked = sorted(counts, key=lambda w: (-counts[w], w))   # 次数降序 + 字母升序
    return ranked[:k]


def sort_by_key(records: list[dict], key: str, *, reverse: bool = False) -> list[dict]:
    """None（含缺键）永远排最后：把"有没有值"拆成两组再各自处理，比构造元组 key 更直白。"""
    valued = [r for r in records if r.get(key) is not None]
    missing = [r for r in records if r.get(key) is None]
    return sorted(valued, key=lambda r: r[key], reverse=reverse) + missing


def chunked(seq: list, size: int) -> list[list]:
    if size < 1:
        raise ValueError(f"size 至少为 1，收到 {size}")
    return [seq[i:i + size] for i in range(0, len(seq), size)]


def merge_dicts(first: dict, second: dict) -> dict:
    merged = dict(first)                      # 先复制，避免改动入参
    for key, value in second.items():
        merged[key] = merged.get(key, 0) + value if key in merged else value
    return merged
