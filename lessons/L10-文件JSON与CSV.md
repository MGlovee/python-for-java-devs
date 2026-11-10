# L10 · 文件、JSON 与 CSV

> 读 40 分钟 · 练 50 分钟
> 对应原文：`Day21-30/21`~`27`（7 篇、1325 行）→ 压缩成这一页（Excel/Word/PDF 四篇只留导览）
> 判分：`py check.py L10` ｜ 卡片：[cards/l10.md](../cards/l10.md)

Java 里你面对的是 `InputStream`/`Reader` 两套流 + try-with-resources。Python 把这件事压成
一个 `open()` + 一个 `with`，剩下的坑**全在编码上**——尤其在 Windows 上。

---

## ① 开课先答 3 题（先答后读，答错才对）

在纸上写下答案，再往下翻。

1. Windows 上执行 `open("a.txt").read()`，文件里是 UTF-8 的中文，最可能抛什么异常？
2. `json.dumps({"名字": "骆昊"})` 打印出来是什么样子？想输出中文原样该加哪个参数？
3. `open(path, "rb").read()` 的返回类型是什么？它能直接 `+` 一个 `str` 吗？

答案在 ⑥。

---

## ② 差异地图（只列你缺的那 20%）

| 主题 | Java | Python | 一句话提醒 |
|---|---|---|---|
| 打开文件 | `new FileReader(p)` | `open(p, mode, encoding=...)` | 一个函数搞定文本/二进制/读/写/追加 |
| 模式 | 类名区分（`BufferedReader`…） | 字符串 `'r' 'w' 'x' 'a' 'b' 't' '+'` | `'w'` **直接清空原文件**，`'x'` 才是"已存在就报错" |
| 编码 | JVM 有 `file.encoding`/`Charset` | **文本模式默认 = 操作系统 locale** | Windows 上默认 `gbk`；不写 `encoding` 迟早炸 |
| 关闭 | try-with-resources | `with open(...) as f:` | `with` 退出即 close，异常也关 |
| 换行 | `\r\n` 自己扛 | 读时通用换行 → `\n`；写时**默认翻译**成 `\r\n` | 写文本传 `newline="\n"`，写 CSV 传 `newline=""` |
| 字节 vs 字符 | `byte[]` / `char[]` | `bytes` / `str`，**两种类型不能混** | `str` ↔ `bytes` 靠 `.encode()` / `.decode()` |
| 路径 | `java.nio.file.Path` + `Files` | `pathlib.Path` | 链式、跨平台、可 `.read_text()` 一行读完 |
| JSON | Jackson / Gson + 注解 | 标准库 `json` + `dict` | Python 的对象↔JSON 要**手写** `__dict__` / `dataclasses.asdict` |
| CSV | OpenCSV / commons-csv | 标准库 `csv` | 有标准库，不必装三方包 |
| 序列化(私有) | `Serializable` | `pickle` | 只能给 Python 自己用，且**不可信数据禁止反序列化** |

### `open()` 的模式表（背下来，原文那张图可以省了）

| mode | 含义 |
|---|---|
| `'r'` | 读文本（默认）。文件不存在 → `FileNotFoundError` |
| `'w'` | 写文本，**先清空** |
| `'x'` | 独占创建，文件已存在 → `FileExistsError` |
| `'a'` | 追加，文件不存在则创建 |
| `'b'` | 叠加用：`'rb' 'wb' 'ab'` → 字节串 |
| `'+'` | 叠加用：`'r+'` 读写同一文件 |

### pathlib vs os.path：只用前者

| 想要 | 老写法（`os.path`） | `pathlib` |
|---|---|---|
| 拼接 | `os.path.join(d, "a", "b.txt")` | `Path(d) / "a" / "b.txt"` |
| 文件名/主名/扩展名 | `basename` + `splitext` 两刀 | `p.name` / `p.stem` / `p.suffix` |
| 父目录 | `os.path.dirname(p)` | `p.parent` |
| 是否存在 / 大小 | `os.path.exists` / `getsize` | `p.exists()` / `p.stat().st_size` |
| 读全文 | `open(p, encoding='utf-8').read()` | `p.read_text(encoding='utf-8')` |
| 遍历目录 | `os.walk` | `p.glob("**/*.csv")` |

纯字符串拆解（不碰磁盘）用 `PureWindowsPath` / `PurePosixPath`，单测里很好使。

### JSON：四个函数 + 两个关键参数

```python
json.dumps(obj)          # 对象 → str        json.dump(obj, file)    # 对象 → 文件
json.loads(text)         # str   → 对象      json.load(file)         # 文件 → 对象
```

| 参数 | 作用 | 默认值 |
|---|---|---|
| `ensure_ascii` | True 时非 ASCII 全变 `\uXXXX` | **True（要中文就显式写 False）** |
| `indent` | 缩进美化 | `None`（压成一行） |
| `sort_keys` | 键排序，输出稳定 | False |
| `default` | 遇到不认的类型时的兜底转换函数 | 无 → 抛 `TypeError` |
| `strict` | 禁止字符串里出现控制字符 | True |

类型映射只有 7 对（`dict↔object`、`list/tuple↔array`、`str↔string`、`int/float↔number`、
`bool↔true/false`、`None↔null`）。**`set`、`datetime`、自定义类都不在里面** —— 要么给 `default=`，
要么自己转：`asdict(person)`（`dataclasses`）或 `person.__dict__`；反回来是 `Person(**data)`。

### CSV：`csv` 模块的正确用法

```python
import csv

# 读：DictReader 给你"列名 → 值"的映射，值全是 str，数字要自己转
with open("scores.csv", encoding="utf-8", newline="") as file:
    for row in csv.DictReader(file):
        print(row["姓名"], int(row["数学"]))

# 写：writerow 吃列表，DictWriter 吃字典
with open("out.csv", "w", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=["姓名", "数学"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
```

`newline=""` 不是可选的：CSV 的引号/换行规则由 `csv` 模块负责，让文本层再翻译一次换行，
Excel 打开就会看到空行。分隔符用 `delimiter="|"`，全加引号用 `quoting=csv.QUOTE_ALL`。

### 其他格式：知道用哪个库就行（本课练习一律不依赖）

| 场景 | 库 | 入口 | 一句话 |
|---|---|---|---|
| `.xlsx` 读写 | `openpyxl` | `load_workbook()` / `wb.save()` | 单元格级操作；原文 [24](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/24.Python%E8%AF%BB%E5%86%99Excel%E6%96%87%E4%BB%B6-1.md)、[25](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/25.Python%E8%AF%BB%E5%86%99Excel%E6%96%87%E4%BB%B6-2.md) |
| 大数据量 Excel | `pandas` | `df.to_excel()` | 见 L15，别用 openpyxl 循环写十万行 |
| `.xls` 老格式 | `xlwt` / `xlrd` | — | 新开源项目已放弃，能转 xlsx 就转 |
| Word | `python-docx` | `Document(path)` | 原文 [26](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/26.Python%E6%93%8D%E4%BD%9CWord%E5%92%8CPowerPoint%E6%96%87%E4%BB%B6.md) |
| PPT | `python-pptx` | `Presentation(path)` | 同上 |
| PDF 读取 | `pdfminer.six` / `pypdf` | `extract_text` | 原文 [27](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/27.Python%E6%93%8D%E4%BD%9CPDF%E6%96%87%E4%BB%B6.md) |
| PDF 生成 | `reportlab` | `canvas` / `platypus` | 中文要额外注册字体 |
| 图片 | `Pillow` | `Image.open()` | 原文 28 |

---

## ③ 完整样例：读 → 跑 → 改

[drills/L10/worked_example.py](../drills/L10/worked_example.py) 直接跑：
`py drills/L10/worked_example.py`。它把 CSV 读成字典、算平均、写成 UTF-8 JSON 报表，
再用二进制模式统计文件字节数，全程落在临时目录并自动清理。

跑完回答：把 `write_report` 里的 `ensure_ascii=False` 删掉，报表字节数会变大还是变小？为什么？

---

## ④ 补全题

打开 [drills/L10/exercises.py](../drills/L10/exercises.py)，10 个函数：前 6 挖空、后 4 只给需求。
所有落盘操作都在测试给的临时目录里，别往仓库写文件。

```powershell
py check.py L10 -v
```

---

## ⑤ 三个 Java 老手必踩的坑

1. **`open()` 不写 `encoding`，Windows 上默认 GBK**。你写的时候没事（同一台机、同一 locale），
   换到 Linux 容器或让别人的 Excel 读就乱码。规则只有一条：**文本模式永远显式 `encoding="utf-8"`**。
   反过来，`b.decode("utf-8")` 遇到 GBK 字节抛的是 `UnicodeDecodeError`（它是 `ValueError` 的子类）。
2. **`str` 和 `bytes` 不能混**。`'a' + b'a'` 两边都报错，但 Python 报的是 `TypeError`。
   `'rb'` 读出来的是 `bytes`，`json.loads` 从 3.6 起能同时吃 `str/bytes`，`csv` 只吃文本行 —— 所以
   CSV 永远用文本模式，二进制模式只用于复制/图片/未知内容。
3. **`json.dumps` 默认把中文转义，且 `set` / `datetime` 会直接抛 `TypeError`**。
   Java 的 Jackson 靠注解解决；Python 靠 `default=` 钩子或先手动 `asdict(obj)`。
   另外别忘：`json.dump`（写文件）和 `json.dumps`（出字符串）只差一个字母，报错信息还都挺含糊。

---

## ⑥ 现在回看开头 3 题

1. **`UnicodeDecodeError`**（默认按 GBK 解 UTF-8 字节）。修复：`open("a.txt", encoding="utf-8")`。
2. **`{"\u540d\u5b57": "\u9a86\u660a"}`**。加 `ensure_ascii=False` 才输出中文原样。
3. **`bytes`**。不能和 `str` 相加，要先 `.decode(encoding)`。

答错的那题，去 [cards/l10.md](../cards/l10.md) 找对应卡片，今天过一遍。

---

## ⑦ 通关标准

- `py check.py L10` 输出 `10/10 通过`（练习 10 题全对，判分器显示 `18/18`）。
- 白板写：把一个 CSV 转成按姓名排序、缩进 2 的 UTF-8 JSON 文件，全程不用 `pandas`。
- 达成后：`py progress.py done L10`。

## ⑧ 还要细节？回原文

| 想要 | 原文 |
|---|---|
| `open` 模式表 / 异常继承树 / 二进制复制 | [Day21-30/21.文件读写和异常处理.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/21.%E6%96%87%E4%BB%B6%E8%AF%BB%E5%86%99%E5%92%8C%E5%BC%82%E5%B8%B8%E5%A4%84%E7%90%86.md)（244 行） |
| JSON 四函数、类型映射表、`pip` 与网络 API | [Day21-30/22.对象的序列化和反序列化.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/22.%E5%AF%B9%E8%B1%A1%E7%9A%84%E5%BA%8F%E5%88%97%E5%8C%96%E5%92%8C%E5%8F%8D%E5%BA%8F%E5%88%97%E5%8C%96.md)（239 行） |
| CSV 读写完整例子 | [Day21-30/23.Python读写CSV文件.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/23.Python%E8%AF%BB%E5%86%99CSV%E6%96%87%E4%BB%B6.md)（82 行） |
| Excel（openpyxl 单元格 / 样式 / 合并） | [24.Python读写Excel文件-1.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/24.Python%E8%AF%BB%E5%86%99Excel%E6%96%87%E4%BB%B6-1.md)、[25](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/25.Python%E8%AF%BB%E5%86%99Excel%E6%96%87%E4%BB%B6-2.md) |
| Word / PPT | [26.Python操作Word和PowerPoint文件.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/26.Python%E6%93%8D%E4%BD%9CWord%E5%92%8CPowerPoint%E6%96%87%E4%BB%B6.md) |
| PDF | [27.Python操作PDF文件.md](https://github.com/jackfrued/Python-100-Days/blob/master/Day21-30/27.Python%E6%93%8D%E4%BD%9CPDF%E6%96%87%E4%BB%B6.md) |
