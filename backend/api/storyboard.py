"""Storyboard generation API routes."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from models.pitch import PitchRequest
from services.image_generator import generate_image
from services.llm_prompter import enhance_prompt
from services.text_processor import segment_text

router = APIRouter(tags=["storyboard"])


@router.post("/generate-storyboard")
async def generate_storyboard(payload: PitchRequest) -> dict[str, list[dict[str, str]]]:
    """Generate storyboard panels from raw narrative input."""
    scenes = segment_text(payload.text, minimum_scenes=3)
    if not scenes:
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    enhanced_prompts = await asyncio.gather(
        *(enhance_prompt(scene, payload.style) for scene in scenes)
    )
    image_urls = await asyncio.gather(*(generate_image(prompt) for prompt in enhanced_prompts))

    panels = [
        {
            "original_text": original_text,
            "enhanced_prompt": enhanced_prompt,
            "image_url": image_url,
        }
        for original_text, enhanced_prompt, image_url in zip(
            scenes, enhanced_prompts, image_urls, strict=True
        )
    ]

    return {"storyboard": panels}
