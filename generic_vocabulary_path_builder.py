"""
📚 Generic Vocabulary Reading Path Builder

A flexible, configurable system for creating progressive reading paths based on any vocabulary
difficulty system (CEFR, grade levels, frequency tiers, custom domains, etc.).

Core Design Philosophy:
1. Level Agnostic: Works with any vocabulary difficulty hierarchy
2. Weight Customization: Allows custom learning weights for different levels
3. Flexible Progression: Supports linear, exponential, and custom progressions
4. Backward Compatible: Maintains algorithmic approach of LayeredCEFRBookSelector
"""

from collections import defaultdict
from enum import Enum
from typing import Annotated, Dict, List, NewType, Optional, Set, Tuple, Union

import numpy as np
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)

# ====================================================================
# CUSTOM TYPE CONSTRAINTS
# ====================================================================

# Custom types for better type safety and validation
BookId = NewType("BookId", str)
LevelName = NewType("LevelName", str)
CoverageRatio = Annotated[
    float, Field(ge=0.0, le=1.0, description="Coverage ratio between 0 and 1")
]
PositiveInt = Annotated[int, Field(gt=0, description="Positive integer greater than 0")]
NonNegativeInt = Annotated[int, Field(ge=0, description="Non-negative integer")]
NonEmptyStr = Annotated[str, Field(min_length=1, description="Non-empty string")]

# ====================================================================
# CORE DATA MODELS AND CONFIGURATION
# ====================================================================


class ProgressionType(Enum):
    """Types of difficulty progression between levels"""

    LINEAR = "linear"  # Equal difficulty gaps between levels
    EXPONENTIAL = "exponential"  # Increasing difficulty gaps
    CUSTOM = "custom"  # User-defined progression rules


class VocabularyLevelConfig(BaseModel):
    """Configuration for vocabulary difficulty levels

    This is the core configuration that defines how vocabulary levels are organized,
    weighted, and progressed through. It replaces the hardcoded CEFR system.

    Examples:
        # CEFR Configuration
        VocabularyLevelConfig(
            levels=["A1", "A2", "B1", "B2", "C1"],
            weights={"A1": 1.5, "A2": 1.3, "B1": 1.1, "B2": 1.0, "C1": 0.9}
        )

        # Grade Level Configuration
        VocabularyLevelConfig(
            levels=["Grade1", "Grade2", "Grade3", "Grade4", "Grade5"],
            weights={"Grade1": 2.0, "Grade2": 1.8, "Grade3": 1.5, "Grade4": 1.2, "Grade5": 1.0},
            progression_type=ProgressionType.EXPONENTIAL
        )
    """

    levels: List[str] = Field(..., description="Ordered from easiest to hardest")
    weights: Dict[str, float] = Field(
        ..., description="Learning value weights per level"
    )
    progression_type: ProgressionType = Field(default=ProgressionType.LINEAR)
    beyond_level_name: str = Field(
        default="BEYOND", description="Name for unknown/unmapped words"
    )
    custom_progression_rules: Optional[Dict[str, float]] = Field(
        default=None, description="For custom progressions"
    )

    @field_validator("levels")
    @classmethod
    def validate_levels(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one level must be specified")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate levels found in configuration")
        return v

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
        if not v:
            raise ValueError("Weights must be specified for at least one level")
        for level, weight in v.items():
            if weight <= 0:
                raise ValueError(
                    f"Weight for level {level} must be positive, got {weight}"
                )
        return v

    @model_validator(mode="after")
    def validate_custom_progression(self) -> "VocabularyLevelConfig":
        progression_type = self.progression_type
        levels = self.levels
        v = self.custom_progression_rules

        if progression_type == ProgressionType.CUSTOM:
            if not v:
                raise ValueError(
                    "Custom progression rules required for CUSTOM progression type"
                )
            for level in levels:
                if level not in v:
                    raise ValueError(
                        f"Custom progression rule missing for level {level}"
                    )
        return self

    @computed_field
    @property
    def level_count(self) -> int:
        """Number of configured levels"""
        return len(self.levels)

    @computed_field
    @property
    def difficulty_range(self) -> Tuple[str, str]:
        """Easiest and hardest levels"""
        return (self.levels[0], self.levels[-1]) if self.levels else ("", "")

    def model_post_init(self, __context):
        """Ensure all levels have weights (use 1.0 as default)"""
        # Ensure all levels have weights (use 1.0 as default)
        for level in self.levels:
            if level not in self.weights:
                self.weights[level] = 1.0

    @classmethod
    def create_cefr_config(cls) -> "VocabularyLevelConfig":
        """Factory method for CEFR configuration (backward compatibility)"""
        return cls(
            levels=["A1", "A2", "B1", "B2", "C1"],
            weights={"A1": 1.5, "A2": 1.3, "B1": 1.1, "B2": 1.0, "C1": 0.9},
            progression_type=ProgressionType.LINEAR,
            beyond_level_name="BEYOND",
        )

    @classmethod
    def create_grade_config(cls, max_grade: int = 6) -> "VocabularyLevelConfig":
        """Factory method for grade-level configuration"""
        levels = [f"Grade{i}" for i in range(1, max_grade + 1)]
        # Higher weights for lower grades (more valuable for beginners)
        weights = {level: 2.0 - (i * 0.2) for i, level in enumerate(levels)}
        return cls(
            levels=levels,
            weights=weights,
            progression_type=ProgressionType.EXPONENTIAL,
            beyond_level_name="ADVANCED",
        )

    @classmethod
    def create_frequency_config(cls) -> "VocabularyLevelConfig":
        """Factory method for frequency-based configuration"""
        return cls(
            levels=["HighFreq", "MidFreq", "LowFreq", "Rare"],
            weights={"HighFreq": 1.8, "MidFreq": 1.3, "LowFreq": 1.0, "Rare": 0.7},
            progression_type=ProgressionType.LINEAR,
            beyond_level_name="UNKNOWN",
        )


class VocabularyLevelStats(BaseModel):
    """Statistics for a specific vocabulary level within a book"""

    words: Set[str] = Field(..., description="Actual words at this level in the book")
    count: NonNegativeInt = Field(..., description="Number of words at this level")
    ratio: CoverageRatio = Field(
        ..., description="Ratio relative to total book vocabulary"
    )
    weighted_value: float = Field(
        ..., ge=0.0, description="Learning value weighted by level importance"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    @field_validator("words")
    @classmethod
    def validate_words_not_empty(cls, v: Set[str]) -> Set[str]:
        # Allow empty sets for some cases, but validate content
        invalid_words = [word for word in v if not word or word.isspace()]
        if invalid_words:
            raise ValueError(f"Invalid words found: {invalid_words}")
        return v

    @model_validator(mode="after")
    def validate_count_matches_words(self) -> "VocabularyLevelStats":
        """Ensure count matches actual word count"""
        if self.count != len(self.words):
            raise ValueError(
                f"Count {self.count} doesn't match words length {len(self.words)}"
            )
        return self


class BookVocabularyAnalysis(BaseModel):
    """Enhanced book statistics for any level system

    This replaces the book_stats dictionary from the CEFR implementation
    with a more structured, type-safe approach.
    """

    book_id: NonEmptyStr = Field(..., description="Unique book identifier")
    total_words: NonNegativeInt = Field(
        ..., description="Total vocabulary words in book"
    )
    level_distributions: Dict[str, VocabularyLevelStats] = Field(
        ..., description="Statistics per level"
    )
    unknown_words: Set[str] = Field(
        default_factory=set, description="Words not in vocabulary mapping"
    )
    unknown_count: NonNegativeInt = Field(..., description="Number of unknown words")
    unknown_ratio: CoverageRatio = Field(..., description="Ratio of unknown words")
    difficulty_score: float = Field(..., ge=0.0, description="Overall difficulty score")
    learning_value: float = Field(..., ge=0.0, description="Learning value score")
    suitability_scores: Dict[str, CoverageRatio] = Field(
        ..., description="Suitability for each level"
    )
    learning_words_ratio: CoverageRatio = Field(
        ..., description="Ratio of known learning words"
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        json_encoders={set: list},  # Convert sets to lists for JSON serialization
    )

    @computed_field
    @property
    def difficulty_category(self) -> str:
        """Categorize book difficulty based on difficulty score"""
        if self.difficulty_score < 2.0:
            return "Beginner"
        elif self.difficulty_score < 4.0:
            return "Intermediate"
        else:
            return "Advanced"

    @computed_field
    @property
    def recommended_levels(self) -> List[str]:
        """Get levels where this book is most suitable (suitability >= 0.6)"""
        return [
            level for level, score in self.suitability_scores.items() if score >= 0.6
        ]

    @field_validator("book_id")
    @classmethod
    def validate_book_id(cls, v: str) -> str:
        if not v or v.isspace():
            raise ValueError("Book ID cannot be empty or whitespace")
        return v.strip()

    @field_validator("level_distributions")
    @classmethod
    def validate_distributions(
        cls, v: Dict[str, VocabularyLevelStats]
    ) -> Dict[str, VocabularyLevelStats]:
        if not v:
            raise ValueError("Level distributions cannot be empty")
        return v

    def model_dump_json(self, **kwargs) -> str:
        """Custom JSON serialization with set handling"""
        return super().model_dump_json(exclude_none=True, by_alias=True, **kwargs)

    @classmethod
    def from_legacy_dict(cls, data: Dict) -> "BookVocabularyAnalysis":
        """Create from legacy dictionary format"""
        # Handle legacy data transformation if needed
        return cls(**data)

    def to_legacy_dict(self) -> Dict:
        """Export to legacy dictionary format for backward compatibility"""
        return self.model_dump(exclude_none=True)


class PathGenerationParameters(BaseModel):
    """Configurable parameters for reading path generation

    This replaces the scattered parameters in create_progressive_reading_path
    with a structured configuration object.
    """

    max_books_per_level: Dict[str, PositiveInt] = Field(
        ..., description="Maximum books per level"
    )
    target_coverage_per_level: Dict[str, CoverageRatio] = Field(
        ..., description="Target coverage ratios"
    )
    max_unknown_ratio: CoverageRatio = Field(
        default=0.15, description="Maximum unknown word ratio"
    )
    min_relevant_ratio: CoverageRatio = Field(
        default=0.4, description="Minimum relevant word ratio"
    )
    min_target_level_words: PositiveInt = Field(
        default=30, description="Minimum target level words"
    )

    @classmethod
    def create_cefr_defaults(cls) -> "PathGenerationParameters":
        """Factory method for CEFR default parameters (backward compatibility)"""
        return cls(
            max_books_per_level={"A1": 3, "A2": 3, "B1": 4, "B2": 3, "C1": 2},
            target_coverage_per_level={
                "A1": 0.85,
                "A2": 0.9,
                "B1": 0.9,
                "B2": 0.9,
                "C1": 0.9,
            },
        )

    @classmethod
    def create_conservative_defaults(
        cls, levels: List[str]
    ) -> "PathGenerationParameters":
        """Factory method for conservative learning parameters"""
        max_books = {
            level: 4 if i < 2 else 3 if i < 4 else 2 for i, level in enumerate(levels)
        }
        coverage = {level: 0.9 if i < 3 else 0.8 for i, level in enumerate(levels)}
        return cls(
            max_books_per_level=max_books,
            target_coverage_per_level=coverage,
            max_unknown_ratio=0.10,
            min_relevant_ratio=0.60,
            min_target_level_words=50,
        )

    @field_validator("max_books_per_level")
    @classmethod
    def validate_max_books(cls, v: Dict[str, int]) -> Dict[str, int]:
        for level, count in v.items():
            if count <= 0:
                raise ValueError(f"Max books for {level} must be positive, got {count}")
        return v

    @model_validator(mode="after")
    def validate_consistency(self) -> "PathGenerationParameters":
        """Validate cross-field consistency"""
        if self.min_relevant_ratio + self.max_unknown_ratio > 1.0:
            raise ValueError("min_relevant_ratio + max_unknown_ratio cannot exceed 1.0")
        return self

    @computed_field
    @property
    def total_max_books(self) -> int:
        """Total maximum books across all levels"""
        return sum(self.max_books_per_level.values())


class BookSelectionCriteria(BaseModel):
    """Criteria for selecting books at each level"""

    max_unknown_ratio: CoverageRatio = Field(
        ..., description="Maximum unknown word ratio"
    )
    min_suitability_score: CoverageRatio = Field(
        ..., description="Minimum suitability score"
    )
    min_target_words: PositiveInt = Field(..., description="Minimum target words")
    prefer_high_coverage: bool = Field(
        default=True, description="Prefer books with high coverage"
    )

    @field_validator("max_unknown_ratio", "min_suitability_score")
    @classmethod
    def validate_ratios(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Ratio must be between 0 and 1, got {v}")
        return v

    @model_validator(mode="after")
    def validate_criteria_consistency(self) -> "BookSelectionCriteria":
        """Validate that criteria are consistent"""
        if self.max_unknown_ratio + self.min_suitability_score < 0.5:
            raise ValueError("Criteria may be too restrictive - no books might qualify")
        return self

    def adjust_for_level(
        self, level_index: int, total_levels: int
    ) -> "BookSelectionCriteria":
        """Create adjusted criteria based on level position"""
        # Make criteria more lenient for higher levels
        adjustment_factor = level_index / max(total_levels - 1, 1)

        return self.model_copy(
            update={
                "max_unknown_ratio": min(
                    self.max_unknown_ratio * (1 + adjustment_factor * 0.5), 1.0
                ),
                "min_suitability_score": max(
                    self.min_suitability_score * (1 - adjustment_factor * 0.2), 0.0
                ),
            }
        )

    @classmethod
    def create_conservative(cls) -> "BookSelectionCriteria":
        """Factory method for conservative criteria"""
        return cls(
            max_unknown_ratio=0.1,
            min_suitability_score=0.7,
            min_target_words=50,
            prefer_high_coverage=True,
        )

    @classmethod
    def create_standard(cls) -> "BookSelectionCriteria":
        """Factory method for standard criteria"""
        return cls(
            max_unknown_ratio=0.15,
            min_suitability_score=0.5,
            min_target_words=30,
            prefer_high_coverage=True,
        )

    @classmethod
    def create_aggressive(cls) -> "BookSelectionCriteria":
        """Factory method for aggressive learning criteria"""
        return cls(
            max_unknown_ratio=0.25,
            min_suitability_score=0.3,
            min_target_words=20,
            prefer_high_coverage=False,
        )


class LevelSelectionResult(BaseModel):
    """Result from selecting books for a specific level"""

    selected_books: List[str]
    coverage: float
    new_words_covered: Set[str]
    level_stats: Dict[str, Union[int, float]]

    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)


class ReadingPathResult(BaseModel):
    """Complete result from path generation"""

    levels: Dict[str, LevelSelectionResult]
    total_books: List[str]
    cumulative_coverage: Dict[str, Dict[str, Dict[str, Union[int, float, str]]]]
    summary: Dict[str, Union[int, List, Dict]]

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        json_encoders={set: list, np.ndarray: lambda x: x.tolist()},
    )

    def model_dump_json(self, **kwargs) -> str:
        """Custom JSON serialization with set handling"""
        return super().model_dump_json(exclude_none=True, by_alias=True, **kwargs)

    @classmethod
    def from_legacy_dict(cls, data: Dict) -> "ReadingPathResult":
        """Create from legacy dictionary format"""
        # Handle legacy data transformation
        return cls(**data)

    def to_legacy_dict(self) -> Dict:
        """Export to legacy dictionary format for backward compatibility"""
        return self.model_dump(exclude_none=True)


class BookEvaluationResult(BaseModel):
    """Result from evaluating a book for a specific level"""

    book_id: str
    target_level: str
    suitability_score: float
    difficulty_analysis: Dict[str, Union[float, Dict]]
    recommendations: List[str]

    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)


# ====================================================================
# VALIDATION CONTEXT
# ====================================================================


class ValidationContext(BaseModel):
    """Context for cross-model validation"""

    available_levels: List[str] = Field(..., description="Available vocabulary levels")
    vocabulary_mapping: Dict[str, str] = Field(..., description="Word to level mapping")
    book_ids: Set[str] = Field(..., description="Available book IDs")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def validate_level_exists(self, level: str) -> bool:
        """Check if level exists in configuration"""
        return level in self.available_levels

    def validate_book_exists(self, book_id: str) -> bool:
        """Check if book exists in dataset"""
        return book_id in self.book_ids

    @classmethod
    def create_from_config(
        cls,
        config: VocabularyLevelConfig,
        vocab_mapping: Dict[str, str],
        book_ids: Set[str],
    ) -> "ValidationContext":
        """Create validation context from configuration"""
        return cls(
            available_levels=config.levels,
            vocabulary_mapping=vocab_mapping,
            book_ids=book_ids,
        )


# ====================================================================
# LEVEL CONFIGURATION MANAGEMENT
# ====================================================================


class LevelConfigurationManager:
    """Manages vocabulary level configurations and provides level-related utilities

    This class encapsulates all logic related to level ordering, validation,
    and progression calculations. It replaces hardcoded level logic from the
    original CEFR implementation.
    """

    def __init__(self, config: VocabularyLevelConfig):
        self.config = config
        self._level_indices = {level: i for i, level in enumerate(config.levels)}

    def get_level_index(self, level: str) -> int:
        """Get numeric index for level ordering"""
        if level not in self._level_indices:
            raise ValueError(f"Unknown level: {level}")
        return self._level_indices[level]

    def get_difficulty_multiplier(self, level: str) -> float:
        """Calculate difficulty multiplier based on progression type"""
        level_idx = self.get_level_index(level)

        if self.config.progression_type == ProgressionType.LINEAR:
            return float(level_idx + 1)
        elif self.config.progression_type == ProgressionType.EXPONENTIAL:
            return 2.0**level_idx
        elif self.config.progression_type == ProgressionType.CUSTOM:
            if self.config.custom_progression_rules is None:
                raise ValueError("Custom progression rules not configured")
            return self.config.custom_progression_rules[level]
        else:
            raise ValueError(
                f"Unknown progression type: {self.config.progression_type}"
            )

    def is_valid_progression(self, from_level: str, to_level: str) -> bool:
        """Check if progression between levels is valid (from_level <= to_level)"""
        try:
            from_idx = self.get_level_index(from_level)
            to_idx = self.get_level_index(to_level)
            return from_idx <= to_idx
        except ValueError:
            return False

    def get_levels_up_to(self, target_level: str) -> List[str]:
        """Get all levels from first up to and including target_level"""
        target_idx = self.get_level_index(target_level)
        return self.config.levels[: target_idx + 1]

    def get_weight(self, level: str) -> float:
        """Get learning weight for a level"""
        return self.config.weights.get(level, 1.0)


# ====================================================================
# BOOK STATISTICS CALCULATOR
# ====================================================================


class BookStatisticsCalculator:
    """Calculate book statistics for any vocabulary level system

    This class generalizes the book analysis functionality from the original
    CEFR implementation to work with any vocabulary level system.
    """

    def __init__(self, config: VocabularyLevelConfig):
        self.config = config
        self.level_manager = LevelConfigurationManager(config)

        # Build level vocabulary mapping from vocab_level_mapping
        self.level_vocab: Dict[str, Set[str]] = {}

    def set_vocabulary_mapping(self, vocab_level_mapping: Dict[str, str]) -> None:
        """Set the vocabulary to level mapping and build level_vocab"""
        self.vocab_level_mapping = vocab_level_mapping

        # Group vocabulary by level (similar to _group_vocab_by_level in original)
        self.level_vocab = defaultdict(set)
        for word, level in vocab_level_mapping.items():
            if level in self.config.levels:
                self.level_vocab[level].add(word)

        # Convert to regular dict
        self.level_vocab = dict(self.level_vocab)

        # Build set of all known learning words (for identifying unknown words)
        self.known_learning_words = set(vocab_level_mapping.keys())

        print(f"📚 学习词表分层统计（{len(self.config.levels)} 个等级）:")
        for level in self.config.levels:
            count = len(self.level_vocab.get(level, set()))
            print(f"  {level}: {count}词")

    def calculate_book_analysis(
        self, book_id: str, book_vocab: Set[str]
    ) -> BookVocabularyAnalysis:
        """Generate comprehensive book analysis for any level system

        This method replaces the book statistics calculation from the original
        CEFR implementation with a generic, configurable approach.
        """
        if not hasattr(self, "vocab_level_mapping"):
            raise RuntimeError(
                "Must call set_vocabulary_mapping() before calculating book analysis"
            )

        total_words = len(book_vocab)
        if total_words == 0:
            # Return empty analysis for books with no vocabulary
            return self._create_empty_analysis(book_id)

        # Calculate level distributions
        level_distributions = {}
        learning_words_count = 0

        for level in self.config.levels:
            level_vocab_set = self.level_vocab.get(level, set())
            words_in_level = book_vocab & level_vocab_set
            count = len(words_in_level)
            ratio = count / total_words
            weighted_value = count * self.level_manager.get_weight(level)

            level_distributions[level] = VocabularyLevelStats(
                words=words_in_level,
                count=count,
                ratio=ratio,
                weighted_value=weighted_value,
            )
            learning_words_count += count

        # Calculate unknown words (words not in any learning level)
        unknown_words = book_vocab - self.known_learning_words
        unknown_count = len(unknown_words)
        unknown_ratio = unknown_count / total_words

        # Add BEYOND level for unknown words
        level_distributions[self.config.beyond_level_name] = VocabularyLevelStats(
            words=unknown_words,
            count=unknown_count,
            ratio=unknown_ratio,
            weighted_value=0.0,  # Unknown words have no learning value
        )

        # Calculate difficulty score
        difficulty_score = self._calculate_difficulty_score(
            level_distributions, total_words
        )

        # Calculate learning value (only from known levels)
        learning_value = self._calculate_learning_value(
            level_distributions, total_words
        )

        # Calculate suitability scores for each level
        suitability_scores = self._calculate_suitability_scores(
            level_distributions, total_words
        )

        # Calculate learning words ratio
        learning_words_ratio = learning_words_count / total_words

        return BookVocabularyAnalysis(
            book_id=book_id,
            total_words=total_words,
            level_distributions=level_distributions,
            unknown_words=unknown_words,
            unknown_count=unknown_count,
            unknown_ratio=unknown_ratio,
            difficulty_score=difficulty_score,
            learning_value=learning_value,
            suitability_scores=suitability_scores,
            learning_words_ratio=learning_words_ratio,
        )

    def calculate_suitability_for_level(
        self, book_vocab: Set[str], target_level: str
    ) -> float:
        """Calculate how suitable a book is for a specific level

        Suitability = (words at target level and below) / total words
        This replaces the suitability_for calculation in the original implementation.
        """
        if not book_vocab:
            return 0.0

        target_idx = self.level_manager.get_level_index(target_level)
        understandable_words = 0

        # Count words from target level and all easier levels
        for i in range(target_idx + 1):
            level = self.config.levels[i]
            level_vocab_set = self.level_vocab.get(level, set())
            understandable_words += len(book_vocab & level_vocab_set)

        return understandable_words / len(book_vocab)

    def _create_empty_analysis(self, book_id: str) -> BookVocabularyAnalysis:
        """Create empty analysis for books with no vocabulary"""
        empty_distributions = {}
        for level in self.config.levels + [self.config.beyond_level_name]:
            empty_distributions[level] = VocabularyLevelStats(
                words=set(), count=0, ratio=0.0, weighted_value=0.0
            )

        empty_suitability = {level: 0.0 for level in self.config.levels}

        return BookVocabularyAnalysis(
            book_id=book_id,
            total_words=0,
            level_distributions=empty_distributions,
            unknown_words=set(),
            unknown_count=0,
            unknown_ratio=0.0,
            difficulty_score=0.0,
            learning_value=0.0,
            suitability_scores=empty_suitability,
            learning_words_ratio=0.0,
        )

    def _calculate_difficulty_score(
        self, level_distributions: Dict[str, VocabularyLevelStats], total_words: int
    ) -> float:
        """Calculate overall difficulty score using configurable weights and progression"""
        if total_words == 0:
            return 0.0

        difficulty_score = 0.0

        # Add weighted difficulty from each learning level
        for level in self.config.levels:
            if level in level_distributions:
                level_multiplier = self.level_manager.get_difficulty_multiplier(level)
                difficulty_score += level_distributions[level].count * level_multiplier

        # Add high penalty for unknown words
        unknown_level = self.config.beyond_level_name
        if unknown_level in level_distributions:
            # Unknown words get penalty equivalent to hardest level + 1
            max_multiplier = max(
                self.level_manager.get_difficulty_multiplier(level)
                for level in self.config.levels
            )
            unknown_penalty = max_multiplier + 1
            difficulty_score += (
                level_distributions[unknown_level].count * unknown_penalty
            )

        return difficulty_score / total_words

    def _calculate_learning_value(
        self, level_distributions: Dict[str, VocabularyLevelStats], total_words: int
    ) -> float:
        """Calculate learning value based on weighted vocabulary counts"""
        if total_words == 0:
            return 0.0

        learning_value = 0.0
        for level in self.config.levels:
            if level in level_distributions:
                learning_value += level_distributions[level].weighted_value

        return learning_value / total_words

    def _calculate_suitability_scores(
        self, level_distributions: Dict[str, VocabularyLevelStats], total_words: int
    ) -> Dict[str, float]:
        """Calculate suitability scores for each level"""
        suitability_scores = {}

        for target_level in self.config.levels:
            target_idx = self.level_manager.get_level_index(target_level)
            understandable_count = 0

            # Sum words from target level and all easier levels
            for i in range(target_idx + 1):
                level = self.config.levels[i]
                if level in level_distributions:
                    understandable_count += level_distributions[level].count

            suitability_scores[target_level] = (
                understandable_count / total_words if total_words > 0 else 0.0
            )

        return suitability_scores


# ====================================================================
# GENERIC PATH GENERATOR
# ====================================================================


class GenericPathGenerator:
    """Generate reading paths for any vocabulary level system

    This class generalizes the path generation algorithm from the original
    CEFR implementation to work with any vocabulary level configuration.
    """

    def __init__(self, config: VocabularyLevelConfig):
        self.config = config
        self.level_manager = LevelConfigurationManager(config)

    def create_progressive_reading_path(
        self,
        books_analysis: Dict[str, BookVocabularyAnalysis],
        target_vocabulary: Dict[str, Set[str]],
        path_parameters: PathGenerationParameters,
    ) -> ReadingPathResult:
        """Main path generation algorithm

        This method replaces create_progressive_reading_path from the original
        implementation with a generic, configurable approach.
        """
        reading_path_levels = {}
        total_books = []
        cumulative_coverage = {}

        cumulative_covered = set()
        already_selected_books = set()

        for level in self.config.levels:
            print(f"\n=== 选择 {level} 等级书籍 ===")

            level_result = self.select_books_for_level(
                target_level=level,
                candidates=list(books_analysis.keys()),
                books_analysis=books_analysis,
                target_vocabulary=target_vocabulary,
                selection_criteria=self._create_selection_criteria(
                    level, path_parameters
                ),
                already_covered=cumulative_covered,
                already_selected_books=already_selected_books,
                max_books=path_parameters.max_books_per_level.get(level, 2),
                target_coverage=path_parameters.target_coverage_per_level.get(
                    level, 0.8
                ),
            )

            reading_path_levels[level] = level_result
            selected_books = level_result.selected_books
            total_books.extend(selected_books)
            already_selected_books.update(selected_books)

            # Update cumulative coverage
            for book_id in selected_books:
                book_analysis = books_analysis[book_id]
                for vocab_level in self.config.levels:
                    if vocab_level in book_analysis.level_distributions:
                        cumulative_covered.update(
                            book_analysis.level_distributions[vocab_level].words
                        )

            # Calculate cumulative coverage statistics
            cumulative_stats = self._calculate_cumulative_coverage(
                cumulative_covered, target_vocabulary
            )
            cumulative_coverage[level] = cumulative_stats

            print(f"完成 {level} 后累积覆盖率:")
            for vocab_level in self.config.levels:
                if vocab_level in cumulative_stats:
                    ratio = cumulative_stats[vocab_level].get("ratio", 0)
                    print(f"  {vocab_level}: {ratio:.1%}")

        # Generate summary
        summary = self._generate_path_summary(
            reading_path_levels, total_books, cumulative_coverage, books_analysis
        )

        return ReadingPathResult(
            levels=reading_path_levels,
            total_books=total_books,
            cumulative_coverage=cumulative_coverage,
            summary=summary,
        )

    def select_books_for_level(
        self,
        target_level: str,
        candidates: List[str],
        books_analysis: Dict[str, BookVocabularyAnalysis],
        target_vocabulary: Dict[str, Set[str]],
        selection_criteria: BookSelectionCriteria,
        already_covered: Set[str],
        already_selected_books: Set[str],
        max_books: int,
        target_coverage: float,
    ) -> LevelSelectionResult:
        """Greedy book selection for specific level

        This method replaces _select_books_for_level from the original implementation.
        """
        # Filter candidates based on criteria
        filtered_candidates = self._filter_candidates(
            candidates,
            books_analysis,
            target_level,
            selection_criteria,
            already_selected_books,
        )

        if not filtered_candidates:
            print(f"警告: {target_level} 没有找到合适的候选书籍")
            return LevelSelectionResult(
                selected_books=[],
                coverage=0.0,
                new_words_covered=set(),
                level_stats={"target_words": 0, "covered_words": 0, "books_count": 0},
            )

        # Get target vocabulary for this level
        level_target_vocab = target_vocabulary.get(target_level, set())
        remaining_words = level_target_vocab - already_covered
        newly_covered = set()
        selected_books = []

        print(
            f"目标词汇: {len(level_target_vocab)}, "
            f"已覆盖: {len(already_covered & level_target_vocab)}, "
            f"待覆盖: {len(remaining_words)}"
        )

        iteration = 0
        while (
            len(selected_books) < max_books
            and len(newly_covered) / len(level_target_vocab) < target_coverage
            and remaining_words
            and filtered_candidates
        ):
            iteration += 1
            best_book = self._select_best_book(
                filtered_candidates,
                books_analysis,
                target_level,
                remaining_words,
                iteration,
            )

            if best_book is None:
                break

            selected_books.append(best_book)
            filtered_candidates.remove(best_book)

            # Update covered words
            book_analysis = books_analysis[best_book]
            if target_level in book_analysis.level_distributions:
                new_words = (
                    book_analysis.level_distributions[target_level].words
                    & remaining_words
                )
                newly_covered.update(new_words)
                remaining_words -= new_words

                print(f"  选择: {best_book}")
                print(f"  新增{target_level}词汇: {len(new_words)}")
                print(
                    f"  当前覆盖率: {len(newly_covered) / len(level_target_vocab):.1%}"
                )

        coverage = (
            len(newly_covered) / len(level_target_vocab) if level_target_vocab else 0.0
        )

        return LevelSelectionResult(
            selected_books=selected_books,
            coverage=coverage,
            new_words_covered=newly_covered,
            level_stats={
                "target_words": len(level_target_vocab),
                "covered_words": len(newly_covered),
                "books_count": len(selected_books),
            },
        )

    def calculate_book_score(
        self,
        book_analysis: BookVocabularyAnalysis,
        target_level: str,
        remaining_words: Set[str],
        iteration: int,
    ) -> float:
        """Calculate selection score for a book

        This method replaces _calculate_book_score_for_level from the original implementation.
        """
        if target_level not in book_analysis.level_distributions:
            return -1.0

        target_level_stats = book_analysis.level_distributions[target_level]
        new_coverage = len(target_level_stats.words & remaining_words)

        if new_coverage == 0:
            return -1.0

        # Base score from new word coverage
        score = new_coverage * 10

        # Bonus for words from easier levels (review value)
        target_idx = self.level_manager.get_level_index(target_level)
        for i in range(target_idx):
            lower_level = self.config.levels[i]
            if lower_level in book_analysis.level_distributions:
                score += book_analysis.level_distributions[lower_level].count * 0.5

        # Small bonus for preview words from next level
        if target_idx < len(self.config.levels) - 1:
            next_level = self.config.levels[target_idx + 1]
            if next_level in book_analysis.level_distributions:
                preview_bonus = (
                    min(book_analysis.level_distributions[next_level].count, 100) * 0.1
                )
                score += preview_bonus

        # Penalty for unknown words
        score -= book_analysis.unknown_count * 0.8

        # Coverage efficiency bonus for later iterations
        if iteration > 2 and remaining_words:
            coverage_efficiency = new_coverage / len(remaining_words)
            score += coverage_efficiency * 50

        return score

    def _create_selection_criteria(
        self, level: str, path_parameters: PathGenerationParameters
    ) -> BookSelectionCriteria:
        """Create selection criteria for a specific level"""
        return BookSelectionCriteria(
            max_unknown_ratio=path_parameters.max_unknown_ratio,
            min_suitability_score=path_parameters.min_relevant_ratio,
            min_target_words=path_parameters.min_target_level_words,
            prefer_high_coverage=True,
        )

    def _filter_candidates(
        self,
        candidates: List[str],
        books_analysis: Dict[str, BookVocabularyAnalysis],
        target_level: str,
        criteria: BookSelectionCriteria,
        already_selected_books: Set[str],
    ) -> List[str]:
        """Filter candidate books based on selection criteria"""
        filtered = []

        for book_id in candidates:
            if book_id in already_selected_books:
                continue

            analysis = books_analysis[book_id]

            # Check unknown word ratio
            if analysis.unknown_ratio > criteria.max_unknown_ratio:
                continue

            # Check suitability score
            suitability = analysis.suitability_scores.get(target_level, 0.0)
            if suitability < criteria.min_suitability_score:
                continue

            # Check minimum target level words
            if target_level in analysis.level_distributions:
                target_word_count = analysis.level_distributions[target_level].count
                if target_word_count >= criteria.min_target_words:
                    filtered.append(book_id)

        # Sort by learning value (descending)
        filtered.sort(key=lambda x: books_analysis[x].learning_value, reverse=True)

        print(f"  {target_level}等级候选书籍: {len(filtered)}本")
        return filtered

    def _select_best_book(
        self,
        candidates: List[str],
        books_analysis: Dict[str, BookVocabularyAnalysis],
        target_level: str,
        remaining_words: Set[str],
        iteration: int,
    ) -> Optional[str]:
        """Select the best book from candidates using scoring algorithm"""
        best_book = None
        best_score = -float("inf")

        for book_id in candidates:
            score = self.calculate_book_score(
                books_analysis[book_id], target_level, remaining_words, iteration
            )
            if score > best_score:
                best_score = score
                best_book = book_id

        return best_book

    def _calculate_cumulative_coverage(
        self, cumulative_covered: Set[str], target_vocabulary: Dict[str, Set[str]]
    ) -> Dict[str, Dict[str, Union[int, float, str]]]:
        """Calculate cumulative coverage statistics"""
        cumulative_stats = {}

        for level in self.config.levels:
            level_vocab = target_vocabulary.get(level, set())
            if level_vocab:
                covered_count = len(cumulative_covered & level_vocab)
                total_count = len(level_vocab)
                ratio = covered_count / total_count if total_count > 0 else 0.0
            else:
                covered_count = 0
                total_count = 0
                ratio = 0.0

            cumulative_stats[level] = {
                "covered": covered_count,
                "total": total_count,
                "ratio": ratio,
            }

        return cumulative_stats

    def _generate_path_summary(
        self,
        reading_path_levels: Dict[str, LevelSelectionResult],
        total_books: List[str],
        cumulative_coverage: Dict[str, Dict[str, Dict[str, Union[int, float, str]]]],
        books_analysis: Dict[str, BookVocabularyAnalysis],
    ) -> Dict[str, Union[int, List, Dict]]:
        """Generate path summary statistics"""
        total_book_count = len(total_books)
        final_level = self.config.levels[-1] if self.config.levels else None
        final_coverage = cumulative_coverage.get(final_level, {}) if final_level else {}

        # Calculate difficulty progression
        difficulty_progression = []
        for level in self.config.levels:
            if (
                level in reading_path_levels
                and reading_path_levels[level].selected_books
            ):
                books = reading_path_levels[level].selected_books
                avg_difficulty = np.mean(
                    [books_analysis[book_id].difficulty_score for book_id in books]
                )
                difficulty_progression.append((level, round(avg_difficulty, 2)))

        # Books per level
        books_per_level = {
            level: len(
                reading_path_levels.get(
                    level,
                    LevelSelectionResult(
                        selected_books=[],
                        coverage=0.0,
                        new_words_covered=set(),
                        level_stats={},
                    ),
                ).selected_books
            )
            for level in self.config.levels
        }

        return {
            "total_books": total_book_count,
            "books_per_level": books_per_level,
            "final_coverage": final_coverage,
            "difficulty_progression": difficulty_progression,
            "recommended_order": total_books,
        }


# ====================================================================
# MAIN LAYERED VOCABULARY PATH BUILDER
# ====================================================================


class LayeredVocabularyPathBuilder:
    """Generic vocabulary-based reading path builder

    This is the main entry point class that replaces LayeredCEFRBookSelector
    with a flexible, configurable system that works with any vocabulary
    difficulty hierarchy.

    Usage Examples:
        # CEFR Configuration
        cefr_config = VocabularyLevelConfig.create_cefr_config()
        builder = LayeredVocabularyPathBuilder(
            books_vocab=books_data,
            vocab_level_mapping=cefr_word_levels,
            level_config=cefr_config
        )

        # Grade Level Configuration
        grade_config = VocabularyLevelConfig.create_grade_config(max_grade=5)
        builder = LayeredVocabularyPathBuilder(
            books_vocab=books_data,
            vocab_level_mapping=grade_word_levels,
            level_config=grade_config
        )
    """

    def __init__(
        self,
        books_vocab: Dict[str, Set[str]],
        vocab_level_mapping: Dict[str, str],
        level_config: VocabularyLevelConfig,
    ):
        """
        Initialize the generic vocabulary path builder

        Args:
            books_vocab: {book_id: set(all_words)} - Vocabulary for each book
            vocab_level_mapping: {word: level} - Word to difficulty level mapping
            level_config: Configuration defining the vocabulary level system
        """
        self.books_vocab = books_vocab
        self.vocab_level_mapping = vocab_level_mapping
        self.config = level_config

        # Initialize core components
        self.level_manager = LevelConfigurationManager(level_config)
        self.calculator = BookStatisticsCalculator(level_config)
        self.path_generator = GenericPathGenerator(level_config)

        # Set up vocabulary mapping for the calculator
        self.calculator.set_vocabulary_mapping(vocab_level_mapping)

        # Pre-calculate book analyses
        print("\n📊 Analyzing book vocabulary distributions...")
        self.book_analyses = self._analyze_all_books()
        print(f"✅ Completed analysis for {len(self.book_analyses)} books")

        # Build target vocabulary sets for path generation
        self.target_vocabulary = self._build_target_vocabulary()

    def create_reading_path(
        self, path_params: Optional[PathGenerationParameters] = None
    ) -> ReadingPathResult:
        """Generate a progressive reading path

        Args:
            path_params: Configuration parameters for path generation.
                        If None, uses defaults based on the level configuration.

        Returns:
            ReadingPathResult containing the complete reading path
        """
        if path_params is None:
            # Create default parameters based on the level configuration
            if self.config.levels == ["A1", "A2", "B1", "B2", "C1"]:
                path_params = PathGenerationParameters.create_cefr_defaults()
            else:
                path_params = PathGenerationParameters.create_conservative_defaults(
                    self.config.levels
                )

        print(f"\n🚀 Generating reading path for {len(self.config.levels)} levels...")

        return self.path_generator.create_progressive_reading_path(
            books_analysis=self.book_analyses,
            target_vocabulary=self.target_vocabulary,
            path_parameters=path_params,
        )

    def evaluate_book_for_level(
        self, book_id: str, target_level: str
    ) -> BookEvaluationResult:
        """Evaluate how suitable a book is for a specific level

        Args:
            book_id: ID of the book to evaluate
            target_level: Target difficulty level

        Returns:
            BookEvaluationResult with detailed evaluation
        """
        if book_id not in self.book_analyses:
            raise ValueError(f"Book {book_id} not found in analysis")

        if target_level not in self.config.levels:
            raise ValueError(f"Unknown level: {target_level}")

        analysis = self.book_analyses[book_id]
        suitability_score = analysis.suitability_scores.get(target_level, 0.0)

        # Generate detailed difficulty analysis
        level_breakdown = {}
        for level in self.config.levels + [self.config.beyond_level_name]:
            if level in analysis.level_distributions:
                stats = analysis.level_distributions[level]
                level_breakdown[level] = {
                    "count": stats.count,
                    "ratio": stats.ratio,
                    "percentage": f"{stats.ratio:.1%}",
                }

        difficulty_analysis = {
            "overall_difficulty_score": round(analysis.difficulty_score, 2),
            "learning_value_score": round(analysis.learning_value, 2),
            "unknown_ratio": analysis.unknown_ratio,
            "suitability_for": {
                level: round(score, 3)
                for level, score in analysis.suitability_scores.items()
            },
            "level_breakdown": level_breakdown,
        }

        # Generate recommendations
        recommendations = []
        best_level = max(analysis.suitability_scores.items(), key=lambda x: x[1])
        recommendations.append(
            f"最适合 {best_level[0]} 级别学习者（适合度：{best_level[1]:.1%}）"
        )

        if analysis.unknown_ratio > 0.2:
            recommendations.append("超纲词较多，建议搭配词典使用")

        if analysis.learning_value > 1.0:
            recommendations.append("学习价值较高，推荐精读")

        return BookEvaluationResult(
            book_id=book_id,
            target_level=target_level,
            suitability_score=suitability_score,
            difficulty_analysis=difficulty_analysis,
            recommendations=recommendations,
        )

    def get_alternative_paths(
        self, strategy_variants: Optional[List[str]] = None
    ) -> List[Tuple[str, ReadingPathResult]]:
        """Generate multiple path strategies

        Args:
            strategy_variants: List of strategy names. If None, uses default strategies.
                             Available: ["conservative", "standard", "fast"]

        Returns:
            List of (strategy_name, ReadingPathResult) tuples
        """
        if strategy_variants is None:
            strategy_variants = ["conservative", "standard", "fast"]

        paths = []

        for strategy in strategy_variants:
            if strategy == "conservative":
                params = self._create_conservative_parameters()
                paths.append(("保守路径", self.create_reading_path(params)))
            elif strategy == "standard":
                params = self._create_standard_parameters()
                paths.append(("标准路径", self.create_reading_path(params)))
            elif strategy == "fast":
                params = self._create_fast_parameters()
                paths.append(("快速路径", self.create_reading_path(params)))
            else:
                print(f"Warning: Unknown strategy '{strategy}' ignored")

        return paths

    def print_reading_path(self, path_result: ReadingPathResult, path_name: str = ""):
        """Format and print reading path results

        Args:
            path_result: The reading path result to print
            path_name: Optional name for the path
        """
        print(f"\n{'=' * 50}")
        print(f"📚 {path_name}阅读路径")
        print(f"{'=' * 50}")

        summary = path_result.summary
        print(f"总书籍数: {summary['total_books']}")
        print(f"各等级分布: {summary['books_per_level']}")

        print("\n📈 学习等级覆盖率:")
        final_coverage = summary.get("final_coverage", {})
        # Ensure final_coverage is a dictionary for type safety
        if not isinstance(final_coverage, dict):
            final_coverage = {}
        for level in self.config.levels:
            if level in final_coverage:
                cov = final_coverage[level]
                covered = cov.get("covered", 0)
                total = cov.get("total", 0)
                ratio = cov.get("ratio", 0.0)
                print(f"  {level}: {covered}/{total} ({ratio:.1%})")
        print(f"  {self.config.beyond_level_name}: N/A (非学习目标，仅供参考)")

        print("\n📖 推荐阅读顺序:")
        current_level = None
        recommended_order = summary.get("recommended_order", [])
        # Ensure recommended_order is a list for type safety
        if not isinstance(recommended_order, list):
            recommended_order = []
        for i, book_id in enumerate(recommended_order, 1):
            # Find which level this book belongs to
            book_level = None
            for level in self.config.levels:
                if (
                    level in path_result.levels
                    and book_id in path_result.levels[level].selected_books
                ):
                    book_level = level
                    break

            if book_level != current_level:
                print(f"\n  === {book_level} 等级 ===")
                current_level = book_level

            if book_id in self.book_analyses:
                analysis = self.book_analyses[book_id]
                target_level_count = 0
                if book_level and book_level in analysis.level_distributions:
                    target_level_count = analysis.level_distributions[book_level].count

                print(f"  {i:2d}. {book_id}")
                print(
                    f"      目标词汇: {target_level_count}, "
                    f"超纲词: {analysis.unknown_count}, "
                    f"难度: {analysis.difficulty_score:.1f}"
                )

    def get_book_statistics(self, book_id: str) -> Optional[BookVocabularyAnalysis]:
        """Get detailed statistics for a specific book

        Args:
            book_id: ID of the book

        Returns:
            BookVocabularyAnalysis if book exists, None otherwise
        """
        return self.book_analyses.get(book_id)

    def get_level_vocabulary_stats(self) -> Dict[str, int]:
        """Get vocabulary count statistics for each level

        Returns:
            Dictionary mapping level names to vocabulary counts
        """
        stats = {}
        for level in self.config.levels:
            level_vocab = self.target_vocabulary.get(level, set())
            stats[level] = len(level_vocab)
        return stats

    def _analyze_all_books(self) -> Dict[str, BookVocabularyAnalysis]:
        """Pre-calculate analysis for all books"""
        analyses = {}
        for book_id, vocab in self.books_vocab.items():
            analyses[book_id] = self.calculator.calculate_book_analysis(book_id, vocab)
        return analyses

    def _build_target_vocabulary(self) -> Dict[str, Set[str]]:
        """Build target vocabulary sets for each level from vocabulary mapping"""
        target_vocab = defaultdict(set)
        for word, level in self.vocab_level_mapping.items():
            if level in self.config.levels:
                target_vocab[level].add(word)
        return dict(target_vocab)

    def _create_conservative_parameters(self) -> PathGenerationParameters:
        """Create conservative path generation parameters"""
        # More books per level, higher coverage requirements, stricter filtering
        max_books = {
            level: 4 if i < 2 else 3 if i < 4 else 2
            for i, level in enumerate(self.config.levels)
        }
        coverage = {
            level: 0.9 if i < 3 else 0.8 for i, level in enumerate(self.config.levels)
        }

        return PathGenerationParameters(
            max_books_per_level=max_books,
            target_coverage_per_level=coverage,
            max_unknown_ratio=0.10,
            min_relevant_ratio=0.60,
            min_target_level_words=50,
        )

    def _create_standard_parameters(self) -> PathGenerationParameters:
        """Create standard path generation parameters"""
        # Balanced approach
        max_books = {
            level: 3 if i < 2 else 4 if i == 2 else 3 if i < 4 else 2
            for i, level in enumerate(self.config.levels)
        }
        coverage = {
            level: 0.85 if i == 0 else 0.9 for i, level in enumerate(self.config.levels)
        }

        return PathGenerationParameters(
            max_books_per_level=max_books,
            target_coverage_per_level=coverage,
            max_unknown_ratio=0.15,
            min_relevant_ratio=0.40,
            min_target_level_words=30,
        )

    def _create_fast_parameters(self) -> PathGenerationParameters:
        """Create fast path generation parameters"""
        # Fewer books, lower coverage, more permissive filtering
        max_books = {
            level: 2 if i < 1 else 3 if i < 3 else 3
            for i, level in enumerate(self.config.levels)
        }
        coverage = {
            level: 0.75 if i < 2 else 0.8 if i < 3 else 0.85
            for i, level in enumerate(self.config.levels)
        }

        return PathGenerationParameters(
            max_books_per_level=max_books,
            target_coverage_per_level=coverage,
            max_unknown_ratio=0.25,
            min_relevant_ratio=0.30,
            min_target_level_words=10,
        )
