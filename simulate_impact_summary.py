"""Plain-English summaries for simulate cut and simulate edit impact."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from scene_dependency import SceneBlock, SceneDependencyEngine

RiskLevel = Literal["none", "low", "medium", "high"]
ImpactSeverity = Literal["direct", "indirect"]


def describe_dependency_path(
    engine: SceneDependencyEngine,
    path: list[str],
) -> tuple[str, list[str], int]:
    """Build a writer-friendly reason for one dependency path.

    Args:
        engine: Built dependency engine with edge metadata.
        path: Ordered scene ids from removed or edited scene to impacted scene.

    Returns:
        Tuple of summary reason, hop explanations, and hop count.
    """
    if len(path) < 2:
        return "", [], 0

    hop_explanations: list[str] = []
    for index in range(len(path) - 1):
        edge_data = engine.graph.get_edge_data(path[index], path[index + 1]) or {}
        explanation = str(edge_data.get("explanation", "")).strip()
        if explanation:
            hop_explanations.append(explanation)
        else:
            hop_explanations.append(
                f"Scene {path[index]} links forward to Scene {path[index + 1]}"
            )

    hop_count = len(path) - 1
    if hop_count == 1:
        reason = f"Depends directly on this beat: {hop_explanations[0]}"
    else:
        reason = (
            f"Depends on this beat through {hop_count - 1} intermediate scene(s). "
            f"First link: {hop_explanations[0]}"
        )
    return reason, hop_explanations, hop_count


def _impact_severity(path: list[str]) -> ImpactSeverity:
    """Return direct when the removed scene feeds the impacted scene in one hop."""
    if len(path) == 2:
        return "direct"
    return "indirect"


def enrich_cut_impact_scenes(
    engine: SceneDependencyEngine,
    impacted_scenes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Add plain-English impact fields to simulate-cut rows.

    Args:
        engine: Built dependency engine with edge metadata.
        impacted_scenes: Raw rows from ``get_delete_impact``.

    Returns:
        Enriched impact rows sorted by total weight descending.
    """
    enriched: list[dict[str, Any]] = []
    for record in impacted_scenes:
        path = list(record["dependency_path"])
        impact_reason, hop_explanations, link_hops = describe_dependency_path(
            engine,
            path,
        )
        enriched.append(
            {
                **record,
                "impact_reason": impact_reason,
                "hop_explanations": hop_explanations,
                "link_hops": link_hops,
                "severity": _impact_severity(path),
            }
        )
    return enriched


def merge_cut_impact_rows(
    graph_rows: list[dict[str, Any]],
    sfi_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge continuity-graph and SFI impact rows by scene id.

    Prefers SFI impact reasons when both sources flag the same scene.

    Args:
        graph_rows: Enriched rows from continuity delete-impact.
        sfi_rows: Rows derived from scene-function losses.

    Returns:
        Deduplicated impact rows sorted by total weight descending.
    """
    merged: dict[str, dict[str, Any]] = {}
    for row in graph_rows:
        merged[row["scene_id"]] = dict(row)
    for row in sfi_rows:
        existing = merged.get(row["scene_id"])
        if existing is None:
            merged[row["scene_id"]] = dict(row)
            continue
        existing["total_weight"] = max(
            float(existing.get("total_weight", 0.0)),
            float(row.get("total_weight", 0.0)),
        )
        sfi_reason = str(row.get("impact_reason", "")).strip()
        if sfi_reason:
            existing["impact_reason"] = sfi_reason
            existing["explanation"] = sfi_reason
            existing["hop_explanations"] = list(row.get("hop_explanations", []))
            existing["severity"] = row.get("severity", existing.get("severity"))
            existing["link_hops"] = int(row.get("link_hops", existing.get("link_hops", 1)))
    return sorted(
        merged.values(),
        key=lambda item: float(item.get("total_weight", 0.0)),
        reverse=True,
    )


def summarize_cut_impact(
    removed_scene: dict[str, Any],
    impacted_scenes: list[dict[str, Any]],
    *,
    sfi_summary: str | None = None,
    sfi_risk_level: RiskLevel | None = None,
    sfi_lost_count: int = 0,
    sfi_is_bridge: bool = False,
) -> dict[str, str]:
    """Return a headline summary and risk level for simulate cut.

    When Scene Function Impact reports lost beats or a bridge scene, that
    wording wins. Otherwise falls back to continuity-graph impact counts.
    ``Safe to cut`` is reserved for terminal / no-impact cases only.

    Args:
        removed_scene: Summary metadata for the scene being removed.
        impacted_scenes: Enriched downstream impact rows.
        sfi_summary: Optional SFI headline.
        sfi_risk_level: Optional SFI risk level.
        sfi_lost_count: Number of lost story functions.
        sfi_is_bridge: Whether the cut removes a pursuit carrier beat.

    Returns:
        Dictionary with ``summary`` and ``risk_level`` keys.
    """
    scene_number = removed_scene["scene_number"]
    count = len(impacted_scenes)

    if sfi_lost_count or sfi_is_bridge:
        return {
            "summary": sfi_summary
            or (
                f"Cutting Scene {scene_number} would affect story functions "
                f"used by later scenes."
            ),
            "risk_level": sfi_risk_level or ("high" if count >= 3 else "medium"),
        }

    if count == 0:
        if sfi_summary and sfi_risk_level:
            return {
                "summary": sfi_summary,
                "risk_level": sfi_risk_level,
            }
        return {
            "summary": (
                f"Safe to cut — no later scenes depend on Scene {scene_number}."
            ),
            "risk_level": "none",
        }

    if count == 1:
        other_number = impacted_scenes[0]["scene_number"]
        return {
            "summary": (
                f"Cutting Scene {scene_number} would affect 1 later scene "
                f"(Scene {other_number})."
            ),
            "risk_level": "low",
        }

    scene_numbers = sorted(row["scene_number"] for row in impacted_scenes)
    if scene_numbers[0] == scene_numbers[-1]:
        range_label = f"Scene {scene_numbers[0]}"
    else:
        range_label = f"Scenes {scene_numbers[0]}–{scene_numbers[-1]}"

    risk_level: RiskLevel = "medium"
    if count >= 3:
        risk_level = "high"
    elif any(row.get("severity") == "indirect" for row in impacted_scenes):
        risk_level = "medium"

    return {
        "summary": (
            f"Cutting Scene {scene_number} would affect {count} later scenes "
            f"({range_label})."
        ),
        "risk_level": risk_level,
    }


def build_downstream_at_risk_records(
    edited_scene_id: str,
    edge_diff: dict[str, list[dict[str, Any]]],
    scene_lookup: dict[str, SceneBlock],
) -> list[dict[str, Any]]:
    """Build structured downstream-at-risk rows for simulate edit.

    Args:
        edited_scene_id: Scene that was rewritten in the preview.
        edge_diff: Added, removed, and changed edge records.
        scene_lookup: Map of scene id to parsed scene blocks.

    Returns:
        Sorted downstream risk records with plain-English reasons.
    """
    records: list[dict[str, Any]] = []
    for record in edge_diff.get("removed", []):
        if record["from_scene_id"] != edited_scene_id:
            continue
        target = scene_lookup.get(record["to_scene_id"])
        explanation = str(record.get("explanation", "")).strip()
        if explanation:
            reason = f"Would lose this setup: {explanation}"
        else:
            reason = "Would lose a story link created in this scene."
        records.append(
            {
                "scene_id": record["to_scene_id"],
                "scene_number": target.scene_number if target else 0,
                "heading": target.heading if target else record["to_scene_id"],
                "reason": reason,
            }
        )

    records.sort(key=lambda row: row["scene_number"])
    return records


def format_orphan_delta_message(before: int, after: int) -> str:
    """Return a plain-English orphan count change message.

    Args:
        before: Orphan count before the simulated edit.
        after: Orphan count after the simulated edit.

    Returns:
        Human-readable orphan delta sentence.
    """
    delta = after - before
    if delta == 0:
        return f"Orphan count unchanged ({before})."
    if delta > 0:
        suffix = "orphans" if delta != 1 else "orphan"
        return f"Would add {delta} new {suffix} ({before} → {after})."
    removed = -delta
    suffix = "orphans" if removed != 1 else "orphan"
    return f"Would clear {removed} {suffix} ({before} → {after})."


def summarize_edit_impact(
    edge_diff: dict[str, list[dict[str, Any]]],
    orphan_delta: dict[str, int],
    downstream_at_risk: list[dict[str, Any]],
) -> dict[str, str]:
    """Return a headline summary and risk level for simulate edit.

    Args:
        edge_diff: Added, removed, and changed edge records.
        orphan_delta: Orphan counts before and after the edit preview.
        downstream_at_risk: Structured downstream risk rows.

    Returns:
        Dictionary with ``summary`` and ``risk_level`` keys.
    """
    removed_count = len(edge_diff.get("removed", []))
    added_count = len(edge_diff.get("added", []))
    changed_count = len(edge_diff.get("changed", []))
    orphan_change = orphan_delta["after"] - orphan_delta["before"]
    risk_count = len(downstream_at_risk)

    if (
        removed_count == 0
        and added_count == 0
        and changed_count == 0
        and orphan_change == 0
        and risk_count == 0
    ):
        return {
            "summary": "Your edit does not change any story dependencies.",
            "risk_level": "none",
        }

    parts: list[str] = []
    if removed_count:
        label = "links" if removed_count != 1 else "link"
        parts.append(f"removes {removed_count} story {label}")
    if added_count:
        label = "links" if added_count != 1 else "link"
        parts.append(f"adds {added_count} new {label}")
    if changed_count:
        label = "links" if changed_count != 1 else "link"
        parts.append(f"changes {changed_count} existing {label}")
    if risk_count:
        label = "scenes" if risk_count != 1 else "scene"
        parts.append(f"puts {risk_count} later {label} at risk")
    if orphan_change > 0:
        label = "orphans" if orphan_change != 1 else "orphan"
        parts.append(f"creates {orphan_change} new {label}")
    elif orphan_change < 0:
        label = "orphans" if -orphan_change != 1 else "orphan"
        parts.append(f"clears {-orphan_change} {label}")

    summary = f"Your edit {', '.join(parts)}."

    risk_level: RiskLevel = "low"
    if risk_count and orphan_change > 0:
        risk_level = "high"
    elif risk_count or orphan_change > 0 or removed_count >= 2:
        risk_level = "medium"

    return {"summary": summary, "risk_level": risk_level}
