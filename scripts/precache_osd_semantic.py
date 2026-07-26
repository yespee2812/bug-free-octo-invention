"""Download and cache the OSD semantic embedding model locally."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from osd_semantic import SEMANTIC_MODEL_NAME, _load_sentence_transformer


def precache_semantic_model() -> None:
    """Load the MiniLM model once so later runs avoid a cold download."""
    model = _load_sentence_transformer()
    sample = model.encode(
        ["INT. OFFICE - DAY\nA character enters."],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    if sample is None or len(sample) == 0:
        raise RuntimeError("Semantic model pre-cache failed to encode a sample.")
    print(f"Cached OSD semantic model: {SEMANTIC_MODEL_NAME}")


def main() -> None:
    """CLI entry point for semantic model pre-cache."""
    parser = argparse.ArgumentParser(
        description="Pre-download the all-MiniLM-L6-v2 model used by orphan detection.",
    )
    parser.parse_args()
    precache_semantic_model()


if __name__ == "__main__":
    main()
