import os
import json
from dotenv import load_dotenv
from videodb import connect

from videodb_utils import get_context_at_timestamp
from main import generate_character_monologue

load_dotenv()

def run_test():
    api_key = os.environ.get("VIDEO_DB_API_KEY")
    conn = connect(api_key=api_key)
    coll = conn.get_collection()

    with open('config.json', 'r') as f:
        config = json.load(f)

    video_id = config["video_id"]
    scene_index_id = config["scene_index_id"]
    sandbox_id = config["sandbox_id"]
    
    # In a full app, the character config would be fetched from a DB 
    # based on the video being watched, allowing any series/character.
    char = config["light_yagami"] 
    
    video = coll.get_video(video_id)

    # Simulate user pausing at 20:00 (1200 seconds)
    timestamp = 1200
    user_question = "Why do you need to eliminate Naomi Misora asap?"

    print(f"--- Simulating Request at {timestamp}s ---")
    print(f"User Question: '{user_question}'\n")

    # Fetch Context
    print("Fetching Context from VideoDB...")
    context = get_context_at_timestamp(video, scene_index_id, timestamp, window=60)
    
    scene_text = str(context["scene"].get('response', context["scene"])) if context["scene"] else "No visual context available."

    print("\n--- Internal Monologue Generation (Gemma 4) ---")
    monologue = generate_character_monologue(
        sandbox_id=sandbox_id,
        character_name=char["name"],
        character_description=char["description"],
        scene=scene_text,
        transcript=context["transcript"],
        user_question=user_question
    )

    print("\n--- RESULTING RESPONSE ---")
    print(f"Light Yagami says: {monologue}")

if __name__ == "__main__":
    run_test()
