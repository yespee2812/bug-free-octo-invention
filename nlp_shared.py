"""Shared spaCy pipeline for ScriptLens engines."""

from typing import Optional

import spacy
from spacy.language import Language

DEFAULT_SPACY_MODEL: str = "en_core_web_sm"

_shared_nlp: Optional[Language] = None


def get_shared_nlp(model: str = DEFAULT_SPACY_MODEL) -> Language:
    """Return a process-wide shared spaCy pipeline, loading it on first use.

    Both ``SceneDependencyEngine`` and ``ContradictionEngine`` call this when
    no pipeline is injected, so the model is loaded once per process rather
    than once per engine instance (Caveat D7 / X3).

    Args:
        model: spaCy model name to load when the singleton is empty.

    Returns:
        The shared ``Language`` pipeline.
    """
    global _shared_nlp
    if _shared_nlp is None:
        _shared_nlp = spacy.load(model)
    return _shared_nlp
