import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from videodb import connect, SandboxModel

from videodb_utils import get_context_at_timestamp

load_dotenv()

app = FastAPI()

with open('config.json', 'r') as f:
    config = json.load(f)

api_key = os.environ.get("VIDEO_DB_API_KEY")
conn = connect(api_key=api_key)
coll = conn.get_collection()

video = coll.get_video(config["video_id"])

class AskRequest(BaseModel):
    timestamp: int
    question: str

def generate_character_monologue(
    sandbox_id: str,
    character_name: str,
    character_description: str,
    scene: str,
    transcript: str,
    user_question: str
) -> str:
    prompt = f"""You are {character_name}.

WHO YOU ARE:
{character_description}

WHAT JUST HAPPENED AROUND YOU:
{scene}

WHAT YOU AND OTHERS SAID IN THE LAST MINUTE:
{transcript}

SOMEONE IS WATCHING YOU. THEY ASKED:
"{user_question}"

Respond as {character_name} speaking directly to this person — breaking the fourth wall, as if they can hear your inner thoughts. This is your internal monologue made audible.

Rules:
- First person. Direct. You are speaking TO them.
- Stay completely in your character's logic and voice.
- 3–4 sentences only. This will be spoken aloud as audio.
- Do not explain yourself generically. Respond specifically to what just happened.
- Do not acknowledge being fictional or AI."""

    # Using SandboxModel.GEMMA_4_31B as model_name for sandbox generation
    job = coll.generate_text(
        prompt=prompt,
        model_name="ultra"
    )
    return job.get("output", "")

@app.post("/api/ask")
async def ask_character(req: AskRequest):
    try:
        # Get context leading up to timestamp
        context = get_context_at_timestamp(video, config["scene_index_id"], req.timestamp, window=60)
        
        char = config["light_yagami"]
        
        # Manage Sandbox state
        try:
            sandbox = conn.get_sandbox(config["sandbox_id"])
            if not sandbox.is_active:
                sandbox = conn.create_sandbox(tier="medium")
                sandbox.wait_for_ready(timeout=300)
                config["sandbox_id"] = sandbox.id
                with open('config.json', 'w') as f:
                    json.dump(config, f, indent=4)
        except Exception:
            sandbox = conn.create_sandbox(tier="medium")
            sandbox.wait_for_ready(timeout=300)
            config["sandbox_id"] = sandbox.id
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)

        scene_text = str(context["scene"].get('response', context["scene"])) if context["scene"] else "No visual context available."
        
        # Build Character Brain Response
        monologue = generate_character_monologue(
            sandbox_id=sandbox.id,
            character_name=char["name"],
            character_description=char["description"],
            scene=scene_text,
            transcript=context["transcript"],
            user_question=req.question
        )
        
        return {"monologue": monologue, "context": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
