"""Service for generating images from enhanced prompts."""

from __future__ import annotations

import asyncio
import base64
import html
import os
from pathlib import Path
from urllib.parse import quote

from dotenv import dotenv_values, load_dotenv
from fastapi import HTTPException
from google import genai
import httpx

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

_client: genai.Client | None = None
RETRY_DELAYS_SECONDS = (1.0, 2.0, 4.0)


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


def _extract_image_data_url(response: object) -> str:
    """Extract image bytes from Gemini response and return a browser-safe data URL."""
    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            inline_data = getattr(part, "inline_data", None)
            if inline_data and getattr(inline_data, "data", None):
                raw_data = inline_data.data
                if isinstance(raw_data, str):
                    encoded = raw_data
                else:
                    encoded = base64.b64encode(raw_data).decode("utf-8")
                mime = getattr(inline_data, "mime_type", "image/png")
                return f"data:{mime};base64,{encoded}"
    raise ValueError("Gemini image model returned no inline image data.")


async def _build_fallback_image(prompt: str) -> str:
    """Return an embedded fallback image when Gemini image quota is exhausted."""
    encoded_prompt = quote(prompt[:700])
    image_url = (
        "https://image.pollinations.ai/prompt/"
        f"{encoded_prompt}?width=1024&height=1024&model=flux&nologo=true"
    )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            mime = response.headers.get("content-type", "image/jpeg")
            encoded = base64.b64encode(response.content).decode("utf-8")
            return f"data:{mime};base64,{encoded}"
    except Exception:
        safe_prompt = html.escape(prompt[:110])
        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' width='1024' height='1024'>"
            "<defs><linearGradient id='bg' x1='0' y1='0' x2='1' y2='1'>"
            "<stop offset='0%' stop-color='#0f172a'/>"
            "<stop offset='100%' stop-color='#1e293b'/>"
            "</linearGradient></defs>"
            "<rect width='1024' height='1024' fill='url(#bg)'/>"
            "<text x='64' y='140' fill='#22d3ee' font-size='44' font-family='Arial'>"
            "Storyboard Preview"
            "</text>"
            "<text x='64' y='220' fill='#e2e8f0' font-size='28' font-family='Arial'>"
            f"{safe_prompt}"
            "</text>"
            "<text x='64' y='980' fill='#94a3b8' font-size='22' font-family='Arial'>"
            "Gemini quota reached: using local fallback image"
            "</text>"
            "</svg>"
        )
        return f"data:image/svg+xml;utf8,{quote(svg)}"


async def generate_image(prompt: str) -> str:
    """Generate an image URL from an enhanced storyboard prompt."""
    client = _get_client()
    for attempt, delay in enumerate((0.0, *RETRY_DELAYS_SECONDS), start=1):
        try:
            if delay:
                await asyncio.sleep(delay)
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=GEMINI_IMAGE_MODEL,
                contents=prompt,
            )
            return _extract_image_data_url(response)
        except HTTPException:
            raise
        except Exception as exc:
            message = str(exc)
            if "429" in message or "RESOURCE_EXHAUSTED" in message:
                return await _build_fallback_image(prompt)
            if "503" in str(exc) or "UNAVAILABLE" in str(exc):
                if attempt <= len(RETRY_DELAYS_SECONDS):
                    continue
            raise HTTPException(
                status_code=502,
                detail=f"Failed to generate image with Gemini: {exc}",
            ) from exc

    raise HTTPException(status_code=502, detail="Failed to generate image with Gemini.")
