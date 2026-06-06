"""Benchmark ScriptLens core engines: parse, graph, contradiction, combined."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from statistics import median
from typing import Callable

from plot_contradiction import ContradictionEngine
from scene_dependency import SceneDependencyEngine
from scriptlens_analyser import analyze_screenplay


def _percentile(sorted_values: list[float], pct: float) -> float:
    """Return the given percentile from a sorted list of floats."""
    if not sorted_values:
        return 0.0
    index = int(round((pct / 100.0) * (len(sorted_values) - 1)))
    return sorted_values[max(0, min(index, len(sorted_values) - 1))]


def _bench_ms(fn: Callable[[], None], runs: int) -> dict[str, float]:
    """Run fn multiple times and return min, p50, p95, max in milliseconds."""
    samples: list[float] = []
    for _ in range(runs):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000.0)
    samples.sort()
    return {
        "min": round(samples[0], 2),
        "p50": round(median(samples), 2),
        "p95": round(_percentile(samples, 95), 2),
        "max": round(samples[-1], 2),
    }


def _load_fixture(name: str) -> str:
    """Load a built-in screenplay fixture by name."""
    if name == "sample":
        from test_screenplay import SAMPLE_SCREENPLAY

        return SAMPLE_SCREENPLAY
    if name == "contradiction":
        from test_contradiction_screenplay import CONTRADICTION_SCREENPLAY

        return CONTRADICTION_SCREENPLAY
    if name == "real":
        from real_screenplay_test import REAL_SCREENPLAY

        return REAL_SCREENPLAY
    raise ValueError(f"Unknown fixture: {name}")


def benchmark_screenplay(
    label: str,
    screenplay_text: str,
    runs: int,
    cold: bool,
) -> None:
    """Print timing breakdown for one screenplay."""
    scene_count = 0
    warm_dep: SceneDependencyEngine | None = None
    warm_con: ContradictionEngine | None = None

    parse_times: list[float] = []
    graph_times: list[float] = []
    delete_times: list[float] = []
    facts_times: list[float] = []
    tier1_times: list[float] = []
    tier2_times: list[float] = []
    full_times: list[float] = []

    for _ in range(runs):
        if cold or warm_dep is None:
            dep_engine = SceneDependencyEngine()
            con_engine = ContradictionEngine()
            if not cold:
                warm_dep = dep_engine
                warm_con = con_engine
        else:
            dep_engine = warm_dep
            con_engine = warm_con

        t0 = time.perf_counter()
        scenes = dep_engine.parse_fountain_text(screenplay_text)
        parse_times.append((time.perf_counter() - t0) * 1000.0)
        scene_count = len(scenes)

        t0 = time.perf_counter()
        dep_engine.build_graph(scenes)
        graph_times.append((time.perf_counter() - t0) * 1000.0)

        mid = scenes[len(scenes) // 2].scene_id if scenes else "scene_001"
        t0 = time.perf_counter()
        dep_engine.get_delete_impact(mid)
        delete_times.append((time.perf_counter() - t0) * 1000.0)

        t0 = time.perf_counter()
        store = con_engine.extract_facts(scenes)
        facts_times.append((time.perf_counter() - t0) * 1000.0)

        t0 = time.perf_counter()
        tier1 = con_engine.run_tier1(store, scenes)
        tier1_times.append((time.perf_counter() - t0) * 1000.0)

        t0 = time.perf_counter()
        con_engine.run_tier2(store, scenes, tier1)
        tier2_times.append((time.perf_counter() - t0) * 1000.0)

        t0 = time.perf_counter()
        analyze_screenplay(screenplay_text)
        full_times.append((time.perf_counter() - t0) * 1000.0)

    def stats(values: list[float]) -> dict[str, float]:
        values_sorted = sorted(values)
        return {
            "p50": round(median(values_sorted), 2),
            "p95": round(_percentile(values_sorted, 95), 2),
        }

    print()
    print("=" * 72)
    print(f"BENCHMARK: {label}  ({scene_count} scenes, {len(screenplay_text)} chars)")
    print(f"  runs={runs}  mode={'cold' if cold else 'warm'}")
    print("=" * 72)
    rows = [
        ("parse_fountain_text", stats(parse_times)),
        ("build_graph", stats(graph_times)),
        ("get_delete_impact", stats(delete_times)),
        ("extract_facts", stats(facts_times)),
        ("run_tier1", stats(tier1_times)),
        ("run_tier2", stats(tier2_times)),
        ("analyze_screenplay (full)", stats(full_times)),
    ]
    for name, timing in rows:
        print(f"  {name:28} p50={timing['p50']:8.2f} ms  p95={timing['p95']:8.2f} ms")


def main() -> None:
    """CLI entry point for engine benchmarks."""
    parser = argparse.ArgumentParser(description="Benchmark ScriptLens core engines.")
    parser.add_argument(
        "--fixture",
        choices=["sample", "contradiction", "real", "all"],
        help="Built-in screenplay fixture.",
    )
    parser.add_argument(
        "--path",
        type=Path,
        help="Path to a .fountain or .txt screenplay file.",
    )
    parser.add_argument("--runs", type=int, default=10, help="Iterations per stage.")
    parser.add_argument(
        "--cold",
        action="store_true",
        help="Create new engine instances each iteration (default).",
    )
    parser.add_argument(
        "--warm",
        action="store_true",
        help="Reuse engine instances across iterations within a fixture.",
    )
    args = parser.parse_args()
    cold = not args.warm

    if args.path:
        text = args.path.read_text(encoding="utf-8")
        benchmark_screenplay(args.path.name, text, args.runs, cold)
        return

    fixtures = (
        ["sample", "contradiction", "real"]
        if args.fixture == "all"
        else [args.fixture or "real"]
    )
    for fixture_name in fixtures:
        benchmark_screenplay(
            fixture_name,
            _load_fixture(fixture_name),
            args.runs,
            cold,
        )


if __name__ == "__main__":
    main()
