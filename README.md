# 给 Java 后端工程师的 Python 速成

> **15 课讲义 + 265 道自动判分练习 + 4 个可验收项目**，
> 为"已经会写 Java、想在两周内用 Python 干活"的人重排的一条最短路径。
> 判分器只用标准库，克隆下来零依赖就能跑。

会写 Java 的人学 Python，六到七成教材内容在讲他已经会的东西：什么是变量、什么是 `for`、
什么是接口。这套材料把它们全部砍掉，只保留 **Python 相对 Java 的真正增量** ——
推导式、生成器、装饰器、上下文管理器、鸭子类型、GIL 与并发模型、pandas 的数据心智，
并且每一课都配**能立刻判分的练习**，而不是"读完感觉自己会了"。

- 目标场景：**爬虫 / 自动化脚本 / 数据处理**
- 节奏：**14 天 × 每天 3 小时 45 分**（约 52.5 小时），见 [14 天冲刺方案](docs/PLAN-14-DAYS.md)
- 也可按 4 周 × 每天 2 小时的宽松版走，两套排期共用同一批材料

---

## 一、先说砍掉了什么（以及为什么）

| 原教程内容 | 处理 | 理由 |
|---|---|---|
| 环境安装 / 变量 / 分支 / 循环 | **压成 L01 一课** | 你不需要有人教你什么是循环，只需要知道 Python 的写法差异 |
| Web 前端（HTML/CSS/JS/Vue） | **砍** | 后端工程师的短板不在这里，投入产出比最低 |
| Linux 命令行 | **砍**（留一页备忘） | 本机练习用不上 |
| SQL 语法教学（DDL/DML/DQL/DCL） | **砍语法，只留 L13 的 Python 接库** | 后端天天写 SQL，这是存量优势不是增量 |
| Django 逐步教程 | **砍成 P4 项目的选做参考** | 框架心智与 Spring 同构，读官方文档比读二手教程快 |
| 机器学习 10 篇 | **砍** | 需要的是数学和 numpy，属于第二阶段 |
| 数据分析 15 篇 | **压成 L15 一课** | 后端日常够用即可 |
| 各类随笔、公开课、几百张配图 | **砍** | 认知负荷高、信息量低 |

砍掉的部分大约省下 30 小时，全部换成了练习和项目的时间。

---

## 二、15 课地图

每课 90 分钟：**读 40 分钟 → 练 50 分钟**。练习必须跑到全绿才算过。

### 第一阶段 · 语法迁移（L01–L04）

| 课 | 主题 | 对应原文 |
|---|---|---|
| [L01](lessons/L01-语法差异地图.md) | 缩进 / 动态类型 / 数值与取模 / 真值 / 分支循环 / `for-else` | Day01–07 |
| [L02](lessons/L02-数据结构四件套.md) | list / tuple / dict / set、切片、**推导式** | Day08–13 |
| [L03](lessons/L03-字符串正则与日期.md) | 字符串方法、f-string、正则、`datetime` | Day11、30 |
| [L04](lessons/L04-函数与一等对象.md) | 参数家族、`*args/**kwargs`、LEGB、lambda、高阶函数 | Day14、16 |

### 第二阶段 · Python 的方式（L05–L09）—— 真正的增量都在这

| 课 | 主题 | 对应原文 |
|---|---|---|
| [L05](lessons/L05-面向对象Python风格.md) | `self`、魔术方法、`@property`、ABC、`dataclass`、MRO | Day18–20 |
| [L06](lessons/L06-异常与上下文管理器.md) | `try/except/else/finally`、`with`、自定义上下文 | Day21 |
| [L07](lessons/L07-迭代器与生成器.md) | 迭代协议、生成器、`yield`、`itertools` / `functools` | Day17、31 |
| [L08](lessons/L08-装饰器与Pythonic.md) | 装饰器、类型注解、PEP 8、常见坑 | Day17、31、番外篇 |
| [L09](lessons/L09-模块虚拟环境与依赖.md) | 模块与包、`pip`、`venv`、`pyproject`、项目结构 | Day14、22、91 |

### 第三阶段 · 后端实战（L10–L14）

| 课 | 主题 | 对应原文 |
|---|---|---|
| [L10](lessons/L10-文件JSON与CSV.md) | 读写文本 / JSON / CSV / Excel、编码坑 | Day22–25 |
| [L11](lessons/L11-HTTP与爬虫最小集.md) | `requests`、HTML 解析、robots 与反爬常识 | Day61–62、64 |
| [L12](lessons/L12-并发GIL线程进程协程.md) | GIL、`threading`、`multiprocessing`、`asyncio` | Day63、番外篇协程 |
| [L13](lessons/L13-数据库访问.md) | `pymysql` / SQLAlchemy、连接池、防注入、ETL | Day44 |
| [L14](lessons/L14-测试与工程化.md) | `pytest`、`logging`、profile、代码检查 | Day96、番外 PEP8 |

### 选做

| 课 | 主题 | 什么时候学 |
|---|---|---|
| [L15](lessons/L15-numpy与pandas速览.md) | ndarray / DataFrame 最小可用集 | 要做数据处理时，或在 P3 项目里现学现用 |

---

## 三、四个项目（边做边学，这才是"会了"的证明）

学完对应阶段就开工，不要等 15 课全看完。

| 项目 | 用到的课 | 产出 |
|---|---|---|
| [P1 日志分析 CLI](projects/P1-日志分析命令行/README.md) | L01–L09 | 统计 Nginx `access.log` 的命令行工具：PV/UV、状态码分布、Top-N URL、慢请求，带 argparse 和自写测试 |
| [P2 数据采集入库](projects/P2-数据采集与入库/README.md) | L10、L11、L13 | 抓公开接口 → 清洗去重 → 写 SQLite/MySQL，断点续传 |
| [P3 报表与数据体检](projects/P3-数据报表/README.md) | L10、L15 | 把 P2 的数据汇成 Excel/CSV 报表，含缺失值、异常值告警 |
| [P4 接口服务](projects/P4-一个HTTP服务/README.md)（选做） | 全部 | FastAPI 起一个 CRUD 接口，带 pytest 与类型注解 |

每个项目给的是**需求 + 验收测试**，不是步骤教程。验收这样跑（`check.py` 只管课程练习，不含项目）：

```bash
python projects/P1-日志分析命令行/verify.py app.py   # 做完后判分
python check.py --solution                          # 先确认题库完好：265/265
```

---

## 四、快速开始

```bash
git clone https://github.com/MGlovee/python-for-java-devs.git
cd python-for-java-devs

python check.py --solution     # 1. 自检：参考答案应当 265/265 全绿
python progress.py             # 2. 看进度、今天该复习哪几张卡
python check.py L01            # 3. 做 drills/L01/exercises.py，反复判分直到 16/16
python progress.py read L01    # 4. 闪卡过完打卡
```

固定的每日节奏：**回忆 → 读 → 练 → 打卡**，别自己发明顺序。

```bash
python progress.py start L03   # 标记开始某课
python check.py L03 -v         # 逐条看每个测试
python check.py L03 --solution # 怀疑题目有问题时，验参考答案
python progress.py reset L03   # 重来某课
```

> 命令里的 `python` 在 Windows 上通常也可以写成 `py`。

---

## 五、这套东西为什么这样设计

依据都写在 [how-to-learn.md](docs/how-to-learn.md) 里，一句话版：

- **重读和划重点是低效用学习**（Dunlosky 2013 综述），只有**提取练习**和**间隔分布**是高效用。
  所以每课开头有"先答 3 题"、每课配闪卡，而不是给你漂亮的排版。
- **样例渐隐**（worked-example fading）：每课练习分三段 —— 挖空 → 半开放 → 只给需求。
  比一上来就独立写题省一半认知负荷。
- **即时反馈**：判分器零依赖（没装 pytest 也能跑），红绿立刻告诉你差在哪。
- **交错练习**：L02/L03 的题故意混排 list/dict/str，相似内容混着练记得更牢。
- **间隔重复**：`progress.py` 按 D+1 / D+2 / D+4 / D+7 点名该复习的闪卡。

---

## 六、环境要求

| 项 | 要求 |
|---|---|
| Python | **3.10+**（在 3.12 / 3.14 上实测通过） |
| 第三方库（可选） | L15 需要 `numpy`、`pandas`；P3 需要 `pandas`（可选 `openpyxl` 导 Excel） |
| `pytest`（可选） | 装了就用真 pytest 跑；没装时判分器自动挂载 `_pytest_shim.py` |

L01–L14 的练习**只用标准库**，不装任何东西也能全绿。

---

## 七、目录结构

```
.
├── lessons/     L01…L15        讲义，每课一页
├── drills/      L01…L15        exercises.py 工作表 / test_*.py 考官 / solution.py 参考 / worked_example.py 样例
├── cards/       l01…l15.md     间隔重复闪卡
├── projects/    P1…P4          项目需求与验收，各自带 verify.py 与 example/ 参考实现
├── docs/
│   ├── PLAN-14-DAYS.md         14 天冲刺排期与取舍
│   ├── how-to-learn.md         学习机制说明与证据
│   └── java-to-python.md       Java → Python 对照速查表
├── check.py                    判分器（标准库实现，兼容 pytest 语法）
├── progress.py                 进度与间隔重复排期
├── tools/linkcheck.py          文档本地链接自检
├── _pytest_shim.py             没装 pytest 时的替身
└── progress.json               个人进度（自动生成，已加入 .gitignore）
```

---

## 八、常见问题

**中文乱码？** 讲义里的示例会打印中文。Git Bash 先 `export PYTHONUTF8=1`，
PowerShell 先 `chcp 65001`。Python 本身没问题，是终端代码页的事。

**`check.py` 能一次跑多课吗？** 不能，`check.py L01 L02` 会被判定为非法参数；
不带参数则跑全套 265 题。

**想看某题为什么红？** 加 `-v` 逐条列出；只盯第一条，后面的多半是连锁失败。

**卡住了怎么办？** 卡 15 分钟以上才看 `solution.py`；看完必须**合上文件凭记忆重写** ——
照抄一遍通过率 100%、记住 0。

---

## 九、出处与致谢

讲义是对 **[jackfrued/Python-100-Days](https://github.com/jackfrued/Python-100-Days)**
的系统性重写与压缩：保留其知识脉络，重排顺序、砍掉冗余、补上练习与判分。
每课末尾的"回原文"链接都指向上游对应文件。

上游仓库未声明开源许可，本项目**不复制其正文**，只做摘要式笔记并链接回原文；
如原作者对任何内容有异议，请提 issue，会立即处理。详见 [NOTICE.md](NOTICE.md)。

## 十、License

本仓库的代码（判分器、练习、项目、脚本）以 **MIT** 发布，见 [LICENSE](LICENSE)。
讲义与闪卡为学习笔记，版权归原作者与笔记作者共同所有，仅限个人学习使用。
