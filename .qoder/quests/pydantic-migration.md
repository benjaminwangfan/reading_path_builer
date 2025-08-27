# Pydantic Migration Design Document

## Overview

This document outlines the migration strategy for replacing dataclass-based models with Pydantic models in the Generic Vocabulary Path Builder system. The migration will leverage Pydantic's advanced features including validators, computed fields, serialization control, and type safety to improve the codebase's robustness and maintainability.

## Current Architecture Analysis

The current system uses a hybrid approach with some Pydantic models already in place:

### Existing Pydantic Models

- `VocabularyLevelConfig` - Configuration for vocabulary levels
- `VocabularyLevelStats` - Statistics for vocabulary levels  
- `BookVocabularyAnalysis` - Book analysis results
- `PathGenerationParameters` - Path generation configuration
- `BookSelectionCriteria` - Book selection criteria
- `LevelSelectionResult` - Level selection results
- `ReadingPathResult` - Complete path results
- `BookEvaluationResult` - Book evaluation results

### Current Limitations

1. **Basic Pydantic Usage**: Only using basic field definitions with minimal validation
2. **Config Classes**: Using `Config` class instead of modern `model_config`
3. **Validator Decorators**: Using deprecated `@validator` instead of `@field_validator`
4. **Missing Features**: No computed fields, custom serialization, or advanced validation
5. **Type Safety**: Could be improved with stricter type checking and validation

## Migration Strategy

### Phase 1: Modernize Existing Pydantic Models

#### 1.1 Update Configuration Pattern

```python
# Before (Current)
class VocabularyLevelConfig(BaseModel):
    levels: List[str] = Field(...)
    weights: Dict[str, float] = Field(...)
    
    class Config:
        arbitrary_types_allowed = True

# After (Pydantic v2 Style)
class VocabularyLevelConfig(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        frozen=False
    )
    
    levels: List[str] = Field(..., min_length=1, description="Vocabulary levels from easiest to hardest")
    weights: Dict[str, float] = Field(..., description="Learning weights per level")
```

#### 1.2 Replace Validator Decorators

```python
# Before
@validator('levels')
def validate_levels(cls, v):
    if not v:
        raise ValueError("At least one level must be specified")
    return v

# After  
@field_validator('levels')
@classmethod
def validate_levels(cls, v: List[str]) -> List[str]:
    if not v:
        raise ValueError("At least one level must be specified")
    if len(v) != len(set(v)):
        raise ValueError("Duplicate levels found")
    return v
```

#### 1.3 Add Computed Fields

```python
class VocabularyLevelConfig(BaseModel):
    levels: List[str] = Field(...)
    weights: Dict[str, float] = Field(...)
    
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
```

### Phase 2: Enhanced Data Models

#### 2.1 Improved Book Analysis Model

```python
class BookVocabularyAnalysis(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        json_encoders={
            set: list  # Convert sets to lists for JSON serialization
        }
    )
    
    book_id: str = Field(..., min_length=1, description="Unique book identifier")
    total_words: int = Field(..., ge=0, description="Total vocabulary words in book")
    level_distributions: Dict[str, VocabularyLevelStats] = Field(...)
    unknown_words: Set[str] = Field(default_factory=set)
    
    @field_validator('book_id')
    @classmethod
    def validate_book_id(cls, v: str) -> str:
        if not v or v.isspace():
            raise ValueError("Book ID cannot be empty or whitespace")
        return v.strip()
    
    @field_validator('level_distributions')
    @classmethod
    def validate_distributions(cls, v: Dict[str, VocabularyLevelStats]) -> Dict[str, VocabularyLevelStats]:
        if not v:
            raise ValueError("Level distributions cannot be empty")
        return v
    
    @computed_field
    @property
    def difficulty_category(self) -> str:
        """Categorize book difficulty"""
        if self.difficulty_score < 2.0:
            return "Beginner"
        elif self.difficulty_score < 4.0:
            return "Intermediate" 
        else:
            return "Advanced"
    
    @computed_field
    @property
    def recommended_levels(self) -> List[str]:
        """Get levels where this book is most suitable"""
        return [
            level for level, score in self.suitability_scores.items()
            if score >= 0.6
        ]
```

#### 2.2 Enhanced Path Generation Parameters

```python
class PathGenerationParameters(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    
    max_books_per_level: Dict[str, int] = Field(..., description="Maximum books per level")
    target_coverage_per_level: Dict[str, float] = Field(..., description="Target coverage ratios")
    max_unknown_ratio: float = Field(default=0.15, ge=0.0, le=1.0)
    min_relevant_ratio: float = Field(default=0.4, ge=0.0, le=1.0)
    min_target_level_words: int = Field(default=30, ge=1)
    
    @field_validator('max_books_per_level')
    @classmethod
    def validate_max_books(cls, v: Dict[str, int]) -> Dict[str, int]:
        for level, count in v.items():
            if count <= 0:
                raise ValueError(f"Max books for {level} must be positive, got {count}")
        return v
    
    @field_validator('target_coverage_per_level')
    @classmethod  
    def validate_coverage(cls, v: Dict[str, float]) -> Dict[str, float]:
        for level, coverage in v.items():
            if not 0.0 <= coverage <= 1.0:
                raise ValueError(f"Coverage for {level} must be between 0 and 1, got {coverage}")
        return v
    
    @model_validator(mode='after')
    def validate_consistency(self) -> 'PathGenerationParameters':
        """Validate cross-field consistency"""
        if self.min_relevant_ratio + self.max_unknown_ratio > 1.0:
            raise ValueError("min_relevant_ratio + max_unknown_ratio cannot exceed 1.0")
        return self
    
    @computed_field
    @property
    def total_max_books(self) -> int:
        """Total maximum books across all levels"""
        return sum(self.max_books_per_level.values())
```

### Phase 3: Advanced Pydantic Features

#### 3.1 Custom Serialization and Deserialization

```python
class ReadingPathResult(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            set: list,
            np.ndarray: lambda x: x.tolist()
        }
    )
    
    levels: Dict[str, LevelSelectionResult] = Field(...)
    total_books: List[str] = Field(...)
    cumulative_coverage: Dict[str, Dict[str, Dict[str, Union[int, float, str]]]] = Field(...)
    summary: Dict[str, Union[int, List, Dict]] = Field(...)
    
    def model_dump_json(self, **kwargs) -> str:
        """Custom JSON serialization with set handling"""
        return super().model_dump_json(
            exclude_none=True,
            by_alias=True,
            **kwargs
        )
    
    @classmethod
    def from_legacy_dict(cls, data: Dict) -> 'ReadingPathResult':
        """Create from legacy dictionary format"""
        # Handle legacy data transformation
        return cls(**data)
    
    def to_legacy_dict(self) -> Dict:
        """Export to legacy dictionary format for backward compatibility"""
        return self.model_dump(exclude_none=True)
```

#### 3.2 Validation Context and Dynamic Validation

```python
class BookSelectionCriteria(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    
    max_unknown_ratio: float = Field(..., ge=0.0, le=1.0)
    min_suitability_score: float = Field(..., ge=0.0, le=1.0)
    min_target_words: int = Field(..., ge=1)
    prefer_high_coverage: bool = Field(default=True)
    difficulty_preference: Optional[str] = Field(default=None, description="Optional difficulty preference")
    
    @field_validator('difficulty_preference')
    @classmethod
    def validate_difficulty_preference(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = ["conservative", "standard", "aggressive"]
            if v not in allowed:
                raise ValueError(f"difficulty_preference must be one of {allowed}, got {v}")
        return v
    
    @model_validator(mode='after')
    def validate_criteria_consistency(self) -> 'BookSelectionCriteria':
        """Validate that criteria are consistent"""
        if self.max_unknown_ratio + self.min_suitability_score < 0.5:
            raise ValueError("Criteria may be too restrictive - no books might qualify")
        return self
    
    def adjust_for_level(self, level_index: int, total_levels: int) -> 'BookSelectionCriteria':
        """Create adjusted criteria based on level position"""
        # Make criteria more lenient for higher levels
        adjustment_factor = level_index / max(total_levels - 1, 1)
        
        return self.model_copy(update={
            'max_unknown_ratio': min(self.max_unknown_ratio * (1 + adjustment_factor * 0.5), 1.0),
            'min_suitability_score': max(self.min_suitability_score * (1 - adjustment_factor * 0.2), 0.0)
        })
```

### Phase 4: Type Safety and Validation Enhancements

#### 4.1 Strict Type Definitions

```python
from typing import Literal, NewType, Annotated
from pydantic import StringConstraints, Field

BookId = NewType('BookId', str)
LevelName = NewType('LevelName', str)
CoverageRatio = Annotated[float, Field(ge=0.0, le=1.0)]
PositiveInt = Annotated[int, Field(gt=0)]

class VocabularyLevelStats(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    words: Set[str] = Field(..., description="Words at this level")
    count: PositiveInt = Field(..., description="Number of words")
    ratio: CoverageRatio = Field(..., description="Ratio relative to total vocabulary")
    weighted_value: float = Field(..., ge=0.0, description="Weighted learning value")
    
    @field_validator('words')
    @classmethod
    def validate_words_not_empty(cls, v: Set[str]) -> Set[str]:
        # Allow empty sets for some cases, but validate content
        invalid_words = [word for word in v if not word or word.isspace()]
        if invalid_words:
            raise ValueError(f"Invalid words found: {invalid_words}")
        return v
    
    @model_validator(mode='after')
    def validate_count_matches_words(self) -> 'VocabularyLevelStats':
        """Ensure count matches actual word count"""
        if self.count != len(self.words):
            raise ValueError(f"Count {self.count} doesn't match words length {len(self.words)}")
        return self
```

#### 4.2 Configuration Validation Context

```python
class ValidationContext(BaseModel):
    """Context for cross-model validation"""
    available_levels: List[str] = Field(...)
    vocabulary_mapping: Dict[str, str] = Field(...)
    book_ids: Set[str] = Field(...)
    
    def validate_level_exists(self, level: str) -> bool:
        """Check if level exists in configuration"""
        return level in self.available_levels
    
    def validate_book_exists(self, book_id: str) -> bool:
        """Check if book exists in dataset"""
        return book_id in self.book_ids

# Usage in validation
@field_validator('target_level')
@classmethod
def validate_target_level(cls, v: str, info: ValidationInfo) -> str:
    if info.context and 'validation_context' in info.context:
        ctx = info.context['validation_context']
        if not ctx.validate_level_exists(v):
            raise ValueError(f"Level {v} not found in available levels")
    return v
```

## Implementation Plan

### Implementation Steps

1. **Phase 1 - Modernize Core Models (Week 1)**
   - Update `VocabularyLevelConfig` with Pydantic v2 patterns
   - Replace all `@validator` with `@field_validator`
   - Update `Config` classes to `model_config`
   - Add basic computed fields

2. **Phase 2 - Enhanced Validation (Week 2)**
   - Implement cross-field validation with `@model_validator`
   - Add comprehensive field validation
   - Implement custom type constraints
   - Add validation context support

3. **Phase 3 - Advanced Features (Week 3)**
   - Implement custom serialization methods
   - Add computed fields for derived properties
   - Create factory methods with validation
   - Add backward compatibility methods

4. **Phase 4 - Integration and Testing (Week 4)**
   - Update all dependent code
   - Comprehensive testing with new models
   - Performance benchmarking
   - Documentation updates

### Migration Checklist

#### Core Model Updates

- [ ] `VocabularyLevelConfig` - Add strict validation and computed fields
- [ ] `VocabularyLevelStats` - Enhance with cross-field validation
- [ ] `BookVocabularyAnalysis` - Add computed properties and custom serialization
- [ ] `PathGenerationParameters` - Implement advanced validation patterns
- [ ] `BookSelectionCriteria` - Add dynamic adjustment methods
- [ ] `LevelSelectionResult` - Enhance with validation and serialization
- [ ] `ReadingPathResult` - Add comprehensive export/import methods
- [ ] `BookEvaluationResult` - Implement recommendation validation

#### Validation Enhancements

- [ ] Add field-level validation for all string fields (non-empty, trimmed)
- [ ] Implement range validation for all numeric fields
- [ ] Add cross-field consistency validation
- [ ] Create validation context for level/book existence checks
- [ ] Implement custom type constraints (BookId, LevelName, etc.)

#### Advanced Features

- [ ] Computed fields for derived properties
- [ ] Custom JSON serialization with set/numpy handling
- [ ] Factory methods with validation
- [ ] Backward compatibility import/export methods
- [ ] Dynamic model adjustment methods

#### Testing Strategy

- [ ] Unit tests for all new validation rules
- [ ] Integration tests with existing codebase
- [ ] Performance comparison tests
- [ ] Serialization/deserialization tests
- [ ] Backward compatibility tests

## Testing Strategy

### Validation Testing

```python
def test_vocabulary_level_config_validation():
    """Test enhanced VocabularyLevelConfig validation"""
    # Test valid configuration
    config = VocabularyLevelConfig(
        levels=["A1", "A2", "B1"],
        weights={"A1": 1.5, "A2": 1.3, "B1": 1.0}
    )
    assert config.level_count == 3
    assert config.difficulty_range == ("A1", "B1")
    
    # Test validation errors
    with pytest.raises(ValidationError):
        VocabularyLevelConfig(levels=[], weights={})  # Empty levels
    
    with pytest.raises(ValidationError):
        VocabularyLevelConfig(
            levels=["A1", "A1"],  # Duplicate levels
            weights={"A1": 1.0}
        )

def test_book_analysis_computed_fields():
    """Test computed fields in BookVocabularyAnalysis"""
    analysis = BookVocabularyAnalysis(
        book_id="test_book",
        total_words=100,
        level_distributions={},
        unknown_words=set(),
        unknown_count=0,
        unknown_ratio=0.0,
        difficulty_score=3.5,
        learning_value=1.2,
        suitability_scores={"A1": 0.8, "A2": 0.3},
        learning_words_ratio=0.9
    )
    
    assert analysis.difficulty_category == "Intermediate"
    assert analysis.recommended_levels == ["A1"]
```

### Serialization Testing

```python
def test_reading_path_result_serialization():
    """Test custom serialization features"""
    # Create result with sets and complex data
    result = ReadingPathResult(
        levels={"A1": level_result},
        total_books=["book1", "book2"],
        cumulative_coverage={},
        summary={}
    )
    
    # Test JSON serialization handles sets properly
    json_str = result.model_dump_json()
    parsed = json.loads(json_str)
    
    # Test backward compatibility
    legacy_dict = result.to_legacy_dict()
    restored = ReadingPathResult.from_legacy_dict(legacy_dict)
    assert restored == result
```

## Benefits and Improvements

### Enhanced Type Safety

- Strict type validation at runtime
- Better IDE support with comprehensive type hints
- Reduced runtime errors through validation

### Improved Developer Experience

- Clear validation error messages
- Computed fields for derived properties
- Factory methods for common configurations

### Better Data Integrity

- Cross-field validation ensures consistency
- Automatic data cleaning and normalization
- Validation context prevents invalid references

### Enhanced Serialization

- Proper handling of complex types (sets, numpy arrays)
- Custom serialization for different formats
- Backward compatibility support

### Performance Benefits

- Validation caching where appropriate
- Efficient serialization patterns
- Optimized field access

The migration will transform the current basic Pydantic usage into a comprehensive, type-safe, and robust data modeling system that fully leverages Pydantic's capabilities while maintaining backward compatibility with existing code.
