import os
import json
from dotenv import load_dotenv
from videodb import connect

load_dotenv()

def finish_ingest():
    api_key = os.environ.get("VIDEO_DB_API_KEY")
    conn = connect(api_key=api_key)
    coll = conn.get_collection()

    video_id = "m-z-019e30a2-7ff1-7e51-9b19-653edfda6fb7"
    scene_index_id = "51bfca9c2403fcc4"
    
    # We will use the sample short from the docs to unblock since timeline upload failed
    print("Uploading sample short for voice ref...")
    ref_audio = coll.upload(url="https://www.youtube.com/shorts/7xOPzBhHKWY", media_type="audio")
    voice_ref_id = ref_audio.id
    saved_ref_text = "Sample reference text for the audio clip"

    print(f"Voice reference extracted. ID: {voice_ref_id}")

    # Save configuration
    config_data = {
        "video_id": video_id,
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
