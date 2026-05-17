import time
from videodb.editor import Timeline, Track, Clip, VideoAsset

def get_context_at_timestamp(video, scene_index_id: str, timestamp: int, window: int = 60):
    scene_index = video.get_scene_index(scene_index_id)
    chunk = timestamp // 60
    scene = scene_index[min(chunk, len(scene_index) - 1)]

    transcript = video.get_transcript()
    window_start = max(0, timestamp - window)
    
    lines = []
    for l in transcript:
        start = float(l.get('start', 0))
        if window_start <= start <= timestamp:
            lines.append(l.get('text', ''))

    return {
        "scene": scene,
        "transcript": " ".join(lines),
        "timestamp": timestamp
    }

def extract_voice_ref(conn, coll, video, start_sec: int, end_sec: int, ref_transcript: str):
    tl = Timeline(conn)
    t = Track()
    t.add_clip(0, Clip(asset=VideoAsset(id=video.id, start=start_sec), duration=(end_sec - start_sec)))
    tl.add_track(t)
    ref_url = tl.generate_stream()
    ref_audio = coll.upload(url=ref_url, media_type="audio")
    return ref_audio.id, ref_transcript

def poll_job(job, label: str, timeout: int = 1800, interval: int = 10):
    """Poll a GenerationJob until done. Prints progress. Returns the asset."""
    deadline = time.time() + timeout
    elapsed = 0
    while True:
        job.refresh()
        if job.status != "processing":
            break
        if time.time() >= deadline:
            raise TimeoutError(f"{label} did not complete within {timeout}s")
        print(f"  [{label}] still processing... ({elapsed}s elapsed)")
        time.sleep(interval)
        elapsed += interval
    
    if job.status == "failed":
        raise RuntimeError(f"{label} FAILED: {job.data}")
    
    print(f"  [{label}] DONE [OK]")
    return job._to_asset()

def compose_response_video(
    conn,
    coll,
    sandbox_id: str,
    monologue_text: str,
    voice_ref_id: str,
    voice_ref_text: str,
    image_prompt: str
) -> str:
    from videodb import SandboxModel
    from videodb.editor import Timeline, Track, Clip, ImageAsset, AudioAsset, Fit

    # --- Fire both jobs async (no wait) ---
    print("Firing FLUX image generation (async)...")
    image_job = coll.generate_image(
        prompt=image_prompt,
        model_name="black-forest-labs/FLUX.1-dev",
        sandbox_id=sandbox_id,
        aspect_ratio="16:9",
        wait=False   # async — returns GenerationJob
    )
    print(f"  Image job dispatched: {image_job.job_id}")

    print("Firing OmniVoice voice cloning (async)...")
    ref_audio = coll.get_audio(voice_ref_id)
    voice_job = coll.generate_voice(
        text=monologue_text,
        model_name=SandboxModel.OMNIVOICE,
        sandbox_id=sandbox_id,
        config={
            "ref_audio": ref_audio.generate_url(),
            "ref_text": voice_ref_text
        },
        wait=False   # async — returns GenerationJob
    )
    print(f"  Voice job dispatched: {voice_job.job_id}")

    # --- Poll both (up to 30 minutes each) ---
    print("\nPolling for results (up to 30 min each)...")
    image_asset = poll_job(image_job, "FLUX Image", timeout=1800)
    voice_asset = poll_job(voice_job, "OmniVoice", timeout=1800)

    # --- Compose on Timeline ---
    print("\nComposing Timeline...")
    duration = float(voice_asset.length)

    timeline = Timeline(conn)

    image_track = Track()
    image_track.add_clip(0, Clip(
        asset=ImageAsset(id=image_asset.id),
        duration=duration,
        fit=Fit.crop
    ))
    timeline.add_track(image_track)

    audio_track = Track()
    audio_track.add_clip(0, Clip(
        asset=AudioAsset(id=voice_asset.id),
        duration=duration
    ))
    timeline.add_track(audio_track)

    stream_url = timeline.generate_stream()
    return stream_url
