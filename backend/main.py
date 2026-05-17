"""
BehindTheEyes — API Backend

Text-only. No voice, no image, no video composition.
Dynamic character engine: works for any show, any character.
"""
import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Literal
from dotenv import load_dotenv
from videodb import connect

from videodb_utils import get_context_at_timestamp
from engine import (
    generate_character_list,
    build_character_prompt,
    build_scene_prompt,
    build_style_guide_prompt,
    build_character_style_rewrite_prompt,
)

load_dotenv()

app = FastAPI(title="BehindTheEyes API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Load stored video/index IDs
with open('config.json', 'r') as f:
    config = json.load(f)

api_key = os.environ.get("VIDEO_DB_API_KEY")
conn = connect(api_key=api_key)
coll = conn.get_collection()

# Cache the default video object
_default_video = coll.get_video(config["video_id"])

# In-memory cache for character lists (keyed by show_title)
_char_cache: dict = {}
_style_cache: dict = {}


def _get_video(video_id: str):
    if video_id == config["video_id"]:
        return _default_video
    return coll.get_video(video_id)


def _get_transcript_text(video) -> str:
    try:
        if hasattr(video, "get_transcript_text"):
            text = video.get_transcript_text()
            if text:
                return str(text)
    except Exception:
        pass

    try:
        transcript_lines = video.get_transcript()
    except Exception:
        return ""

    return " ".join(
        (line.get("text") or getattr(line, "text", "")).strip()
        for line in transcript_lines
    )


def _generate_text(prompt: str) -> str:
    result = coll.generate_text(prompt=prompt, model_name="ultra")
    return (result.get("output", "") if isinstance(result, dict) else str(result)).strip()


def _get_style_guide(video, show_title: str, char_name: str) -> str:
    cache_key = f"{show_title.strip().lower()}::{char_name.strip().lower()}"
    if cache_key in _style_cache:
        return _style_cache[cache_key]

    transcript_sample = _get_transcript_text(video)
    prompt = build_style_guide_prompt(show_title, char_name, transcript_sample)
    style_guide = _generate_text(prompt)
    if style_guide:
        _style_cache[cache_key] = style_guide
    return style_guide


# ── Request Models ─────────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    timestamp: int
    question: str
    show_title: str
    mode: Literal["character", "scene"] = "character"
    character_name: Optional[str] = None   # exact name, no keys needed
    video_id: Optional[str] = None
    scene_index_id: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/api/ask")
async def ask(req: AskRequest):
    """
    Main endpoint. Works for any show and any character.
    Character profile is generated dynamically by Gemma 4.
    """
    try:
        vid_id    = req.video_id    or config["video_id"]
        scene_idx = req.scene_index_id or config["scene_index_id"]

        video   = _get_video(vid_id)
        context = get_context_at_timestamp(video, scene_idx, req.timestamp, window=60)
        scene   = context["scene"]
        transcript = context["transcript"]

        if req.mode == "scene":
            prompt    = build_scene_prompt(req.show_title, scene, transcript, req.question)
            response_text = _generate_text(prompt)
            responder = f"{req.show_title} — Scene"
        else:
            char_name = req.character_name or "the main character"
            prompt    = build_character_prompt(req.show_title, char_name, scene, transcript, req.question)
            response_text = _generate_text(prompt)
            responder = char_name

            try:
                style_guide = _get_style_guide(video, req.show_title, char_name)
                if style_guide:
                    rewrite_prompt = build_character_style_rewrite_prompt(
                        req.show_title,
                        char_name,
                        req.question,
                        scene,
                        transcript,
                        response_text,
                        style_guide,
                    )
                    styled = _generate_text(rewrite_prompt)
                    if styled:
                        response_text = styled
            except Exception:
                # Style adaptation should never block the core answer path.
                pass

        return {
            "response":   response_text,
            "responder":  responder,
            "mode":       req.mode,
            "timestamp":  req.timestamp,
            "show_title": req.show_title,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/characters")
async def get_characters(
    show_title: str,
    video_id: Optional[str] = None,
    scene_index_id: Optional[str] = None,
):
    """
    Dynamically generate the character list for any show.
    Uses the video's indexed transcript + Gemma 4's knowledge of the show.
    Result is cached in-memory per show title.
    """
    cache_key = show_title.strip().lower()
    if cache_key in _char_cache:
        return {"show_title": show_title, "characters": _char_cache[cache_key]}

    try:
        vid_id = video_id or config["video_id"]
        video  = _get_video(vid_id)

        # Get a representative transcript sample
        transcript_lines = video.get_transcript()
        transcript_text  = " ".join(
            (l.get("text") or getattr(l, "text", "")).strip()
            for l in transcript_lines
        )

        characters = generate_character_list(coll, show_title, transcript_text)
        if characters:
            _char_cache[cache_key] = characters

        return {"show_title": show_title, "characters": characters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/characters/cache")
async def clear_character_cache():
    """Clear the in-memory character cache (useful when switching shows)."""
    _char_cache.clear()
    _style_cache.clear()
    return {"status": "cleared"}


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "BehindTheEyes"}
