# 系统运转流程

下文 `SKILL_DIR` 指本 skill 所在目录，`HOME` 指修行档案目录（默认 `~/.coder-cultivation`，可用环境变量 `CULTIVATION_HOME` 覆盖）。所有命令在 `SKILL_DIR/scripts/` 下以 `python3 cultivate.py <子命令>` 执行。

## 强制规则

1. **`HOME/bench/scores.yaml` 只能通过 `cultivate.py add` / `cultivate.py score` 修改**，禁止手工编辑。
2. **评分前不得泄露天机**：`HOME/bench/sealed/` 的任何内容都不能在回复里引用、总结或暗示。开启秘境时只告诉宿主题面路径。
3. **宗门任务日志和照心镜由宿主填写**。系统只在宿主要求时修正格式，不改数值。
4. **品阶按 `scoring.md` 的客观特征打分**。每项特征的打分理由写进天机。
5. **除魔秘境必须先在本机验证**：能编译或能运行，现象能复现。验证不了的不发。
6. **评分时 `--grader` 填当前模型名**。评分尺度要稳定：换模型后的第一次评分，先抽一处已评过的旧秘境重评，偏差超过 0.1 时告诉宿主。
7. 不删除 `HOME/bench/repos/` 之外的任何修行记录。

## 流程零：首次绑定

1. `cultivate.py status`。输出"未检测到宿主绑定记录"（退出码 2）即为首次使用。
2. 按 `world.md` 第 2 节讲述世界背景。
3. `cultivate.py sects` 列出门派，结合 `sects.md` 的门派简介展示给宿主。请宿主选一个主修门派，可以再选若干兼修门派。宿主没选之前不往下走。
4. `cultivate.py init --sects <主修>,<兼修>...`。
5. 讲解修行功课（SKILL.md 中的表格）和测灵根规则：前 3 周是测灵根期，只出暂估修为。
6. 询问宿主是否现在开启第一周秘境。同意则进入流程一。

宿主以后想改门派，再运行一次 `init --sects ...`，只更新门派，不动修行记录。

## 流程一：开启本周秘境

1. `cultivate.py status`，`cultivate.py week`。记下三类秘境的建议品阶、本周已开启的秘境、近期用过的素材。本周已有的类型不再重复开。
2. 选素材：从所修门派的素材中挑，尽量和近期不重复。兼修时三处秘境在门派之间轮换。`cultivate.py repo list` 看清单，`cultivate.py repo clone <name>` 克隆或更新。
3. 按类型准备秘境（见下文），四项品阶特征之和应接近建议品阶。
4. 登记：`cultivate.py add --type <debug|read|design> --project <素材|none> --source <real|injected|na> --title "<标题>" --difficulty k=v,...`。命令会生成 `HOME/bench/weekly/<week>/<qid>/README.md` 题面模板，并打印天机路径。
5. 填写题面 README.md 的"题面"一节，把参考答案写进天机 `HOME/bench/sealed/<week>/<qid>.md`。
6. 用系统口吻宣布秘境开启：三处秘境的题面路径、品阶、时限、作答路径。不附任何答案线索。

### 除魔秘境（debug）

- **真实心魔**：在素材仓库中找修复 commit。优先选带测试改动的修复（例如 `git log -i --grep fix -- '*test*'`），要能用一个测试或一段命令复现。快照取修复前的版本：`cultivate.py snapshot --repo <p> --commit <fix>^ --dest bench/weekly/<week>/<qid>/src`。把修复 commit 里新增的测试单独放进题面作为"失败测试"，只给测试，不给修复。
- **注入心魔**：在 `HOME/bench/repos/<p>` 工作区修改代码，`git -C HOME/bench/repos/<p> diff > HOME/bench/sealed/<week>/<qid>.patch`，再 `git -C HOME/bench/repos/<p> checkout .` 还原，然后 `cultivate.py snapshot ... --patch HOME/bench/sealed/<week>/<qid>.patch`。注入的 bug 要像真实代码会犯的错（边界、生命周期、并发、单位、状态机），不要出语法错误或一眼可见的低级错误。
- `git archive` 不包含子模块。素材依赖子模块时，在题面写清楚构建方式，或把所需依赖一并放进 `src/`。
- 题面写：构建与运行命令、现象或失败测试、作答要求（根因位置与原因，可附修复）。
- 天机写：根因、修复方式或修复 commit、品阶打分理由、"定位到正确函数"的判定标准。

### 藏经秘境（read）

- 选规模适中的模块，题面给出入口（函数或类）和要回答的问题，例如"一次写入从入口函数到数据落盘的完整调用链和数据流"。
- 同样用 `snapshot` 导出到 `src/`，宿主在快照中阅读，不要让宿主在 `bench/repos/` 里切换 commit。
- 天机写：要点清单，每条可独立判定对错，一般 8~15 条。

### 炼器秘境（design）

- 题目不依赖业务背景，写清需求和约束，例如线程安全、过期淘汰、内存上限、读多写少。
- 最好对应素材里的某个真实实现，天机写参考设计和实现位置，评分时对照。
- `--source na`。与素材无关时 `--project none`。

## 流程二：评定战绩

1. `cultivate.py status` 看未评定的秘境。读 `HOME/bench/answers/<week>/<qid>.md`，第一行是用时。
2. 对照天机，按 `scoring.md` 第 3 节评分。超时完成的除魔秘境按 0 分计。
3. `cultivate.py score <qid> --s <s> --minutes <用时> --grader <模型名> --note "<一句话评语>"`。
4. 输出里有"突破""跌境""灵根测定完成"时，用系统口吻隆重播报。
5. 三处都评完后 `cultivate.py report`，告诉宿主修为面板路径。
6. 给宿主的战报：每处秘境的得分和扣分点，此时可以公开天机。总结本周修为变化，再按薄弱点从 `sects.md` 推荐 1~2 本秘籍。

## 流程三：日常功课

- 宗门任务日志：`cultivate.py day`，把生成的文件路径告诉宿主。
- 照心镜：`cultivate.py retro`。
- 宿主填完后可运行 `cultivate.py check` 检查格式。

## 流程四：查看修为

`cultivate.py report`。报错时先 `cultivate.py check` 列出错误，告诉宿主哪个文件哪一项灵力紊乱，由宿主修正。

解读时注意：

- 测灵根期没有修为曲线，只有暂估修为。
- 单周波动不代表修为变化，看 4 周滑动和季度对比。
- 心境长期偏低时，同期指标下滑可能来自状态，不一定是修为倒退。

## 维护

修改 `scripts/` 后，用临时目录测试：`CULTIVATION_HOME=<临时目录> python3 cultivate.py ...`，不会影响真实修行档案。
