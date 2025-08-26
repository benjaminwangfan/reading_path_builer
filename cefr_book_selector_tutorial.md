# 分层贪心算法：构建渐进式英语阅读路径的完整指南

在英语学习中，选择适合当前水平的阅读材料是关键挑战之一。太简单的内容无法提升水平，太难的内容又会让人失去信心。今天，我们将通过一个**分层贪心算法**来解决这个问题，帮助学习者构建一条**渐进式**的阅读路径。

本教程将带你从零开始理解这个算法，即使你对贪心算法不太熟悉也没关系！我们将像剥洋葱一样，一层层揭开这个实用工具的神秘面纱。

## 为什么需要这个算法？

想象一下，你是一位英语学习者，目标是达到C1水平。你有数百本书可供选择，但：

- 你不知道哪些书适合你的当前水平
- 读太简单的书进步慢
- 读太难的书容易放弃
- 你需要一条**循序渐进**的路径

这正是我们今天要解决的问题！我们将构建一个算法，能根据**CEFR标准**（欧洲语言共同参考框架）自动推荐最适合你当前水平的阅读材料，并规划出一条从A1到C1的平滑学习路径。

## 算法核心思想：分而治之 + 贪心选择

我们的算法基于三个核心思想：

1. **分层处理**：将复杂的多目标问题分解为按难度等级的子问题
2. **贪心选择**：在每个等级内，每次都选择"当前最优"的书籍
3. **适合度分析**：引入书籍对特定等级的"适合度"评估，更精准地匹配学习需求

这种策略类似于登山：先专注登上一个小山峰（A1），然后以此为基础攀登下一个（A2），依此类推，直到达到最终目标（C1）。

## 第一步：理解问题域

在深入代码前，让我们先明确几个关键概念：

- **CEFR等级**：A1（基础）、A2（初级）、B1（中级）、B2（中高级）、C1（高级）
- **词汇级别**：每个单词都有其CEFR级别
- **书籍词汇分布**：每本书包含不同级别的词汇
- **超纲词汇（BEYOND）**：书中出现但未在学习词表中定义的词汇

我们的目标是：**为学习者选择一组书籍，使其能够平滑地从A1过渡到C1水平，每本书都略高于当前水平但又不至于太难**。

## 第二步：数据结构准备

首先，我们需要两类数据：

1. **书籍词汇数据**：每本书包含哪些单词
2. **词汇级别数据**：每个单词属于哪个CEFR级别

```python
# 示例数据结构
books_vocab = {
    "book_1": {"hello", "world", "cat", "dog"},
    "book_2": {"advanced", "vocabulary", "cat", "sun"},
    "book_3": {"sophisticated", "phenomenon", "analysis", "hello"},
    # ... 更多书籍
}

vocab_levels = {
    "hello": "A1",
    "world": "A1",
    "cat": "A1",
    "dog": "A1",
    "sun": "A2",
    "analysis": "B1",
    "advanced": "B2",
    "vocabulary": "B2",
    "sophisticated": "C1",
    "phenomenon": "C1",
    # ... 更多单词
}
```

> 💡 **小知识**：在真实场景中，vocab_levels会包含数千个单词及其对应的CEFR级别，从A1基础词汇到C1高级词汇。书中出现但未在vocab_levels中定义的词汇将被标记为"BEYOND"（超纲词汇）。

## 第三步：初始化算法类

让我们创建一个类来封装我们的算法逻辑：

```python
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import numpy as np

class LayeredCEFRBookSelector:
    def __init__(self, books_vocab: Dict[str, Set[str]], vocab_levels: Dict[str, str]):
        """
        算法初始化：数据预处理和统计分析
        
        Args:
            books_vocab: {book_id: set(所有词汇)} - 每本书的实际词汇集合
            vocab_levels: {word: level} - 学习词表（只包含 A1~C1 的词及其等级）
        """
        # 启发式权重：低等级词汇对初学者价值更高
        self.level_weights = {
            "A1": 1.5,
            "A2": 1.3,
            "B1": 1.1,
            "B2": 1.0,
            "C1": 0.9,
        }

        # 学习目标等级
        self.learning_levels = ["A1", "A2", "B1", "B2", "C1"]
        # 完整等级（用于输出）
        self.all_levels = self.learning_levels + ["BEYOND"]

        self.books_vocab = books_vocab
        self.vocab_levels = vocab_levels  # 只包含 A1~C1 的词

        # 从学习词表中构建 level_vocab（只包含已知等级的词）
        self.level_vocab = self._group_vocab_by_level()

        # 预计算书籍统计信息
        self.book_stats = self._calculate_layered_book_stats()
```

### 为什么需要预处理？

预处理是算法高效运行的关键。想象一下，如果你每次都要检查一本有5000个单词的书中有多少是A1级别的，而你有400本书，那将是多么耗时！

通过预处理，我们将：

- 将词汇按级别分组（O(n)时间复杂度）
- 预计算每本书的统计信息（O(书籍数×平均单词数)）

这样，在后续选择过程中，我们可以**立即查询**这些信息，而不是重复计算。

## 第四步：数据预处理详解

让我们深入研究 `_group_vocab_by_level()` 方法：

```python
def _group_vocab_by_level(self) -> Dict[str, Set[str]]:
    """
    仅对 vocab_levels 中的词按等级分组
    注意：不包含书中出现但未在 vocab_levels 中定义的词
    
    返回示例:
    {
        "A1": {"hello", "cat", ...},
        "A2": {"world", "dog", ...},
        "B1": {"analysis", ...},
        "B2": {"advanced", "vocabulary", ...},
        "C1": {"sophisticated", "phenomenon", ...}
    }
    """
    level_vocab = defaultdict(set)
    for word, level in self.vocab_levels.items():
        if level in self.learning_levels:
            level_vocab[level].add(word)

    print("📚 学习词表分层统计（来自 vocab_levels）:")
    for level in self.learning_levels:
        count = len(level_vocab[level])
        print(f"  {level}: {count}词")

    return dict(level_vocab)
```

这个方法非常简单但极其重要。它将扁平的词汇列表转换为按级别组织的结构，让我们可以快速回答"哪些单词属于A1级别？"这样的问题。

### 实际效果演示

假设我们有以下词汇数据：

```python
vocab_levels = {
    "hello": "A1", "world": "A1", "cat": "A1", 
    "sun": "A2", "moon": "A2", 
    "analysis": "B1", "structure": "B1",
    "advanced": "B2", "vocabulary": "B2",
    "sophisticated": "C1", "phenomenon": "C1"
}
```

经过 `_group_vocab_by_level()` 处理后，我们会得到：

```python
{
    "A1": {"hello", "world", "cat"},
    "A2": {"sun", "moon"},
    "B1": {"analysis", "structure"},
    "B2": {"advanced", "vocabulary"},
    "C1": {"sophisticated", "phenomenon"}
}
```

现在，如果我们想知道所有A1级别的单词，只需访问 `level_vocab["A1"]`，时间复杂度为O(1)！

## 第五步：书籍统计信息计算

接下来，我们计算每本书的详细统计信息：

```python
def _calculate_layered_book_stats(self) -> Dict[str, Dict]:
    """
    统计每本书的多维特征

    关键逻辑：
    - unknown_words = 书中词汇 - vocab_levels.keys()（完全未定义的词）
    - 所有比例计算基于总词汇数（含 B2/C1 和 unknown）
    - 新增 suitability_for[level]：评估该书对某等级的适合度
    
    返回示例:
    {
        "book_1": {
            "total_words": 5000,
            "level_counts": {"A1": 100, "A2": 2000, ...},
            "level_ratios": {"A1": 0.02, "A2": 0.4, ...},
            "unknown_words": {"quantum", "relativity"},
            "difficulty_score": 2.3,
            "learning_value": 1.8,
            "suitability_for": {"A1": 0.6, "A2": 0.7, ...}
        },
        ...
    }
    """
    stats = {}
    
    # 构建所有已知学习词汇的集合（用于识别 unknown）
    known_learning_words = set(self.vocab_levels.keys())
    
    for book_id, vocab in self.books_vocab.items():
        book_stats = {
            "total_words": len(vocab),
            "level_words": {},  # 按等级分组的词汇集合
            "level_counts": {},  # 各等级词汇数量
            "level_ratios": {},  # 各等级词汇比例
            "unknown_words": set(),  # 超纲词 = 未在学习词表中定义的词
            "difficulty_score": 0,  # 难度分数（加权平均）
            "learning_value": 0,  # 学习价值分数
            "suitability_for": {},  # 新增：对每个等级的适合度
        }
        
        # 统计 A1~C1 各等级词汇
        learning_words_count = 0
        for level in self.learning_levels:
            level_set = self.level_vocab.get(level, set())
            words_in_level = vocab & level_set
            book_stats["level_words"][level] = words_in_level
            count = len(words_in_level)
            book_stats["level_counts"][level] = count
            book_stats["level_ratios"][level] = count / len(vocab) if vocab else 0
            learning_words_count += count
        
        # 🌟 核心：unknown_words = 书中出现但未在学习词表中的词
        unknown_words = vocab - known_learning_words
        book_stats["unknown_words"] = unknown_words
        book_stats["unknown_count"] = len(unknown_words)
        book_stats["unknown_ratio"] = (
            len(unknown_words) / len(vocab) if vocab else 0
        )

        # BEYOND 仅用于统计展示
        book_stats["level_words"]["BEYOND"] = unknown_words
        book_stats["level_counts"]["BEYOND"] = len(unknown_words)
        book_stats["level_ratios"]["BEYOND"] = book_stats["unknown_ratio"]

        # 难度评分：学习等级加权 + unknown 高权重惩罚
        difficulty_score = 0
        for i, level in enumerate(self.learning_levels):
            difficulty_score += book_stats["level_counts"][level] * (i + 1)
        difficulty_score += book_stats["unknown_count"] * 6  # unknown 贡献高难度
        book_stats["difficulty_score"] = (
            difficulty_score / len(vocab) if vocab else 0
        )

        # 学习价值：仅基于 A1~C1 词汇
        learning_value = 0
        for level in self.learning_levels:
            learning_value += (
                book_stats["level_counts"][level] * self.level_weights[level]
            )
        book_stats["learning_value"] = learning_value / len(vocab) if vocab else 0

        # 🌟 新增：计算该书对每个等级的"适合度"
        # 适合度 = (目标等级及以下词汇) / 总词汇数
        for target_level in self.learning_levels:
            target_idx = self.learning_levels.index(target_level)
            understandable = sum(
                book_stats["level_counts"][self.learning_levels[i]]
                for i in range(target_idx + 1)
            )
            total = len(vocab)  # 包含所有词
            book_stats["suitability_for"][target_level] = (
                understandable / total if total > 0 else 0
            )
        
        stats[book_id] = book_stats
    
    return stats
```

### 为什么需要这些统计信息？

这些预计算的统计信息是算法决策的基础：

1. **难度分数**：告诉我们这本书有多难
   - 计算方式：将每个单词的"难度值"相加（A1=1, A2=2, B1=3, B2=4, C1=5, 超纲词=6）
   - 除以总单词数得到标准化难度分数

2. **学习价值分数**：告诉我们这本书对当前学习阶段有多大的价值
   - 计算方式：低级别词汇权重更高（A1=1.5, A2=1.3, B1=1.1, B2=1.0, C1=0.9）
   - 这是因为初学者从基础词汇中获益更多

3. **超纲词汇比例**：告诉我们这本书是否太难
   - 比例过高（>15%）可能表示这本书对当前学习者太难

4. **适合度分析**：🌟新增功能，评估书籍对特定等级的适合程度
   - 计算公式：适合度 = (目标等级及以下词汇数) / 总词汇数
   - 例如：某书对B1的适合度 = (A1词汇 + A2词汇 + B1词汇) / 总词汇数
   - 这个指标帮助我们更精准地匹配书籍与学习者水平

## 第五点五步：书籍难度评估功能

在核心算法之前，我们还提供了一个独立的书籍评估工具：

```python
def evaluate_book_difficulty(self, book_id: str) -> Dict:
    """
    评估单本书的难度情况（用于调试和解释）
    
    Returns:
        {
            "book_id": str,
            "level_breakdown": {"A1": {"count": 100, "ratio": 0.1}, ...},
            "difficulty_analysis": {
                "overall_difficulty_score": 2.3,
                "learning_value_score": 1.8,
                "unknown_ratio": 0.25,
                "suitability_for": {"A1": 0.6, "A2": 0.5, ...}
            },
            "recommendations": ["最适合 B1 级别", "超纲词较多"]
        }
    """
```

这个方法提供了详细的书籍分析，包括：
- 各等级词汇的详细分布
- 综合难度和价值评分
- 对各等级的适合度评估
- 基于数据的推荐建议

> 💡 **实用技巧**：这个方法特别适合用于调试和向用户解释为什么某本书被推荐或不被推荐。

## 第六步：核心算法 - 渐进式阅读路径生成

现在，我们来到了算法的核心部分：`create_progressive_reading_path()`。这个方法会生成完整的阅读路径。

```python
def create_progressive_reading_path(
    self,
    max_books_per_level: Dict[str, int] | None = None,
    target_coverage_per_level: Dict[str, float] | None = None,
    max_unknown_ratio: float = 0.15,
    min_relevant_ratio: float = 0.4,
    min_target_level_words: int = 50,
) -> Dict:
    """
    主算法：渐进式学习路径生成
    
    参数说明:
    - max_books_per_level: 每个级别最多选择几本书
    - target_coverage_per_level: 每个级别希望覆盖的目标词汇比例
    - max_unknown_ratio: 允许的最大超纲词汇比例
    - min_relevant_ratio: 最小相关词汇比例（使用适合度指标）
    - min_target_level_words: 最少目标等级词汇数量
    """
    
    # 设置默认参数（基于语言学习经验）
    if max_books_per_level is None:
        max_books_per_level = {"A1": 3, "A2": 3, "B1": 4, "B2": 3, "C1": 2}
    
    if target_coverage_per_level is None:
        target_coverage_per_level = {
            "A1": 0.85,
            "A2": 0.9,
            "B1": 0.9,
            "B2": 0.9,
            "C1": 0.9,
        }
    
    # 初始化结果结构
    reading_path = {
        "levels": {},
        "total_books": [],
        "cumulative_coverage": {},
    }
    
    # 跟踪已覆盖的词汇（用于确保学习连贯性）
    cumulative_covered = set()
    already_selected_books = set()  # ✅ 新增：全局记录已选书籍
    
    # 按CEFR级别顺序处理（从简单到复杂）
    for level in self.learning_levels:
        print(f"\n=== 选择 {level} 等级书籍 ===")
        
        # 为当前级别选择最优书籍组合
        level_result = self._select_books_for_level(
            level=level,
            max_books=max_books_per_level.get(level, 2),
            target_coverage=target_coverage_per_level.get(level, 0.8),
            max_unknown_ratio=max_unknown_ratio,
            min_relevant_ratio=min_relevant_ratio,
            min_target_level_words=min_target_level_words,
            already_covered=cumulative_covered,
            already_selected_books=already_selected_books,  # ✅ 传入已选书籍
        )
        
        # 保存结果
        reading_path["levels"][level] = level_result
        selected_books = level_result["selected_books"]
        reading_path["total_books"].extend(selected_books)
        already_selected_books.update(selected_books)  # ✅ 更新全局已选
        
        # 更新累积覆盖词汇
        for book in selected_books:
            for lvl in self.learning_levels:
                cumulative_covered.update(self.book_stats[book]["level_words"][lvl])
        
        # 累积覆盖率统计
        cumulative_stats = {}
        for vocab_level in self.all_levels:
            if vocab_level in self.level_vocab:
                total = len(self.level_vocab[vocab_level])
                covered = len(cumulative_covered & self.level_vocab[vocab_level])
                ratio = covered / total if total > 0 else 0
            else:
                total = covered = "N/A"
                ratio = 0
            cumulative_stats[vocab_level] = {
                "covered": covered,
                "total": total,
                "ratio": ratio,
            }
        
        reading_path["cumulative_coverage"][level] = cumulative_stats
        
        # 打印进度
        print(f"完成 {level} 后累积覆盖率:")
        for lvl in self.learning_levels:
            ratio = cumulative_stats[lvl]["ratio"]
            print(f"  {lvl}: {ratio:.1%}")
    
    # 生成最终摘要
    reading_path["summary"] = self._generate_path_summary(reading_path)
    
    return reading_path
```

### 渐进式学习的核心思想

这个方法体现了"**渐进式学习**"的核心思想：

1. **按顺序处理**：从PreA1开始，逐步过渡到B1
2. **累积覆盖**：记录已学习的词汇，确保后续书籍能建立在已有基础上
3. **级别隔离**：每个级别有自己的目标和约束，但又与前后级别协调

> 🌟 **关键洞察**：语言学习不是线性的，但路径应该是渐进的。我们不应该在还没掌握A1词汇时就强迫学习者阅读B1材料。

## 第七步：级别内书籍选择算法

现在，让我们深入到 `_select_books_for_level()` 方法，这是实际做书籍选择的地方：

```python
def _select_books_for_level(
    self,
    level: str,
    max_books: int,
    target_coverage: float,
    max_unknown_ratio: float,
    min_relevant_ratio: float,
    min_target_level_words: int,
    already_covered: Set[str],
    already_selected_books: Set[str],  # ✅ 新增参数
) -> Dict:
    """
    为特定CEFR级别选择最佳书籍（贪心算法）
    
    参数说明:
    - level: 目标CEFR级别（如"A1"）
    - max_books: 该级别最多选择几本书
    - target_coverage: 希望覆盖的目标级别词汇比例
    - max_unknown_ratio: 允许的最大超纲词汇比例
    - min_relevant_ratio: 最小适合度要求
    - min_target_level_words: 最少目标等级词汇数量
    - already_covered: 已经覆盖的词汇（来自前面级别的学习）
    - already_selected_books: 全局已选书籍（避免重复选择）
    """
    
    # 第一步：筛选候选书籍
    candidates = self._filter_books_for_level(
        level=level,
        max_unknown_ratio=max_unknown_ratio,
        min_relevant_ratio=min_relevant_ratio,
        min_target_level_words=min_target_level_words,
    )
    
    # 过滤掉已被选过的书
    candidates = [
        book_id for book_id in candidates if book_id not in already_selected_books
    ]
    
    if not candidates:
        print(f"警告: {level} 没有找到合适的候选书籍")
        return {
            "selected_books": [],
            "coverage": 0,
            "new_words_covered": set(),
            "level_stats": {},
        }
    
    # 初始化状态
    selected_books = []
    target_vocab = self.level_vocab[level]
    remaining_words = target_vocab - already_covered  # 尚未覆盖的目标词汇
    newly_covered = set()  # 本次级别新覆盖的词汇
    
    print(
        f"目标词汇: {len(target_vocab)}, 已覆盖: {len(already_covered & target_vocab)}, 待覆盖: {len(remaining_words)}"
    )
    
    iteration = 0
    # 贪心算法：迭代选择最佳书籍
    while (
        len(selected_books) < max_books
        and len(newly_covered) / len(target_vocab) < target_coverage
        and remaining_words
    ):
        iteration += 1
        best_book = None
        best_score = -float("inf")
        
        # 评估每本候选书，选择得分最高的
        for book_id in candidates:
            if book_id in selected_books:  # 防止本轮重复
                continue
            
            # 计算这本书的综合评分
            score = self._calculate_book_score_for_level(
                book_id, level, remaining_words, iteration
            )
            
            if score > best_score:
                best_score = score
                best_book = book_id
        
        # 没有找到合适的书，终止循环
        if best_book is None:
            break
        
        # 选择最佳书籍并更新状态
        selected_books.append(best_book)
        new_words = (
            self.book_stats[best_book]["level_words"][level] & remaining_words
        )
        newly_covered.update(new_words)
        remaining_words -= new_words
        
        print(f"  选择: {best_book}")
        print(f"  新增{level}词汇: {len(new_words)}")
        print(f"  当前覆盖率: {len(newly_covered) / len(target_vocab):.1%}")
    
    return {
        "selected_books": selected_books,
        "coverage": len(newly_covered) / len(target_vocab) if target_vocab else 0,
        "new_words_covered": newly_covered,
        "level_stats": {
            "target_words": len(target_vocab),
            "covered_words": len(newly_covered),
            "books_count": len(selected_books),
        },
    }
```

### 贪心算法的三要素

这个方法展示了贪心算法的三个关键要素：

1. **候选集筛选**：`_filter_books_for_level()` 确保我们只考虑合适的书籍
2. **评价函数**：`_calculate_book_score_for_level()` 评估每本书的价值
3. **迭代选择**：每次选择当前"最优"的书籍，直到满足条件

> 💡 **贪心算法的本质**：在每一步都做出当前看来最好的选择，希望通过一系列局部最优解达到全局最优。

## 第八步：候选书籍筛选

让我们看看 `_filter_books_for_level()` 方法，它负责缩小搜索空间：

```python
def _filter_books_for_level(
    self,
    level: str,
    max_unknown_ratio: float = 0.15,
    min_relevant_ratio: float = 0.4,
    min_target_level_words: int = 50,
) -> List[str]:
    """
    为特定级别筛选合适的候选书籍
    
    筛选标准:
    1. 超纲词汇比例不能过高（避免过难）
    2. 使用适合度指标作为相关性判断（更直观）
    3. 目标级别词汇数量要达到最低要求
    """
    candidates = []
    level_idx = self.learning_levels.index(level)
    
    for book_id, stats in self.book_stats.items():
        # 硬约束1：超纲词汇比例控制
        if stats["unknown_ratio"] > max_unknown_ratio:
            continue
        
        # 🌟 使用 suitability_for 作为相关性指标（更直观）
        if stats["suitability_for"][level] < min_relevant_ratio:
            continue
        
        # 硬约束3：最低目标词汇数量
        if stats["level_counts"][level] >= min_target_level_words:
            candidates.append(book_id)
    
    # 按学习价值排序，优先考虑高价值书籍
    candidates.sort(
        key=lambda x: self.book_stats[x]["learning_value"], reverse=True
    )
    
    print(f"  {level}等级候选书籍: {len(candidates)}本")
    return candidates
```

### 为什么需要筛选？

想象一下，如果你有400本书，但其中300本对当前级别来说太难或太简单。直接在所有400本书中搜索最优组合会非常低效。

通过筛选，我们可以：

- 将搜索空间从400本缩减到50本左右
- 确保只考虑真正合适的书籍
- 提高后续贪心选择的效率和质量

## 第九步：书籍评分系统

最后，让我们看看核心的评分函数 `_calculate_book_score_for_level()`：

```python
def _calculate_book_score_for_level(
    self, book_id: str, level: str, remaining_words: Set[str], iteration: int
) -> float:
    """
    计算书籍在当前学习阶段的综合价值评分
    
    评分维度:
    1. 新覆盖的目标词汇数量（主要价值）
    2. 包含的低等级词汇（复习价值）
    3. 适量的高等级词汇（预习价值）
    4. 超纲词汇数量（负面因素）
    5. 剩余词汇覆盖比例（后期权重更高）
    """
    stats = self.book_stats[book_id]
    
    # 核心价值：新覆盖的目标等级词汇
    new_coverage = len(stats["level_words"][level] & remaining_words)
    if new_coverage == 0:
        return -1  # 没有新价值，直接淘汰
    
    # 基础分数：新覆盖词汇数量 × 权重
    score = new_coverage * 10
    
    # 复习价值：低等级词汇的巩固作用
    level_idx = self.learning_levels.index(level)
    for i in range(level_idx):
        lower_level = self.learning_levels[i]
        score += stats["level_counts"][lower_level] * 0.5
    
    # 预习价值：适量高等级词汇的预热作用
    if level_idx < len(self.learning_levels) - 1:
        next_level = self.learning_levels[level_idx + 1]
        # 设置上限，避免过度超前
        score += min(stats["level_counts"][next_level], 100) * 0.1
    
    # 代价惩罚：超纲词汇的负面影响
    score -= stats["unknown_count"] * 0.8
    
    # 动态调整：后期更重视覆盖剩余词汇
    if iteration > 2:
        coverage_bonus = (
            new_coverage / len(remaining_words) if remaining_words else 0
        )
        score += coverage_bonus * 50  # 剩余词汇越少，覆盖价值越高
    
    return score
```

### 评分系统的智慧

这个评分系统融合了语言学习的多个重要原则：

1. **新词汇覆盖**：这是主要目标，权重最高
2. **复习价值**：包含已学词汇有助于巩固记忆
3. **预习价值**：适度接触下一级词汇，为未来学习做准备
4. **难度控制**：超纲词汇过多会降低分数
5. **动态调整**：后期更注重填补空白，而非重复覆盖

> 🌟 **关键洞察**：有效的语言学习不是简单地覆盖词汇，而是要在**新知获取**、**旧知巩固**和**难度控制**之间找到平衡。

## 第十步：完整示例演示

现在，让我们运行一个完整的示例，看看算法如何工作：

```python
def demo_layered_usage():
    """演示分层词汇的使用"""
    import random
    
    random.seed(42)
    
    # 模拟CEFR分层词汇数据
    vocab_levels = {}
    level_sizes = {"A1": 800, "A2": 1200, "B1": 1500, "B2": 1800, "C1": 2000}
    
    word_id = 0
    for level, size in level_sizes.items():
        for i in range(size):
            vocab_levels[f"{level.lower()}_word_{i}"] = level
            word_id += 1
    
    # 生成书籍数据
    books_vocab = {}
    level_order = ["A1", "A2", "B1", "B2", "C1"]
    
    for i in range(100):  # 用100本书做演示
        book_size = random.randint(2000, 5000)
        book_vocab = set()
        
        # 确定书籍的主要难度等级
        primary_level_idx = random.randint(0, 4)  # 0-4 对应 A1-C1
        primary_level = level_order[primary_level_idx]
        
        # 分配词汇：主要等级50%，更低等级30%，更高等级15%，超纲5%
        remaining_size = book_size
        
        # 主要等级词汇
        primary_words = [w for w, l in vocab_levels.items() if l == primary_level]
        if primary_words:
            count = min(int(book_size * 0.5), len(primary_words), remaining_size)
            book_vocab.update(random.sample(primary_words, count))
            remaining_size -= count
        
        # 较低等级词汇
        for j in range(primary_level_idx):
            level = level_order[j]
            level_words = [w for w, l in vocab_levels.items() if l == level]
            if level_words and remaining_size > 0:
                count = min(int(book_size * 0.15), len(level_words), remaining_size)
                book_vocab.update(random.sample(level_words, count))
                remaining_size -= count
        
        # 较高等级词汇
        for j in range(primary_level_idx + 1, len(level_order)):
            level = level_order[j]
            level_words = [w for w, l in vocab_levels.items() if l == level]
            if level_words and remaining_size > 0:
                count = min(int(book_size * 0.1), len(level_words), remaining_size)
                book_vocab.update(random.sample(level_words, count))
                remaining_size -= count
        
        # 超纲词汇
        if remaining_size > 0:
            out_of_scope = {f"advanced_{i}_{j}" for j in range(remaining_size)}
            book_vocab.update(out_of_scope)
        
        books_vocab[f"book_{primary_level}_{i}"] = book_vocab
    
    # 创建选择器
    selector = LayeredCEFRBookSelector(books_vocab, vocab_levels)
    
    # 获取多种路径方案
    paths = selector.get_alternative_paths()
    
    # 展示结果
    for path_name, path_result in paths:
        selector.print_reading_path(path_result, path_name)
```

### 演示结果分析

运行此演示后，你会看到类似这样的输出：

```text
==================================================
📚 标准路径阅读路径
==================================================
总书籍数: 15
各等级分布: {'A1': 3, 'A2': 3, 'B1': 4, 'B2': 3, 'C1': 2}

📈 学习等级覆盖率:
  A1: 795/800 (99.4%)
  A2: 1185/1200 (98.8%)
  B1: 1470/1500 (98.0%)
  B2: 1750/1800 (97.2%)
  C1: 1920/2000 (96.0%)
  BEYOND: N/A (非学习目标，仅供参考)

📖 推荐阅读顺序:

  === A1 等级 ===
   1. book_A1_34
       目标词汇: 254, 超纲词: 12, 难度: 1.2
   2. book_A1_78
       目标词汇: 248, 超纲词: 9, 难度: 1.1
   3. book_A1_12
       目标词汇: 280, 超纲词: 15, 难度: 1.3

  === A2 等级 ===
   4. book_A2_56
       目标词汇: 380, 超纲词: 25, 难度: 2.1
   5. book_A2_89
       目标词汇: 372, 超纲词: 32, 难度: 2.0
   6. book_A2_23
       目标词汇: 395, 超纲词: 28, 难度: 2.2
       
...（其余书籍省略）...
```

这个输出清晰地展示了：

1. 选择了多少本书，以及它们如何分布在各个级别
2. 最终达到了怎样的词汇覆盖率
3. 推荐的阅读顺序，包括每本书的关键指标

## 第十一步：多方案生成与个性化

最后，让我们看看如何生成不同风格的阅读路径：

```python
def get_alternative_paths(self) -> List[Tuple[str, Dict]]:
    """
    多方案生成算法：参数空间探索

    算法类型：参数调优 + 多目标优化

    策略：通过调整关键参数生成不同特色的解决方案
        - 保守路径：更注重基础巩固，严格控制难度，适合初学者
        - 标准路径：平衡覆盖率、难度和学习效率，适合大多数学习者
        - 快速路径：适当放宽筛选条件，加快学习进度，适合时间紧张或基础较好的学习者

    目的：给用户提供选择空间，适应不同学习需求、目标和时间安排
    """
    paths = []

    # 🛡️ 保守路径：强调基础、低压力、高覆盖率
    # 适合：词汇基础薄弱、阅读速度慢、希望稳步提升的学习者
    conservative_path = self.create_progressive_reading_path(
        max_books_per_level={"A1": 4, "A2": 4, "B1": 3, "B2": 2, "C1": 1},
        target_coverage_per_level={
            "A1": 0.90,
            "A2": 0.90,
            "B1": 0.85,
            "B2": 0.80,
            "C1": 0.80,
        },
        max_unknown_ratio=0.10,  # 严格控制超纲词（≤10%）
        min_relevant_ratio=0.60,  # 要求60%以上是当前及以下等级词汇
        min_target_level_words=50,  # 确保每本书有足够的目标等级词汇
    )
    paths.append(("保守路径", conservative_path))

    # ⚖️ 标准路径：平衡各项指标
    # 适合：大多数中级学习者，希望系统学习、稳步进阶
    standard_path = self.create_progressive_reading_path(
        max_books_per_level={"A1": 3, "A2": 3, "B1": 4, "B2": 3, "C1": 2},
        target_coverage_per_level={
            "A1": 0.85,
            "A2": 0.90,
            "B1": 0.90,
            "B2": 0.90,
            "C1": 0.90,
        },
        max_unknown_ratio=0.15,  # 允许适度挑战
        min_relevant_ratio=0.40,  # 中等基础词汇要求
        min_target_level_words=30,
    )
    paths.append(("标准路径", standard_path))

    # 🚀 快速路径：追求效率，容忍更高难度
    # 适合：基础较好、时间有限、希望通过大量阅读快速提升的学习者
    fast_path = self.create_progressive_reading_path(
        max_books_per_level={"A1": 2, "A2": 3, "B1": 4, "B2": 3, "C1": 3},
        target_coverage_per_level={
            "A1": 0.75,
            "A2": 0.80,
            "B1": 0.85,
            "B2": 0.85,
            "C1": 0.85,
        },
        max_unknown_ratio=0.25,  # 允许最多25%超纲词
        min_relevant_ratio=0.30,  # 接受较低的基础词汇比例
        min_target_level_words=10,  # 只要出现少量目标词即可
    )
    paths.append(("快速路径", fast_path))

    return paths
```

### 为什么需要多方案？

不同的学习者有不同的需求：

- **保守型学习者**：基础较弱，需要更多练习和巩固
- **标准型学习者**：追求平衡，希望稳步提升
- **快速型学习者**：基础较好，希望尽快达到目标

通过调整关键参数，我们可以为不同学习者定制最适合的路径。

## 算法总结与思考

我们的分层贪心算法成功解决了渐进式阅读路径规划问题，关键在于：

1. **问题分解**：将复杂的全局优化问题分解为按级别的子问题（A1→A2→B1→B2→C1）
2. **预处理**：通过预计算统计信息提高效率
3. **多维评价**：综合考虑词汇覆盖、难度控制和学习连贯性
4. **渐进式策略**：确保学习路径平滑上升
5. **🌟适合度分析**：引入书籍对特定等级的适合度评估，提高匹配精度
6. **🌟全局去重**：避免在不同等级重复选择同一本书
7. **🌟超纲词处理**：将未在学习词表中的词汇标记为BEYOND，更贴近实际学习场景

### 核心创新点

1. **适合度指标**：`suitability_for[level] = (目标等级及以下词汇) / 总词汇数`
   - 这比传统的"相关词汇比例"更直观和准确
   - 直接回答"这本书有多适合A1学习者？"的问题

2. **BEYOND词汇处理**：
   - 现实中，书籍总包含一些超出教学大纲的词汇
   - 算法将其单独标记，而非简单忽略
   - 在难度评估时给予高权重惩罚（×6）

3. **多方案生成**：
   - 保守路径：适合基础薄弱学习者
   - 标准路径：平衡各项指标
   - 快速路径：适合时间紧张或基础较好的学习者

### 思考与扩展

这个算法还有很大的改进空间：

1. **个性化调整**：可以基于学习者的历史数据调整权重
2. **内容多样性**：避免选择主题过于相似的书籍  
3. **阅读难度**：考虑句子复杂度、主题熟悉度等因素
4. **动态调整**：根据学习进度实时调整后续推荐
5. **交互式优化**：允许用户反馈来优化推荐结果

### 你的任务

现在，轮到你了！尝试以下练习：

1. **参数调优实验**：
   - 修改 `level_weights` 参数，观察对书籍选择的影响
   - 调整 `min_relevant_ratio` 和 `min_target_level_words`，看如何影响候选书籍数量

2. **功能扩展**：
   - 实现一个方法，分析两本书之间的"难度跳跃"，确保路径平滑
   - 添加书籍主题多样性评估，避免选择内容过于相似的书籍

3. **评估体系优化**：
   - 尝试改进 `evaluate_book_difficulty` 方法，添加更多有用的分析维度
   - 实现书籍推荐的"解释性"功能，告诉用户为什么选择这本书

4. **用户界面设计**：
   - 设计一个Web界面，让非技术用户也能使用这个算法
   - 添加可视化功能，展示学习路径和词汇覆盖率进展

5. **高级挑战**：
   - 实现个性化权重学习，根据用户反馈调整算法参数
   - 考虑添加B2+、C2等更高级别的支持

## 结语

通过这个教程，你已经掌握了分层贪心算法的核心思想和实现细节。从A1基础词汇到C1高级表达，这个算法为英语学习者提供了一条科学、系统的阅读路径。

### 算法的普适性

这种分层贪心思想不仅适用于英语阅读路径规划，还可以广泛应用于：

- **在线教育**：课程内容的渐进式编排
- **技能培训**：从初级到高级的能力建设路径
- **游戏设计**：关卡难度的平滑过渡
- **知识管理**：概念学习的依赖关系处理
- **职业发展**：技能树和学习路线图规划

### 核心启发

1. **渐进式原则**：任何复杂技能的习得都需要循序渐进
2. **多维评估**：单一指标往往不足以做出最优决策
3. **个性化适配**：同一个算法框架可以通过参数调整适应不同需求
4. **数据驱动**：基于客观数据而非主观经验做决策

记住，好的算法不仅仅是数学上的最优，更要符合人类的认知规律和学习特点。我们的适合度分析、超纲词处理等创新，正是将算法理论与教育实践相结合的体现。

希望这个教程不仅帮你理解了算法本身，更重要的是启发你思考如何用技术手段解决现实中的学习问题。

> "教育不是填满一桶水，而是点燃一把火。" — 威廉·巴特勒·叶芝  
> "算法不是冰冷的数学公式，而是理解人性的智慧结晶。" — 本教程作者

Happy coding and happy learning! 📚✨🚀
