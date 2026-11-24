# 程序员修仙系统（coder-cultivation-system）

> 【叮！程序员修仙系统已激活，正在与宿主绑定……】

一个给 AI 编程助手用的 skill。装上之后，agent 会扮演绑定在你身上的"修仙系统"，用"重生之程序员修仙"的设定，陪你持续评估自己的编程能力：你是不是还在进步，进步得有多快。

## 世界观

你重生在种花国。这里的修仙者靠写代码修行，最大的门派叫码门，用代码建设和改善世界。码门下按编程语言分为各个功法门派，论文和教程是武功秘籍，代码题和开源项目是秘境。

| 门派 | 功法 |
|---|---|
| 段错宗 | C++ |
| 野指针门 | C |
| 调包宗 | Python |
| 判错宗 | Go |
| 重写宗 | Rust |
| 八股宗 | Java |
| 学不动宗 | JavaScript/TypeScript |
| 最好宗 | PHP |

境界：练气 → 筑基 → 金丹 → 元婴 → 化神，每个大境界分初期、中期、后期、大圆满。

## 怎么衡量能力

| 修行 | 现实含义 | 频率 |
|---|---|---|
| 除魔秘境 | 调试题：从开源项目的真实 bug 或注入的 bug 中定位根因 | 每周 |
| 藏经秘境 | 阅读题：限时读懂开源项目的一个模块，写出调用链和数据流 | 每周 |
| 炼器秘境 | 设计题：不依赖业务背景的通用系统设计 | 每周 |
| 宗门任务日志 | 日常工作任务按客观特征定难度，记录预测与实际，衡量判断力 | 每天 |
| 照心镜 | 重读几个月前自己写的代码，看现在能发现多少问题 | 每月 |

几个关键设计：

- **修为用 Elo 计算**。每处秘境按客观特征定品阶，相当于一个有难度分的对手。难题做对加分多，简单题做错扣分多，所以难度不同的题也能放在一起比。
- **难度按客观特征打分，不按感觉**。人变强之后，原来难的事会感觉不难。如果按感觉打分，难度会跟着能力一起涨，进步就看不出来了。
- **秘境素材用开源项目**，尽量排除业务背景的影响，测的是可迁移的通用能力。
- **前 3 周是测灵根期**，用来校准初始修为，不计入趋势。
- **天机（参考答案）单独保存**，评分前系统不会透露。

修为面板是一个 HTML 页面，包含修为曲线、能力边界图、同难度耗时、判断准确度、心境和季度雷达图。

## 安装

依赖：Python 3.9+，以及 `pyyaml`、`matplotlib`、`numpy`。面板里的中文需要系统装有 CJK 字体（如 Noto Sans CJK），否则会显示为方块。

```bash
pip install pyyaml matplotlib numpy
git clone https://github.com/Yanna-lee/coder-cultivation-system.git
```

把仓库放到（或软链到）你的 agent 的 skills 目录，例如：

```bash
ln -s "$PWD/coder-cultivation-system" ~/.claude/skills/coder-cultivation-system
```

修行档案默认存放在 `~/.coder-cultivation/`。要换位置，设置环境变量 `CULTIVATION_HOME`。

## 使用

在对话里说"启动程序员修仙系统"或"绑定系统"。第一次使用时，系统会讲述世界背景，请你选择门派，然后开启第一周的秘境。

之后常用的说法：

- "开启本周秘境"
- "我做完了，评分"
- "生成今天的宗门任务日志"
- "我现在什么境界"

也可以直接用命令行：

```bash
cd coder-cultivation-system/scripts
python3 cultivate.py sects                 # 全部门派
python3 cultivate.py init --sects cpp,python
python3 cultivate.py status                # 宿主档案、修为、未评定秘境
python3 cultivate.py week                  # 本周秘境目录与建议品阶
python3 cultivate.py day                   # 生成今天的宗门任务日志
python3 cultivate.py report                # 生成修为面板
python3 cultivate.py -h
```

## 自定义

在修行档案目录下创建 `config.yaml`，可以覆盖 `config.default.yaml` 中的任意项，例如调整 Elo 参数，或者用 `extra_repos` 添加自己的秘境素材：

```yaml
elo:
  k: 24
extra_repos:
  my-lib: {url: https://github.com/someone/my-lib, sect: 段错宗, lang: C++}
```

## 目录

```
SKILL.md               # skill 入口
references/            # 世界观、门派与秘籍、流程、评分规则
scripts/cultivate.py   # 命令行工具
templates/             # 任务日志、照心镜、题面模板
config.default.yaml    # 默认配置
```

## License

MIT
