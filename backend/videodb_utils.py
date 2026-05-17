from videodb.editor import Timeline, Track, Clip, VideoAsset

def get_context_at_timestamp(video, scene_index_id: str, timestamp: int, window: int = 60):
    scene_index = video.get_scene_index(scene_index_id)
    chunk = timestamp // 60
    scene = scene_index[min(chunk, len(scene_index) - 1)]

    transcript = video.get_transcript()
    window_start = max(0, timestamp - window)
    
    lines = []
    for l in transcript:
        # Assuming l is a dict with 'start', 'end', 'text'
        start = float(l.get('start', 0))
        if window_start <= start <= timestamp:
            lines.append(l.get('text', ''))

    return {
        "scene": scene,
        "transcript": " ".join(lines),
        "timestamp": timestamp
    }

def extract_voice_ref(conn, coll, video, start_sec: int, end_sec: int, ref_transcript: str):
    """
    Extracts a clean audio clip from the video to serve as a voice reference.
    """
    tl = Timeline(conn)
    t = Track()
    t.add_clip(0, Clip(asset=VideoAsset(id=video.id, start=start_sec), duration=(end_sec - start_sec)))
    tl.add_track(t)
    ref_url = tl.generate_stream()

    ref_audio = coll.upload(url=ref_url, media_type="audio")
    return ref_audio.id, ref_transcript
