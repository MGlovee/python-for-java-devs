# 出处与使用说明

## 内容来源

本仓库的**知识脉络与章节划分**来自开源教程
[jackfrued/Python-100-Days](https://github.com/jackfrued/Python-100-Days)（作者：骆昊 / jackfrued）。

在此基础上，本仓库做了四类加工：

1. **重写**：`lessons/` 下的讲义是对上游内容的重写笔记 —— 面向"已掌握 Java"的读者，
   砍掉语言入门部分，重新组织为 15 课，并补充 Java↔Python 的对照说明；
2. **新增**：`drills/`（265 道可自动判分的练习）、`cards/`（间隔重复闪卡）、
   `projects/`（4 个带验收脚本的实战项目）、`check.py`、`progress.py` 均为原创；
3. **链接**：讲义与项目文档末尾的"回原文"链接指向 GitHub 上的上游文件，
   **本仓库不镜像、不复制上游正文**；
4. **取舍**：删除了上游中与"爬虫 / 自动化 / 数据处理"目标无关或对 Java 工程师属于重复的章节，
   详见 README 第一节。

## 版权

- **代码部分**（`check.py`、`progress.py`、`_pytest_shim.py`、`drills/`、`projects/`）：
  以 MIT 许可发布，见 [LICENSE](LICENSE)。
- **讲义与闪卡**（`lessons/`、`cards/`、`docs/`）：为个人学习笔记，仅供学习交流；
  其中转述、概括自上游教程的部分，其版权归原作者 jackfrued 所有。
- 上游仓库当前未声明开源许可。若原作者认为本仓库的任何内容不妥，
  请在 issue 中指出，我会在收到通知后立即删除相关内容或调整引用方式。

## 引用建议

如果你要引用本项目的内容，建议同时引用上游原始教程，并注明：

> 参考：MGlovee/python-for-java-devs（基于 jackfrued/Python-100-Days 的重写学习笔记）
