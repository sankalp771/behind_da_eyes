import os
import json
from dotenv import load_dotenv
from videodb import connect

from videodb_utils import compose_response_video

load_dotenv()

def run_test():
    api_key = os.environ.get("VIDEO_DB_API_KEY")
    conn = connect(api_key=api_key)
    coll = conn.get_collection()

    with open('config.json', 'r') as f:
        config = json.load(f)

    sandbox_id = config["sandbox_id"]
    char = config["light_yagami"]
    
    # We will use the exact monologue generated from Phase 2
    monologue = "Naomi Misora is a threat to my vision of a perfect world. Her intuition and investigative skills are dangerously close to uncovering my identity as Kira. If she continues to dig, she could unravel everything I've meticulously built. Eliminating her is not just necessary; it's imperative to maintain control and ensure justice prevails."

    print("--- Phase 3: Composing Video Response ---")
    try:
        # Check if sandbox is active
        try:
            sandbox = conn.get_sandbox(sandbox_id)
            if not sandbox.is_active:
                print("Starting new sandbox...")
                sandbox = conn.create_sandbox(tier="medium")
                sandbox.wait_for_ready(timeout=300)
                config["sandbox_id"] = sandbox.id
                with open('config.json', 'w') as f:
                    json.dump(config, f, indent=4)
        except Exception:
            print("Starting new sandbox...")
            sandbox = conn.create_sandbox(tier="medium")
            sandbox.wait_for_ready(timeout=300)
            config["sandbox_id"] = sandbox.id
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)

        stream_url = compose_response_video(
            conn=conn,
            coll=coll,
            sandbox_id=sandbox.id,
            monologue_text=monologue,
            voice_ref_id=char["voice_ref_id"],
            voice_ref_text=char["voice_ref_text"],
            image_prompt=char["video_prompt"]
        )
        
        print("\n--- PHASE 3 SUCCESS ---")
        print("You can watch the fully composed response video here:")
        print(stream_url)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_test()
