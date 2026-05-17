import os
import json
from dotenv import load_dotenv
from videodb import connect, SandboxTier, SandboxModel, SceneExtractionType

load_dotenv()

def retry_index():
    api_key = os.environ.get("VIDEO_DB_API_KEY")
    conn = connect(api_key=api_key)
    coll = conn.get_collection()

    with open('config.json', 'r') as f:
        config = json.load(f)

    video_id = config["video_id"]
    video = coll.get_video(video_id)

    print("Creating sandbox...")
    sandbox = conn.create_sandbox(tier=SandboxTier.medium)
    sandbox.wait_for_ready(timeout=300, interval=5)
    print(f"Sandbox ready: {sandbox.id}")

    try:
        print("Starting Scene Indexing (GEMMA_4_31B) with 60s intervals to avoid timeout...")
        # For a 22 minute video, this means 22 frames instead of 132
        scene_index_id = video.index_scenes(
            extraction_type=SceneExtractionType.time_based,
            extraction_config={"time": 60, "select_frames": ["first"], "frame_count": 1},
            model_name=SandboxModel.GEMMA_4_31B,
            prompt="""Analyze this anime scene frame. Return:
- Characters present and their visible emotional state
- What just happened or is actively happening
- Tension level and mood
- Any visible actions or body language that reveal inner state
Be vivid and specific. This will be used for character psychology.""",
            sandbox_id=sandbox.id,
        )
        print(f"Scene indexing complete. ID: {scene_index_id}")

        config["scene_index_id"] = scene_index_id
        config["sandbox_id"] = sandbox.id

        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        print("\n--- SCENE INDEX ---")
        scene_index = video.get_scene_index(scene_index_id)
        for i, scene in enumerate(scene_index[:3]):
            print(f"\nScene {i+1} (approx {i*60}s):")
            scene_data = scene.get('response', scene)
            if isinstance(scene_data, dict):
                for k, v in scene_data.items():
                    print(f"{k.capitalize()}: {v}")
            else:
                print(scene_data)

    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        print("Stopping sandbox...")
        sandbox.stop()
        print("Sandbox stopped.")

if __name__ == "__main__":
    retry_index()
