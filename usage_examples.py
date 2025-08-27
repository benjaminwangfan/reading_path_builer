#!/usr/bin/env python3
"""
Usage Examples for Generic Vocabulary Path Builder

Key examples demonstrating the flexibility of the new system.
"""

from generic_vocabulary_path_builder import (
    LayeredVocabularyPathBuilder,
    PathGenerationParameters,
    ProgressionType,
    VocabularyLevelConfig,
)


def create_sample_data():
    """Create sample data for examples"""
    books_vocab = {
        "elementary": {"the", "cat", "dog", "run", "play", "happy", "book", "read"},
        "intermediate": {
            "adventure",
            "discover",
            "mystery",
            "solve",
            "courage",
            "challenge",
        },
        "advanced": {
            "theoretical",
            "framework",
            "methodology",
            "analysis",
            "synthesis",
        },
    }

    cefr_vocab = {
        "the": "A1",
        "cat": "A1",
        "dog": "A1",
        "run": "A1",
        "play": "A2",
        "happy": "A2",
        "book": "A2",
        "read": "A2",
        "adventure": "B1",
        "discover": "B1",
        "mystery": "B1",
        "solve": "B1",
        "courage": "B2",
        "challenge": "B2",
        "theoretical": "C1",
        "framework": "C1",
    }

    return books_vocab, cefr_vocab


def example_1_cefr_backward_compatibility():
    """Example 1: CEFR backward compatibility"""
    print("Example 1: CEFR Backward Compatibility")
    print("=" * 40)

    books_vocab, cefr_vocab = create_sample_data()

    # Use CEFR configuration (same as original system)
    cefr_config = VocabularyLevelConfig.create_cefr_config()
    builder = LayeredVocabularyPathBuilder(
        books_vocab=books_vocab,
        vocab_level_mapping=cefr_vocab,
        level_config=cefr_config,
    )

    # Generate reading path
    path_result = builder.create_reading_path()
    builder.print_reading_path(path_result, "CEFR")

    print(f"Total books selected: {path_result.summary['total_books']}")


def example_2_grade_levels():
    """Example 2: Grade-level configuration"""
    print("\nExample 2: Grade-Level System")
    print("=" * 40)

    books_vocab, _ = create_sample_data()

    # Create grade-level vocabulary mapping
    grade_vocab = {
        "the": "Grade1",
        "cat": "Grade1",
        "dog": "Grade1",
        "run": "Grade1",
        "play": "Grade2",
        "happy": "Grade2",
        "book": "Grade2",
        "read": "Grade2",
        "adventure": "Grade3",
        "discover": "Grade3",
        "mystery": "Grade3",
    }

    # Use grade-level configuration
    grade_config = VocabularyLevelConfig.create_grade_config(max_grade=3)
    builder = LayeredVocabularyPathBuilder(
        books_vocab=books_vocab,
        vocab_level_mapping=grade_vocab,
        level_config=grade_config,
    )

    # Generate path with conservative parameters
    conservative_params = PathGenerationParameters.create_conservative_defaults(
        grade_config.levels
    )
    path_result = builder.create_reading_path(conservative_params)

    print(f"Grade system levels: {grade_config.levels}")
    print(f"Progression type: {grade_config.progression_type.value}")


def example_3_custom_configuration():
    """Example 3: Custom vocabulary system"""
    print("\nExample 3: Custom Configuration")
    print("=" * 40)

    books_vocab, _ = create_sample_data()

    # Create custom domain vocabulary
    domain_vocab = {
        "the": "Basic",
        "cat": "Basic",
        "dog": "Basic",
        "adventure": "Intermediate",
        "discover": "Intermediate",
        "theoretical": "Expert",
        "framework": "Expert",
    }

    # Custom configuration with exponential progression
    custom_config = VocabularyLevelConfig(
        levels=["Basic", "Intermediate", "Expert"],
        weights={"Basic": 2.0, "Intermediate": 1.2, "Expert": 0.8},
        progression_type=ProgressionType.EXPONENTIAL,
        beyond_level_name="SPECIALIZED",
    )

    builder = LayeredVocabularyPathBuilder(
        books_vocab=books_vocab,
        vocab_level_mapping=domain_vocab,
        level_config=custom_config,
    )

    # Custom parameters
    custom_params = PathGenerationParameters(
        max_books_per_level={"Basic": 2, "Intermediate": 2, "Expert": 1},
        target_coverage_per_level={"Basic": 0.8, "Intermediate": 0.7, "Expert": 0.6},
        max_unknown_ratio=0.3,
        min_relevant_ratio=0.3,
        min_target_level_words=5,
    )

    path_result = builder.create_reading_path(custom_params)
    print(f"Custom system: {custom_config.levels}")
    print(f"Custom weights: {custom_config.weights}")


def run_examples():
    """Run all examples"""
    print("🚀 Generic Vocabulary Path Builder - Usage Examples\n")

    try:
        example_1_cefr_backward_compatibility()
        example_2_grade_levels()
        example_3_custom_configuration()

        print("\n" + "=" * 50)
        print("✅ All examples completed successfully!")
        print("\nKey Benefits:")
        print("• Full CEFR backward compatibility")
        print("• Support for any vocabulary hierarchy")
        print("• Flexible configuration options")
        print("• Type-safe structured approach")

    except Exception as e:
        print(f"❌ Example failed: {e}")


if __name__ == "__main__":
    run_examples()
