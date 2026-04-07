"""Pydantic models for pitch-processing requests and responses."""

from pydantic import BaseModel, Field


class PitchRequest(BaseModel):
    """Core request payload for storyboard generation."""

    text: str = Field(..., min_length=1, description="Narrative text to process.")
    style: str | None = Field(
        default=None,
        description="Optional visual style, for example 'cyberpunk'.",
    )
