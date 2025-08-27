# 04. 路径生成算法：多层贪心策略的智慧

> *"贪心算法的艺术在于：在每个关键时刻，做出当前看来最明智的选择，并相信这些局部最优能通向全局最优。"*

在前面的章节中，我们建立了配置系统和分析引擎。现在，我们将探索系统的"智慧核心"——**路径生成算法**。这是一个精心设计的多层贪心算法，它能在成千上万本书中找到最优的学习路径。

## 🧠 算法设计哲学

### 核心挑战：多目标优化

路径生成面临的是一个复杂的多目标优化问题：

```text
给定：
- N本书，每本书有词汇分布 V_i
- M个难度级别 L_1, L_2, ..., L_M  
- 每个级别的目标覆盖率 C_1, C_2, ..., C_M
- 各种约束条件（书籍数量、难度限制等）

求解：
- 选择书籍子集 S ⊆ {1,2,...,N}
- 最大化词汇覆盖率
- 最小化难度跳跃
- 确保学习路径的平滑性
```

这是一个**NP-hard**问题。如果用暴力搜索，时间复杂度是O(2^N)，对于现实应用完全不可行。

### 分而治之 + 贪心策略

我们的解决方案采用**分层贪心**策略：

```text
整体问题：为所有级别选择最优书籍
    ↓
分解：为每个级别单独选择最优书籍
    ↓
贪心：在每个级别内，迭代选择当前最优书籍
```

**核心洞察**：虽然全局最优难以直接求解，但通过合理的问题分解和启发式评分，我们可以得到接近最优的实用解。

## 🏗️ GenericPathGenerator：算法核心

### 主算法流程

```python
def create_progressive_reading_path(self, books_analysis, target_vocabulary, path_parameters):
    """
    主算法：渐进式阅读路径生成
    
    核心思路：
    1. 按级别顺序处理（A1 → A2 → B1 → B2 → C1）
    2. 为每个级别贪心选择最优书籍组合
    3. 维护全局状态（已覆盖词汇、已选书籍）
    4. 确保学习路径的连贯性和递进性
    """
    
    reading_path_levels = {}
    total_books = []
    cumulative_coverage = {}
    
    # 全局状态跟踪
    cumulative_covered = set()      # 已覆盖的词汇
    already_selected_books = set()  # 已选择的书籍
    
    # 🌟 核心循环：按级别顺序处理
    for level in self.config.levels:
        print(f"\n=== 选择 {level} 等级书籍 ===")
        
        # 为当前级别选择最优书籍
        level_result = self.select_books_for_level(
            target_level=level,
            candidates=list(books_analysis.keys()),
            books_analysis=books_analysis,
            target_vocabulary=target_vocabulary,
            selection_criteria=self._create_selection_criteria(level, path_parameters),
            already_covered=cumulative_covered,
            already_selected_books=already_selected_books,
            max_books=path_parameters.max_books_per_level.get(level, 2),
            target_coverage=path_parameters.target_coverage_per_level.get(level, 0.8)
        )
        
        # 更新全局状态
        selected_books = level_result.selected_books
        total_books.extend(selected_books)
        already_selected_books.update(selected_books)
        
        # 更新累积覆盖词汇
        for book_id in selected_books:
            book_analysis = books_analysis[book_id]
            for vocab_level in self.config.levels:
                if vocab_level in book_analysis.level_distributions:
                    cumulative_covered.update(
                        book_analysis.level_distributions[vocab_level].words
                    )
        
        # 保存结果
        reading_path_levels[level] = level_result
        cumulative_coverage[level] = self._calculate_cumulative_coverage(
            cumulative_covered, target_vocabulary
        )
    
    return ReadingPathResult(...)
```

### 关键设计决策解析

#### 1. 为什么按级别顺序处理？

**语言学习的认知规律**：

- 学习者需要在基础牢固后再进入下一阶段
- 词汇习得具有层次性和依赖性
- 过早接触高难度材料会影响学习效果

**算法优势**：

- 保证路径的**连贯性**：每个级别都建立在前面级别的基础上
- 简化**状态管理**：只需维护已覆盖词汇的累积状态
- 降低**计算复杂度**：从O(2^N)降低到O(M×N×log N)

#### 2. 为什么使用贪心策略？

**全局最优 vs 实用可行**：

```python
# ❌ 理论最优但不可行
def find_optimal_path_exhaustive(books, levels):
    best_score = -1
    best_path = None
    
    # 遍历所有可能的书籍组合 - O(2^N)
    for book_combination in all_combinations(books):
        score = evaluate_path_quality(book_combination)
        if score > best_score:
            best_score = score
            best_path = book_combination
    
    return best_path  # 需要几十年才能算完！

# ✅ 贪心近似但高效
def find_good_path_greedy(books, levels):
    path = []
    remaining_words = target_vocabulary.copy()
    
    for level in levels:
        # 在当前级别选择最优书籍 - O(N×log N)
        level_books = select_best_books_for_level(
            books, level, remaining_words
        )
        path.extend(level_books)
        update_remaining_words(remaining_words, level_books)
    
    return path  # 几秒钟就能算完！
```

## 🎯 级别内书籍选择：贪心算法的精髓

### 核心算法实现

```python
def select_books_for_level(self, target_level, candidates, books_analysis, 
                          target_vocabulary, selection_criteria, 
                          already_covered, already_selected_books, 
                          max_books, target_coverage):
    """
    单级别书籍选择：贪心算法核心
    
    算法步骤：
    1. 筛选合格候选书籍
    2. 初始化状态（目标词汇、已覆盖词汇）
    3. 迭代贪心选择：
       - 为每本候选书计算评分
       - 选择得分最高的书
       - 更新状态
       - 检查终止条件
    """
    
    # 第一步：候选筛选
    filtered_candidates = self._filter_candidates(
        candidates, books_analysis, target_level, 
        selection_criteria, already_selected_books
    )
    
    if not filtered_candidates:
        return self._empty_result()
    
    # 第二步：初始化状态
    level_target_vocab = target_vocabulary.get(target_level, set())
    remaining_words = level_target_vocab - already_covered
    newly_covered = set()
    selected_books = []
    
    print(f"目标词汇: {len(level_target_vocab)}, "
          f"已覆盖: {len(already_covered & level_target_vocab)}, "
          f"待覆盖: {len(remaining_words)}")
    
    # 第三步：迭代贪心选择
    iteration = 0
    while (len(selected_books) < max_books and 
           len(newly_covered) / len(level_target_vocab) < target_coverage and
           remaining_words and filtered_candidates):
        
        iteration += 1
        
        # 🌟 核心：选择当前最优书籍
        best_book = self._select_best_book(
            filtered_candidates, books_analysis, 
            target_level, remaining_words, iteration
        )
        
        if best_book is None:
            break  # 没有合适的书籍了
        
        # 更新状态
        selected_books.append(best_book)
        filtered_candidates.remove(best_book)
        
        # 计算新覆盖的词汇
        book_analysis = books_analysis[best_book]
        if target_level in book_analysis.level_distributions:
            new_words = (book_analysis.level_distributions[target_level].words 
                        & remaining_words)
            newly_covered.update(new_words)
            remaining_words -= new_words
            
            print(f"  选择: {best_book}")
            print(f"  新增{target_level}词汇: {len(new_words)}")
            print(f"  当前覆盖率: {len(newly_covered) / len(level_target_vocab):.1%}")
    
    return LevelSelectionResult(...)
```

## 📊 评分机制：量化书籍价值

### 多维度评分模型

书籍评分是贪心算法的**决策核心**。我们设计了一个多维度评分模型：

```python
def calculate_book_score(self, book_analysis, target_level, remaining_words, iteration):
    """
    书籍评分：多维度价值量化
    
    评分维度：
    1. 新词汇覆盖（主要价值）
    2. 复习价值（低级别词汇）
    3. 预习价值（高级别词汇）
    4. 难度惩罚（超纲词汇）
    5. 效率奖励（后期迭代）
    """
    
    if target_level not in book_analysis.level_distributions:
        return -1.0  # 无相关内容，直接排除
    
    target_level_stats = book_analysis.level_distributions[target_level]
    new_coverage = len(target_level_stats.words & remaining_words)
    
    if new_coverage == 0:
        return -1.0  # 无新价值，排除
    
    # 🎯 核心价值：新词汇覆盖
    score = new_coverage * 10
    
    # 💪 复习价值：巩固已学知识
    target_idx = self.level_manager.get_level_index(target_level)
    for i in range(target_idx):
        lower_level = self.config.levels[i]
        if lower_level in book_analysis.level_distributions:
            review_bonus = book_analysis.level_distributions[lower_level].count * 0.5
            score += review_bonus
    
    # 🔮 预习价值：适度超前学习
    if target_idx < len(self.config.levels) - 1:
        next_level = self.config.levels[target_idx + 1]
        if next_level in book_analysis.level_distributions:
            preview_count = book_analysis.level_distributions[next_level].count
            preview_bonus = min(preview_count, 100) * 0.1  # 设置上限，避免过度超前
            score += preview_bonus
    
    # 💥 难度惩罚：控制学习负担
    unknown_penalty = book_analysis.unknown_count * 0.8
    score -= unknown_penalty
    
    # ⚡ 效率奖励：后期更注重效率
    if iteration > 2 and remaining_words:
        efficiency_ratio = new_coverage / len(remaining_words)
        efficiency_bonus = efficiency_ratio * 50
        score += efficiency_bonus
    
    return score
```

### 评分策略的智慧

#### 价值递减原理

```python
# 示例：B1级别第3轮选择
remaining_words = {"government", "environment", "situation", "development"}

# 候选书A：覆盖{"government", "environment"} - 50%剩余词汇
score_A = 2 * 10 + efficiency_bonus(0.5) = 20 + 25 = 45

# 候选书B：覆盖{"situation"} - 25%剩余词汇  
score_B = 1 * 10 + efficiency_bonus(0.25) = 10 + 12.5 = 22.5

# 算法选择书A：高覆盖率在后期更有价值
```

#### 平衡机制

```python
# 防止过度偏向某一维度
def balanced_score(new_coverage, review_value, preview_value, difficulty_penalty):
    """平衡各维度贡献"""
    
    # 主要价值（50%权重）
    primary = new_coverage * 10
    
    # 辅助价值（30%权重）
    secondary = (review_value + preview_value) * 0.6
    
    # 难度控制（20%权重）
    penalty = difficulty_penalty * 1.2
    
    return primary + secondary - penalty
```

## 🔄 候选筛选：质量门控

### 多重筛选条件

```python
def _filter_candidates(self, candidates, books_analysis, target_level, 
                      criteria, already_selected_books):
    """
    候选筛选：多重质量门控
    
    筛选条件：
    1. 全局去重：避免重复选择
    2. 超纲词控制：确保难度适宜
    3. 适合度要求：确保相关性
    4. 最低词汇量：确保学习价值
    """
    
    filtered = []
    
    for book_id in candidates:
        # 门控1：全局去重
        if book_id in already_selected_books:
            continue
        
        analysis = books_analysis[book_id]
        
        # 门控2：超纲词控制
        if analysis.unknown_ratio > criteria.max_unknown_ratio:
            continue  # 太难了，跳过
        
        # 门控3：适合度要求
        suitability = analysis.suitability_scores.get(target_level, 0.0)
        if suitability < criteria.min_suitability_score:
            continue  # 不够相关，跳过
        
        # 门控4：最低词汇量
        if target_level in analysis.level_distributions:
            target_word_count = analysis.level_distributions[target_level].count
            if target_word_count >= criteria.min_target_words:
                filtered.append(book_id)
    
    # 预排序：按学习价值降序排列
    filtered.sort(key=lambda x: books_analysis[x].learning_value, reverse=True)
    
    print(f"  {target_level}等级候选书籍: {len(filtered)}本")
    return filtered
```

### 自适应筛选策略

```python
def adaptive_filtering(self, candidates, target_level, iteration):
    """根据迭代轮次自适应调整筛选条件"""
    
    base_criteria = self.default_criteria
    
    if iteration == 1:
        # 第一轮：严格筛选，确保高质量
        return base_criteria.model_copy(update={
            "max_unknown_ratio": base_criteria.max_unknown_ratio * 0.8,
            "min_suitability_score": base_criteria.min_suitability_score * 1.2,
            "min_target_words": base_criteria.min_target_words * 1.5
        })
    elif iteration >= 3:
        # 后期轮次：放宽条件，确保能找到候选
        return base_criteria.model_copy(update={
            "max_unknown_ratio": base_criteria.max_unknown_ratio * 1.3,
            "min_suitability_score": base_criteria.min_suitability_score * 0.7,
            "min_target_words": base_criteria.min_target_words * 0.5
        })
    else:
        # 中期：使用标准条件
        return base_criteria
```

## 📈 算法性能分析

### 时间复杂度

```text
主算法：create_progressive_reading_path
├── 外层循环：M个级别 - O(M)
└── 内层循环：select_books_for_level
    ├── 候选筛选：O(N) 
    ├── 贪心选择迭代：最多k轮
    │   ├── 每轮评分：O(N)
    │   └── 最优选择：O(N)
    └── 总计：O(k×N)

总体复杂度：O(M×k×N)

其中：
- M：级别数量（通常5-10）
- N：书籍总数（通常100-10000）  
- k：每级别最大书籍数（通常2-5）

实际复杂度：O(N) - 近似线性！
```

### 空间复杂度

```text
主要存储：
├── 书籍分析结果：O(N×V) - N本书，每本V个词汇
├── 目标词汇集合：O(M×W) - M个级别，每级别W个词汇
├── 累积状态：O(Total_Words) - 累积覆盖的词汇
└── 中间结果：O(M×k) - 每级别选择k本书

总体：O(N×V + M×W) - 主要受书籍数量和词汇量影响
```

### 性能优化技巧

#### 1. 预计算优化

```python
class OptimizedPathGenerator(GenericPathGenerator):
    """性能优化版路径生成器"""
    
    def __init__(self, config):
        super().__init__(config)
        self._score_cache = {}  # 评分缓存
        self._filter_cache = {}  # 筛选缓存
    
    def calculate_book_score(self, book_analysis, target_level, remaining_words, iteration):
        # 生成缓存键
        remaining_hash = hash(frozenset(remaining_words))
        cache_key = (book_analysis.book_id, target_level, remaining_hash, iteration)
        
        if cache_key in self._score_cache:
            return self._score_cache[cache_key]
        
        score = super().calculate_book_score(book_analysis, target_level, remaining_words, iteration)
        self._score_cache[cache_key] = score
        return score
```

#### 2. 并行计算优化

```python
def parallel_book_scoring(self, candidates, target_level, remaining_words, iteration):
    """并行计算候选书籍评分"""
    
    from concurrent.futures import ThreadPoolExecutor
    
    def score_single_book(book_id):
        analysis = self.books_analysis[book_id]
        score = self.calculate_book_score(analysis, target_level, remaining_words, iteration)
        return book_id, score
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(score_single_book, candidates))
    
    return results
```

## 🎯 算法调优策略

### 参数敏感性分析

不同参数对结果的影响：

```python
def parameter_sensitivity_analysis(self, base_params):
    """参数敏感性分析"""
    
    results = {}
    
    # 测试覆盖率目标的影响
    for coverage in [0.7, 0.8, 0.85, 0.9, 0.95]:
        modified_params = base_params.model_copy(update={
            "target_coverage_per_level": {level: coverage for level in self.config.levels}
        })
        result = self.create_progressive_reading_path(..., modified_params)
        results[f"coverage_{coverage}"] = {
            "total_books": len(result.total_books),
            "final_coverage": result.summary["final_coverage"],
            "difficulty_progression": result.summary["difficulty_progression"]
        }
    
    # 测试最大书籍数的影响
    for max_books in [2, 3, 4, 5]:
        modified_params = base_params.model_copy(update={
            "max_books_per_level": {level: max_books for level in self.config.levels}
        })
        result = self.create_progressive_reading_path(..., modified_params)
        results[f"max_books_{max_books}"] = {...}
    
    return results
```

### A/B测试框架

```python
def compare_algorithm_variants(self, variant_configs):
    """比较不同算法配置的效果"""
    
    results = {}
    
    for variant_name, config in variant_configs.items():
        # 使用相同数据测试不同配置
        generator = GenericPathGenerator(config)
        result = generator.create_progressive_reading_path(...)
        
        # 评估指标
        metrics = {
            "coverage_efficiency": self._calculate_coverage_efficiency(result),
            "difficulty_smoothness": self._calculate_difficulty_smoothness(result),
            "learning_value_density": self._calculate_learning_value_density(result),
            "path_coherence": self._calculate_path_coherence(result)
        }
        
        results[variant_name] = {
            "path_result": result,
            "metrics": metrics
        }
    
    return results
```

## 🎯 实践练习

### 练习1：算法改进

尝试实现以下算法改进：

1. **多样性优化**：避免选择内容过于相似的书籍
2. **动态权重调整**：根据学习进度调整评分权重
3. **回溯机制**：允许撤销不良选择，重新选择
4. **多目标优化**：同时优化覆盖率、难度平滑性和学习价值

### 练习2：评分函数设计

设计专门的评分函数：

1. **时间敏感评分**：考虑学习时间成本
2. **兴趣导向评分**：基于学习者兴趣偏好
3. **记忆优化评分**：基于记忆曲线和遗忘规律
4. **技能导向评分**：针对特定技能的词汇权重

### 练习3：算法可视化

实现算法过程的可视化：

1. **决策树可视化**：展示每一步的决策过程
2. **评分热力图**：展示书籍评分的分布
3. **覆盖率进展图**：展示词汇覆盖的增长曲线
4. **算法收敛图**：展示算法的收敛过程

## 🔄 下一步预告

算法是理论，应用是实践。在下一章中，我们将通过**丰富的实现示例**，看看这些算法如何在真实场景中发挥作用，包括：

- CEFR标准配置的最佳实践
- K-12年级制系统的完整实现
- 专业领域词汇路径的设计技巧
- 多种学习策略的对比分析

**思考题**：

1. 如何设计算法来处理书籍之间的依赖关系（如系列丛书）？
2. 贪心算法在什么情况下可能产生次优解？如何检测和改进？
3. 如何将用户反馈整合到算法中，实现自适应优化？

让我们在实践中见证算法的威力！

---

> "The algorithm is the soul of the system - it embodies the wisdom of countless decisions, distilled into elegant mathematical logic."
> "算法是系统的灵魂——它体现了无数决策的智慧，提炼成优雅的数学逻辑。"
