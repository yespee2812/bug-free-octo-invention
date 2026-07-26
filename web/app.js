/**
 * ScriptLens structure workspace — upload, scene list, reader, simulate cut/edit.
 */

const API_BASE = "";

/** @type {{
 *   scriptId: string|null,
 *   scenes: object[],
 *   orphanIds: Set<string>,
 *   orphanRecords: Map<string, object>,
 *   selectedSceneId: string|null,
 *   sceneCache: Map<string, object>,
 *   editMode: boolean,
 *   draftRevision: number,
 *   canUndo: boolean,
 *   graphView: { active: boolean, controller: object|null },
 *   preview: { mode: string|null, sceneId: string|null, result: object|null }
 * }} */
const state = {
  scriptId: null,
  scenes: [],
  orphanIds: new Set(),
  orphanRecords: new Map(),
  selectedSceneId: null,
  sceneCache: new Map(),
  editMode: false,
  draftRevision: 0,
  canUndo: false,
  graphView: {
    active: false,
    controller: null,
  },
  preview: {
    mode: null,
    sceneId: null,
    result: null,
  },
};

const uploadScreen = document.getElementById("upload-screen");
const workspace = document.getElementById("workspace");
const fileInput = document.getElementById("file-input");
const dropzone = document.getElementById("dropzone");
const uploadStatus = document.getElementById("upload-status");
const orphanCountEl = document.getElementById("orphan-count");
const orphanSummaryEl = document.getElementById("orphan-summary");
const sceneCountLabel = document.getElementById("scene-count-label");
const sceneListEl = document.getElementById("scene-list");
const readerEl = document.getElementById("reader");
const readerView = document.getElementById("reader-view");
const editView = document.getElementById("edit-view");
const editTextarea = document.getElementById("edit-textarea");
const editSceneTitle = document.getElementById("edit-scene-title");
const simulateCutBtn = document.getElementById("simulate-cut-btn");
const deleteSceneBtn = document.getElementById("delete-scene-btn");
const editSceneBtn = document.getElementById("edit-scene-btn");
const undoDraftBtn = document.getElementById("undo-draft-btn");
const exportDraftBtn = document.getElementById("export-draft-btn");
const storyGraphBtn = document.getElementById("story-graph-btn");
const runEditBtn = document.getElementById("run-edit-btn");
const applyEditBtn = document.getElementById("apply-edit-btn");
const cancelEditBtn = document.getElementById("cancel-edit-btn");
const structureBanner = document.getElementById("structure-banner");
const simulationBanner = document.getElementById("simulation-banner");
const newUploadBtn = document.getElementById("new-upload-btn");
const resultsPlaceholder = document.getElementById("results-placeholder");
const resultsPanel = document.getElementById("results-panel");

/**
 * Perform a JSON fetch against the structure API.
 * @param {string} path
 * @param {RequestInit} [options]
 * @returns {Promise<any>}
 */
async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = await response.json();
      if (payload.detail) {
        detail = typeof payload.detail === "string"
          ? payload.detail
          : JSON.stringify(payload.detail);
      }
    } catch (_error) {
      // Keep default detail when body is not JSON.
    }
    throw new Error(detail);
  }
  return response.json();
}

/**
 * Set upload status message text.
 * @param {string} message
 * @param {boolean} [isError]
 */
function setUploadStatus(message, isError = false) {
  uploadStatus.textContent = message;
  uploadStatus.classList.toggle("error", isError);
}

/**
 * Hide the results panel and show the placeholder.
 */
function hideResultsPanel() {
  resultsPanel.classList.add("hidden");
  resultsPanel.hidden = true;
  resultsPlaceholder.classList.remove("hidden");
  resultsPanel.innerHTML = "";
}

/**
 * Update the structure banner for draft revision state.
 */
function updateDraftBanner() {
  if (state.draftRevision > 0) {
    structureBanner.textContent =
      `Working draft · revision ${state.draftRevision} (import unchanged on disk)`;
  } else if (structureBanner.classList.contains("mode-full")) {
    structureBanner.textContent = "Full structure mode";
  }
}

/**
 * Enable or disable draft undo/export controls.
 * @param {{ canUndo?: boolean }} [options]
 */
function updateDraftControls(options = {}) {
  if (options.canUndo !== undefined) {
    state.canUndo = options.canUndo;
  }
  undoDraftBtn.disabled = !state.scriptId || !state.canUndo;
  exportDraftBtn.disabled = !state.scriptId;
  storyGraphBtn.disabled = !state.scriptId;
}

/**
 * Apply draft mutation payload to client state and refresh the workspace.
 * @param {object} payload Draft delete/apply-edit API response.
 * @param {{ selectSceneNumber?: number }} [options]
 */
async function applyDraftMutation(payload, options = {}) {
  state.draftRevision = payload.draft_revision;
  state.scenes = payload.scenes;
  state.sceneCache = new Map();
  sceneCountLabel.textContent = String(payload.scene_count);
  orphanCountEl.textContent = String(payload.orphan_count);
  updateDraftBanner();
  updateDraftControls({ canUndo: payload.can_undo === true });

  if (payload.previous_scene_count !== payload.scene_count) {
    window.alert(
      `Scene list updated: ${payload.previous_scene_count} → ${payload.scene_count} scenes.`,
    );
  }

  clearPreview();
  closeEditMode();
  readerView.classList.remove("hidden");

  await loadOrphans();

  let nextSceneId = state.scenes[0]?.scene_id ?? null;
  if (options.selectSceneNumber) {
    const match = state.scenes.find(
      (row) => row.scene_number === options.selectSceneNumber,
    );
    if (match) {
      nextSceneId = match.scene_id;
    }
  } else if (state.selectedSceneId) {
    const previous = payload.affected_scene;
    if (previous && payload.scene_count < payload.previous_scene_count) {
      const fallbackNumber = Math.min(previous.scene_number, payload.scene_count);
      const match = state.scenes.find((row) => row.scene_number === fallbackNumber);
      nextSceneId = match?.scene_id ?? nextSceneId;
    }
  }

  if (nextSceneId) {
    await selectScene(nextSceneId);
  } else {
    state.selectedSceneId = null;
    simulateCutBtn.disabled = true;
    deleteSceneBtn.disabled = true;
    editSceneBtn.disabled = true;
    renderSceneList();
  }
}

/**
 * Hide the orphan graph and restore the results placeholder.
 */
function hideOrphanGraphView() {
  state.graphView.active = false;
  state.graphView.controller = null;
  storyGraphBtn.textContent = "Story graph";
  hideResultsPanel();
}

/**
 * Load and render the orphan story graph in the right panel.
 */
async function showOrphanGraphView() {
  if (!state.scriptId) {
    return;
  }

  if (state.graphView.active) {
    hideOrphanGraphView();
    return;
  }

  clearPreview();
  closeEditMode();
  readerView.classList.remove("hidden");

  storyGraphBtn.disabled = true;
  storyGraphBtn.classList.add("is-loading");
  storyGraphBtn.textContent = "Loading graph…";

  try {
    const payload = await apiFetch(`/api/scripts/${state.scriptId}/orphan-graph`);
    resultsPlaceholder.classList.add("hidden");
    resultsPanel.classList.remove("hidden");
    resultsPanel.hidden = false;
    resultsPanel.innerHTML = "";

    const controller = window.OrphanGraphView.render(resultsPanel, payload, {
      selectedSceneId: state.selectedSceneId,
      focusOrphans: payload.stats.orphan_count > 0,
      onSelectScene: (sceneId) => {
        selectScene(sceneId, { preservePreview: true, flashHighlight: true });
        controller.updateSelection(sceneId);
      },
    });

    state.graphView.active = true;
    state.graphView.controller = controller;
    storyGraphBtn.textContent = "Close graph";

    const clearBtn = document.createElement("button");
    clearBtn.type = "button";
    clearBtn.className = "clear-sim-btn";
    clearBtn.textContent = "Close graph";
    clearBtn.addEventListener("click", hideOrphanGraphView);
    resultsPanel.appendChild(clearBtn);
  } catch (error) {
    hideOrphanGraphView();
    window.alert(`Could not load story graph: ${error.message}`);
  } finally {
    storyGraphBtn.classList.remove("is-loading");
    storyGraphBtn.disabled = !state.scriptId;
  }
}

/**
 * Clear any active simulate-cut or simulate-edit preview.
 */
function clearPreview() {
  if (state.graphView.active) {
    hideOrphanGraphView();
  }
  state.preview.mode = null;
  state.preview.sceneId = null;
  state.preview.result = null;

  simulationBanner.classList.add("hidden");
  hideResultsPanel();

  simulateCutBtn.textContent = "Simulate cut";
  simulateCutBtn.disabled = !state.selectedSceneId;
  deleteSceneBtn.disabled = !state.selectedSceneId;
  editSceneBtn.disabled = !state.selectedSceneId;

  if (state.selectedSceneId && !state.editMode) {
    renderSceneInReader(state.selectedSceneId, false);
  }
  renderSceneList();
}

/**
 * Close the edit textarea view and return to the reader.
 */
function closeEditMode() {
  state.editMode = false;
  editView.classList.add("hidden");
  editView.hidden = true;
  readerView.classList.remove("hidden");
  editSceneBtn.textContent = "Edit scene";
  editSceneBtn.disabled = !state.selectedSceneId;
}

/**
 * Reset client state and return to the upload screen.
 */
function resetWorkspace() {
  state.scriptId = null;
  state.scenes = [];
  state.orphanIds = new Set();
  state.orphanRecords = new Map();
  state.selectedSceneId = null;
  state.sceneCache = new Map();
  state.editMode = false;
  state.draftRevision = 0;
  state.canUndo = false;
  state.graphView.active = false;
  state.graphView.controller = null;
  state.preview.mode = null;
  state.preview.sceneId = null;
  state.preview.result = null;

  sceneListEl.innerHTML = "";
  readerEl.innerHTML = '<p class="reader-placeholder">Select a scene from the list.</p>';
  editTextarea.value = "";
  closeEditMode();
  readerView.classList.remove("hidden");

  simulateCutBtn.textContent = "Simulate cut";
  simulateCutBtn.disabled = true;
  deleteSceneBtn.disabled = true;
  editSceneBtn.textContent = "Edit scene";
  editSceneBtn.disabled = true;
  updateDraftControls({ canUndo: false });

  simulationBanner.classList.add("hidden");
  hideResultsPanel();

  workspace.classList.add("hidden");
  workspace.hidden = true;
  uploadScreen.classList.remove("hidden");
  fileInput.value = "";
  setUploadStatus("");
}

/**
 * Update the structure banner from upload metadata.
 * @param {object} payload Upload or script detail payload.
 */
function updateStructureBanner(payload) {
  const parts = [];

  if (payload.structure_mode === "limited") {
    parts.push(
      "Limited structure mode — scene breaks not detected. Upload Fountain or a text-based PDF.",
    );
    structureBanner.classList.remove("mode-full");
  } else if (payload.input_format === "pdf") {
    const stage = payload.pdf_conversion || "refined";
    parts.push(`PDF imported (${stage} cleanup · ${payload.scene_count} scenes)`);
    structureBanner.classList.add("mode-full");
  } else {
    parts.push("Full structure mode");
    structureBanner.classList.add("mode-full");
  }

  for (const warning of payload.ingest_warnings || []) {
    parts.push(warning);
  }

  structureBanner.textContent = parts.join(" · ");
  structureBanner.classList.remove("hidden");
}

/**
 * Show the workspace after a successful upload.
 * @param {object} payload Upload API response.
 */
function showWorkspace(payload) {
  state.scriptId = payload.script_id;
  state.draftRevision = payload.draft_revision ?? 0;
  state.scenes = payload.scenes;
  state.selectedSceneId = null;
  state.sceneCache = new Map();
  state.editMode = false;
  clearPreview();
  closeEditMode();
  readerView.classList.remove("hidden");

  uploadScreen.classList.add("hidden");
  workspace.classList.remove("hidden");
  workspace.hidden = false;

  orphanCountEl.textContent = String(payload.orphan_count);
  sceneCountLabel.textContent = String(payload.scene_count);

  structureBanner.classList.remove("hidden");
  updateStructureBanner(payload);
  updateDraftBanner();
  updateDraftControls({ canUndo: false });

  renderSceneList();
  if (state.scenes.length > 0) {
    selectScene(state.scenes[0].scene_id);
  }
  loadOrphans();
}

/**
 * Human-readable label for an orphan classification type.
 * @param {string} orphanType
 * @returns {string}
 */
function orphanTypeLabel(orphanType) {
  if (orphanType === "subplot_chain") {
    return "Subplot chain";
  }
  return "Hard orphan";
}

/**
 * Render the orphan summary panel under the orphans metric card.
 */
function renderOrphanSummary() {
  orphanSummaryEl.innerHTML = "";
  if (state.orphanRecords.size === 0) {
    orphanSummaryEl.classList.add("hidden");
    orphanSummaryEl.hidden = true;
    return;
  }

  orphanSummaryEl.classList.remove("hidden");
  orphanSummaryEl.hidden = false;

  for (const record of [...state.orphanRecords.values()].sort(
    (left, right) => left.scene_number - right.scene_number,
  )) {
    const item = document.createElement("article");
    item.className = "orphan-summary-item";
    item.dataset.sceneId = record.scene_id;

    const title = document.createElement("button");
    title.type = "button";
    title.className = "orphan-summary-title";
    title.textContent = `Scene ${record.scene_number} · ${orphanTypeLabel(record.orphan_type)}`;
    title.addEventListener("click", () => selectScene(record.scene_id));

    const heading = document.createElement("p");
    heading.className = "orphan-summary-heading";
    heading.textContent = record.heading;

    const reasons = document.createElement("ul");
    reasons.className = "orphan-summary-reasons";
    for (const reason of record.reasons || []) {
      const row = document.createElement("li");
      row.textContent = reason;
      reasons.appendChild(row);
    }

    item.appendChild(title);
    item.appendChild(heading);
    if (record.reasons?.length) {
      item.appendChild(reasons);
    }
    orphanSummaryEl.appendChild(item);
  }
}

/**
 * Load orphan ids and mark orphan rows in the scene list.
 */
async function loadOrphans() {
  if (!state.scriptId) {
    return;
  }
  const payload = await apiFetch(`/api/scripts/${state.scriptId}/orphans`);
  state.orphanRecords = new Map(
    payload.orphans.map((row) => [row.scene_id, row]),
  );
  state.orphanIds = new Set(payload.orphans.map((row) => row.scene_id));
  orphanCountEl.textContent = String(payload.orphan_count);
  renderOrphanSummary();
  renderSceneList();
}

/**
 * Map a scene id to a display scene number.
 * @param {string} sceneId
 * @returns {string}
 */
function sceneNumberLabel(sceneId) {
  const match = state.scenes.find((scene) => scene.scene_id === sceneId);
  return match ? String(match.scene_number) : sceneId;
}

/**
 * Render the left-panel scene list from current state.
 */
function renderSceneList() {
  sceneListEl.innerHTML = "";
  for (const scene of state.scenes) {
    const item = document.createElement("li");
    item.className = "scene-item";
    item.role = "option";
    item.dataset.sceneId = scene.scene_id;
    if (scene.scene_id === state.selectedSceneId) {
      item.classList.add("selected");
      item.setAttribute("aria-selected", "true");
    }
    if (
      state.preview.mode === "cut"
      && state.preview.sceneId === scene.scene_id
    ) {
      item.classList.add("simulated-cut");
    }
    if (
      state.preview.mode === "edit"
      && state.preview.sceneId === scene.scene_id
    ) {
      item.classList.add("simulated-edit");
    }
    if (state.orphanIds.has(scene.scene_id)) {
      item.classList.add("orphan");
    }

    const num = document.createElement("span");
    num.className = "scene-num";
    num.textContent = String(scene.scene_number);

    const heading = document.createElement("span");
    heading.className = "scene-heading";
    heading.textContent = scene.heading;
    heading.title = scene.heading;

    item.appendChild(num);
    item.appendChild(heading);

    if (state.orphanIds.has(scene.scene_id)) {
      const record = state.orphanRecords.get(scene.scene_id);
      if (record) {
        item.title = `${orphanTypeLabel(record.orphan_type)}: ${(record.reasons || []).join(" ")}`;
        const badge = document.createElement("span");
        badge.className = "orphan-badge";
        badge.textContent = record.orphan_type === "subplot_chain" ? "chain" : "orphan";
        item.appendChild(badge);
      }
    }
    item.addEventListener("click", () => selectScene(scene.scene_id));
    sceneListEl.appendChild(item);
  }
}

/**
 * Fetch scene detail, using the in-memory cache when available.
 * @param {string} sceneId
 * @returns {Promise<object>}
 */
async function fetchScene(sceneId) {
  let scene = state.sceneCache.get(sceneId);
  if (!scene) {
    scene = await apiFetch(`/api/scripts/${state.scriptId}/scenes/${sceneId}`);
    state.sceneCache.set(sceneId, scene);
  }
  return scene;
}

/**
 * Render one scene in the center reader.
 * @param {string} sceneId
 * @param {boolean} [flashHighlight]
 */
async function renderSceneInReader(sceneId, flashHighlight = false) {
  if (state.editMode) {
    return;
  }

  readerEl.innerHTML = '<p class="reader-placeholder">Loading scene…</p>';

  try {
    const scene = await fetchScene(sceneId);
    const isRemoved =
      state.preview.mode === "cut" && sceneId === state.preview.sceneId;
    const isSelected = sceneId === state.selectedSceneId;

    readerEl.innerHTML = "";
    const block = window.ScriptReader.renderSceneBlock(
      scene,
      isSelected,
      isRemoved,
    );
    readerEl.appendChild(block);

    const orphanRecord = state.orphanRecords.get(sceneId);
    if (orphanRecord) {
      const banner = document.createElement("aside");
      banner.className = "orphan-reader-banner";
      banner.setAttribute("role", "note");

      const title = document.createElement("strong");
      title.textContent = orphanTypeLabel(orphanRecord.orphan_type);

      const reasons = document.createElement("ul");
      for (const reason of orphanRecord.reasons || []) {
        const row = document.createElement("li");
        row.textContent = reason;
        reasons.appendChild(row);
      }

      banner.appendChild(title);
      if (orphanRecord.reasons?.length) {
        banner.appendChild(reasons);
      }
      readerEl.insertBefore(banner, block);
    }

    if (flashHighlight) {
      block.classList.add("highlight-flash");
      window.setTimeout(() => block.classList.remove("highlight-flash"), 2600);
    }

    block.scrollIntoView({ block: "start", behavior: "smooth" });
  } catch (error) {
    readerEl.innerHTML = `<p class="reader-placeholder">Could not load scene: ${error.message}</p>`;
  }
}

/**
 * Select a scene and update the reader or edit view.
 * @param {string} sceneId
 * @param {{ preservePreview?: boolean, flashHighlight?: boolean }} [options]
 */
async function selectScene(sceneId, options = {}) {
  if (!state.scriptId) {
    return;
  }

  const preservePreview = options.preservePreview === true;
  if (state.preview.mode && !preservePreview) {
    clearPreview();
  }
  if (state.editMode && sceneId !== state.selectedSceneId) {
    closeEditMode();
  }

  state.selectedSceneId = sceneId;
  simulateCutBtn.disabled = false;
  deleteSceneBtn.disabled = false;
  editSceneBtn.disabled = false;

  if (state.preview.mode === "cut") {
    simulateCutBtn.textContent = "Clear simulation";
  }

  renderSceneList();

  if (state.graphView.active && state.graphView.controller) {
    state.graphView.controller.updateSelection(sceneId);
  }

  if (state.editMode) {
    await openEditMode(false);
    return;
  }

  await renderSceneInReader(sceneId, options.flashHighlight === true);
}

/**
 * Open the edit textarea for the selected scene.
 * @param {boolean} [reloadText]
 */
async function openEditMode(reloadText = true) {
  if (!state.selectedSceneId) {
    return;
  }

  clearPreview();
  state.editMode = true;
  readerView.classList.add("hidden");
  editView.classList.remove("hidden");
  editView.hidden = false;
  editSceneBtn.textContent = "Editing…";

  const scene = await fetchScene(state.selectedSceneId);
  const summary = state.scenes.find((row) => row.scene_id === state.selectedSceneId);
  const label = summary
    ? `Edit Scene ${summary.scene_number}`
    : "Edit scene";
  editSceneTitle.textContent = label;

  if (reloadText) {
    editTextarea.value = scene.body;
  }
  editTextarea.focus();
}

/**
 * Append a clear button to the active results panel.
 * @param {() => void} onClear
 */
function appendClearButton(onClear) {
  const clearBtn = document.createElement("button");
  clearBtn.type = "button";
  clearBtn.className = "clear-sim-btn";
  clearBtn.textContent = "Clear preview";
  clearBtn.addEventListener("click", onClear);
  resultsPanel.appendChild(clearBtn);
}

/**
 * Human-readable label for simulate risk levels.
 * @param {string} riskLevel
 * @returns {string}
 */
function riskLevelLabel(riskLevel) {
  const labels = {
    none: "Safe",
    low: "Low risk",
    medium: "Medium risk",
    high: "High risk",
  };
  return labels[riskLevel] || "Impact";
}

/**
 * Append a risk badge and summary line to a results panel header block.
 * @param {HTMLElement} container
 * @param {string} summary
 * @param {string} riskLevel
 */
function appendImpactSummary(container, summary, riskLevel) {
  const badge = document.createElement("div");
  badge.className = `impact-risk-badge risk-${riskLevel || "none"}`;
  badge.textContent = riskLevelLabel(riskLevel);
  container.appendChild(badge);

  const summaryEl = document.createElement("p");
  summaryEl.className = "impact-summary";
  summaryEl.textContent = summary;
  container.appendChild(summaryEl);
}

/**
 * Render simulate-cut impact rows in the right panel.
 * @param {object} payload Simulate-cut API response.
 */
function renderSimulateCutResults(payload) {
  resultsPlaceholder.classList.add("hidden");
  resultsPanel.classList.remove("hidden");
  resultsPanel.hidden = false;
  resultsPanel.innerHTML = "";

  const removed = payload.removed_scene;
  const header = document.createElement("h2");
  header.className = "results-header";
  header.textContent = `Impact of removing Scene ${removed.scene_number}`;
  resultsPanel.appendChild(header);

  const sub = document.createElement("p");
  sub.className = "results-sub";
  sub.textContent = removed.heading;
  resultsPanel.appendChild(sub);

  appendImpactSummary(resultsPanel, payload.summary, payload.risk_level);

  if (!payload.impacted_scenes.length) {
    const empty = document.createElement("div");
    empty.className = "results-empty";
    empty.textContent =
      payload.risk_level === "none"
        ? "No later scenes rely on this scene's story functions."
        : "No unique continuity links, but review the summary before cutting.";
    resultsPanel.appendChild(empty);
  } else {
    const list = document.createElement("ul");
    list.className = "impact-list";

    for (const row of payload.impacted_scenes) {
      const item = document.createElement("li");
      item.className = "impact-item";

      const title = document.createElement("strong");
      const severityLabel = row.severity === "direct" ? "Direct impact" : "Downstream impact";
      title.textContent = `Scene ${row.scene_number} — ${severityLabel}`;
      item.appendChild(title);

      const heading = document.createElement("p");
      heading.className = "impact-explanation";
      heading.textContent = row.heading;
      item.appendChild(heading);

      const reason = row.impact_reason || row.explanation;
      if (reason) {
        const explanation = document.createElement("p");
        explanation.className = "impact-explanation";
        explanation.textContent = reason;
        item.appendChild(explanation);
      }

      const path = document.createElement("p");
      path.className = "impact-path";
      const labels = row.dependency_path.map((id) => sceneNumberLabel(id));
      path.textContent = `Story path: ${labels.join(" → ")}`;
      item.appendChild(path);

      const goBtn = document.createElement("button");
      goBtn.type = "button";
      goBtn.className = "go-scene-btn";
      goBtn.textContent = `Go to scene ${row.scene_number}`;
      goBtn.addEventListener("click", () => {
        closeEditMode();
        readerView.classList.remove("hidden");
        selectScene(row.scene_id, {
          preservePreview: true,
          flashHighlight: true,
        });
      });
      item.appendChild(goBtn);

      list.appendChild(item);
    }

    resultsPanel.appendChild(list);
  }

  appendClearButton(clearPreview);
}

/**
 * Render one edge diff block.
 * @param {string} label
 * @param {object[]} records
 * @param {string} cssClass
 */
function renderDiffGroup(label, records, cssClass) {
  if (!records.length) {
    return;
  }

  const title = document.createElement("p");
  title.className = "diff-section-title";
  title.textContent = label;
  resultsPanel.appendChild(title);

  for (const record of records) {
    const item = document.createElement("div");
    item.className = `diff-item ${cssClass}`;
    const from = sceneNumberLabel(record.from_scene_id);
    const to = sceneNumberLabel(record.to_scene_id);
    item.textContent = `${from} → ${to}: ${record.explanation || record.edge_type}`;
    resultsPanel.appendChild(item);
  }
}

/**
 * Render simulate-edit diff in the right panel.
 * @param {object} payload Simulate-edit API response.
 */
function renderSimulateEditResults(payload) {
  resultsPlaceholder.classList.add("hidden");
  resultsPanel.classList.remove("hidden");
  resultsPanel.hidden = false;
  resultsPanel.innerHTML = "";

  const edited = payload.edited_scene;
  const header = document.createElement("h2");
  header.className = "results-header";
  header.textContent = `Changes if you edit Scene ${edited.scene_number}`;
  resultsPanel.appendChild(header);

  const sub = document.createElement("p");
  sub.className = "results-sub";
  sub.textContent = edited.heading;
  resultsPanel.appendChild(sub);

  appendImpactSummary(resultsPanel, payload.summary, payload.risk_level);

  const delta = payload.orphan_delta;
  const deltaEl = document.createElement("div");
  const deltaChange = delta.after - delta.before;
  deltaEl.className = "orphan-delta";
  if (deltaChange > 0) {
    deltaEl.classList.add("increase");
  } else if (deltaChange < 0) {
    deltaEl.classList.add("decrease");
  }
  deltaEl.textContent = delta.message || `Orphans: ${delta.before} → ${delta.after}`;
  resultsPanel.appendChild(deltaEl);

  if (payload.scene_count_before !== payload.scene_count_after) {
    const countEl = document.createElement("div");
    countEl.className = "orphan-delta increase";
    countEl.textContent =
      `Scenes: ${payload.scene_count_before} → ${payload.scene_count_after} if applied`;
    resultsPanel.appendChild(countEl);
  }

  const diff = payload.edge_diff;
  const totalChanges =
    diff.added.length + diff.removed.length + diff.changed.length;

  if (totalChanges === 0) {
    const empty = document.createElement("div");
    empty.className = "results-empty";
    empty.textContent = "No dependency edges changed.";
    resultsPanel.appendChild(empty);
  } else {
    renderDiffGroup("Added links", diff.added, "added");
    renderDiffGroup("Removed links", diff.removed, "removed");
    if (diff.changed.length) {
      const title = document.createElement("p");
      title.className = "diff-section-title";
      title.textContent = "Changed links";
      resultsPanel.appendChild(title);
      for (const record of diff.changed) {
        const item = document.createElement("div");
        item.className = "diff-item changed";
        const from = sceneNumberLabel(record.from_scene_id);
        const to = sceneNumberLabel(record.to_scene_id);
        item.textContent =
          `${from} → ${to}: weight ${record.before.weight} → ${record.after.weight}`;
        resultsPanel.appendChild(item);
      }
    }
  }

  if (payload.downstream_at_risk.length) {
    const riskTitle = document.createElement("p");
    riskTitle.className = "diff-section-title";
    riskTitle.textContent = "Scenes at risk";
    resultsPanel.appendChild(riskTitle);

    for (const row of payload.downstream_at_risk) {
      const item = document.createElement("div");
      item.className = "diff-item removed";

      const label = document.createElement("strong");
      label.textContent = `Scene ${row.scene_number} — ${row.heading}`;
      item.appendChild(label);

      if (row.reason) {
        const reason = document.createElement("p");
        reason.className = "impact-explanation";
        reason.textContent = row.reason;
        item.appendChild(reason);
      }

      const goBtn = document.createElement("button");
      goBtn.type = "button";
      goBtn.className = "go-scene-btn";
      goBtn.textContent = "Go to scene";
      goBtn.addEventListener("click", () => {
        closeEditMode();
        readerView.classList.remove("hidden");
        selectScene(row.scene_id, {
          preservePreview: true,
          flashHighlight: true,
        });
      });
      item.appendChild(document.createElement("br"));
      item.appendChild(goBtn);
      resultsPanel.appendChild(item);
    }
  }

  appendClearButton(() => {
    clearPreview();
    if (state.editMode) {
      openEditMode(false);
    }
  });
}

/**
 * Run simulate-cut for the currently selected scene.
 */
async function runSimulateCut() {
  if (!state.scriptId || !state.selectedSceneId) {
    return;
  }

  closeEditMode();
  readerView.classList.remove("hidden");

  simulateCutBtn.disabled = true;
  simulateCutBtn.classList.add("is-loading");
  simulateCutBtn.textContent = "Simulating…";

  try {
    const payload = await apiFetch(
      `/api/scripts/${state.scriptId}/simulate/cut`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scene_id: state.selectedSceneId }),
      },
    );

    state.preview.mode = "cut";
    state.preview.sceneId = state.selectedSceneId;
    state.preview.result = payload;

    simulationBanner.classList.remove("hidden");
    simulationBanner.textContent = "Preview only — working draft unchanged";
    simulateCutBtn.textContent = "Clear simulation";
    simulateCutBtn.disabled = false;

    renderSceneList();
    renderSimulateCutResults(payload);
    await renderSceneInReader(state.preview.sceneId, false);
  } catch (error) {
    window.alert(`Simulate cut failed: ${error.message}`);
    simulateCutBtn.textContent = "Simulate cut";
    simulateCutBtn.disabled = !state.selectedSceneId;
  } finally {
    simulateCutBtn.classList.remove("is-loading");
  }
}

/**
 * Run simulate-edit for the textarea contents.
 */
async function runSimulateEdit() {
  if (!state.scriptId || !state.selectedSceneId) {
    return;
  }

  const modifiedText = editTextarea.value.trim();
  if (!modifiedText) {
    window.alert("Enter scene text before simulating edit.");
    return;
  }

  runEditBtn.disabled = true;
  runEditBtn.classList.add("is-loading");
  runEditBtn.textContent = "Simulating…";

  try {
    const payload = await apiFetch(
      `/api/scripts/${state.scriptId}/simulate/edit`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scene_id: state.selectedSceneId,
          modified_text: modifiedText,
        }),
      },
    );

    state.preview.mode = "edit";
    state.preview.sceneId = state.selectedSceneId;
    state.preview.result = payload;

    simulationBanner.classList.remove("hidden");
    simulationBanner.textContent = "Preview only — working draft unchanged";
    renderSceneList();
    renderSimulateEditResults(payload);
  } catch (error) {
    window.alert(`Simulate edit failed: ${error.message}`);
  } finally {
    runEditBtn.disabled = false;
    runEditBtn.classList.remove("is-loading");
    runEditBtn.textContent = "Simulate edit";
  }
}

/**
 * Delete the selected scene from the working draft.
 */
async function runDeleteScene() {
  if (!state.scriptId || !state.selectedSceneId) {
    return;
  }

  const summary = state.scenes.find((row) => row.scene_id === state.selectedSceneId);
  const label = summary
    ? `Scene ${summary.scene_number}: ${summary.heading}`
    : state.selectedSceneId;
  const confirmed = window.confirm(
    `Delete ${label} from your working draft? This updates orphans and simulate results.`,
  );
  if (!confirmed) {
    return;
  }

  deleteSceneBtn.disabled = true;
  deleteSceneBtn.classList.add("is-loading");
  deleteSceneBtn.textContent = "Deleting…";

  try {
    const payload = await apiFetch(
      `/api/scripts/${state.scriptId}/draft/delete`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scene_id: state.selectedSceneId }),
      },
    );
    await applyDraftMutation(payload);
  } catch (error) {
    window.alert(`Delete scene failed: ${error.message}`);
  } finally {
    deleteSceneBtn.disabled = !state.selectedSceneId;
    deleteSceneBtn.classList.remove("is-loading");
    deleteSceneBtn.textContent = "Delete scene";
  }
}

/**
 * Apply the textarea contents to the working draft.
 */
async function runApplyEdit() {
  if (!state.scriptId || !state.selectedSceneId) {
    return;
  }

  const modifiedText = editTextarea.value.trim();
  if (!modifiedText) {
    window.alert("Enter scene text before applying edit.");
    return;
  }

  const confirmed = window.confirm(
    "Apply this edit to your working draft? Scene count may change if you added sluglines.",
  );
  if (!confirmed) {
    return;
  }

  applyEditBtn.disabled = true;
  applyEditBtn.classList.add("is-loading");
  applyEditBtn.textContent = "Applying…";

  try {
    const payload = await apiFetch(
      `/api/scripts/${state.scriptId}/draft/apply-edit`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scene_id: state.selectedSceneId,
          modified_text: modifiedText,
        }),
      },
    );
    const keepNumber = state.scenes.find(
      (row) => row.scene_id === state.selectedSceneId,
    )?.scene_number;
    await applyDraftMutation(payload, { selectSceneNumber: keepNumber });
  } catch (error) {
    window.alert(`Apply edit failed: ${error.message}`);
  } finally {
    applyEditBtn.disabled = false;
    applyEditBtn.classList.remove("is-loading");
    applyEditBtn.textContent = "Apply edit";
  }
}

/**
 * Undo the most recent draft delete or applied edit.
 */
async function runUndoDraft() {
  if (!state.scriptId || !state.canUndo) {
    return;
  }

  undoDraftBtn.disabled = true;
  undoDraftBtn.classList.add("is-loading");
  undoDraftBtn.textContent = "Undoing…";

  try {
    const payload = await apiFetch(
      `/api/scripts/${state.scriptId}/draft/undo`,
      { method: "POST" },
    );
    await applyDraftMutation(payload);
  } catch (error) {
    window.alert(`Undo failed: ${error.message}`);
  } finally {
    undoDraftBtn.classList.remove("is-loading");
    undoDraftBtn.textContent = "Undo draft";
    updateDraftControls();
  }
}

/**
 * Download the current working draft as a Fountain file.
 */
function exportDraft() {
  if (!state.scriptId) {
    return;
  }
  window.location.assign(`${API_BASE}/api/scripts/${state.scriptId}/draft/export`);
}

/**
 * Upload a screenplay file to the API.
 * @param {File} file
 */
async function uploadFile(file) {
  setUploadStatus("Building scene graph…");
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE}/api/upload`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      let detail = response.statusText;
      try {
        const payload = await response.json();
        detail = payload.detail || detail;
      } catch (_error) {
        // Ignore JSON parse errors.
      }
      throw new Error(detail);
    }
    const payload = await response.json();
    showWorkspace(payload);
    await loadOrphans();
    setUploadStatus("");
  } catch (error) {
    setUploadStatus(error.message || "Upload failed.", true);
  }
}

/**
 * Handle file selection from the native picker.
 * @param {Event} event
 */
function onFileInputChange(event) {
  const input = /** @type {HTMLInputElement} */ (event.target);
  const file = input.files && input.files[0];
  if (file) {
    uploadFile(file);
  }
}

/**
 * Prevent default drag behavior and highlight the dropzone.
 * @param {DragEvent} event
 */
function onDragOver(event) {
  event.preventDefault();
  dropzone.classList.add("dragover");
}

/**
 * Remove dropzone highlight when drag leaves.
 */
function onDragLeave() {
  dropzone.classList.remove("dragover");
}

/**
 * Handle screenplay file drop.
 * @param {DragEvent} event
 */
function onDrop(event) {
  event.preventDefault();
  dropzone.classList.remove("dragover");
  const file = event.dataTransfer && event.dataTransfer.files[0];
  if (file) {
    uploadFile(file);
  }
}

/**
 * Toggle simulate cut or clear an active cut preview.
 */
function onSimulateCutClick() {
  if (state.preview.mode === "cut") {
    clearPreview();
    return;
  }
  runSimulateCut();
}

/**
 * Open edit mode or return to the reader if already editing.
 */
async function onEditSceneClick() {
  if (state.editMode) {
    closeEditMode();
    readerView.classList.remove("hidden");
    if (state.selectedSceneId) {
      await renderSceneInReader(state.selectedSceneId, false);
    }
    return;
  }
  await openEditMode(true);
}

/**
 * Cancel edit mode without running simulate edit.
 */
function onCancelEditClick() {
  clearPreview();
  closeEditMode();
  readerView.classList.remove("hidden");
  if (state.selectedSceneId) {
    renderSceneInReader(state.selectedSceneId, false);
  }
}

fileInput.addEventListener("change", onFileInputChange);
dropzone.addEventListener("dragover", onDragOver);
dropzone.addEventListener("dragleave", onDragLeave);
dropzone.addEventListener("drop", onDrop);
newUploadBtn.addEventListener("click", resetWorkspace);
simulateCutBtn.addEventListener("click", onSimulateCutClick);
deleteSceneBtn.addEventListener("click", runDeleteScene);
editSceneBtn.addEventListener("click", onEditSceneClick);
runEditBtn.addEventListener("click", runSimulateEdit);
applyEditBtn.addEventListener("click", runApplyEdit);
cancelEditBtn.addEventListener("click", onCancelEditClick);
undoDraftBtn.addEventListener("click", runUndoDraft);
exportDraftBtn.addEventListener("click", exportDraft);
storyGraphBtn.addEventListener("click", showOrphanGraphView);

document.getElementById("orphans-card").addEventListener("click", async () => {
  if (!state.scriptId || state.orphanIds.size === 0) {
    return;
  }
  const firstOrphan = state.scenes.find((scene) => state.orphanIds.has(scene.scene_id));
  if (firstOrphan) {
    await selectScene(firstOrphan.scene_id);
  }
});
