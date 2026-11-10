# 这套课程为什么长这样

> 你不是没有时间，你是在用低效用的方法读一份给零基础写的材料。
> 这一页讲清楚本项目里每个设计选择对应哪条研究结论，以及卡住时该怎么办。
> 14 天冲刺的排期和取舍见 [PLAN-14-DAYS.md](PLAN-14-DAYS.md)；本页讲的是"为什么这样设计"，与走哪张日程表无关。

---

## 一、"100 天"是个营销单位，不是学习单位

同类课程横向对比一下就明白：

| 课程 | 官方标称投入 |
|---|---|
| Boot.dev Python | **30 小时** / 168 课 |
| Codecademy Python 2 | **24 小时** |
| Udemy《100 Days of Code》 | 57 小时视频 + 100 个项目（也叫 100 天） |
| Harvard CS50P | 3–9 小时/周 × 10 周 |
| 赫尔辛基大学 Python MOOC | 约 135 小时（250+ 练习，零基础） |

**行业里"100 天"约等于 50–135 小时**，跟天数无关。原仓库这 118 篇讲义，
按每篇精读 15–25 分钟算，光是读完就要 31–52 小时——而且其中大量内容对一个会写 Java 的人是重复表述。

所以这套讲义的账是这么算的：

| 阶段 | 课时 | 预计 |
|---|---|---|
| 语法迁移 L01–L04 | 4 课 | 6 小时 |
| Python 的方式 L05–L09 | 5 课 | 8 小时 |
| 后端实战 L10–L14 | 5 课 | 8 小时 |
| 项目 P1–P2 | 2 个 | 10 小时 |
| 复习（间隔重复） | — | 4 小时 |
| **合计** | | **约 36–50 小时** |

对照经验值：**有编程基础的人，语法可用 20–30 小时，能写生产级 60–80 小时**。
四周排期落在 50 小时附近，是"紧但不作弊"的量。

---

## 二、四条机制，每条都有出处

### 1. 提取练习优先于重读

Dunlosky 等人 2013 年那篇被引 6000+ 的方法综述里评估了 10 种学习技术：
**只有 practice testing（提取练习）和 distributed practice（间隔分布）评为高效用**；
而重读、划重点、摘要这三样——也就是绝大多数人"看书学习"的动作——评为**低效用**。

这就是每课开头都有「① 开课先答 3 题」的原因。先答错，比后看懂记得牢。
读的时候不让你划线，也是这个原因：划线给人的"我会了"的感觉是假的。

> 出处：Dunlosky et al. 2013, *Improving Students' Learning With Effective Learning Techniques*
> [全文 PDF](https://www.whz.de/fileadmin/lehre/hochschuldidaktik/docs/dunloskiimprovingstudentlearning.pdf)

### 2. 样例渐隐（worked-example fading）

练习一律三段：**挖空 → 半开放 → 只给需求**。
2023 年的元分析显示，带样例的练习在保持和迁移测试上都优于纯独立解题，同时认知负荷更低；
而"渐隐"（样例逐步撤走）比一直给样例或一直不给都好。

所以 L01 的 10 道题里，前 6 题 docstring 给你提示和一个 `>>>` 示例，后 4 题只说要求。

> 出处：[Worked example effect](https://en.wikipedia.org/wiki/Worked-example_effect)、
> [Chen et al. 2023 元分析](https://www.tandfonline.com/doi/full/10.1080/01443410.2023.2273762)

### 3. 先读代码再写代码（PRIMM）

每课的 `worked_example.py` 不是装饰。用法固定四步：**预测输出 → 跑 → 改一个地方再看 → 合上屏幕默写**。
PRIMM（Predict-Run-Investigate-Modify-Make）是把文本密集型编程教材转成练习型教材的成熟模板。

默写不出来就跑第二遍，别往下翻。这一步省掉的时间最少，价值最大。

> 出处：[PRIMM 项目页](https://computingeducationresearch.org/projects/primm/)、[Sentance et al. 论文](https://www.researchgate.net/publication/320885814_PRIMM_Exploring_pedagogical_approaches_for_teaching_text-based_programming_in_school)

### 4. 间隔重复 + 交错

闪卡按 `progress.py` 里的 `INTERVALS` 排期（当前值 `[1, 2, 4, 7]`，配合 14 天冲刺；
回到 4 周方案时改 `[1, 3, 7, 21]`），`py progress.py` 会自动点名今天该翻哪几张。
**间隔要跟"需要保持多久"配套**——Cepeda 等 2006 的元分析给出的正是这条：最优间隔随保持期增长而增长，
保持期只有几周时短间隔就够，硬套 D+21 只会让复习槽在截止日前一次都不触发。
另外 L02/L03 的题目是**混排**的（list/dict/str 交替出现）——研究显示相似类别交错练习比按块练习收益大，
差异很大的新材料才适合分块首学（所以装饰器、GIL 这类是单独一课）。

> 出处：[Cepeda et al. 2006, Distributed Practice in Verbal Recall Tasks（317 个实验的元分析，间隔×保持期结论）](https://www.yorku.ca/ncepeda/publications/CPVWR2006.html)、
> [Rohrer, Interleaved practice](https://www.researchgate.net/publication/227530785_The_Effects_of_Interleaved_Practice)、
> [Carvalho & Goldstone 2015](https://www.academia.edu/15575016/The_benefits_of_interleaved_and_blocked_study_Different_tasks_benefit_from_different_schedules_of_study)、
> [Thompson et al. 2023 综述](https://www.sciencedirect.com/science/article/pii/S1546144023006464)

### 附带一条：砍图也是按证据来的

认知负荷理论里的**冗余原则**说：与目标无关的装饰性信息会挤占工作记忆。
原仓库 428 张配图里大部分是 IDE 截图和装饰图。本目录的讲义里一张图都没有——
代码块能表达的东西不该用图片表达，图片还不能搜索、不能复制、不能跑。

> 出处：[NSW CESE 2017 认知负荷教师简报](https://education.nsw.gov.au/content/dam/main-education/about-us/educational-data/cese/2017-cognitive-load-theory.pdf)

---

## 三、每天的固定动作（15 秒能记住）

```powershell
py progress.py           # 今天该做什么、该复习哪张卡
py check.py L03          # 做练习，反复跑到全绿
py progress.py read L01  # 翻完闪卡打个卡
```

一次学习时长的建议分配：**读 40 分钟 → 练 50 分钟**。
读超过 40 分钟还没开始动手，就是在做低效用的重读。

判分器红了不要立刻去看 `solution.py`。**卡住 15 分钟以上再看**，
并且看完要合上文件、凭记忆重写一遍——照着抄一遍的通过率是 100%，记住的东西是 0。

---

## 四、卡住了怎么办

| 症状 | 处理 |
|---|---|
| 判分红了一堆，看不出为什么 | 跑 `py check.py L03 -v`，逐条看中文失败消息，只盯**第一条**红 |
| 提示"未做"而不是"失败" | 函数体里还有 `raise NotImplementedError`，删掉它 |
| 题目本身看着有毛病 | 跑 `py check.py L03 --solution`，参考答案全绿说明题没错，是你的理解偏了 |
| 一直卡在同一个知识点 | 说明它需要的是前置课，不是更多练习。回上一课的闪卡测一遍 |
| 想深入某个话题 | 用每课底部「⑧ 回原文」的链接查原仓库；查不到再考虑外部文档 |
| 觉得整课都是已会的东西 | 直接 `--solution` 全绿就跳过它，进度自己记。别为完整性陪读 |

顺带说一句被研究反复证实、但大家都不爱听的话：**"我看得懂" 和 "我写得出来" 是两个不同的能力**。
这套课程里所有课的唯一通关标准都是"写得出来且跑绿"，不是"读完了"。

---

## 五、还要外部资源的话

按"最省时间"排序，别贪多：

1. [官方 Python 教程（中文）](https://docs.python.org/zh-cn/3/tutorial/index.html) —— 权威且短，跳过第 1–3 章即可。忘了语法先查它。
2. [A Byte of Python](https://python.swaroopch.com/) —— 110 页，体量约是原仓库的 1/5，适合当索引跳读。
3. [Exercism Python Track](https://exercism.org/tracks/python) —— 146 题、自动测试、有真人导师点评，**免费**。
   做完本课程的 L01–L09 后拿它当交错练习场，这是最划算的下一步。
4. [Effective Python](https://medium.com/javarevisited/i-tried-50-python-courses-here-are-my-top-5-recommendations-0c439c53691b)（Brett Slatkin）—— 90 条 items，第二阶段的读物，别当第一本书。
5. [廖雪峰 Python 教程](https://liaoxuefeng.com/books/python/index.html) —— 中文同类里最简明的，某处没看懂时换个人讲一遍。
6. [PyMOTW](https://pymotw.com/) —— 标准库按需查，不要通读。

如果你的目标其实是**通过 NCRE 二级 Python**，那么课程边界应该由考纲定，不是由我这 14 课定：
[2025 版考试大纲 PDF](https://ncre.neea.edu.cn/res/Home/2412/dcf184e2f5b6d8ccdb90b3f8eb417ab6.pdf)。
题型是单选 40 分（含公共基础 10 分）+ 操作题 60 分，60 分及格；
在现有基础上再加 15–25 小时刷真题与机考环境练习。
