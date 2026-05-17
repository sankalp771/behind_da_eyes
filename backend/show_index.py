import os
import json
from dotenv import load_dotenv
from videodb import connect

load_dotenv()

def show_index():
    api_key = os.environ.get("VIDEO_DB_API_KEY")
    conn = connect(api_key=api_key)
    coll = conn.get_collection()

    with open('config.json', 'r') as f:
        config = json.load(f)

    video_id = config["video_id"]
    scene_index_id = config["scene_index_id"]

    video = coll.get_video(video_id)
    
    print("\n--- TRANSCRIPT (First 10 lines) ---")
    transcript = video.get_transcript()
    for l in transcript[:10]:
        print(f"[{l.get('start', 0):.2f} - {l.get('end', 0):.2f}] {l.get('text', '').strip()}")
    
    print("\n--- SCENE INDEX (First 3 scenes) ---")
    scene_index = video.get_scene_index(scene_index_id)
    for i, scene in enumerate(scene_index[:3]):
        print(f"\nScene {i+1} (approx {i*10}s):")
        
        # Format the dictionary response for readability
        scene_data = scene.get('response', scene)
        if isinstance(scene_data, dict):
            for k, v in scene_data.items():
                print(f"{k.capitalize()}: {v}")
        else:
            print(scene_data)

if __name__ == "__main__":
    show_index()
