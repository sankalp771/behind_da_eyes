import os
import json
from dotenv import load_dotenv
from videodb import connect, SandboxTier, SandboxModel
from videodb_utils import extract_voice_ref, get_context_at_timestamp
from videodb.video import Video

load_dotenv()

def finish_ingest():
    api_key = os.environ.get("VIDEO_DB_API_KEY")
    conn = connect(api_key=api_key)
    coll = conn.get_collection()

    video_id = "m-z-019e30a2-7ff1-7e51-9b19-653edfda6fb7"
    scene_index_id = "51bfca9c2403fcc4"
    start_sec = 1226
    end_sec = 1238

    print("Fetching video...")
    video = coll.get_video(video_id)
    
    transcript = video.get_transcript()
    words = []
    for l in transcript:
        # Some transcripts have words, some have segments. Let's look at lines.
        start = float(l.get('start', 0))
        end = float(l.get('end', 0))
        # If the line overlaps with our range
        if start <= end_sec and end >= start_sec:
            words.append(l.get('text', '').strip())
    ref_text = " ".join(words)
    print(f"Extracted Reference Text: {ref_text}")

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

if __name__ == "__main__":
    finish_ingest()
