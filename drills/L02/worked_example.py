# -*- coding: utf-8 -*-
"""L02 完整样例 —— 直接跑：py drills/L02/worked_example.py

同一个"订单统计"场景，用五种写法各解一遍。每种都注释了对应的 Java 写法，
目的是让你把手上的 Stream 心智**平移**到推导式，而不是重新学一遍统计。
"""
from __future__ import annotations

from collections import Counter, defaultdict

ORDERS = [
    {"id": 1, "customer": "张三", "amount": 120, "city": "北京"},
    {"id": 2, "customer": "李四", "amount": 80, "city": "上海"},
    {"id": 3, "customer": "张三", "amount": 300, "city": "北京"},
    {"id": 4, "customer": "王五", "amount": 50, "city": "深圳"},
    {"id": 5, "customer": "李四", "amount": 240, "city": "上海"},
    {"id": 6, "customer": "赵六", "amount": 0, "city": "北京"},
]


def total_per_customer() -> dict[str, int]:
    """写法一：defaultdict 累加。

    Java: orders.stream().collect(groupingBy(Order::customer,
          summingInt(Order::amount)))
    """
    totals: dict[str, int] = defaultdict(int)      # 声明只是给人看的，运行时不检查
    for order in ORDERS:
        totals[order["customer"]] += order["amount"]
    return dict(totals)


def counts_by_city() -> Counter:
    """写法二：Counter 一行搞定频次。

    Java: groupingBy(Order::city, counting())
    """
    return Counter(order["city"] for order in ORDERS)


def rich_customers(threshold: int) -> list[str]:
    """写法三：推导式 = filter + map 一次做完，不需要 collect。

    Java: totals.entrySet().stream().filter(e -> e.getValue() > threshold)
          .map(Entry::getKey).collect(toList())
    """
    totals = total_per_customer()
    return [name for name, amount in totals.items() if amount > threshold]


def top_two_orders() -> list[dict]:
    """写法四：sorted(key=...) 取代 Comparator。

    Java: orders.stream().max(comparingInt(Order::amount))；要前两名得排序。
    注意 sorted 返回新列表，list.sort 原地改，别混用。
    """
    return sorted(ORDERS, key=lambda o: o["amount"], reverse=True)[:2]


def unique_cities_ordered() -> list[str]:
    """写法五：dict.fromkeys 保序去重。

    Java: orders.stream().map(Order::city).distinct().collect(toList())
    换成 set 会丢顺序 —— Python 也一样，别用 sorted(set(...)) 蒙混，那是按字母序。
    """
    return list(dict.fromkeys(order["city"] for order in ORDERS))


if __name__ == "__main__":
    print("每人消费：", total_per_customer())
    print("城市分布：", dict(counts_by_city()), "最常见：", counts_by_city().most_common(1))
    print("高价值客户（>300）：", rich_customers(300))
    print("金额前两单：", [(o["id"], o["amount"]) for o in top_two_orders()])
    print("出现过的城市：", unique_cities_ordered())

    # 改这里看效果：把 threshold 从 300 改成 100，输出多了谁？
    # 再把 ORDERS 里加一条 amount 为 None 的记录，哪个函数先炸？为什么会炸？
