import os
import json
import argparse
from dotenv import load_dotenv
from videodb import connect, SandboxTier, SandboxModel, SceneExtractionType
from videodb_utils import extract_voice_ref

load_dotenv()

def run_ingest(youtube_url: str, start_sec: int, end_sec: int, ref_text: str):
    api_key = os.environ.get("VIDEO_DB_API_KEY")
    conn = connect(api_key=api_key)
    coll = conn.get_collection()

    print("Creating sandbox...")
    sandbox = conn.create_sandbox(tier=SandboxTier.medium)
    sandbox.wait_for_ready(timeout=300, interval=5)
    print(f"Sandbox ready: {sandbox.id}")

    try:
        print(f"Uploading source video from {youtube_url}...")
        video = coll.upload(youtube_url)
        print(f"Video uploaded. ID: {video.id}")

        print("Starting Scene Indexing (GEMMA_4_31B)...")
        scene_index_id = video.index_scenes(
            extraction_type=SceneExtractionType.time_based,
            extraction_config={"time": 10, "select_frames": ["first"], "frame_count": 1},
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

        print("Starting Transcript Indexing...")
        video.index_spoken_words()
        print("Transcript indexing complete.")

        print("Extracting voice reference...")
        voice_ref_id, saved_ref_text = extract_voice_ref(conn, coll, video, start_sec, end_sec, ref_text)
        print(f"Voice reference extracted. ID: {voice_ref_id}")

        # Save configuration
        config_data = {
            "video_id": video.id,
            "scene_index_id": scene_index_id,
            "light_yagami": {
                "name": "Light Yagami",
                "description": "A genius who believes he is a god of justice. Calculating, cold, charismatic. He eliminates threats with zero hesitation and justifies everything through his vision of a perfect world.",
                "video_prompt": "Light Yagami anime character, extreme close-up, staring directly into camera, intense calculating eyes, dramatic chiaroscuro lighting, Death Note anime style, dark background, cinematic, high detail",
                "voice_ref_id": voice_ref_id,
                "voice_ref_text": saved_ref_text
            }
        }

        with open('config.json', 'w') as f:
            json.dump(config_data, f, indent=4)
        
        print("Ingest complete. Saved to config.json.")

    finally:
        print("Stopping sandbox...")
        sandbox.stop()
        print("Sandbox stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest video and create indexes.")
    parser.add_argument("--url", type=str, required=True, help="YouTube URL to ingest")
    parser.add_argument("--start", type=int, required=True, help="Start second for voice ref")
    parser.add_argument("--end", type=int, required=True, help="End second for voice ref")
    parser.add_argument("--text", type=str, required=True, help="Transcript of voice ref")
    args = parser.parse_args()

    run_ingest(args.url, args.start, args.end, args.text)
