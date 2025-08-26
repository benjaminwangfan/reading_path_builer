from collections import defaultdict
from typing import Dict, List, Set, Tuple

import numpy as np

"""
📚 LayeredCEFRBookSelector - 渐进式英语阅读路径生成器

核心设计思想：
1. 输入：书籍词汇表 + A1~C1 学习词表
2. 书中不在学习词表中的词 → 全部视为超纲词（unknown_words）
3. 难度评估时，分母包含所有词汇（含 B2/C1 和 unknown）
4. 新增“适合度分析”，解释为何某本书适合某个等级
"""


class LayeredCEFRBookSelector:
    def __init__(self, books_vocab: Dict[str, Set[str]], vocab_levels: Dict[str, str]):
        """
        算法初始化

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

    def _group_vocab_by_level(self) -> Dict[str, Set[str]]:
        """
        仅对 vocab_levels 中的词按等级分组
        注意：不包含书中出现但未在 vocab_levels 中定义的词
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

    def _calculate_layered_book_stats(self) -> Dict[str, Dict]:
        """
        统计每本书的多维特征

        关键逻辑：
        - unknown_words = 书中词汇 - vocab_levels.keys()（完全未定义的词）
        - 所有比例计算基于总词汇数（含 B2/C1 和 unknown）
        - 新增 suitability_for[level]：评估该书对某等级的适合度
        """
        stats = {}

        # 构建所有已知学习词汇的集合（用于识别 unknown）
        known_learning_words = set(self.vocab_levels.keys())

        for book_id, vocab in self.books_vocab.items():
            book_stats = {
                "total_words": len(vocab),
                "level_words": {},
                "level_counts": {},
                "level_ratios": {},
                "unknown_words": set(),  # 超纲词 = 未在学习词表中定义的词
                "difficulty_score": 0,
                "learning_value": 0,
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

            # 学习相关词汇占比（用于筛选）
            book_stats["learning_words_ratio"] = (
                learning_words_count / len(vocab) if vocab else 0
            )

            # 🌟 新增：计算该书对每个等级的“适合度”
            # 适合度 = (目标等级及以下词汇) / 总词汇数
            # 分母包含：A1~C1 + unknown（完全符合你的构想）
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
        if book_id not in self.book_stats:
            return {"error": f"书籍 {book_id} 不存在"}

        stats = self.book_stats[book_id]

        result = {
            "book_id": book_id,
            "total_words": stats["total_words"],
            "level_breakdown": {},
            "difficulty_analysis": {},
            "recommendations": [],
        }

        # 词汇分级统计
        for level in self.all_levels:
            if level == "BEYOND":
                count = stats["unknown_count"]
                ratio = stats["unknown_ratio"]
            else:
                count = stats["level_counts"].get(level, 0)
                ratio = stats["level_ratios"].get(level, 0)
            result["level_breakdown"][level] = {
                "count": count,
                "ratio": ratio,
                "percentage": f"{ratio:.1%}",
            }

        # 难度分析
        result["difficulty_analysis"] = {
            "overall_difficulty_score": round(stats["difficulty_score"], 2),
            "learning_value_score": round(stats["learning_value"], 2),
            "unknown_ratio": stats["unknown_ratio"],
            "suitability_for": {
                lvl: round(ratio, 3) for lvl, ratio in stats["suitability_for"].items()
            },
        }

        # 推荐建议
        best_level = max(stats["suitability_for"].items(), key=lambda x: x[1])
        result["recommendations"].append(
            f"最适合 {best_level[0]} 级别学习者（适合度：{best_level[1]:.1%}）"
        )

        if stats["unknown_ratio"] > 0.2:
            result["recommendations"].append("超纲词较多，建议搭配词典使用")

        if stats["learning_value"] > 1.0:
            result["recommendations"].append("学习价值较高，推荐精读")

        return result

    def create_progressive_reading_path(
        self,
        max_books_per_level: Dict[str, int] | None = None,
        target_coverage_per_level: Dict[str, float] | None = None,
        max_unknown_ratio: float = 0.15,
        min_relevant_ratio: float = 0.4,
        min_target_level_words: int = 50,
    ) -> Dict:
        """生成渐进式学习路径"""
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

        reading_path = {
            "levels": {},
            "total_books": [],
            "cumulative_coverage": {},
        }

        cumulative_covered = set()
        already_selected_books = set()  # ✅ 新增：全局记录已选书籍

        for level in self.learning_levels:
            print(f"\n=== 选择 {level} 等级书籍 ===")

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

            print(f"完成 {level} 后累积覆盖率:")
            for lvl in self.learning_levels:
                ratio = cumulative_stats[lvl]["ratio"]
                print(f"  {lvl}: {ratio:.1%}")

        reading_path["summary"] = self._generate_path_summary(reading_path)
        return reading_path

    def _filter_books_for_level(
        self,
        level: str,
        max_unknown_ratio: float = 0.15,
        min_relevant_ratio: float = 0.4,
        min_target_level_words: int = 50,
    ) -> List[str]:
        """筛选候选书籍"""
        candidates = []
        level_idx = self.learning_levels.index(level)

        for book_id, stats in self.book_stats.items():
            if stats["unknown_ratio"] > max_unknown_ratio:
                continue

            # 使用 suitability_for 作为相关性指标（更直观）
            if stats["suitability_for"][level] < min_relevant_ratio:
                continue

            if stats["level_counts"][level] >= min_target_level_words:
                candidates.append(book_id)

        candidates.sort(
            key=lambda x: self.book_stats[x]["learning_value"], reverse=True
        )
        print(f"  {level}等级候选书籍: {len(candidates)}本")
        return candidates

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
        """贪心选择书籍"""
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

        selected_books = []
        target_vocab = self.level_vocab[level]
        remaining_words = target_vocab - already_covered
        newly_covered = set()

        print(
            f"目标词汇: {len(target_vocab)}, 已覆盖: {len(already_covered & target_vocab)}, 待覆盖: {len(remaining_words)}"
        )

        iteration = 0
        while (
            len(selected_books) < max_books
            and len(newly_covered) / len(target_vocab) < target_coverage
            and remaining_words
        ):
            iteration += 1
            best_book = None
            best_score = -float("inf")
            for book_id in candidates:
                if book_id in selected_books:  # 防止本轮重复
                    continue
                score = self._calculate_book_score_for_level(
                    book_id, level, remaining_words, iteration
                )
                if score > best_score:
                    best_score = score
                    best_book = book_id
            if best_book is None:
                break
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

    def _calculate_book_score_for_level(
        self, book_id: str, level: str, remaining_words: Set[str], iteration: int
    ) -> float:
        """计算书籍评分"""
        stats = self.book_stats[book_id]
        new_coverage = len(stats["level_words"][level] & remaining_words)
        if new_coverage == 0:
            return -1
        score = new_coverage * 10
        level_idx = self.learning_levels.index(level)
        for i in range(level_idx):
            lower_level = self.learning_levels[i]
            score += stats["level_counts"][lower_level] * 0.5
        if level_idx < len(self.learning_levels) - 1:
            next_level = self.learning_levels[level_idx + 1]
            score += min(stats["level_counts"][next_level], 100) * 0.1
        score -= stats["unknown_count"] * 0.8
        if iteration > 2:
            coverage_bonus = (
                new_coverage / len(remaining_words) if remaining_words else 0
            )
            score += coverage_bonus * 50
        return score

    def _generate_path_summary(self, reading_path: Dict) -> Dict:
        """生成摘要"""
        total_books = len(reading_path["total_books"])
        final_level = self.learning_levels[-1]
        final_coverage = reading_path["cumulative_coverage"][final_level]

        difficulty_progression = []
        for level in self.learning_levels:
            if (
                level in reading_path["levels"]
                and reading_path["levels"][level]["selected_books"]
            ):
                books = reading_path["levels"][level]["selected_books"]
                avg_difficulty = np.mean(
                    [self.book_stats[b]["difficulty_score"] for b in books]
                )
                difficulty_progression.append((level, round(avg_difficulty, 2)))

        return {
            "total_books": total_books,
            "books_per_level": {
                level: len(
                    reading_path["levels"].get(level, {}).get("selected_books", [])
                )
                for level in self.learning_levels
            },
            "final_coverage": {
                level: final_coverage[level] for level in self.learning_levels
            },
            "difficulty_progression": difficulty_progression,
            "recommended_order": reading_path["total_books"],
        }

    def print_reading_path(self, path_result: Dict, path_name: str = ""):
        """格式化输出学习路径"""
        print(f"\n{'=' * 50}")
        print(f"📚 {path_name}阅读路径")
        print(f"{'=' * 50}")

        summary = path_result["summary"]
        print(f"总书籍数: {summary['total_books']}")
        print(f"各等级分布: {summary['books_per_level']}")

        print("\n📈 学习等级覆盖率:")
        for level in self.learning_levels:
            cov = summary["final_coverage"][level]
            print(f"  {level}: {cov['covered']}/{cov['total']} ({cov['ratio']:.1%})")
        print("  BEYOND: N/A (非学习目标，仅供参考)")

        print("\n📖 推荐阅读顺序:")
        current_level = None
        for i, book in enumerate(summary["recommended_order"], 1):
            book_level = None
            for level in self.learning_levels:
                if (
                    level in path_result["levels"]
                    and book in path_result["levels"][level]["selected_books"]
                ):
                    book_level = level
                    break
            if book_level != current_level:
                print(f"\n  === {book_level} 等级 ===")
                current_level = book_level
            stats = self.book_stats[book]
            print(f"  {i:2d}. {book}")
            print(
                f"      目标词汇: {stats['level_counts'][book_level]}, "
                f"超纲词: {stats['unknown_count']}, "
                f"难度: {stats['difficulty_score']:.1f}"
            )

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
