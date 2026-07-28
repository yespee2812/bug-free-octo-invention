"""Render a self-explanatory dependency-graph SVG from real demo engine output.

Runs the ScriptLens structure engine on the five-scene action demo and draws the
actual scene dependency graph it produces: connected scenes, the real weighted
links between them, and the hard-orphan scene that connects to nothing. The
output is a static SVG suitable for the landing page.

Semantic (E) scoring is disabled so the diagram reflects the deterministic
character / location / prop linkage core, which is fully reproducible.
"""

from __future__ import annotations

import os

os.environ.setdefault("OSD_DISABLE_SEMANTIC", "1")

import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from orphan_graph_export import build_orphan_graph_view_payload  # noqa: E402
from orphan_scene_detector import attach_orphan_graph  # noqa: E402
from scene_dependency import SceneDependencyEngine  # noqa: E402

DEMO_SCRIPT = _REPO_ROOT / "docs/demo_scripts/action_5scene_simulate_demo.fountain"
OUTPUT_PATH = _REPO_ROOT / "landing/dependency_graph.svg"

CANVAS_WIDTH = 960
CANVAS_HEIGHT = 620
NODE_WIDTH = 184
NODE_HEIGHT = 64

# Fixed positions (scene number -> centre x, y) tuned for the 5-scene demo so the
# connected chain reads left-to-right and the orphan sits visibly apart.
POSITIONS: dict[int, tuple[int, int]] = {
    1: (160, 372),
    2: (452, 132),
    3: (452, 372),
    4: (760, 288),
    5: (760, 456),
}

# Gold / black theme, matching the landing page palette.
COLOR_BG = "#0d0d0d"
COLOR_INK = "#f3ead3"  # ivory text
COLOR_ACCENT = "#d4af37"  # gold: scene labels, setup/payoff tags
COLOR_GOLD_BORDER = "#d4af37"
COLOR_TITLE = "#f0d77b"  # bright gold
COLOR_NODE_FILL = "#151515"
COLOR_EDGE = "#b2933a"  # dim gold links
COLOR_ORPHAN = "#c67b3c"  # tarnished copper: the odd one out
COLOR_ORPHAN_FILL = "#1a1206"
COLOR_MUTED = "#9a927d"  # muted ivory


def short_location(heading: str) -> str:
    """Reduce a slugline to a short, human-readable location label.

    Args:
        heading: Full scene heading, e.g. ``INT. ABANDONED WAREHOUSE - NIGHT``.

    Returns:
        A title-cased location fragment, e.g. ``Abandoned Warehouse``.
    """
    text = heading
    for prefix in ("INT./EXT.", "INT/EXT", "INT.", "EXT.", "INT", "EXT"):
        if text.upper().startswith(prefix):
            text = text[len(prefix):]
            break
    text = text.split(" - ")[0].strip(" .-")
    return text.title()


def load_graph_payload() -> dict[str, Any]:
    """Run the engine on the demo script and return the orphan-graph payload.

    Returns:
        Payload dict with ``nodes``, ``edges``, and ``stats`` keys.

    Raises:
        FileNotFoundError: When the demo script is missing.
    """
    if not DEMO_SCRIPT.is_file():
        raise FileNotFoundError(f"Demo script not found: {DEMO_SCRIPT}")
    text = DEMO_SCRIPT.read_text(encoding="utf-8")
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(text)
    attach_orphan_graph(engine, scenes)
    orphan_records = [
        {"scene_id": scene_id, "orphan_type": "hard"}
        for scene_id in engine.get_orphan_scenes()
    ]
    return build_orphan_graph_view_payload(engine, orphan_records)


def _anchor(scene_number: int, side: str) -> tuple[int, int]:
    """Return an anchor point on a node's bounding box.

    Args:
        scene_number: Scene whose node to anchor on.
        side: One of ``left``, ``right``, ``top``, ``bottom``.

    Returns:
        The (x, y) coordinate of the requested edge midpoint.
    """
    cx, cy = POSITIONS[scene_number]
    half_w = NODE_WIDTH // 2
    half_h = NODE_HEIGHT // 2
    if side == "left":
        return cx - half_w, cy
    if side == "right":
        return cx + half_w, cy
    if side == "top":
        return cx, cy - half_h
    return cx, cy + half_h


def _stroke_width(weight: float) -> float:
    """Map an edge weight to a visible stroke width.

    Args:
        weight: Engine link weight (roughly 0.2 - 0.5 in the demo).

    Returns:
        Stroke width in SVG user units.
    """
    return round(1.6 + weight * 6.5, 2)


def _edge_path(from_scene: int, to_scene: int) -> str:
    """Build the SVG path data for one directed dependency edge.

    Args:
        from_scene: Source scene number.
        to_scene: Target scene number.

    Returns:
        SVG ``d`` attribute string routing the arrow cleanly.
    """
    routes = {
        (1, 3): "M {0},{1} L {2},{3}",
        (3, 4): "M {0},{1} L {2},{3}",
        (3, 5): "M {0},{1} L {2},{3}",
    }
    if (from_scene, to_scene) == (1, 5):
        sx, sy = _anchor(1, "bottom")
        ex, ey = _anchor(5, "left")
        return f"M {sx},{sy} C 320,560 540,540 {ex},{ey}"
    if (from_scene, to_scene) == (1, 4):
        sx, sy = _anchor(1, "right")
        ex, ey = _anchor(4, "left")
        return f"M {sx},{sy - 12} C 430,306 560,300 {ex},{ey}"
    template = routes[(from_scene, to_scene)]
    sx, sy = _anchor(from_scene, "right")
    ex, ey = _anchor(to_scene, "left")
    return template.format(sx, sy, ex, ey)


def _scene_number_for(scene_id: str, nodes: list[dict[str, Any]]) -> int:
    """Look up a scene number from its id.

    Args:
        scene_id: Engine scene id, e.g. ``scene_003``.
        nodes: Node payload list.

    Returns:
        The 1-based scene number.
    """
    for node in nodes:
        if node["scene_id"] == scene_id:
            return int(node["scene_number"])
    raise KeyError(scene_id)


def _node_svg(node: dict[str, Any]) -> str:
    """Render one scene node (rounded box + labels) as SVG.

    Args:
        node: Node payload dict.

    Returns:
        SVG fragment for the node.
    """
    number = int(node["scene_number"])
    cx, cy = POSITIONS[number]
    x = cx - NODE_WIDTH // 2
    y = cy - NODE_HEIGHT // 2
    is_orphan = bool(node["is_orphan"])
    border = COLOR_ORPHAN if is_orphan else COLOR_GOLD_BORDER
    fill = COLOR_ORPHAN_FILL if is_orphan else COLOR_NODE_FILL
    label = short_location(str(node["heading"]))
    num_color = COLOR_ORPHAN if is_orphan else COLOR_ACCENT
    dash = ' stroke-dasharray="7 5"' if is_orphan else ""
    group_open = '<g opacity="0.9">' if is_orphan else "<g>"
    return (
        f'{group_open}'
        f'<rect x="{x}" y="{y}" width="{NODE_WIDTH}" height="{NODE_HEIGHT}" rx="12" '
        f'fill="{fill}" stroke="{border}" stroke-width="2"{dash}/>'
        f'<text x="{x + 16}" y="{cy - 6}" font-size="13" font-weight="700" '
        f'fill="{num_color}" font-family="Verdana, sans-serif">SCENE {number}</text>'
        f'<text x="{x + 16}" y="{cy + 16}" font-size="14" fill="{COLOR_INK}" '
        f'font-family="Georgia, serif">{label}</text>'
        f'</g>'
    )


def _edge_svg(from_scene: int, to_scene: int, weight: float) -> str:
    """Render one dependency edge with a weight label as SVG.

    Args:
        from_scene: Source scene number.
        to_scene: Target scene number.
        weight: Engine link weight.

    Returns:
        SVG fragment for the edge and its label.
    """
    path = _edge_path(from_scene, to_scene)
    skip = abs(to_scene - from_scene) > 1
    dash = ' stroke-dasharray="6 5"' if skip else ""
    width = _stroke_width(weight)
    label_pos = {
        (1, 3): (300, 362),
        (3, 4): (588, 320),
        (3, 5): (588, 424),
        (1, 5): (405, 548),
        (1, 4): (515, 312),
    }[(from_scene, to_scene)]
    lx, ly = label_pos
    return (
        f'<path d="{path}" fill="none" stroke="{COLOR_EDGE}" stroke-width="{width}"'
        f'{dash} marker-end="url(#arrow)"/>'
        f'<text x="{lx}" y="{ly}" font-size="11" fill="{COLOR_MUTED}" '
        f'font-family="Verdana, sans-serif">{weight:.2f}</text>'
    )


def render_svg(payload: dict[str, Any]) -> str:
    """Render the full dependency-graph SVG document from a graph payload.

    Args:
        payload: Orphan-graph payload with nodes, edges, and stats.

    Returns:
        A complete SVG document string.
    """
    nodes: list[dict[str, Any]] = payload["nodes"]
    edges: list[dict[str, Any]] = payload["edges"]
    stats: dict[str, Any] = payload["stats"]

    edge_fragments = [
        _edge_svg(
            _scene_number_for(edge["from_scene_id"], nodes),
            _scene_number_for(edge["to_scene_id"], nodes),
            float(edge["weight"]),
        )
        for edge in edges
    ]
    node_fragments = [_node_svg(node) for node in nodes]

    orphan_callout = (
        '<line x1="544" y1="132" x2="612" y2="132" stroke="%s" stroke-width="1.5" '
        'stroke-dasharray="4 4"/>'
        '<text x="620" y="122" font-size="13" font-weight="700" fill="%s" '
        'font-family="Verdana, sans-serif">Orphan scene</text>'
        '<text x="620" y="142" font-size="12" fill="%s" font-family="Verdana, sans-serif">'
        '0 links in, 0 links out</text>'
        '<text x="620" y="160" font-size="12" fill="%s" font-family="Verdana, sans-serif">'
        'nothing sets it up; nothing needs it</text>'
    ) % (COLOR_ORPHAN, COLOR_ORPHAN, COLOR_MUTED, COLOR_MUTED)

    setup_tag = (
        '<text x="160" y="330" font-size="11" font-weight="700" fill="%s" '
        'text-anchor="middle" font-family="Verdana, sans-serif">SETUP - briefcase introduced</text>'
    ) % COLOR_ACCENT
    payoff_tag = (
        '<text x="760" y="506" font-size="11" font-weight="700" fill="%s" '
        'text-anchor="middle" font-family="Verdana, sans-serif">PAYOFF - the handoff</text>'
    ) % COLOR_ACCENT

    legend = (
        f'<g font-family="Verdana, sans-serif">'
        f'<rect x="40" y="566" width="22" height="16" rx="4" fill="{COLOR_NODE_FILL}" '
        f'stroke="{COLOR_GOLD_BORDER}" stroke-width="2"/>'
        f'<text x="70" y="579" font-size="12" fill="{COLOR_INK}">Connected scene</text>'
        f'<rect x="214" y="566" width="22" height="16" rx="4" fill="{COLOR_ORPHAN_FILL}" '
        f'stroke="{COLOR_ORPHAN}" stroke-width="2" stroke-dasharray="4 3"/>'
        f'<text x="244" y="579" font-size="12" fill="{COLOR_INK}">Orphan scene</text>'
        f'<line x1="372" y1="574" x2="410" y2="574" stroke="{COLOR_EDGE}" stroke-width="3" '
        f'marker-end="url(#arrow)"/>'
        f'<text x="420" y="579" font-size="12" fill="{COLOR_INK}">'
        f'Dependency (shared characters / objects) - thicker = stronger</text>'
        f'</g>'
    )

    header = (
        f'<text x="40" y="46" font-size="22" font-weight="700" fill="{COLOR_TITLE}" '
        f'font-family="Georgia, serif">How ScriptLens reads a script</text>'
        f'<text x="40" y="70" font-size="13" fill="{COLOR_MUTED}" '
        f'font-family="Verdana, sans-serif">Real output for the demo script "DOCKS RUN" '
        f'({stats["scene_count"]} scenes). Every arrow is a structural link the engine '
        f'actually found.</text>'
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_WIDTH}" '
        f'height="{CANVAS_HEIGHT}" viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}" '
        f'role="img" aria-label="ScriptLens dependency graph for the demo script">'
        f'<defs>'
        f'<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        f'markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{COLOR_EDGE}"/>'
        f'</marker>'
        f'</defs>'
        f'<rect width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" fill="{COLOR_BG}"/>'
        f'{header}'
        f'{"".join(edge_fragments)}'
        f'{setup_tag}{payoff_tag}'
        f'{"".join(node_fragments)}'
        f'{orphan_callout}'
        f'{legend}'
        f'</svg>'
    )


def build_svg() -> Path:
    """Generate the dependency-graph SVG and write it to the landing folder.

    Returns:
        The resolved path to the written SVG file.
    """
    payload = load_graph_payload()
    svg = render_svg(payload)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(svg, encoding="utf-8")
    return OUTPUT_PATH.resolve()


def main() -> None:
    """Write the dependency-graph SVG for the landing page."""
    written = build_svg()
    print(f"Wrote SVG: {written}")


if __name__ == "__main__":
    main()
