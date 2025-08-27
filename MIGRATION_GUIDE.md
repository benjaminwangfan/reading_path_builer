# Migration Guide: From LayeredCEFRBookSelector to LayeredVocabularyPathBuilder

This guide provides step-by-step instructions for migrating from the CEFR-specific `LayeredCEFRBookSelector` to the new generic `LayeredVocabularyPathBuilder` system.

## Overview

The new `LayeredVocabularyPathBuilder` is a complete rewrite that:

- ✅ Maintains the same algorithmic approach for path generation
- ✅ Provides backward compatibility with CEFR configurations
- ✅ Supports any vocabulary difficulty hierarchy (grades, frequency, custom domains)
- ✅ Offers improved type safety and configurability
- ✅ Uses structured data models instead of dictionaries

## Quick Migration (CEFR Users)

If you're currently using CEFR levels and want minimal changes:

### Before (Original Code)

```python
from reading_path_builder import LayeredCEFRBookSelector

# Original CEFR usage
selector = LayeredCEFRBookSelector(
    books_vocab=books_vocabulary_data,
    vocab_levels=cefr_word_mapping
)

# Generate reading path
path_result = selector.create_progressive_reading_path(
    max_books_per_level={"A1": 3, "A2": 3, "B1": 4, "B2": 3, "C1": 2},
    target_coverage_per_level={"A1": 0.85, "A2": 0.9, "B1": 0.9, "B2": 0.9, "C1": 0.9}
)

# Get alternative paths
alternative_paths = selector.get_alternative_paths()

# Print results
selector.print_reading_path(path_result, "Standard")
```

### After (New Generic Code)

```python
from generic_vocabulary_path_builder import (
    LayeredVocabularyPathBuilder, 
    VocabularyLevelConfig,
    PathGenerationParameters
)

# New generic system with CEFR configuration
cefr_config = VocabularyLevelConfig.create_cefr_config()
builder = LayeredVocabularyPathBuilder(
    books_vocab=books_vocabulary_data,
    vocab_level_mapping=cefr_word_mapping,
    level_config=cefr_config
)

# Generate reading path (same parameters, structured format)
path_params = PathGenerationParameters(
    max_books_per_level={"A1": 3, "A2": 3, "B1": 4, "B2": 3, "C1": 2},
    target_coverage_per_level={"A1": 0.85, "A2": 0.9, "B1": 0.9, "B2": 0.9, "C1": 0.9}
)
path_result = builder.create_reading_path(path_params)

# Get alternative paths
alternative_paths = builder.get_alternative_paths()

# Print results
builder.print_reading_path(path_result, "Standard")
```

## Complete Migration Steps

### Step 1: Update Imports

```python
# Remove old import
# from reading_path_builder import LayeredCEFRBookSelector

# Add new imports
from generic_vocabulary_path_builder import (
    LayeredVocabularyPathBuilder,
    VocabularyLevelConfig, 
    PathGenerationParameters,
    ProgressionType
)
```

### Step 2: Create Level Configuration

Choose the appropriate configuration for your vocabulary system:

#### Option A: CEFR (Backward Compatibility)

```python
# Exact equivalent to original CEFR system
config = VocabularyLevelConfig.create_cefr_config()
```

#### Option B: Grade Levels

```python
# Elementary/Middle school grades
config = VocabularyLevelConfig.create_grade_config(max_grade=6)
```

#### Option C: Frequency-Based

```python
# High/Medium/Low/Rare frequency tiers
config = VocabularyLevelConfig.create_frequency_config()
```

#### Option D: Custom Configuration

```python
# Define your own level system
config = VocabularyLevelConfig(
    levels=["Beginner", "Intermediate", "Advanced", "Expert"],
    weights={"Beginner": 2.0, "Intermediate": 1.5, "Advanced": 1.0, "Expert": 0.8},
    progression_type=ProgressionType.EXPONENTIAL,
    beyond_level_name="SPECIALIZED"
)
```

### Step 3: Initialize the Builder

```python
# Replace LayeredCEFRBookSelector initialization
builder = LayeredVocabularyPathBuilder(
    books_vocab=your_books_vocabulary_data,        # Same format as before
    vocab_level_mapping=your_vocabulary_mapping,   # Same format as before  
    level_config=config                            # New: configuration object
)
```

### Step 4: Configure Path Generation Parameters

The new system uses structured parameter objects instead of loose keyword arguments:

```python
# Option A: Use defaults (CEFR-compatible)
path_result = builder.create_reading_path()

# Option B: Create custom parameters
custom_params = PathGenerationParameters(
    max_books_per_level={"A1": 2, "A2": 3, "B1": 3, "B2": 2, "C1": 2},
    target_coverage_per_level={"A1": 0.8, "A2": 0.85, "B1": 0.9, "B2": 0.9, "C1": 0.85},
    max_unknown_ratio=0.2,
    min_relevant_ratio=0.5,
    min_target_level_words=25
)
path_result = builder.create_reading_path(custom_params)

# Option C: Use preset strategies
conservative_params = PathGenerationParameters.create_conservative_defaults(config.levels)
path_result = builder.create_reading_path(conservative_params)
```

### Step 5: Update Result Access Patterns

The new system uses structured result objects:

#### Before (Dictionary Access)

```python
# Old way - accessing dictionary keys
total_books = path_result["summary"]["total_books"]
selected_books = path_result["levels"]["A1"]["selected_books"]
coverage = path_result["levels"]["A1"]["coverage"]
```

#### After (Structured Objects)

```python
# New way - accessing object attributes
total_books = path_result.summary["total_books"]
selected_books = path_result.levels["A1"].selected_books
coverage = path_result.levels["A1"].coverage
```

### Step 6: Update Method Calls

Some method names and signatures have changed:

#### Book Evaluation

```python
# Before
book_evaluation = selector.evaluate_book_difficulty("book_id")

# After  
book_evaluation = builder.evaluate_book_for_level("book_id", "A1")
book_stats = builder.get_book_statistics("book_id")
```

#### Alternative Paths

```python
# Before
alternative_paths = selector.get_alternative_paths()

# After
alternative_paths = builder.get_alternative_paths()
# or specify strategies
alternative_paths = builder.get_alternative_paths(["conservative", "standard", "fast"])
```

## Advanced Features

### Custom Progression Types

The new system supports different difficulty progression models:

```python
# Linear progression (like original CEFR)
linear_config = VocabularyLevelConfig(
    levels=["Level1", "Level2", "Level3"],
    weights={"Level1": 1.5, "Level2": 1.0, "Level3": 0.8},
    progression_type=ProgressionType.LINEAR
)

# Exponential progression (steeper difficulty curve)
exponential_config = VocabularyLevelConfig(
    levels=["Basic", "Intermediate", "Advanced"],
    weights={"Basic": 2.0, "Intermediate": 1.0, "Advanced": 0.5},
    progression_type=ProgressionType.EXPONENTIAL
)

# Custom progression rules
custom_config = VocabularyLevelConfig(
    levels=["A", "B", "C"],
    weights={"A": 1.5, "B": 1.0, "C": 0.8},
    progression_type=ProgressionType.CUSTOM,
    custom_progression_rules={"A": 1.0, "B": 3.0, "C": 10.0}
)
```

### Enhanced Book Analysis

The new system provides more detailed book analysis:

```python
# Get detailed book statistics
book_analysis = builder.get_book_statistics("book_id")

print(f"Total words: {book_analysis.total_words}")
print(f"Unknown ratio: {book_analysis.unknown_ratio:.1%}")
print(f"Learning value: {book_analysis.learning_value:.2f}")

# Level-specific statistics
for level, stats in book_analysis.level_distributions.items():
    print(f"{level}: {stats.count} words ({stats.ratio:.1%})")

# Suitability for each level
for level, score in book_analysis.suitability_scores.items():
    print(f"Suitability for {level}: {score:.1%}")
```

### Vocabulary System Statistics

```python
# Get vocabulary statistics for your level system
vocab_stats = builder.get_level_vocabulary_stats()
for level, count in vocab_stats.items():
    print(f"{level}: {count} vocabulary words")
```

## Validation and Testing

Validate your migration with the provided test framework:

```python
# Run the comprehensive test suite
import subprocess
result = subprocess.run(["python", "test_vocabulary_path_builder.py"], 
                       capture_output=True, text=True)
print(result.stdout)
```

## Common Migration Issues

### Issue 1: Parameter Names Changed

**Problem**: `vocab_levels` parameter renamed to `vocab_level_mapping`

```python
# Old
LayeredCEFRBookSelector(books_vocab, vocab_levels)

# New  
LayeredVocabularyPathBuilder(books_vocab, vocab_level_mapping, level_config)
```

### Issue 2: Configuration Required

**Problem**: New system requires explicit level configuration

```python
# Solution: Add configuration
config = VocabularyLevelConfig.create_cefr_config()  # For CEFR compatibility
builder = LayeredVocabularyPathBuilder(books_vocab, vocab_level_mapping, config)
```

### Issue 3: Result Structure Changed

**Problem**: Results are now structured objects instead of dictionaries

```python
# Old dictionary access
books = result["levels"]["A1"]["selected_books"]

# New object access  
books = result.levels["A1"].selected_books
```

### Issue 4: Method Signatures Changed

**Problem**: Some methods have new parameters or names

```python
# Old
evaluation = selector.evaluate_book_difficulty("book_id")

# New - requires target level
evaluation = builder.evaluate_book_for_level("book_id", "A1")
```

## Benefits of Migration

1. **Flexibility**: Support for any vocabulary level system
2. **Type Safety**: Structured data models prevent errors
3. **Extensibility**: Easy to add new progression types and configurations
4. **Maintainability**: Cleaner, more modular code architecture
5. **Performance**: Optimized algorithms and data structures
6. **Documentation**: Better type hints and documentation

## Rollback Plan

If you need to rollback to the original system:

1. Keep the original `reading_path_builder.py` file
2. Switch imports back to `LayeredCEFRBookSelector`
3. Revert to dictionary-based parameter passing
4. Update result access patterns back to dictionary keys

## Support

For migration assistance:

- Review the test file: `test_vocabulary_path_builder.py`
- Check usage examples in the main implementation
- Refer to the comprehensive docstrings in `generic_vocabulary_path_builder.py`

The new system is designed to be a drop-in replacement for CEFR users while providing extensive new capabilities for other vocabulary systems.
