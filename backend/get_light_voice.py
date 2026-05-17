import os
import json
from dotenv import load_dotenv
from videodb import connect

load_dotenv()

def run():
    api_key = os.environ.get("VIDEO_DB_API_KEY")
    conn = connect(api_key=api_key)
    coll = conn.get_collection()

    url = "https://youtu.be/VnvwpqDEY7g"
    print("Uploading as video to get transcript...")
    video = coll.upload(url=url)
    
    print("Fetching transcript...")
    video.index_spoken_words()
    transcript = video.get_transcript()
    
    words = []
    for l in transcript:
        start = float(l.get('start', 0))
        end = float(l.get('end', 0))
        if start <= 16.0 and end >= 0.0:
            words.append(l.get('text', '').strip())
    
    ref_text = " ".join(words)
    print(f"Extracted Reference Text: {ref_text}")

    print("Uploading as audio for OmniVoice...")
    audio = coll.upload(url=url, media_type="audio")

    with open('config.json', 'r') as f:
        config = json.load(f)
    
    config["light_yagami"]["voice_ref_id"] = audio.id
    config["light_yagami"]["voice_ref_text"] = ref_text
    
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
        
    print("Config updated with real Light Yagami voice!")

if __name__ == "__main__":
    run()
