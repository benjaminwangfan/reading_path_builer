"""
Comprehensive Test Suite for Pydantic Migration Enhancements

This test suite validates all the new Pydantic v2 features implemented:
1. Custom type constraints
2. Enhanced field validation
3. Cross-field validation
4. Computed fields
5. Custom serialization
6. Factory methods
"""

import json

import pytest
from pydantic import ValidationError

from generic_vocabulary_path_builder import (
    BookSelectionCriteria,
    BookVocabularyAnalysis,
    PathGenerationParameters,
    ProgressionType,
    ValidationContext,
    VocabularyLevelConfig,
    VocabularyLevelStats,
)


class TestCustomTypeConstraints:
    """Test custom type constraints"""

    def test_vocabulary_level_stats_validation(self):
        """Test VocabularyLevelStats with custom types"""
        # Valid data
        stats = VocabularyLevelStats(
            words={"hello", "world"}, count=2, ratio=0.5, weighted_value=1.5
        )
        assert stats.count == 2
        assert stats.ratio == 0.5

        # Test invalid count (negative)
        with pytest.raises(ValidationError):
            VocabularyLevelStats(
                words={"hello"}, count=-1, ratio=0.5, weighted_value=1.0
            )

        # Test invalid ratio (> 1.0)
        with pytest.raises(ValidationError):
            VocabularyLevelStats(
                words={"hello"}, count=1, ratio=1.5, weighted_value=1.0
            )

    def test_book_vocabulary_analysis_validation(self):
        """Test BookVocabularyAnalysis with enhanced validation"""
        level_stats = VocabularyLevelStats(
            words={"test"}, count=1, ratio=0.1, weighted_value=1.0
        )

        # Valid data
        analysis = BookVocabularyAnalysis(
            book_id="test_book",
            total_words=10,
            level_distributions={"A1": level_stats},
            unknown_words={"unknown"},
            unknown_count=1,
            unknown_ratio=0.1,
            difficulty_score=2.5,
            learning_value=1.2,
            suitability_scores={"A1": 0.8},
            learning_words_ratio=0.9,
        )
        assert analysis.book_id == "test_book"
        assert analysis.difficulty_category == "Intermediate"
        assert analysis.recommended_levels == ["A1"]

        # Test empty book_id
        with pytest.raises(ValidationError):
            BookVocabularyAnalysis(
                book_id="",
                total_words=10,
                level_distributions={"A1": level_stats},
                unknown_words=set(),
                unknown_count=0,
                unknown_ratio=0.0,
                difficulty_score=1.0,
                learning_value=1.0,
                suitability_scores={"A1": 0.5},
                learning_words_ratio=0.5,
            )


class TestComputedFields:
    """Test computed field functionality"""

    def test_vocabulary_level_config_computed_fields(self):
        """Test computed fields in VocabularyLevelConfig"""
        config = VocabularyLevelConfig(
            levels=["A1", "A2", "B1"], weights={"A1": 1.5, "A2": 1.3, "B1": 1.0}
        )

        assert config.level_count == 3
        assert config.difficulty_range == ("A1", "B1")

        # Test empty levels
        empty_config = VocabularyLevelConfig(levels=[], weights={})
        assert empty_config.level_count == 0
        assert empty_config.difficulty_range == ("", "")

    def test_book_analysis_computed_fields(self):
        """Test computed fields in BookVocabularyAnalysis"""
        level_stats = VocabularyLevelStats(
            words={"test"}, count=1, ratio=0.1, weighted_value=1.0
        )

        # Test different difficulty categories
        beginner_analysis = BookVocabularyAnalysis(
            book_id="beginner_book",
            total_words=10,
            level_distributions={"A1": level_stats},
            unknown_words=set(),
            unknown_count=0,
            unknown_ratio=0.0,
            difficulty_score=1.5,  # < 2.0 = Beginner
            learning_value=1.0,
            suitability_scores={"A1": 0.8, "A2": 0.3},
            learning_words_ratio=0.9,
        )
        assert beginner_analysis.difficulty_category == "Beginner"
        assert beginner_analysis.recommended_levels == ["A1"]

        advanced_analysis = BookVocabularyAnalysis(
            book_id="advanced_book",
            total_words=10,
            level_distributions={"C1": level_stats},
            unknown_words=set(),
            unknown_count=0,
            unknown_ratio=0.0,
            difficulty_score=4.5,  # >= 4.0 = Advanced
            learning_value=2.0,
            suitability_scores={"C1": 0.9},
            learning_words_ratio=0.8,
        )
        assert advanced_analysis.difficulty_category == "Advanced"
        assert advanced_analysis.recommended_levels == ["C1"]


class TestCrossFieldValidation:
    """Test cross-field validation using @model_validator"""

    def test_vocabulary_level_stats_cross_validation(self):
        """Test that count matches words length"""
        # Valid case
        stats = VocabularyLevelStats(
            words={"hello", "world"}, count=2, ratio=0.5, weighted_value=1.0
        )
        assert stats.count == len(stats.words)

        # Invalid case - count doesn't match words
        with pytest.raises(
            ValidationError, match="Count .* doesn't match words length"
        ):
            VocabularyLevelStats(
                words={"hello", "world"},
                count=3,  # Should be 2
                ratio=0.5,
                weighted_value=1.0,
            )

    def test_path_generation_parameters_consistency(self):
        """Test PathGenerationParameters consistency validation"""
        # Valid case
        params = PathGenerationParameters(
            max_books_per_level={"A1": 3, "A2": 2},
            target_coverage_per_level={"A1": 0.8, "A2": 0.9},
            max_unknown_ratio=0.2,
            min_relevant_ratio=0.4,
        )
        assert params.total_max_books == 5

        # Invalid case - ratios sum > 1.0
        with pytest.raises(
            ValidationError,
            match="min_relevant_ratio \\+ max_unknown_ratio cannot exceed 1.0",
        ):
            PathGenerationParameters(
                max_books_per_level={"A1": 3},
                target_coverage_per_level={"A1": 0.8},
                max_unknown_ratio=0.7,
                min_relevant_ratio=0.6,  # 0.7 + 0.6 = 1.3 > 1.0
            )

    def test_book_selection_criteria_consistency(self):
        """Test BookSelectionCriteria consistency validation"""
        # Valid case
        criteria = BookSelectionCriteria(
            max_unknown_ratio=0.2, min_suitability_score=0.6, min_target_words=30
        )

        # Test adjustment for level
        adjusted = criteria.adjust_for_level(2, 5)  # Level 2 of 5
        assert adjusted.max_unknown_ratio > criteria.max_unknown_ratio
        assert adjusted.min_suitability_score < criteria.min_suitability_score

        # Invalid case - too restrictive
        with pytest.raises(ValidationError, match="Criteria may be too restrictive"):
            BookSelectionCriteria(
                max_unknown_ratio=0.1,
                min_suitability_score=0.1,  # 0.1 + 0.1 = 0.2 < 0.5
                min_target_words=30,
            )


class TestFactoryMethods:
    """Test factory methods with validation"""

    def test_vocabulary_level_config_factories(self):
        """Test VocabularyLevelConfig factory methods"""
        # CEFR factory
        cefr_config = VocabularyLevelConfig.create_cefr_config()
        assert cefr_config.levels == ["A1", "A2", "B1", "B2", "C1"]
        assert cefr_config.progression_type == ProgressionType.LINEAR

        # Grade factory
        grade_config = VocabularyLevelConfig.create_grade_config(max_grade=3)
        assert grade_config.levels == ["Grade1", "Grade2", "Grade3"]
        assert grade_config.progression_type == ProgressionType.EXPONENTIAL

        # Frequency factory
        freq_config = VocabularyLevelConfig.create_frequency_config()
        assert freq_config.levels == ["HighFreq", "MidFreq", "LowFreq", "Rare"]

    def test_book_selection_criteria_factories(self):
        """Test BookSelectionCriteria factory methods"""
        # Conservative
        conservative = BookSelectionCriteria.create_conservative()
        assert conservative.max_unknown_ratio == 0.1
        assert conservative.min_suitability_score == 0.7

        # Standard
        standard = BookSelectionCriteria.create_standard()
        assert standard.max_unknown_ratio == 0.15
        assert standard.min_suitability_score == 0.5

        # Aggressive
        aggressive = BookSelectionCriteria.create_aggressive()
        assert aggressive.max_unknown_ratio == 0.25
        assert aggressive.min_suitability_score == 0.3


class TestCustomSerialization:
    """Test custom serialization features"""

    def test_book_analysis_json_serialization(self):
        """Test custom JSON serialization with set handling"""
        level_stats = VocabularyLevelStats(
            words={"hello", "world"}, count=2, ratio=0.5, weighted_value=1.0
        )

        analysis = BookVocabularyAnalysis(
            book_id="test_book",
            total_words=10,
            level_distributions={"A1": level_stats},
            unknown_words={"unknown", "words"},
            unknown_count=2,
            unknown_ratio=0.2,
            difficulty_score=2.5,
            learning_value=1.2,
            suitability_scores={"A1": 0.8},
            learning_words_ratio=0.8,
        )

        # Test JSON serialization
        json_str = analysis.model_dump_json()
        parsed = json.loads(json_str)

        # Sets should be converted to lists
        assert isinstance(parsed["unknown_words"], list)
        assert set(parsed["unknown_words"]) == {"unknown", "words"}

        # Test legacy compatibility
        legacy_dict = analysis.to_legacy_dict()  # type: ignore
        restored = BookVocabularyAnalysis.from_legacy_dict(legacy_dict)
        assert restored.book_id == analysis.book_id


class TestValidationContext:
    """Test ValidationContext functionality"""

    def test_validation_context_creation(self):
        """Test ValidationContext creation and methods"""
        config = VocabularyLevelConfig.create_cefr_config()
        vocab_mapping = {"hello": "A1", "world": "A2"}
        book_ids = {"book1", "book2"}

        context = ValidationContext.create_from_config(config, vocab_mapping, book_ids)

        assert context.validate_level_exists("A1")
        assert not context.validate_level_exists("X1")
        assert context.validate_book_exists("book1")
        assert not context.validate_book_exists("book3")


def run_all_tests():
    """Run all validation tests"""
    test_classes = [
        TestCustomTypeConstraints(),
        TestComputedFields(),
        TestCrossFieldValidation(),
        TestFactoryMethods(),
        TestCustomSerialization(),
        TestValidationContext(),
    ]

    total_tests = 0
    passed_tests = 0

    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\n=== {class_name} ===")

        for method_name in dir(test_class):
            if method_name.startswith("test_"):
                total_tests += 1
                try:
                    method = getattr(test_class, method_name)
                    method()
                    print(f"✅ {method_name}")
                    passed_tests += 1
                except Exception as e:
                    print(f"❌ {method_name}: {e}")

    print("\n=== Test Summary ===")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {passed_tests / total_tests * 100:.1f}%")


if __name__ == "__main__":
    run_all_tests()
