"""Utilities to segment narrative text into storyboard-ready scenes."""

from __future__ import annotations

from math import ceil

import spacy
from spacy.language import Language

_NLP: Language | None = None


def _get_nlp() -> Language:
    """Lazily load and cache a spaCy pipeline for sentence splitting."""
    global _NLP
    if _NLP is not None:
        return _NLP

    try:
        _NLP = spacy.load("en_core_web_sm")
    except OSError:
        _NLP = spacy.blank("en")
        _NLP.add_pipe("sentencizer")
    return _NLP


def segment_text(text: str, minimum_scenes: int = 3) -> list[str]:
    """Split a block of narrative text into logical scenes."""
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    nlp = _get_nlp()
    doc = nlp(cleaned)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    if not sentences:
        return [cleaned]

    if len(sentences) >= minimum_scenes:
        return sentences

    group_size = ceil(len(sentences) / minimum_scenes)
    grouped: list[str] = []
    for index in range(0, len(sentences), group_size):
        chunk = " ".join(sentences[index : index + group_size]).strip()
        if chunk:
            grouped.append(chunk)

    while len(grouped) < minimum_scenes:
        grouped.append(grouped[-1] if grouped else cleaned)

    return grouped
