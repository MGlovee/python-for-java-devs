# P3 · 数据体检 + Excel 报表

> 本项目的完整可运行参考实现见 example/app.py，卡住 20 分钟以上再看。

| 项 | 值 |
|---|---|
| 交付物 | 一个 `app.py`：pandas 读 CSV → 缺失/重复/异常值体检 → 分组聚合 → 输出汇总 CSV + 统计文本（Excel 可选） |
| 预计工时 | 3–5 小时 |
| 用到的课 | L10（文件与编码）、L15（numpy/pandas 速览）；P2 的输出可直接喂给它 |
| 依赖 | `pandas`（已装）；`openpyxl` **可选**——没装必须优雅跳过，装了才出 xlsx |
| 验收 | `py verify.py`（9 条探测全 `[通过]`，退出码 0） |

数据量小（几百行）用标准库 `csv` 也能做完 M1/M2，**但 groupby 和分位数请用 pandas**——
这项目的目的就是练 L15 那套 DataFrame 心智。

---

## 1. 需求

- 读一个 CSV（位置参数；**省略参数时用内联样本跑通全流程**，方便无数据也能演示）。
- **体检** `data_check(df)` 返回一个纯 Python dict（必须能 `json.dumps`，numpy 标量要转 `int/float`）：
  - `rows`：总行数；
  - `missing`：每列缺失计数 `NaN` 个数（`王五` 那行销售额为空要算 1）；
  - `duplicate_rows`：整行重复的**多余副本数**（同一条记录出现 2 次 → 计 1，用 `df.duplicated().sum()`）；
  - `outliers`：对每个数值列用 **IQR 1.5 法则**（`[Q1-1.5·IQR, Q3+1.5·IQR]` 之外），
    值为命中行的**下标列表**；IQR 为 0 的列跳过；
- **聚合** `summarize(df, group_by, value)` 返回 `list[dict]`，每行键为
  `{分组列名: 组值, "count": 非空个数, "sum": 合计, "mean": 均值}`，**按 sum 降序**。
  分组列/值列不存在 → 允许抛 `KeyError`，但 `main` 必须捕获并友好报错、非 0 退出。
- **产出** `write_outputs(df, out_dir, group_by, value)` 固定写三个东西（前两个必选）：
  - `out_dir/summary.csv`：表头**必须**是 `[分组列, count, sum, mean]`，`index=False`，编码 `utf-8-sig`（Excel 打开不乱码）；
  - `out_dir/stats.txt`：人类可读体检结果（含"缺失"与"重复"字样即可）；
  - `out_dir/report.xlsx`：**仅当本机装了 openpyxl**；未装时打印一句提示并跳过，**不许崩**。
- **CLI**：`py app.py 数据.csv --group-by 部门 --value 销售额 --out-dir 目录`；
  `--group-by` 默认 `部门`、`--value` 默认 `销售额`；`--out-dir` 省略时写临时目录。
- 边界：文件不存在 → stderr 报错、非 0 退出、无 Traceback；不传 CSV 参数时不得在仓库留下任何文件。

## 2. 函数契约表（verify.py 按这个探测）

| 函数 | 签名 | 返回 | 异常 |
|---|---|---|---|
| `load_data` | `(path: str \| Path) -> pd.DataFrame` | shape (9,3) 的样本数据 | 文件问题可抛，main 里兜住 |
| `data_check` | `(df) -> dict` | `{"rows","missing","duplicate_rows","outliers"}`，纯 Python 类型 | 不抛 |
| `summarize` | `(df, group_by: str, value: str) -> list[dict]` | sum 降序，`mean` 为 float | 列名错抛 `KeyError` |
| `write_outputs` | `(df, out_dir, group_by, value) -> list[Path]` | 实际写出的文件路径列表 | 不抛（openpyxl 缺失走 except） |
| `main` | `(argv=None) -> int` | 退出码 | — |

固定文件名 `summary.csv` / `stats.txt` / `report.xlsx` 是契约的一部分，别自创前缀。

### 体检样本数据字典（verify 用的就是这 9 行，先手算再写代码）

| 下标 | 部门 | 姓名 | 销售额 | 埋的雷 |
|---|---|---|---|---|
| 0 | 研发 | 张三 | 100 | |
| 1 | 研发 | 李四 | 120 | |
| 2 | 研发 | 王五 | （空） | **缺失 1**，且不计入研发 count |
| 3 | 销售 | 赵六 | 200 | |
| 4 | 销售 | 赵六 | 200 | **整行重复**，duplicate_rows=1 |
| 5 | 销售 | 孙七 | 150 | |
| 6 | 财务 | 周八 | 130 | |
| 7 | 财务 | 吴九 | 999999 | **IQR 异常值**，outliers 含下标 7 |
| 8 | 财务 | 郑十 | 110 | |

期望的 `summarize(df, "部门", "销售额")`（sum 降序）：

```json
[{"部门": "财务", "count": 3, "sum": 1000239.0, "mean": 333413.0},
 {"部门": "销售", "count": 3, "sum": 550.0,     "mean": 183.33333333333334},
 {"部门": "研发", "count": 2, "sum": 220.0,     "mean": 110.0}]
```

`summary.csv` 头两行（表头契约）：

```csv
部门,count,sum,mean
财务,3,1000239.0,333413.0
```

## 3. 里程碑

| 阶段 | 目标 | 检查点 |
|---|---|---|
| M1 读入+体检 | `data_check` 三类指标全对且可 JSON 化 | verify 探测 2–5 绿 |
| M2 聚合 | `summarize` 对上心算值（研发 count=2、sum=220、mean=110） | 探测 6 绿 |
| M3 产出 | 三个文件按契约写出，openpyxl 缺失不崩 | 探测 7、9 绿 |
| M4 CLI | 参数化 + 错误处理 + 临时目录零残留 | 探测 8 绿；`git status` 干净 |

## 4. 验收标准（= verify.py 探测清单）

1. 模块可导入（pandas 可用），四个契约函数齐全，无副作用。
2. `load_data` 读出 9 行 3 列。
3. 缺失计数正确 + 结果 `json.dumps` 不炸。
4. 重复行计数正确。
5. IQR 异常值命中下标 7 且不误伤。
6. `summarize` 的 count/sum/mean 与降序正确。
7. `write_outputs` 产出 `summary.csv`（表头契约）与 `stats.txt`。
8. CLI 带 `--out-dir` 全流程退出码 0、无堆栈。
9. openpyxl 装了出 xlsx / 没装优雅跳过。

**额外自拟一条**：给 `data_check` 增加 `negative_values`（每数值列的负数个数），
自己扩展 verify 的一个副本加一条探测（别改原 verify.py）。

### 交卷前自查

| 问题 | 为什么要问 |
|---|---|
| `data_check` 的返回值 `json.dumps` 一下会炸吗？ | numpy 标量（`np.int64`）不是 int，序列化会 `TypeError`（L15） |
| `count` 用的是 pandas 的 `.count()`（非空个数）而不是 `len(df)` 吗？ | 王五那行销售额是 NaN，研发应该是 2 不是 3（L15） |
| `to_csv` 带 `index=False` 和 `encoding="utf-8-sig"` 吗？ | 不带前者会多出一列 `Unnamed: 0`，不带后者 Excel 双击乱码（L10） |
| openpyxl 的探测是 `try: import openpyxl` 写在函数里，而不是模块顶层吗？ | 顶层 import 失败会让整个 app 无法加载（L06/L09） |

## 5. 参考实现提示（代码在 example/app.py）

| 里程碑 | 关键思路 | 该用的 API |
|---|---|---|
| M1 | 三行体检各一个惯用式；返回 dict 前把 numpy 标量 `int()`/`float()` 转纯类型 | `df[col].isna().sum()`、`df.duplicated().sum()`、`s.quantile(0.25/0.75)` |
| M1 | 异常值用布尔掩码：`mask = (df[col] < lo) \| (df[col] > hi)`，`df.index[mask]` 拿原始行下标 | L15 布尔索引 |
| M2 | 一个 groupby 链搞定，`.agg(["count","sum","mean"])`，`sort_values("sum", ascending=False)` | `DataFrame.groupby` |
| M3 | openpyxl 探测用 `try: import openpyxl except ModuleNotFoundError: 跳过`；写 xlsx 用 `pd.ExcelWriter` 多 sheet | `to_excel`、L06 |
| M3 | CSV 编码写 `utf-8-sig`——读也兼容。Windows Excel 双击不带 BOM 的 UTF-8 会乱码 | L10 编码坑 |
| M4 | `--out-dir` 省略时用 `contextlib.ExitStack` + `tempfile.TemporaryDirectory` 包住，函数退出即焚 | L06/L09 |

## 6. 常见错（Java 老手三连）

1. **for 循环逐行算均值**。你已经从 Spring 的 for-each 里出来了：pandas 的价值在整列向量化，
   循环行数上 10 万就是分钟 vs 毫秒的差距。`df.groupby(...).agg(...)` 一行顶你写 30 行。
2. **numpy 标量当纯类型返回**。`{"missing": {"销售额": np.int64(1)}}` 看着像 int，
   `json.dumps` 立刻 `TypeError`。契约写明"纯 Python 类型"，出口处统一 `int()/float()`。
3. **NaN 比较直觉照搬**。`df[col] == None` 永远是 False，`if x == x` 判 NaN 是 Java 没有的黑暗写法——
   用 `isna()/dropna()`；缺失值参与 sum/mean 会被 pandas 自动跳过，这个行为和你 SQL 直觉一致。

## 7. 进阶

- 装 openpyxl（`pip install openpyxl`）后加条件格式：异常值单元格标红（原文 Day24/25）。
- 把 P2 的 SQLite 导出成 CSV 喂给本项目，两个项目串成管线。
- 用 matplotlib 出一张分组柱状图 PNG（原文 Day78）。
- 全量类型注解 + `py -m mypy app.py`；`pip install pytest` 后给体检函数补单测（L14）。

## 8. 回原文

| 想要 | 原文 |
|---|---|
| 读写 CSV | [Day21-30/23.Python读写CSV文件.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/23.Python%E8%AF%BB%E5%86%99CSV%E6%96%87%E4%BB%B6.md) |
| Excel 读写（openpyxl 详解） | [Day21-30/24.Python读写Excel文件-1.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/24.Python%E8%AF%BB%E5%86%99Excel%E6%96%87%E4%BB%B6-1.md)、[25.Python读写Excel文件-2.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/25.Python%E8%AF%BB%E5%86%99Excel%E6%96%87%E4%BB%B6-2.md) |
| pandas 入门（DataFrame/缺失值/分组） | [Day66-80/72.深入浅出pandas-1.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day66-80/72.%E6%B7%B1%E5%85%A5%E6%B5%85%E5%87%BApandas-1.md)、[73.深入浅出pandas-2.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day66-80/73.%E6%B7%B1%E5%85%A5%E6%B5%85%E5%87%BApandas-2.md)、[74.深入浅出pandas-3.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day66-80/74.%E6%B7%B1%E5%85%A5%E6%B5%85%E5%87%BApandas-3.md) |
| NumPy 基础 | [Day66-80/68.NumPy的应用-1.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day66-80/68.NumPy%E7%9A%84%E5%BA%94%E7%94%A8-1.md) |
| pandas 速成心法 | [番外篇/如何快速驾驭 pandas 库.md](https://github.com/jackfrued/Python-100-Days/blob/master/%E7%95%AA%E5%A4%96%E7%AF%87/%E5%A6%82%E4%BD%95%E5%BF%AB%E9%80%9F%E9%A9%BE%E9%A9%AD%20pandas%20%E5%BA%93.md) |

主索引与判分机制见 [../../README.md](../../README.md)。

体检三件套（缺失/重复/异常值）的口径全部在 `data_check` 一个函数里——报告类工具最重要的
就是"指标口径单点定义"，Java 里你也不会把 SQL 抄七份，同一个道理。
