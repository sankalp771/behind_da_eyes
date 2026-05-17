import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Literal
from dotenv import load_dotenv
from videodb import connect

from videodb_utils import get_context_at_timestamp
from characters import SERIES_REGISTRY, build_character_prompt, build_scene_prompt

load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

with open('config.json', 'r') as f:
    config = json.load(f)

api_key = os.environ.get("VIDEO_DB_API_KEY")
conn = connect(api_key=api_key)
coll = conn.get_collection()
video = coll.get_video(config["video_id"])


class AskRequest(BaseModel):
    timestamp: int
    question: str
    mode: Literal["character", "scene"] = "character"
    character_key: Optional[str] = "light_yagami"
    series_key: Optional[str] = "death_note"
    # Fallback custom character (when not in registry)
    custom_character_name: Optional[str] = None
    custom_character_description: Optional[str] = None
    video_id: Optional[str] = None
    scene_index_id: Optional[str] = None


@app.post("/api/ask")
async def ask(req: AskRequest):
    try:
        vid_id = req.video_id or config["video_id"]
        scene_idx = req.scene_index_id or config["scene_index_id"]
        target_video = video if vid_id == config["video_id"] else coll.get_video(vid_id)

        context = get_context_at_timestamp(target_video, scene_idx, req.timestamp, window=60)
        scene_text = str(context["scene"].get('response', context["scene"])) if context["scene"] else "No visual context available."
        transcript = context["transcript"] or "No dialogue in this window."

        series = SERIES_REGISTRY.get(req.series_key, {})
        series_context = series.get("series_context", "")

        if req.mode == "scene":
            prompt = build_scene_prompt(scene_text, transcript, req.question, series_context)
            responder = "Scene Companion"
        else:
            # Resolve character
            char_profile = series.get("characters", {}).get(req.character_key)

            if char_profile:
                prompt = build_character_prompt(char_profile, scene_text, transcript, req.question, series_context)
                responder = char_profile["name"]
            else:
                # Custom character fallback
                name = req.custom_character_name or "Unknown Character"
                desc = req.custom_character_description or "A fictional character."
                custom_profile = {"name": name, "profile": f"You are {name}.\n\n{desc}"}
                prompt = build_character_prompt(custom_profile, scene_text, transcript, req.question, series_context)
                responder = name

        result = coll.generate_text(prompt=prompt, model_name="ultra")
        response_text = result.get("output", "").strip()

        return {
            "response": response_text,
            "responder": responder,
            "mode": req.mode,
            "timestamp": req.timestamp,
            "player_url": None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/characters")
async def get_characters(series_key: str = "death_note"):
    series = SERIES_REGISTRY.get(series_key)
    if not series:
        raise HTTPException(status_code=404, detail=f"Series '{series_key}' not found")
    return {
        "series": series["name"],
        "characters": [
            {"key": k, "name": v["name"], "role": v["role"]}
            for k, v in series["characters"].items()
        ]
    }


@app.get("/api/series")
async def get_series():
    return [{"key": k, "name": v["name"]} for k, v in SERIES_REGISTRY.items()]


@app.get("/api/health")
async def health():
    return {"status": "ok"}
