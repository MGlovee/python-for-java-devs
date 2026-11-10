# L15 · numpy 与 pandas 速览（选做课）

> 读 35 分钟 · 练 55 分钟
> 对应原文：`Day66-80/66`、`68`–`71`（NumPy）、`72`–`77`（pandas 1–6）+ `番外篇/如何快速驾驭 pandas 库.md`
> —— 实测 12 篇、6264 行 → 压缩成这一页（`67.环境准备.md` 158 行是装包说明，没算）
> 判分：`py check.py L15` ｜ 卡片：[cards/l15.md](../cards/l15.md)

这是**选做课**：做 P3 那种"读 CSV → 体检 → 分组汇总"的报表时才需要。
你的存量优势是 SQL 和集合操作，本课只讲 Python 侧的增量：
**numpy = 一整块同类型数字 + 轴/广播；pandas = 带列名的表 + 分组/合并/缺失值**。
练习需要 numpy、pandas（实测 2.4.3 / 3.0.1）；全程内存造数据，不联网、不落盘。

---

## ① 开课先答 3 题（先答后读，答错才对）

1. `m = np.array([[1, 2, 3], [4, 5, 6]])`，`m.mean(axis=0)` 和 `m.mean(axis=1)` 各自返回什么值、什么形状？
2. `base = np.arange(6)`，`grid = base.reshape(2, 3)`，然后 `grid[0, 0] = 99` —— `base` 变了吗？
3. `df["销售额"][df["销售额"] > 150] = 0` 在 pandas 3 上跑一遍，原表会被改掉吗？会发生什么？

答案在 ⑥。

---

## ② 差异地图（Java → numpy / pandas）

| 主题 | Java | Python | 一句话提醒 |
|---|---|---|---|
| 数字数组 | `int[][]`（行引用数组）、`List<Integer>`（装箱） | `np.ndarray`：一块**连续内存** + `(shape, strides)` 元数据 | 没有对象头、没有装箱，所以快、所以能整块运算 |
| 元素类型 | 编译期定死 | `dtype`：`int64` / `float64` / `bool` / `str` … | 一个 ndarray 只能一种 dtype；混着放会整体向上转 |
| 造数组 | `new int[r][c]` | `np.array([[1, 2], [3, 4]])`、`np.arange(6).reshape(2, 3)` | 嵌套 list 是给 numpy 的"初始化数据"，不是数组本身 |
| 逐元素运算 | 手写双重 for / `Stream.map` | `m * 2`、`m + other`（**向量化**，循环在 C 里跑） | 写出 `for r in range(rows)` 说明还没转过来 |
| 行列聚合 | 双重循环 / `Collectors` | `axis`：`axis=0` 沿行方向压缩（得每列），`axis=1` 沿列方向（得每行） | 见下面的小矩阵算例，这一条必须讲透 |
| 形状变换 | 没有对应概念 | `reshape` / `ravel` / `keepdims=True` | `reshape` 返回**视图**，切片也是视图（⑤ 的坑 1） |
| 过滤 | `stream.filter(...)` | 布尔索引 `arr[arr > 80]`、花式索引 `arr[[0, 3]]` | 条件用 `&`/`\|` 并加括号，`and`/`or` 直接报错 |
| 排序 | `Arrays.sort` / `Comparator` | `np.sort(a)`（值）、`np.argsort(a)`（**下标**） | `argsort` = "排完还想知道每行是谁" |
| 带列名的表 | `List<Map<String, Object>>` | `pd.DataFrame`（+ 每列是一个 `Series`，带索引） | 列名、行索引、缺失值都是**一等公民** |
| 读 CSV | 手写 `BufferedReader` 切分 | `pd.read_csv(path)`，内存字符串用 `io.StringIO(text)` | 数字列自动转型，空字段自动当缺失 |
| GROUP BY | SQL / `groupingBy + reducing` | `df.groupby("部门")["销售额"].agg(["count", "sum", "mean"])` | `count` 是**非空**个数，跟 SQL 一致 |
| JOIN | SQL JOIN | `pd.merge(left, right, on="部门", how="inner"/"left")` | 列名冲突时加 `suffixes=`，别靠默认 |
| 缺失值 | `null` / `Optional` | `NaN`（浮点）/ `None` / `pd.NA` | 只能用 `isna()`；`x == None` 永远 False |
| 逐行调函数 | for-each | `df["col"].apply(f)`、`df.map(f)` | **比向量化慢一个量级**（`applymap` 在 pandas 3 已删） |

### 轴 axis：Java 里没有的那个概念，用一个小矩阵讲透

```python
m = np.array([[1.0, 2.0, 3.0],
              [4.0, 5.0, 6.0]])          # shape (2, 3)：轴 0 = 行，轴 1 = 列
m.sum(axis=0)        # [5., 8., 11.]  shape (3,)  ← 把"行"这一轴压掉，得每列
m.sum(axis=1)        # [6., 15.]      shape (2,)  ← 把"列"这一轴压掉，得每行
m.mean(axis=1, keepdims=True)          # [[2.], [5.]]   shape (2, 1)：形状不塌
```

口诀：**axis 是"被消灭的那根轴"**，结果形状里就没有这个维度了（除非 `keepdims=True`）。
`keepdims` 的用处：算完全体还要拿它去广播回原形状（每行减每行均值），形状对得上才不会炸。

### 广播（broadcasting）一句话版

> 两个形状从**右往左**逐位对齐：相等就通过，某一边是 1（或压根没这一轴）就沿着这一轴复制补齐，都对不上抛 `ValueError`。

```python
m - m.mean(axis=0)            # (2,3) 减 (3,)：最后一轴 3 对 3 → 每列减自己的均值，通过
m + m.sum(axis=1)             # (2,3) 加 (2,)：最后一轴 3 对 2 → ValueError
m + m.sum(axis=1, keepdims=True)   # (2,3) 加 (2,1)：补一列 → 每行加自己的行和，通过
```

想验证"向量化比循环快多少"，自己用 `timeit` 计时；本课**不**把它写进判分断言（离线环境时间不稳）。

### 索引三兄弟：谁是视图，谁是拷贝

```python
base = np.arange(6)
base[1:4]                # 切片 → 视图，改了会写回 base
base[[0, 3, 5]]          # 花式索引 → 拷贝，改了不影响 base
base[base > 2]           # 布尔索引 → 拷贝，且结果永远降成 1 维
grid = base.reshape(2, 3)
np.shares_memory(base, grid)     # True —— 这就是"改视图会改原数组"的检测工具
```

### pandas 最小可用动作集（做报表就这十行）

```python
df = pd.read_csv(io.StringIO(text))                 # 读：路径 / StringIO / bytes
df[["部门", "销售额"]]                              # 选列：按列名，返回新表
df[df["销售额"] > 150]                              # 条件筛选：NaN 行自动被滤掉
df.loc[df["销售额"] > 150, "销售额"] = 0            # 赋值：一步到位，别走链式
df["部门"].value_counts()                           # 频次分布 ≈ GROUP BY 计数
df.groupby("部门")["销售额"].agg(["count", "sum", "mean"])   # 透视前的聚合
pd.merge(df, budget, on="部门", how="left")         # 两张表按键拼列
int(df["销售额"].isna().sum())                      # 缺失体检
df.assign(销售额=df["销售额"].fillna(0))            # 填充并返回新表
df.to_csv(path_or_buf, index=False, encoding="utf-8-sig")   # 写出（L10 的编码坑同样适用）
```

### 什么时候**别**用 pandas

| 场景 | 用什么 | 为什么 |
|---|---|---|
| 只有几百行、就是读几列 CSV | 标准库 `csv.DictReader`（L10） | 少一个依赖、启动快、行为全在你手里 |
| 只要一个平均/中位数 | `statistics.mean` / `median` | 为一行代码拉进整个 numpy |
| 数据是逐条流式来的（日志、爬虫） | 生成器 + 累加（L07） | pandas 要一次性装进内存 |
| 要打包成 CLI / 容器最小镜像、在意体积 | 标准库 | numpy+pandas 带几十个 MB 和编译扩展 |
| 需要**事务性写入**、复杂关联查询 | 直接写 SQL（L13） | pandas 没有索引/事务/约束那套 |

P3 的口径以它自己的 README 为准：那边**声明了依赖 pandas**（`load_data` 直接 `pd.read_csv` 出 DataFrame），
分组聚合、缺失/重复/异常值体检、分位数这几步就该用 pandas；而 CLI 参数、文件编码、`utf-8-sig` 写出仍是
L10/L14 的标准库功夫。上面这张"别用 pandas"的表是给**下一个不需要透视的小脚本**做取舍用的，
不是给 P3 减验收条件，也别反过来把 P3 的 `groupby` 手写成标准库双重循环。

---

## ③ 完整样例：读 → 跑 → 改

[drills/L15/worked_example.py](../drills/L15/worked_example.py) 直接跑：
`py -X utf8 drills/L15/worked_example.py`。六段：视图 vs 拷贝、轴、广播报错、
布尔/花式索引与 `argsort` 稳定性、DataFrame 选列筛选与链式赋值告警、`groupby`/`merge`/缺失值。

跑完回答：把 `demo_axis()` 里的 `axis=1` 改成 `axis=0`，输出的形状怎么变？为什么？

---

## ④ 补全题

打开 [drills/L15/exercises.py](../drills/L15/exercises.py)，10 个函数：前 5 挖空、后 5 只给需求。
挖空：`create_grid`、`column_means`、`pick_by_mask`、`normalize`、`read_csv_frame`；
独立写：`center_columns`（广播）、`rank_names`（`np.argsort`）、`select_and_sort`（选列+排序+`reset_index`）、
`group_summary`（`groupby().agg()`，返回值必须能 `json.dumps`）、`fill_missing`（`isna`/`fillna`，不许链式赋值）。

```powershell
py check.py L15 -v
```

numpy / pandas 没装时判分器会记「缺依赖」，那是环境问题，别在文件里 `try/except import` 掩盖。

---

## ⑤ 三个 Java 老手必踩的坑

1. **"我就改了一个格子，原数组怎么全变了？"** —— 切片和 `reshape` 返回的是**视图**：同一块内存换了个
   形状解释。`Arrays.copyOfRange` 那种"拿到的是新数组"的直觉在这里是反的。要独立副本必须 `.copy()`，
   怀疑时用 `np.shares_memory(a, b)` 判一下。
2. **链式赋值静默失效。** `df["销售额"][mask] = 0` 中间那步在 copy-on-write 下**永远是一张拷贝**，
   pandas 3 只给你一条 `ChainedAssignmentError` 告警，数据一个字没改（旧教程里这种写法能改到一半）。
   写成一步：`df.loc[mask, "销售额"] = 0`，或者 `df = df.assign(销售额=...)`。
3. **axis 方向反了，结果不报错。** `m.mean(axis=0)` 是每列均值、`axis=1` 是每行均值，轴用反只是
   "数字看起来挺合理"，不会抛异常 —— 但后面广播就会炸 `ValueError: operands could not be broadcast
   together with shapes (2,3) (2,)`。记法：**axis 是被压掉的那根轴**；算完还要用回去就 `keepdims=True`。

顺带三条小的：`arr.ptp()` 在 numpy 2 已删（改 `np.ptp(arr)`）、`DataFrame.applymap` 在 pandas 3 已删
（改 `DataFrame.map`）、`json.dumps` 遇到 `np.int64` 会 `TypeError`（出口统一 `int()` / `float()`）。

---

## ⑥ 现在回看开头 3 题

1. `mean(axis=0)` → `array([2.5, 4.5, 6.5])`，形状 `(3,)`（每列）；`mean(axis=1)` → `array([2., 5.])`，
   形状 `(2,)`（每行）。压掉哪根轴，结果里就没哪根轴。
2. **变了**。`reshape` 不拷贝，`grid` 和 `base` 共用同一块内存，`base[0]` 就是 99。
3. **不会**。pandas 3 默认 copy-on-write：它发一条 `ChainedAssignmentError` 告警并什么都不改。
   正确写法是 `df.loc[df["销售额"] > 150, "销售额"] = 0`。

答错的那题，去 [cards/l15.md](../cards/l15.md) 找对应卡片。

---

## ⑦ 通关标准

- `py check.py L15` 输出 `18/18 通过`（空白工作表是 `0/18 通过 ｜ 未做 18`）。
- 白板写出：`np.arange(6).reshape(2, 3)` 的 `mean(axis=0)` / `mean(axis=1, keepdims=True)` 各是什么，
  以及"为什么 `reshape` 之后改一格会影响原数组"。
- 用 `io.StringIO` 读一段 CSV，`groupby().agg()` 出 count/sum/mean，结果能直接 `json.dumps`。
- 达成后：`py progress.py done L15`（判分全绿也会自动记完成日）。

## ⑧ 还要细节？回原文

| 想要 | 原文 |
|---|---|
| 数据分析流程、分析师职责与技能栈 | [66.数据分析概述.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day66-80/66.%E6%95%B0%E6%8D%AE%E5%88%86%E6%9E%90%E6%A6%82%E8%BF%B0.md)（88 行） |
| 创建数组、dtype、属性、普通/切片/花式/布尔索引、图像切片案例 | [68.NumPy的应用-1.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day66-80/68.NumPy%E7%9A%84%E5%BA%94%E7%94%A8-1.md)（891 行） |
| 描述统计信息、数组的其他方法 | [69.NumPy的应用-2.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day66-80/69.NumPy%E7%9A%84%E5%BA%94%E7%94%A8-2.md)（343 行） |
| 数组运算、通用函数、**广播机制** | [70.NumPy的应用-3.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day66-80/70.NumPy%E7%9A%84%E5%BA%94%E7%94%A8-3.md)（478 行） |
| 向量/矩阵/行列式/线性代数/多项式（本课不要求） | [71.NumPy的应用-4.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day66-80/71.NumPy%E7%9A%84%E5%BA%94%E7%94%A8-4.md)（726 行） |
| `Series` 与 `DataFrame` 创建、索引切片、数据筛选 | [72.深入浅出pandas-1.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day66-80/72.%E6%B7%B1%E5%85%A5%E6%B5%85%E5%87%BApandas-1.md)（798 行）、[73.深入浅出pandas-2.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day66-80/73.%E6%B7%B1%E5%85%A5%E6%B5%85%E5%87%BApandas-2.md)（473 行） |
| 数据重塑、清洗（缺失/重复/异常值）、`merge` | [74.深入浅出pandas-3.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day66-80/74.%E6%B7%B1%E5%85%A5%E6%B5%85%E5%87%BApandas-3.md)（648 行，注意其中 `applymap` 已失效） |
| 描述统计、排序取头部、分组聚合、透视表 | [75.深入浅出pandas-4.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day66-80/75.%E6%B7%B1%E5%85%A5%E6%B5%85%E5%87%BApandas-4.md)（482 行） |
| 同比环比、窗口计算、相关性 | [76.深入浅出pandas-5.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day66-80/76.%E6%B7%B1%E5%85%A5%E6%B5%85%E5%87%BApandas-5.md)（247 行） |
| 各类索引（范围/分类/多级/日期时间） | [77.深入浅出pandas-6.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day66-80/77.%E6%B7%B1%E5%85%A5%E6%B5%85%E5%87%BApandas-6.md)（471 行） |
| pandas 心法与完整分析流程 | [如何快速驾驭 pandas 库.md](https://github.com/jackfrued/Python-100-Days/blob/master/%E7%95%AA%E5%A4%96%E7%AF%87/%E5%A6%82%E4%BD%95%E5%BF%AB%E9%80%9F%E9%A9%BE%E9%A9%AD%20pandas%20%E5%BA%93.md)（619 行） |
