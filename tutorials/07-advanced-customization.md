# 07. 高级定制与扩展：解锁系统的无限可能

> *"真正的力量不在于系统能做什么，而在于你能让系统为你做什么。"*

## 🎯 定制的哲学

通用词汇路径构建器遵循**开放-封闭原则**：对扩展开放，对修改封闭。

### 定制的层次

1. **🟢 配置层定制**：调整参数和权重
2. **🟡 扩展层定制**：添加新的分析维度和评分算法
3. **🔴 架构层定制**：实现全新的组件和工作流

## 🟢 配置层定制：参数的艺术

### 自定义进展类型

```python
class CustomProgressionType(ProgressionType):
    """扩展的进展类型"""
    LOGARITHMIC = "logarithmic"    # 对数增长
    FIBONACCI = "fibonacci"        # 斐波那契增长
    SKILL_BASED = "skill_based"    # 基于技能难度

def create_logarithmic_config():
    """创建对数增长配置"""
    
    class LogarithmicManager(LevelConfigurationManager):
        def get_difficulty_multiplier(self, level: str) -> float:
            level_idx = self.get_level_index(level)
            
            if self.config.progression_type == CustomProgressionType.LOGARITHMIC:
                import math
                return math.log2(level_idx + 2)
            elif self.config.progression_type == CustomProgressionType.FIBONACCI:
                return self._fibonacci(level_idx + 1)
            else:
                return super().get_difficulty_multiplier(level)
        
        def _fibonacci(self, n: int) -> float:
            if n <= 1:
                return 1
            a, b = 1, 1
            for _ in range(2, n):
                a, b = b, a + b
            return float(b)
    
    config = VocabularyLevelConfig(
        levels=["Novice", "Beginner", "Intermediate", "Advanced", "Expert"],
        weights={"Novice": 2.0, "Beginner": 1.8, "Intermediate": 1.5, "Advanced": 1.2, "Expert": 1.0},
        progression_type=CustomProgressionType.LOGARITHMIC,
        beyond_level_name="LEGENDARY"
    )
    
    return config, LogarithmicManager
```

### 领域特化配置

```python
def create_domain_configs():
    """创建领域特化配置"""
    
    # 编程学习配置
    programming_config = VocabularyLevelConfig(
        levels=["Syntax", "Basics", "OOP", "Algorithms", "Architecture"],
        weights={"Syntax": 3.0, "Basics": 2.5, "OOP": 2.0, "Algorithms": 1.5, "Architecture": 1.0},
        progression_type=ProgressionType.CUSTOM,
        custom_progression_rules={"Syntax": 1, "Basics": 2, "OOP": 5, "Algorithms": 12, "Architecture": 30}
    )
    
    # 音乐学习配置
    music_config = VocabularyLevelConfig(
        levels=["Theory", "Scales", "Chords", "Harmony", "Composition"],
        weights={"Theory": 2.5, "Scales": 2.2, "Chords": 2.0, "Harmony": 1.8, "Composition": 1.5},
        progression_type=ProgressionType.EXPONENTIAL
    )
    
    return {"programming": programming_config, "music": music_config}
```

## 🟡 扩展层定制：新维度分析

### 扩展书籍分析模型

```python
class ExtendedBookAnalysis(BookVocabularyAnalysis):
    """扩展的书籍分析模型"""
    
    readability_score: float = Field(..., description="可读性分数")
    topic_diversity: float = Field(..., description="主题多样性")
    cultural_content: float = Field(..., description="文化内容比例")
    temporal_relevance: float = Field(..., description="时效性相关度")
    topic_tags: Set[str] = Field(default_factory=set, description="主题标签")
    sentiment_score: float = Field(default=0.0, description="情感倾向分数")

class AdvancedBookAnalyzer(BookStatisticsCalculator):
    """高级书籍分析器"""
    
    def calculate_extended_analysis(self, book_id: str, book_vocab: Set[str], 
                                  book_text: str = None) -> ExtendedBookAnalysis:
        """计算扩展分析"""
        
        # 基础分析
        base_analysis = self.calculate_book_analysis(book_id, book_vocab)
        
        # 扩展分析
        if book_text:
            readability = self._analyze_readability(book_text)
            topic_diversity = self._calculate_topic_diversity(book_text)
            cultural_content = self._analyze_cultural_content(book_text)
            topic_tags = self._extract_topic_tags(book_text)
        else:
            # 基于词汇的简化分析
            readability = self._estimate_readability_from_vocab(book_vocab)
            topic_diversity = self._estimate_diversity_from_vocab(book_vocab)
            cultural_content = self._estimate_cultural_content(book_vocab)
            topic_tags = self._extract_topic_from_vocab(book_vocab)
        
        return ExtendedBookAnalysis(
            **base_analysis.model_dump(),
            readability_score=readability,
            topic_diversity=topic_diversity,
            cultural_content=cultural_content,
            temporal_relevance=self._calculate_temporal_relevance(book_vocab),
            topic_tags=topic_tags,
            sentiment_score=0.0
        )
    
    def _estimate_readability_from_vocab(self, vocab: Set[str]) -> float:
        """基于词汇估算可读性"""
        if not vocab:
            return 0.0
        
        avg_word_length = sum(len(word) for word in vocab) / len(vocab)
        complex_words = sum(1 for word in vocab if len(word) > 8)
        complexity_ratio = complex_words / len(vocab)
        
        readability = 10.0 - (avg_word_length * 0.5 + complexity_ratio * 5.0)
        return max(0.0, min(10.0, readability))
    
    def _extract_topic_from_vocab(self, vocab: Set[str]) -> Set[str]:
        """从词汇中提取主题标签"""
        topic_keywords = {
            "science": ["experiment", "research", "theory", "data"],
            "technology": ["computer", "software", "digital", "system"],
            "business": ["market", "profit", "company", "strategy"],
            "health": ["medical", "health", "treatment", "doctor"]
        }
        
        detected_topics = set()
        vocab_lower = {word.lower() for word in vocab}
        
        for topic, keywords in topic_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in vocab_lower)
            if matches >= 2:
                detected_topics.add(topic)
        
        return detected_topics
```

### 自定义评分算法

```python
class MultiDimensionalScorer:
    """多维度评分算法"""
    
    def __init__(self, scoring_weights: Dict[str, float] = None):
        self.weights = scoring_weights or {
            "vocabulary_coverage": 0.4,
            "readability_match": 0.2,
            "topic_relevance": 0.15,
            "cultural_appropriateness": 0.1,
            "temporal_relevance": 0.1,
            "learning_efficiency": 0.05
        }
    
    def calculate_comprehensive_score(self, 
                                    book_analysis: ExtendedBookAnalysis,
                                    target_level: str,
                                    remaining_words: Set[str],
                                    learner_profile: Dict = None) -> float:
        """计算综合评分"""
        
        # 各维度分数
        vocab_score = self._calculate_vocabulary_score(book_analysis, target_level, remaining_words)
        readability_score = self._calculate_readability_score(book_analysis, target_level)
        topic_score = self._calculate_topic_score(book_analysis, learner_profile)
        cultural_score = self._calculate_cultural_score(book_analysis, learner_profile)
        temporal_score = book_analysis.temporal_relevance
        efficiency_score = self._calculate_efficiency_score(book_analysis, remaining_words)
        
        # 加权综合分数
        comprehensive_score = (
            vocab_score * self.weights["vocabulary_coverage"] +
            readability_score * self.weights["readability_match"] +
            topic_score * self.weights["topic_relevance"] +
            cultural_score * self.weights["cultural_appropriateness"] +
            temporal_score * self.weights["temporal_relevance"] +
            efficiency_score * self.weights["learning_efficiency"]
        )
        
        return comprehensive_score
    
    def _calculate_readability_score(self, analysis: ExtendedBookAnalysis, target_level: str) -> float:
        """计算可读性匹配分数"""
        ideal_readability = {
            "A1": (8.0, 10.0), "A2": (7.0, 9.0), "B1": (6.0, 8.0),
            "B2": (5.0, 7.0), "C1": (4.0, 6.0)
        }
        
        if target_level not in ideal_readability:
            return 50.0
        
        min_ideal, max_ideal = ideal_readability[target_level]
        book_readability = analysis.readability_score
        
        if min_ideal <= book_readability <= max_ideal:
            return 100.0
        elif book_readability < min_ideal:
            distance = min_ideal - book_readability
            return max(0.0, 100.0 - distance * 20)
        else:
            distance = book_readability - max_ideal
            return max(0.0, 100.0 - distance * 15)
    
    def _calculate_topic_score(self, analysis: ExtendedBookAnalysis, learner_profile: Dict = None) -> float:
        """计算主题相关性分数"""
        if not learner_profile or "interests" not in learner_profile:
            return 50.0
        
        learner_interests = set(learner_profile["interests"])
        book_topics = analysis.topic_tags
        
        if not book_topics:
            return 30.0
        
        overlap = learner_interests & book_topics
        if overlap:
            match_ratio = len(overlap) / len(book_topics)
            return min(100.0, 60.0 + match_ratio * 40.0)
        else:
            diversity_bonus = analysis.topic_diversity * 30
            return min(50.0, 20.0 + diversity_bonus)
```

## 🔴 架构层定制：重构核心组件

### 自定义路径生成器

```python
class AdvancedPathGenerator(GenericPathGenerator):
    """高级路径生成器"""
    
    def __init__(self, config: VocabularyLevelConfig, custom_scorer: MultiDimensionalScorer = None):
        super().__init__(config)
        self.custom_scorer = custom_scorer or MultiDimensionalScorer()
    
    def create_adaptive_reading_path(self,
                                   books_analysis: Dict[str, ExtendedBookAnalysis],
                                   target_vocabulary: Dict[str, Set[str]],
                                   path_parameters: PathGenerationParameters,
                                   learner_profile: Dict = None) -> ReadingPathResult:
        """创建自适应阅读路径"""
        
        print("🧠 生成自适应阅读路径...")
        
        # 生成基础路径
        base_path = self.create_progressive_reading_path(
            books_analysis, target_vocabulary, path_parameters
        )
        
        # 多样性优化
        diverse_path = self._optimize_diversity(base_path, books_analysis)
        
        # 添加学习建议
        enhanced_path = self._add_learning_suggestions(diverse_path, learner_profile)
        
        return enhanced_path
    
    def calculate_book_score(self, book_analysis: ExtendedBookAnalysis,
                           target_level: str, remaining_words: Set[str],
                           iteration: int, learner_profile: Dict = None) -> float:
        """使用自定义评分算法"""
        
        # 使用多维度评分器
        comprehensive_score = self.custom_scorer.calculate_comprehensive_score(
            book_analysis, target_level, remaining_words, learner_profile
        )
        
        # 添加迭代衰减因子
        iteration_factor = 1.0 / (1.0 + iteration * 0.1)
        
        return comprehensive_score * iteration_factor
    
    def _optimize_diversity(self, path_result: ReadingPathResult, 
                          books_analysis: Dict[str, ExtendedBookAnalysis]) -> ReadingPathResult:
        """优化路径多样性"""
        
        # 分析当前路径的主题分布
        topic_distribution = self._analyze_topic_distribution(path_result, books_analysis)
        
        # 识别主题过于集中的级别
        diverse_levels = {}
        
        for level, books in path_result.levels.items():
            level_topics = set()
            for book_id in books.selected_books:
                if book_id in books_analysis:
                    level_topics.update(books_analysis[book_id].topic_tags)
            
            # 如果主题过于单一，尝试替换部分书籍
            if len(level_topics) < 2 and len(books.selected_books) > 1:
                diverse_books = self._find_diverse_alternatives(
                    books.selected_books, books_analysis, level
                )
                diverse_levels[level] = books.model_copy(update={"selected_books": diverse_books})
            else:
                diverse_levels[level] = books
        
        return path_result.model_copy(update={"levels": diverse_levels})
    
    def _add_learning_suggestions(self, path_result: ReadingPathResult,
                                learner_profile: Dict = None) -> ReadingPathResult:
        """添加学习建议"""
        
        suggestions = []
        
        if learner_profile:
            learning_style = learner_profile.get("learning_style", "mixed")
            
            if learning_style == "visual":
                suggestions.append("建议结合图表和思维导图进行学习")
            elif learning_style == "auditory":
                suggestions.append("建议使用朗读和音频材料辅助学习")
            elif learning_style == "kinesthetic":
                suggestions.append("建议通过写作和练习强化词汇记忆")
        
        # 基于路径特征的建议
        total_books = len(path_result.total_books)
        if total_books > 15:
            suggestions.append("学习路径较长，建议制定明确的时间计划")
        elif total_books < 10:
            suggestions.append("学习路径较短，可以适当增加复习材料")
        
        # 添加建议到summary
        enhanced_summary = path_result.summary.copy()
        enhanced_summary["learning_suggestions"] = suggestions
        
        return path_result.model_copy(update={"summary": enhanced_summary})
```

### 个性化学习系统

```python
class PersonalizedLearningSystem:
    """个性化学习系统"""
    
    def __init__(self, config: VocabularyLevelConfig):
        self.config = config
        self.advanced_analyzer = AdvancedBookAnalyzer(config)
        self.custom_scorer = MultiDimensionalScorer()
        self.path_generator = AdvancedPathGenerator(config, self.custom_scorer)
    
    def create_personalized_path(self,
                               books_vocab: Dict[str, Set[str]],
                               vocab_level_mapping: Dict[str, str],
                               learner_profile: Dict) -> Dict:
        """创建个性化学习路径"""
        
        print("👤 创建个性化学习路径...")
        
        # 1. 分析学习者特征
        learning_preferences = self._analyze_learner_preferences(learner_profile)
        
        # 2. 扩展书籍分析
        extended_analyses = {}
        for book_id, book_vocab in books_vocab.items():
            extended_analyses[book_id] = self.advanced_analyzer.calculate_extended_analysis(
                book_id, book_vocab
            )
        
        # 3. 调整评分权重
        personalized_scorer = self._create_personalized_scorer(learning_preferences)
        self.path_generator.custom_scorer = personalized_scorer
        
        # 4. 生成目标词汇
        target_vocabulary = self._build_target_vocabulary(vocab_level_mapping)
        
        # 5. 创建个性化参数
        personalized_params = self._create_personalized_parameters(learning_preferences)
        
        # 6. 生成自适应路径
        personalized_path = self.path_generator.create_adaptive_reading_path(
            extended_analyses, target_vocabulary, personalized_params, learner_profile
        )
        
        return {
            "path_result": personalized_path,
            "learner_analysis": learning_preferences,
            "recommendations": self._generate_learning_recommendations(learner_profile, personalized_path)
        }
    
    def _analyze_learner_preferences(self, learner_profile: Dict) -> Dict:
        """分析学习者偏好"""
        
        preferences = {
            "difficulty_tolerance": learner_profile.get("difficulty_tolerance", 0.5),
            "learning_speed": learner_profile.get("learning_speed", "medium"),
            "interests": learner_profile.get("interests", []),
            "cultural_openness": learner_profile.get("cultural_openness", 0.5),
            "time_availability": learner_profile.get("time_availability", "medium")
        }
        
        return preferences
    
    def _create_personalized_scorer(self, preferences: Dict) -> MultiDimensionalScorer:
        """创建个性化评分器"""
        
        # 基于偏好调整权重
        base_weights = {
            "vocabulary_coverage": 0.4,
            "readability_match": 0.2,
            "topic_relevance": 0.15,
            "cultural_appropriateness": 0.1,
            "temporal_relevance": 0.1,
            "learning_efficiency": 0.05
        }
        
        # 根据兴趣调整主题权重
        if preferences.get("interests"):
            base_weights["topic_relevance"] *= 1.5
            base_weights["vocabulary_coverage"] *= 0.9
        
        # 根据文化开放度调整
        cultural_openness = preferences.get("cultural_openness", 0.5)
        base_weights["cultural_appropriateness"] *= (cultural_openness + 0.5)
        
        # 根据时间可用性调整效率权重
        time_availability = preferences.get("time_availability", "medium")
        if time_availability == "low":
            base_weights["learning_efficiency"] *= 2.0
        
        # 重新归一化权重
        total_weight = sum(base_weights.values())
        normalized_weights = {k: v/total_weight for k, v in base_weights.items()}
        
        return MultiDimensionalScorer(normalized_weights)
    
    def _generate_learning_recommendations(self, learner_profile: Dict, 
                                         path_result: ReadingPathResult) -> List[str]:
        """生成学习建议"""
        
        recommendations = []
        
        # 基于学习速度的建议
        learning_speed = learner_profile.get("learning_speed", "medium")
        total_books = len(path_result.total_books)
        
        if learning_speed == "fast" and total_books > 12:
            recommendations.append("您的学习速度较快，可以考虑并行阅读多本书籍")
        elif learning_speed == "slow" and total_books < 15:
            recommendations.append("建议适当延长每本书的学习时间，确保充分消化")
        
        # 基于兴趣的建议
        interests = learner_profile.get("interests", [])
        if interests:
            recommendations.append(f"您对{', '.join(interests)}感兴趣，已为您优化相关主题的书籍选择")
        
        # 基于时间可用性的建议
        time_availability = learner_profile.get("time_availability", "medium")
        if time_availability == "low":
            recommendations.append("时间有限时，建议专注于核心词汇，可以跳过部分进阶内容")
        
        return recommendations

# 使用示例
def demonstrate_personalized_system():
    """演示个性化学习系统"""
    
    # 学习者档案
    learner_profile = {
        "name": "Alice",
        "current_level": "B1",
        "target_level": "C1",
        "learning_speed": "fast",
        "difficulty_tolerance": 0.7,
        "interests": ["science", "technology", "business"],
        "cultural_openness": 0.8,
        "time_availability": "medium",
        "learning_style": "visual",
        "preferred_topics": ["innovation", "sustainability", "AI"]
    }
    
    # 创建个性化系统
    config = VocabularyLevelConfig.create_cefr_config()
    personalized_system = PersonalizedLearningSystem(config)
    
    # 生成个性化路径
    result = personalized_system.create_personalized_path(
        books_vocab, vocab_levels, learner_profile
    )
    
    print("👤 个性化学习路径结果:")
    print(f"学习者: {learner_profile['name']}")
    print(f"总书籍数: {len(result['path_result'].total_books)}")
    print(f"学习建议: {result['recommendations']}")
    
    return result
```

## 🎯 实践练习

### 练习1：自定义进展类型

设计一个"技能树"式的进展类型，其中某些高级技能需要多个前置技能。

### 练习2：多模态分析

扩展书籍分析，加入图像、音频等多媒体内容的分析。

### 练习3：协作学习系统

设计支持多人协作学习的路径生成算法。

### 练习4：实时适应系统

实现基于学习实时反馈的动态路径调整机制。

## 🔄 下一步预告

定制给了我们无限可能，但如何确保这些可能在大规模应用中依然高效？在最后一章**性能优化指南**中，我们将学习：

- 内存使用优化策略
- 并行处理与缓存设计
- 大数据集处理技巧
- 性能监控与调试

**思考题**：

1. 如何平衡个性化和系统复杂度？
2. 哪些定制功能适合作为核心特性集成？
3. 如何设计测试来验证定制功能的正确性？

准备好迎接性能优化的挑战了吗？

---

> "Customization is not about making the system do everything; it's about making the system do exactly what you need, exactly how you need it."
> "定制不是让系统做所有事情；而是让系统按照你的需要，以你需要的方式，做你需要的事情。"
