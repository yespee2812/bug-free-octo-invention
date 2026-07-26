/**
 * Lightweight Fountain scene renderer for the script reader.
 */

/**
 * Return true when a line looks like a character cue.
 * @param {string} line
 * @returns {boolean}
 */
function isCharacterCue(line) {
  const trimmed = line.trim();
  if (!trimmed || trimmed.length > 40) {
    return false;
  }
  if (!/^[A-Z][A-Z0-9 .'\-()@]+$/.test(trimmed)) {
    return false;
  }
  return !/^(INT\.|EXT\.|INT\/EXT\.|I\/E\.|FADE|CUT TO|DISSOLVE)/.test(trimmed);
}

/**
 * Return true when a line is a parenthetical.
 * @param {string} line
 * @returns {boolean}
 */
function isParenthetical(line) {
  const trimmed = line.trim();
  return trimmed.startsWith("(") && trimmed.endsWith(")");
}

/**
 * Classify one screenplay line for basic HTML rendering.
 * @param {string} line
 * @param {string} previousKind
 * @returns {string}
 */
function classifyLine(line, previousKind) {
  const trimmed = line.trim();
  if (!trimmed) {
    return "blank";
  }
  if (isCharacterCue(trimmed)) {
    return "character";
  }
  if (isParenthetical(trimmed)) {
    return "parenthetical";
  }
  if (previousKind === "character" || previousKind === "parenthetical") {
    return "dialogue";
  }
  return "action";
}

/**
 * Render raw Fountain scene text into a DOM element.
 * @param {object} scene
 * @param {string} scene.scene_id
 * @param {number} scene.scene_number
 * @param {string} scene.heading
 * @param {string} scene.body
 * @param {boolean} selected
 * @param {boolean} [simulatedRemoval]
 * @returns {HTMLElement}
 */
function renderSceneBlock(scene, selected, simulatedRemoval = false) {
  const block = document.createElement("article");
  block.className = "scene-block";
  block.id = `scene-${scene.scene_number}`;
  block.dataset.sceneId = scene.scene_id;
  if (selected) {
    block.classList.add("selected-scene");
  }
  if (simulatedRemoval) {
    block.classList.add("simulated-removal");
  }

  if (simulatedRemoval) {
    const chip = document.createElement("div");
    chip.className = "simulation-chip";
    chip.textContent = "Simulated removal";
    block.appendChild(chip);
  }

  const slug = document.createElement("h2");
  slug.className = "slugline";
  slug.textContent = scene.heading;
  block.appendChild(slug);

  const lines = scene.body.split(/\r?\n/);
  let previousKind = "blank";
  let skippedHeading = false;

  for (const line of lines) {
    if (!skippedHeading) {
      skippedHeading = true;
      if (line.trim().toUpperCase() === scene.heading.trim().toUpperCase()) {
        continue;
      }
    }

    const kind = classifyLine(line, previousKind);
    if (kind === "blank") {
      previousKind = "blank";
      continue;
    }

    const row = document.createElement("p");
    row.className = `script-line ${kind}`;
    row.textContent = line.trim();
    block.appendChild(row);
    previousKind = kind;
  }

  return block;
}

window.ScriptReader = {
  renderSceneBlock,
};
