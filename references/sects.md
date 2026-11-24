# 功法门派与武功秘籍

门派 key 用于 `cultivate.py init --sects`。秘境素材清单以 `config.default.yaml` 为准，宿主可以在修行档案的 `config.yaml` 中用 `extra_repos` 补充。

## 门派

| key | 门派 | 功法 | 门派简介（名字来自社区梗） |
|---|---|---|---|
| cpp | 段错宗 | C++ | 威力极大，稍有不慎便 Segmentation fault，原地走火入魔 |
| c | 野指针门 | C | 万法之源，指针一乱，灵力乱窜 |
| python | 调包宗 | Python | 江湖人称调包侠，一句 import 能借来万千法宝 |
| go | 判错宗 | Go | 门规：凡事先判错，三行一个 `if err != nil` |
| rust | 重写宗 | Rust | 立派宏愿是"用 Rust 重写一切"，编译器即戒律堂 |
| java | 八股宗 | Java | 面试八股天下闻名，门下弟子人人能背 JVM |
| js | 学不动宗 | JavaScript/TypeScript | 功法每月一变，弟子常哀叹"学不动了" |
| php | 最好宗 | PHP | 自称世界上最好的门派 |

门派诨号只是玩笑。系统可以拿诨号调侃宿主，但出题、评分、推荐秘籍都按该语言的真实特点来。

兼修多门时，每周的三处秘境在所修门派之间轮换素材。修为不分门派计算，测的是可迁移的通用能力。

## 镇派秘籍

评分后，系统按宿主暴露的薄弱点，从下面挑 1~2 本推荐。只推荐，不记录阅读进度。

### 段错宗（C++）

- Scott Meyers，《Effective Modern C++》
- Anthony Williams，《C++ Concurrency in Action》
- C++ Core Guidelines（isocpp.github.io/CppCoreGuidelines）
- cppreference.com

### 野指针门（C）

- Kernighan & Ritchie，《The C Programming Language》
- Peter van der Linden，《Expert C Programming: Deep C Secrets》
- Bryant & O'Hallaron，《Computer Systems: A Programmer's Perspective》

### 调包宗（Python）

- Luciano Ramalho，《Fluent Python》
- Brett Slatkin，《Effective Python》
- Python 官方教程（docs.python.org/3/tutorial）

### 判错宗（Go）

- Donovan & Kernighan，《The Go Programming Language》
- Effective Go（go.dev/doc/effective_go）
- The Go Memory Model（go.dev/ref/mem）

### 重写宗（Rust）

- 《The Rust Programming Language》（doc.rust-lang.org/book）
- Jon Gjengset，《Rust for Rustaceans》
- The Rustonomicon（doc.rust-lang.org/nomicon）

### 八股宗（Java）

- Joshua Bloch，《Effective Java》
- Brian Goetz 等，《Java Concurrency in Practice》

### 学不动宗（JavaScript/TypeScript）

- Kyle Simpson，《You Don't Know JS》
- MDN Web Docs（developer.mozilla.org）
- TypeScript Handbook（typescriptlang.org/docs/handbook）

### 最好宗（PHP）

- PHP 官方手册（php.net/manual）
- PHP: The Right Way（phptherightway.com）

### 码门通用秘籍（不分门派）

| 薄弱点 | 秘籍 |
|---|---|
| 设计与抽象 | John Ousterhout，《A Philosophy of Software Design》 |
| 分布式与存储 | Martin Kleppmann，《Designing Data-Intensive Applications》 |
| 调试方法 | David J. Agans，《Debugging: The 9 Indispensable Rules》 |
| 工程习惯 | Hunt & Thomas，《The Pragmatic Programmer》 |
| 一致性算法 | Ongaro & Ousterhout，"In Search of an Understandable Consensus Algorithm"（Raft 论文） |
| 存储引擎 | Chang 等，"Bigtable: A Distributed Storage System for Structured Data"；O'Neil 等，"The Log-Structured Merge-Tree" |
| AI 模型 | Vaswani 等，"Attention Is All You Need" |
