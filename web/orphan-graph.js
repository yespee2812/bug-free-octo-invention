/**
 * SVG orphan graph viewer for the ScriptLens structure workspace.
 */

/** @typedef {{
 *   scene_id: string,
 *   scene_number: number,
 *   heading: string,
 *   is_orphan: boolean,
 *   orphan_type?: string|null,
 *   in_degree: number,
 *   out_degree: number
 * }} OrphanGraphNode */

/** @typedef {{
 *   from_scene_id: string,
 *   to_scene_id: string,
 *   weight: number,
 *   explanation?: string,
 *   character?: number,
 *   spatial?: number,
 *   prop?: number,
 *   semantic?: number
 * }} OrphanGraphEdge */

const NODE_RADIUS = 7;
const NODE_SPACING = 34;
const BASELINE_Y = 130;
const SVG_PADDING = 24;

/**
 * Return whether a node is connected to any orphan node.
 * @param {string} sceneId
 * @param {OrphanGraphNode[]} nodes
 * @param {OrphanGraphEdge[]} edges
 * @returns {boolean}
 */
function isConnectedToOrphan(sceneId, nodes, edges) {
  const orphanIds = new Set(
    nodes.filter((node) => node.is_orphan).map((node) => node.scene_id),
  );
  if (orphanIds.has(sceneId)) {
    return true;
  }
  for (const edge of edges) {
    if (orphanIds.has(edge.from_scene_id) && edge.to_scene_id === sceneId) {
      return true;
    }
    if (orphanIds.has(edge.to_scene_id) && edge.from_scene_id === sceneId) {
      return true;
    }
  }
  return false;
}

/**
 * Build a map of scene id to x/y coordinates.
 * @param {OrphanGraphNode[]} nodes
 * @returns {Map<string, { x: number, y: number }>}
 */
function buildNodePositions(nodes) {
  /** @type {Map<string, { x: number, y: number }>} */
  const positions = new Map();
  for (const node of nodes) {
    positions.set(node.scene_id, {
      x: SVG_PADDING + (node.scene_number - 1) * NODE_SPACING,
      y: BASELINE_Y,
    });
  }
  return positions;
}

/**
 * Render the orphan graph into a container element.
 * @param {HTMLElement} container
 * @param {{ nodes: OrphanGraphNode[], edges: OrphanGraphEdge[], stats: object }} payload
 * @param {{
 *   selectedSceneId?: string|null,
 *   focusOrphans?: boolean,
 *   onSelectScene?: (sceneId: string) => void,
 * }} [options]
 */
function renderOrphanGraph(container, payload, options = {}) {
  container.innerHTML = "";

  const header = document.createElement("div");
  header.className = "orphan-graph-header";
  header.innerHTML = `
    <h2 class="results-header">Story graph</h2>
    <p class="results-sub">
      OSD links between scenes. Orphans have no incoming links above the
      ${payload.stats.link_threshold} threshold.
    </p>
  `;
  container.appendChild(header);

  const toolbar = document.createElement("div");
  toolbar.className = "orphan-graph-toolbar";

  const focusToggle = document.createElement("label");
  focusToggle.className = "orphan-graph-toggle";
  const focusInput = document.createElement("input");
  focusInput.type = "checkbox";
  focusInput.checked = options.focusOrphans !== false;
  focusToggle.appendChild(focusInput);
  focusToggle.appendChild(document.createTextNode(" Focus orphans"));

  const stats = document.createElement("span");
  stats.className = "orphan-graph-stats";
  stats.textContent =
    `${payload.stats.scene_count} scenes · ${payload.stats.edge_count} links · `
    + `${payload.stats.orphan_count} orphans`;

  toolbar.appendChild(focusToggle);
  toolbar.appendChild(stats);
  container.appendChild(toolbar);

  const scroll = document.createElement("div");
  scroll.className = "orphan-graph-scroll";
  container.appendChild(scroll);

  const positions = buildNodePositions(payload.nodes);
  const maxX = Math.max(
    ...payload.nodes.map((node) => positions.get(node.scene_id)?.x ?? 0),
    SVG_PADDING,
  );
  const width = maxX + SVG_PADDING + NODE_RADIUS * 2;
  const height = 220;

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("width", String(width));
  svg.setAttribute("height", String(height));
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", "Orphan scene story graph");
  scroll.appendChild(svg);

  const edgeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
  const nodeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
  svg.appendChild(edgeLayer);
  svg.appendChild(nodeLayer);

  /**
   * Re-render edges and nodes for the current focus mode.
   */
  function paintGraph() {
    const focusOrphans = focusInput.checked;
    edgeLayer.innerHTML = "";
    nodeLayer.innerHTML = "";

    for (const edge of payload.edges) {
      const source = positions.get(edge.from_scene_id);
      const target = positions.get(edge.to_scene_id);
      if (!source || !target) {
        continue;
      }

      const sourceNode = payload.nodes.find((node) => node.scene_id === edge.from_scene_id);
      const targetNode = payload.nodes.find((node) => node.scene_id === edge.to_scene_id);
      const edgeRelevant = !focusOrphans || (
        (sourceNode?.is_orphan || targetNode?.is_orphan)
      );
      if (!edgeRelevant) {
        continue;
      }

      const hop = Math.max(1, (targetNode?.scene_number ?? 1) - (sourceNode?.scene_number ?? 1));
      const controlY = BASELINE_Y - Math.min(90, 18 + hop * 8);
      const midX = (source.x + target.x) / 2;

      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute(
        "d",
        `M ${source.x} ${source.y} Q ${midX} ${controlY} ${target.x} ${target.y}`,
      );
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", "#94a3b8");
      path.setAttribute("stroke-width", String(1 + edge.weight * 2));
      path.setAttribute("opacity", String(0.35 + edge.weight * 0.45));
      if (edge.explanation) {
        const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
        title.textContent = edge.explanation;
        path.appendChild(title);
      }
      edgeLayer.appendChild(path);
    }

    for (const node of payload.nodes) {
      const point = positions.get(node.scene_id);
      if (!point) {
        continue;
      }

      const relevant = !focusOrphans || node.is_orphan || isConnectedToOrphan(
        node.scene_id,
        payload.nodes,
        payload.edges,
      );
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", String(point.x));
      circle.setAttribute("cy", String(point.y));
      circle.setAttribute("r", String(NODE_RADIUS));
      circle.setAttribute("class", "orphan-graph-node");
      circle.dataset.sceneId = node.scene_id;

      if (node.is_orphan) {
        circle.setAttribute("fill", "#f59e0b");
        circle.setAttribute("stroke", "#b45309");
      } else {
        circle.setAttribute("fill", "#e2e8f0");
        circle.setAttribute("stroke", "#64748b");
      }

      if (node.scene_id === options.selectedSceneId) {
        circle.setAttribute("stroke", "#0f766e");
        circle.setAttribute("stroke-width", "3");
      } else {
        circle.setAttribute("stroke-width", "1.5");
      }

      if (!relevant) {
        circle.setAttribute("opacity", "0.18");
      }

      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = `Scene ${node.scene_number}: ${node.heading}`;
      circle.appendChild(title);

      circle.addEventListener("click", () => {
        if (typeof options.onSelectScene === "function") {
          options.onSelectScene(node.scene_id);
        }
      });
      nodeLayer.appendChild(circle);

      if (node.is_orphan || node.scene_number % 5 === 1 || node.scene_number === 1) {
        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", String(point.x));
        label.setAttribute("y", String(point.y + 20));
        label.setAttribute("text-anchor", "middle");
        label.setAttribute("class", "orphan-graph-label");
        label.textContent = String(node.scene_number);
        if (!relevant) {
          label.setAttribute("opacity", "0.18");
        }
        nodeLayer.appendChild(label);
      }
    }
  }

  focusInput.addEventListener("change", paintGraph);
  paintGraph();

  const legend = document.createElement("div");
  legend.className = "orphan-graph-legend";
  legend.innerHTML = `
    <span><i class="legend-dot orphan"></i> Orphan scene</span>
    <span><i class="legend-dot link"></i> Story link (thicker = stronger)</span>
    <span>Click a dot to jump to that scene</span>
  `;
  container.appendChild(legend);

  const detail = document.createElement("div");
  detail.className = "orphan-graph-detail";
  detail.id = "orphan-graph-detail";
  container.appendChild(detail);

  /**
   * Update the detail panel for one selected node.
   * @param {string|null} sceneId
   */
  function updateDetail(sceneId) {
    if (!sceneId) {
      detail.textContent = "Select a scene dot to inspect its links.";
      return;
    }
    const node = payload.nodes.find((row) => row.scene_id === sceneId);
    if (!node) {
      detail.textContent = "";
      return;
    }

    const incoming = payload.edges.filter((edge) => edge.to_scene_id === sceneId);
    const outgoing = payload.edges.filter((edge) => edge.from_scene_id === sceneId);
    detail.innerHTML = "";

    const title = document.createElement("strong");
    title.textContent = `Scene ${node.scene_number} · ${node.heading}`;
    detail.appendChild(title);

    if (node.is_orphan) {
      const badge = document.createElement("div");
      badge.className = "orphan-graph-detail-badge";
      badge.textContent = node.orphan_type === "subplot_chain"
        ? "Subplot chain orphan"
        : "Hard orphan";
      detail.appendChild(badge);
    }

    const meta = document.createElement("p");
    meta.className = "orphan-graph-detail-meta";
    meta.textContent =
      `${incoming.length} incoming link(s), ${outgoing.length} outgoing link(s)`;
    detail.appendChild(meta);

    const list = document.createElement("ul");
    list.className = "orphan-graph-detail-links";
    for (const edge of [...incoming, ...outgoing]) {
      const item = document.createElement("li");
      const direction = edge.to_scene_id === sceneId ? "from" : "to";
      const otherId = direction === "from" ? edge.from_scene_id : edge.to_scene_id;
      const other = payload.nodes.find((row) => row.scene_id === otherId);
      const label = other
        ? `Scene ${other.scene_number}`
        : otherId;
      item.textContent = `${direction === "from" ? "←" : "→"} ${label}: `
        + (edge.explanation || `link weight ${edge.weight.toFixed(2)}`);
      list.appendChild(item);
    }
    if (list.childElementCount > 0) {
      detail.appendChild(list);
    }
  }

  updateDetail(options.selectedSceneId ?? null);

  return {
    updateSelection(sceneId) {
      options.selectedSceneId = sceneId;
      paintGraph();
      updateDetail(sceneId);
    },
  };
}

window.OrphanGraphView = {
  render: renderOrphanGraph,
};
