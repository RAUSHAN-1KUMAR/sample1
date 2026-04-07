"""Service for upgrading plain sentences into rich visual prompts."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv
from fastapi import HTTPException
from google import genai

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

GEMINI_TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash")

_client: genai.Client | None = None
RETRY_DELAYS_SECONDS = (1.0, 2.0, 4.0)


def _fallback_prompt(sentence: str, style: str) -> str:
    """Create a deterministic prompt when Gemini text model is unavailable."""
    return (
        f"{sentence}. Visual style: {style}. Cinematic composition, detailed lighting, "
        "rich textures, dynamic framing, high detail, concept art quality."
    )


def _get_client() -> genai.Client:
    """Return a lazily initialized Gemini client."""
    global _client
    if _client is None:
        gemini_api_key = os.getenv("GEMINI_API_KEY") or dotenv_values(ENV_PATH).get(
            "GEMINI_API_KEY"
        )
        if not gemini_api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set.")
        _client = genai.Client(api_key=gemini_api_key)
    return _client


async def enhance_prompt(sentence: str, style: str | None) -> str:
    """Convert a narrative sentence into an image-generation-ready prompt."""
    selected_style = (style or "cinematic").strip()
    system_prompt = (
        "You are an expert visual prompt engineer. Transform user narrative text into one "
        "highly descriptive image-generation prompt. Keep subject/action from the source, "
        "add camera framing, lighting, mood, composition cues, and tactile details. "
        f"Apply a consistent visual style for every output: '{selected_style}'. "
        "Always include explicit style keywords that reflect this style. "
        "Output only the final prompt."
    )

    client = _get_client()
    request = (
        f"{system_prompt}\n\n"
        f"Narrative sentence to convert:\n{sentence}\n\n"
        "Return only the final enhanced image prompt."
    )

    for attempt, delay in enumerate((0.0, *RETRY_DELAYS_SECONDS), start=1):
        try:
            if delay:
                await asyncio.sleep(delay)
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=GEMINI_TEXT_MODEL,
                contents=request,
            )
            enhanced = (getattr(response, "text", "") or "").strip()
            if not enhanced:
                raise ValueError("Model returned an empty enhanced prompt.")
            return enhanced
        except HTTPException:
            raise
        except Exception as exc:
            message = str(exc)
            if (
                "503" in message
                or "UNAVAILABLE" in message
                or "429" in message
                or "RESOURCE_EXHAUSTED" in message
            ):
                if attempt <= len(RETRY_DELAYS_SECONDS):
                    continue
                return _fallback_prompt(sentence, selected_style)
            raise HTTPException(
                status_code=502,
                detail=f"Failed to enhance prompt via LLM service: {exc}",
            ) from exc

    raise HTTPException(status_code=502, detail="Failed to enhance prompt via LLM service.")
