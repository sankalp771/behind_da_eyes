import os
import json
import argparse
from dotenv import load_dotenv
from videodb import connect, SandboxTier, SandboxModel, SceneExtractionType
from videodb_utils import extract_voice_ref

load_dotenv()

def get_transcript_text_for_range(video, start_sec: int, end_sec: int) -> str:
    transcript = video.get_transcript()
    words = []
    for l in transcript:
        # Some transcripts have words, some have segments. Let's look at lines.
        start = float(l.get('start', 0))
        end = float(l.get('end', 0))
        # If the line overlaps with our range
        if start <= end_sec and end >= start_sec:
            words.append(l.get('text', '').strip())
    return " ".join(words)

def run_ingest(url: str, start_sec: int, end_sec: int):
    api_key = os.environ.get("VIDEO_DB_API_KEY")
    conn = connect(api_key=api_key)
    coll = conn.get_collection()

    print("Creating sandbox...")
    sandbox = conn.create_sandbox(tier=SandboxTier.medium)
    sandbox.wait_for_ready(timeout=300, interval=5)
    print(f"Sandbox ready: {sandbox.id}")

    try:
        print(f"Uploading source video from {url}...")
        video = coll.upload(url)
        print(f"Video uploaded. ID: {video.id}")

        print("Starting Transcript Indexing...")
        video.index_spoken_words()
        print("Transcript indexing complete.")

        print("Fetching transcript text for voice reference...")
        ref_text = get_transcript_text_for_range(video, start_sec, end_sec)
        print(f"Extracted Reference Text: {ref_text}")

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

    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        print("Stopping sandbox...")
        sandbox.stop()
        print("Sandbox stopped.")

if __name__ == "__main__":
    url = "https://archive.org/download/death-note-complete-2006-2007/E06%20-%20Unraveling.mkv"
    run_ingest(url, 1213, 1238)
