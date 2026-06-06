"""Run Tier 1 and Tier 2 plot contradiction analysis on the test screenplay."""

from dataclasses import dataclass

from scene_dependency import SceneDependencyEngine
from plot_contradiction import Contradiction, ContradictionEngine
from test_contradiction_screenplay import (
    CLEAN_SCENES,
    CONTRADICTION_SCREENPLAY,
    EXPECTED_CONTRADICTIONS,
    EXPECTED_TIER2_CONTRADICTIONS,
    GROUND_TRUTH_CONTRADICTIONS,
)


@dataclass
class AccuracyMetrics:
    """Precision/recall metrics for contradiction detection."""

    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    matched_truth: list[tuple[str, str, str]]
    missed_truth: list[tuple[str, str, str]]
    spurious_detections: list[Contradiction]


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def contradiction_key(contradiction: Contradiction) -> tuple[str, str, str]:
    """Build a comparable key for a detected contradiction."""
    return (
        contradiction.contradiction_type,
        contradiction.scene_id_a,
        contradiction.scene_id_b,
    )


def print_contradiction(index: int, contradiction: Contradiction) -> None:
    """Print one detected contradiction in a readable format."""
    print(f"\n--- Contradiction {index} ---")
    print(f"Type:       {contradiction.contradiction_type}")
    print(f"Scenes:     {contradiction.scene_id_a} (#{contradiction.scene_number_a})")
    print(f"         -> {contradiction.scene_id_b} (#{contradiction.scene_number_b})")
    print(f"Confidence: {contradiction.confidence}")
    print(f"Tier:       {contradiction.tier}")
    print(f"Established fact ({contradiction.fact_a.fact_type}):")
    print(f"  Entity: {contradiction.fact_a.entity}")
    print(f"  Value:  {contradiction.fact_a.value}")
    print(f"  Source: {contradiction.fact_a.raw_excerpt}")
    print(f"Contradicting excerpt:")
    print(f"  {contradiction.excerpt_b}")
    print(f"Explanation:")
    print(f"  {contradiction.explanation}")


def evaluate_expected(
    detected: list[Contradiction],
    expected: list[tuple[str, str, str]],
) -> tuple[int, list[tuple[str, str, str]], list[Contradiction]]:
    """Compare detected contradictions to an expected set."""
    detected_keys = {contradiction_key(item) for item in detected}
    matched = [item for item in expected if item in detected_keys]
    unexpected = [
        item for item in detected if contradiction_key(item) not in set(expected)
    ]
    missing = [item for item in expected if item not in detected_keys]
    return len(matched), missing, unexpected


def measure_accuracy(
    ground_truth: list[tuple[str, str, str]] | None = None,
    detected: list[Contradiction] | None = None,
) -> AccuracyMetrics:
    """Run analysis and measure detection accuracy against ground truth.

    Args:
        ground_truth: Known contradictions as (type, scene_a, scene_b).
            Defaults to GROUND_TRUTH_CONTRADICTIONS from the test screenplay.
        detected: Precomputed contradictions from run_analysis. If None,
            the full pipeline is executed.

    Returns:
        AccuracyMetrics with TP/FP/FN and precision, recall, and F1.
    """
    if ground_truth is None:
        ground_truth = GROUND_TRUTH_CONTRADICTIONS

    if detected is None:
        dependency_engine = SceneDependencyEngine()
        scenes = dependency_engine.parse_fountain_text(CONTRADICTION_SCREENPLAY)
        contradiction_engine = ContradictionEngine()
        detected = contradiction_engine.run_analysis(scenes)

    truth_keys = set(ground_truth)
    detected_keys = {contradiction_key(item): item for item in detected}

    matched_truth = [entry for entry in ground_truth if entry in detected_keys]
    missed_truth = [entry for entry in ground_truth if entry not in detected_keys]
    spurious_detections = [
        item for key, item in detected_keys.items() if key not in truth_keys
    ]

    true_positives = len(matched_truth)
    false_positives = len(spurious_detections)
    false_negatives = len(missed_truth)

    precision = (
        true_positives / (true_positives + false_positives)
        if (true_positives + false_positives) > 0
        else 0.0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if (true_positives + false_negatives) > 0
        else 0.0
    )
    f1_score = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return AccuracyMetrics(
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        precision=round(precision, 2),
        recall=round(recall, 2),
        f1_score=round(f1_score, 2),
        matched_truth=matched_truth,
        missed_truth=missed_truth,
        spurious_detections=spurious_detections,
    )


def print_accuracy_report(metrics: AccuracyMetrics) -> None:
    """Print a formatted accuracy report card."""
    total_truth = (
        metrics.true_positives
        + metrics.false_negatives
    )
    print_section("ACCURACY REPORT")
    print("===============")
    print(
        f"True Positives:  {metrics.true_positives}/{total_truth} "
        "real contradictions caught"
    )
    print(f"False Positives: {metrics.false_positives} spurious flags")
    print(f"False Negatives: {metrics.false_negatives} missed contradictions")
    print(f"Precision: {metrics.precision:.2f} (we want > 0.85)")
    print(f"Recall:    {metrics.recall:.2f} (we want > 0.75)")
    print(f"F1 Score:  {metrics.f1_score:.2f} (we want > 0.80)")

    targets_met = (
        metrics.precision > 0.85
        and metrics.recall > 0.75
        and metrics.f1_score > 0.80
    )
    print()
    if targets_met:
        print("All accuracy targets met.")
    else:
        print("Below target — review details:")
        if metrics.missed_truth:
            print("\nMissed (false negatives):")
            for entry in metrics.missed_truth:
                print(f"  - {entry[0]}: {entry[1]} -> {entry[2]}")
        if metrics.spurious_detections:
            print("\nSpurious (false positives):")
            for item in metrics.spurious_detections:
                print(
                    f"  - {item.contradiction_type}: "
                    f"{item.scene_id_a} -> {item.scene_id_b} "
                    f"(tier {item.tier}, confidence {item.confidence})"
                )


def main() -> None:
    """Parse the test screenplay and print contradiction analysis results."""
    print_section("SCRIPTLENS CONTRADICTION TEST (TIER 1 + TIER 2)")
    print("Pipeline: parse_fountain_text -> run_analysis")

    dependency_engine = SceneDependencyEngine()
    scenes = dependency_engine.parse_fountain_text(CONTRADICTION_SCREENPLAY)
    print(f"\nScenes parsed: {len(scenes)}")

    contradiction_engine = ContradictionEngine()
    fact_store = contradiction_engine.extract_facts(scenes)
    tier1_results = contradiction_engine.run_tier1(fact_store, scenes)
    tier2_results = contradiction_engine.run_tier2(fact_store, scenes, tier1_results)
    contradictions = contradiction_engine.run_analysis(scenes)

    print_section("TIER 1 RESULTS")
    print(f"Tier 1 contradictions: {len(tier1_results)}")
    for index, contradiction in enumerate(tier1_results, start=1):
        print_contradiction(index, contradiction)

    print_section("TIER 2 RESULTS")
    print(f"Tier 2 contradictions: {len(tier2_results)}")
    if not tier2_results:
        print("No Tier 2 contradictions detected.")
    for index, contradiction in enumerate(tier2_results, start=1):
        print_contradiction(index, contradiction)

    print_section("COMBINED DETECTED CONTRADICTIONS")
    print(f"Total after deduplication: {len(contradictions)}")
    for index, contradiction in enumerate(contradictions, start=1):
        print_contradiction(index, contradiction)

    tier1_matched, tier1_missing, tier1_unexpected = evaluate_expected(
        tier1_results, EXPECTED_CONTRADICTIONS
    )
    tier2_matched, tier2_missing, tier2_unexpected = evaluate_expected(
        tier2_results, EXPECTED_TIER2_CONTRADICTIONS
    )

    false_positive_clean = [
        item
        for item in contradictions
        if item.scene_id_a in CLEAN_SCENES or item.scene_id_b in CLEAN_SCENES
    ]

    print_section("SUMMARY")
    print(
        f"Tier 1: {tier1_matched}/{len(EXPECTED_CONTRADICTIONS)} expected, "
        f"{len(tier1_unexpected)} unexpected"
    )
    print(
        f"Tier 2: {tier2_matched}/{len(EXPECTED_TIER2_CONTRADICTIONS)} expected, "
        f"{len(tier2_unexpected)} unexpected"
    )
    print(f"Combined total: {len(contradictions)}")
    print(f"False positives on clean scenes: {len(false_positive_clean)}")

    if tier1_missing:
        print("\nMissing Tier 1 contradictions:")
        for item in tier1_missing:
            print(f"  - {item[0]}: {item[1]} -> {item[2]}")

    if tier2_missing:
        print("\nMissing Tier 2 contradictions:")
        for item in tier2_missing:
            print(f"  - {item[0]}: {item[1]} -> {item[2]}")

    tier2_caught_warehouse = any(
        item.contradiction_type == "semantic_location"
        and {item.scene_id_a, item.scene_id_b} == {"scene_005", "scene_010"}
        for item in tier2_results
    )
    tier1_missed_warehouse = not any(
        item.scene_id_a in {"scene_005", "scene_010"}
        and item.scene_id_b in {"scene_005", "scene_010"}
        for item in tier1_results
    )

    print()
    if tier2_caught_warehouse and tier1_missed_warehouse:
        print(
            "Tier 2 check: warehouse contradiction caught (scene_005 vs scene_010) "
            "and not flagged by Tier 1 alone."
        )

    all_passed = (
        tier1_matched == len(EXPECTED_CONTRADICTIONS)
        and tier2_matched == len(EXPECTED_TIER2_CONTRADICTIONS)
        and not tier1_missing
        and not tier2_missing
        and not false_positive_clean
        and len(tier1_unexpected) == 0
        and len(tier2_unexpected) == 0
    )
    if all_passed:
        print(
            "RESULT: All Tier 1 and Tier 2 contradictions detected "
            "with 0 false positives on clean scenes."
        )
    else:
        print("RESULT: Review mismatches above.")

    print_accuracy_report(measure_accuracy(detected=contradictions))


if __name__ == "__main__":
    main()
