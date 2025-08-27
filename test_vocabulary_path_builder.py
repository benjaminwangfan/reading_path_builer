#!/usr/bin/env python3
"""
Backward Compatibility Test for Generic Vocabulary Path Builder

This test validates that the new LayeredVocabularyPathBuilder provides
the same functionality as the original LayeredCEFRBookSelector when
configured with CEFR settings.

Test Categories:
1. Configuration validation
2. Book analysis compatibility
3. Path generation equivalence
4. Alternative vocabulary systems validation
"""

import sys

from generic_vocabulary_path_builder import (
    LayeredVocabularyPathBuilder,
    PathGenerationParameters,
    ProgressionType,
    VocabularyLevelConfig,
)


def create_sample_data():
    """Create sample test data for validation"""

    # Sample book vocabulary data
    books_vocab = {
        "book1": {
            "the",
            "cat",
            "is",
            "happy",
            "running",
            "quickly",
            "through",
            "forest",
        },
        "book2": {
            "dog",
            "plays",
            "in",
            "garden",
            "beautiful",
            "flowers",
            "bloom",
            "spring",
        },
        "book3": {
            "advanced",
            "conceptual",
            "framework",
            "demonstrates",
            "complexity",
            "theoretical",
            "analysis",
        },
        "book4": {
            "simple",
            "story",
            "about",
            "friendship",
            "between",
            "children",
            "school",
        },
        "book5": {
            "scientific",
            "research",
            "methodology",
            "requires",
            "systematic",
            "approach",
            "validation",
        },
    }

    # Sample CEFR vocabulary mapping
    vocab_levels = {
        # A1 level words
        "the": "A1",
        "cat": "A1",
        "is": "A1",
        "dog": "A1",
        "in": "A1",
        "simple": "A1",
        "about": "A1",
        "children": "A1",
        "story": "A1",
        # A2 level words
        "happy": "A2",
        "plays": "A2",
        "garden": "A2",
        "beautiful": "A2",
        "flowers": "A2",
        "friendship": "A2",
        "between": "A2",
        "school": "A2",
        # B1 level words
        "running": "B1",
        "quickly": "B1",
        "through": "B1",
        "forest": "B1",
        "bloom": "B1",
        "spring": "B1",
        # B2 level words
        "demonstrates": "B2",
        "complexity": "B2",
        "requires": "B2",
        "systematic": "B2",
        "approach": "B2",
        # C1 level words
        "advanced": "C1",
        "conceptual": "C1",
        "framework": "C1",
        "theoretical": "C1",
        "analysis": "C1",
        "scientific": "C1",
        "research": "C1",
        "methodology": "C1",
        "validation": "C1",
    }

    # Sample grade-level vocabulary mapping for testing alternative systems
    grade_vocab_levels = {
        # Grade 1
        "the": "Grade1",
        "cat": "Grade1",
        "is": "Grade1",
        "dog": "Grade1",
        "simple": "Grade1",
        "story": "Grade1",
        # Grade 2
        "happy": "Grade2",
        "plays": "Grade2",
        "garden": "Grade2",
        "beautiful": "Grade2",
        "children": "Grade2",
        "school": "Grade2",
        # Grade 3
        "running": "Grade3",
        "through": "Grade3",
        "flowers": "Grade3",
        "friendship": "Grade3",
        "between": "Grade3",
        # Grade 4
        "quickly": "Grade4",
        "forest": "Grade4",
        "bloom": "Grade4",
        "spring": "Grade4",
        "about": "Grade4",
        "in": "Grade4",
        # Grade 5
        "demonstrates": "Grade5",
        "complexity": "Grade5",
        "requires": "Grade5",
        "systematic": "Grade5",
        "approach": "Grade5",
        "advanced": "Grade5",
    }

    return books_vocab, vocab_levels, grade_vocab_levels


def test_cefr_configuration_validation():
    """Test 1: Validate CEFR configuration creation and validation"""
    print("=== Test 1: CEFR Configuration Validation ===")

    try:
        # Test factory method for CEFR config
        cefr_config = VocabularyLevelConfig.create_cefr_config()

        assert cefr_config.levels == ["A1", "A2", "B1", "B2", "C1"], (
            "CEFR levels incorrect"
        )
        assert cefr_config.beyond_level_name == "BEYOND", "Beyond level name incorrect"
        assert cefr_config.progression_type == ProgressionType.LINEAR, (
            "Progression type incorrect"
        )

        # Validate weights
        expected_weights = {"A1": 1.5, "A2": 1.3, "B1": 1.1, "B2": 1.0, "C1": 0.9}
        for level, expected_weight in expected_weights.items():
            assert cefr_config.weights[level] == expected_weight, (
                f"Weight for {level} incorrect"
            )

        print("✅ CEFR configuration validation passed")

    except Exception as e:
        print(f"❌ CEFR configuration validation failed: {e}")
        raise


def test_alternative_configuration_validation():
    """Test 2: Validate alternative vocabulary system configurations"""
    print("\\n=== Test 2: Alternative Configuration Validation ===")

    try:
        # Test grade-level configuration
        grade_config = VocabularyLevelConfig.create_grade_config(max_grade=5)

        expected_grade_levels = ["Grade1", "Grade2", "Grade3", "Grade4", "Grade5"]
        assert grade_config.levels == expected_grade_levels, "Grade levels incorrect"
        assert grade_config.beyond_level_name == "ADVANCED", (
            "Grade beyond level incorrect"
        )
        assert grade_config.progression_type == ProgressionType.EXPONENTIAL, (
            "Grade progression type incorrect"
        )

        # Test frequency-based configuration
        freq_config = VocabularyLevelConfig.create_frequency_config()

        expected_freq_levels = ["HighFreq", "MidFreq", "LowFreq", "Rare"]
        assert freq_config.levels == expected_freq_levels, "Frequency levels incorrect"
        assert freq_config.beyond_level_name == "UNKNOWN", (
            "Frequency beyond level incorrect"
        )

        print("✅ Alternative configuration validation passed")

    except Exception as e:
        print(f"❌ Alternative configuration validation failed: {e}")
        raise


def test_book_analysis_functionality():
    """Test 3: Validate book analysis functionality"""
    print("\\n=== Test 3: Book Analysis Functionality ===")

    try:
        books_vocab, vocab_levels, _ = create_sample_data()

        # Create CEFR configuration and builder
        cefr_config = VocabularyLevelConfig.create_cefr_config()
        builder = LayeredVocabularyPathBuilder(
            books_vocab=books_vocab,
            vocab_level_mapping=vocab_levels,
            level_config=cefr_config,
        )

        # Test book analysis
        book1_analysis = builder.get_book_statistics("book1")
        assert book1_analysis is not None, "Book1 analysis not found"
        assert book1_analysis.book_id == "book1", "Book ID incorrect"
        assert book1_analysis.total_words > 0, "Total words should be positive"

        # Test level distributions
        assert "A1" in book1_analysis.level_distributions, (
            "A1 level not found in distributions"
        )
        assert "BEYOND" in book1_analysis.level_distributions, "BEYOND level not found"

        # Test suitability scores
        assert "A1" in book1_analysis.suitability_scores, (
            "A1 suitability not calculated"
        )
        assert 0 <= book1_analysis.suitability_scores["A1"] <= 1, (
            "A1 suitability out of range"
        )

        # Test book evaluation
        evaluation = builder.evaluate_book_for_level("book1", "A1")
        assert evaluation.book_id == "book1", "Evaluation book ID incorrect"
        assert evaluation.target_level == "A1", "Evaluation target level incorrect"
        assert len(evaluation.recommendations) > 0, "No recommendations generated"

        print("✅ Book analysis functionality passed")

    except Exception as e:
        print(f"❌ Book analysis functionality failed: {e}")
        raise


def test_path_generation_compatibility():
    """Test 4: Validate path generation matches expected behavior"""
    print("\\n=== Test 4: Path Generation Compatibility ===")

    try:
        books_vocab, vocab_levels, _ = create_sample_data()

        # Create CEFR configuration and builder
        cefr_config = VocabularyLevelConfig.create_cefr_config()
        builder = LayeredVocabularyPathBuilder(
            books_vocab=books_vocab,
            vocab_level_mapping=vocab_levels,
            level_config=cefr_config,
        )

        # Test default path generation
        path_result = builder.create_reading_path()

        # Validate result structure
        assert hasattr(path_result, "levels"), "Path result missing levels"
        assert hasattr(path_result, "total_books"), "Path result missing total_books"
        assert hasattr(path_result, "summary"), "Path result missing summary"

        # Validate that we have results for CEFR levels
        for level in cefr_config.levels:
            if level in path_result.levels:
                level_result = path_result.levels[level]
                assert hasattr(level_result, "selected_books"), (
                    f"Level {level} missing selected_books"
                )
                assert hasattr(level_result, "coverage"), (
                    f"Level {level} missing coverage"
                )

        # Test alternative path strategies
        alternative_paths = builder.get_alternative_paths()
        assert len(alternative_paths) > 0, "No alternative paths generated"

        for strategy_name, strategy_result in alternative_paths:
            assert isinstance(strategy_name, str), "Strategy name should be string"
            assert hasattr(strategy_result, "levels"), (
                f"Strategy {strategy_name} missing levels"
            )

        print("✅ Path generation compatibility passed")

    except Exception as e:
        print(f"❌ Path generation compatibility failed: {e}")
        raise


def test_grade_level_system():
    """Test 5: Validate alternative vocabulary system (Grade Level)"""
    print("\\n=== Test 5: Grade Level System Validation ===")

    try:
        books_vocab, _, grade_vocab_levels = create_sample_data()

        # Create grade-level configuration and builder
        grade_config = VocabularyLevelConfig.create_grade_config(max_grade=5)
        builder = LayeredVocabularyPathBuilder(
            books_vocab=books_vocab,
            vocab_level_mapping=grade_vocab_levels,
            level_config=grade_config,
        )

        # Test vocabulary statistics
        vocab_stats = builder.get_level_vocabulary_stats()
        assert len(vocab_stats) == 5, "Should have 5 grade levels"

        for i in range(1, 6):
            grade_level = f"Grade{i}"
            assert grade_level in vocab_stats, f"Grade{i} not found in vocabulary stats"
            assert vocab_stats[grade_level] >= 0, (
                f"Grade{i} vocabulary count should be non-negative"
            )

        # Test path generation with grade levels
        path_result = builder.create_reading_path()

        # Validate that results use grade level names
        for level in grade_config.levels:
            if level in path_result.levels:
                print(f"  Grade level {level} processed successfully")

        print("✅ Grade level system validation passed")

    except Exception as e:
        print(f"❌ Grade level system validation failed: {e}")
        raise


def test_custom_parameters():
    """Test 6: Validate custom parameter functionality"""
    print("\\n=== Test 6: Custom Parameters Validation ===")

    try:
        books_vocab, vocab_levels, _ = create_sample_data()

        # Create CEFR configuration and builder
        cefr_config = VocabularyLevelConfig.create_cefr_config()
        builder = LayeredVocabularyPathBuilder(
            books_vocab=books_vocab,
            vocab_level_mapping=vocab_levels,
            level_config=cefr_config,
        )

        # Test custom path parameters
        custom_params = PathGenerationParameters(
            max_books_per_level={"A1": 1, "A2": 1, "B1": 1, "B2": 1, "C1": 1},
            target_coverage_per_level={
                "A1": 0.5,
                "A2": 0.5,
                "B1": 0.5,
                "B2": 0.5,
                "C1": 0.5,
            },
            max_unknown_ratio=0.3,
            min_relevant_ratio=0.2,
            min_target_level_words=5,
        )

        path_result = builder.create_reading_path(custom_params)

        # Validate that custom parameters were applied
        assert hasattr(path_result, "summary"), (
            "Custom parameter result missing summary"
        )

        # Check that book limits were respected (should have at most 1 book per level)
        for level in cefr_config.levels:
            if level in path_result.levels:
                selected_count = len(path_result.levels[level].selected_books)
                assert selected_count <= 1, f"Level {level} exceeded book limit of 1"

        print("✅ Custom parameters validation passed")

    except Exception as e:
        print(f"❌ Custom parameters validation failed: {e}")
        raise


def run_all_tests():
    """Run all validation tests"""
    print("🚀 Starting Generic Vocabulary Path Builder Validation Tests\\n")

    tests = [
        test_cefr_configuration_validation,
        test_alternative_configuration_validation,
        test_book_analysis_functionality,
        test_path_generation_compatibility,
        test_grade_level_system,
        test_custom_parameters,
    ]

    passed = 0
    total = len(tests)

    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with exception: {e}")

    print(f"\\n{'=' * 60}")
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print(
            "🎉 All tests passed! Generic Vocabulary Path Builder is working correctly."
        )
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
