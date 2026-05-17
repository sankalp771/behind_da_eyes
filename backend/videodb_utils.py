"""
BehindTheEyes — Context Retrieval Utilities

Proper scene alignment: finds the scene whose time range contains (or is
closest to) the requested timestamp — not a naive integer division.
"""


def get_context_at_timestamp(video, scene_index_id: str, timestamp: int, window: int = 60) -> dict:
    """
    Retrieves scene description and transcript window at a given timestamp.

    Scene alignment: iterates the scene index to find the entry whose
    [start, end] range contains the timestamp. Falls back to the closest
    scene by start time if none fully contains it.
    """
    scene_index = video.get_scene_index(scene_index_id)

    # --- Real scene alignment ---
    best_scene = None
    best_distance = float('inf')

    for scene in scene_index:
        try:
            start = float(scene.get('start', 0))
            end   = float(scene.get('end', start + 60))
        except (TypeError, AttributeError):
            # scene might be an object, try attribute access
            try:
                start = float(getattr(scene, 'start', 0))
                end   = float(getattr(scene, 'end',   start + 60))
            except Exception:
                continue

        # Perfect match: timestamp is inside this scene's window
        if start <= timestamp <= end:
            best_scene = scene
            break

        # Otherwise track the closest by start time
        distance = abs(start - timestamp)
        if distance < best_distance:
            best_distance = distance
            best_scene = scene

    # --- Transcript window ---
    try:
        transcript = video.get_transcript()
    except Exception:
        transcript = []

    window_start = max(0, timestamp - window)
    lines = []
    for line in transcript:
        try:
            t = float(line.get('start', 0))
        except (TypeError, AttributeError):
            try:
                t = float(getattr(line, 'start', 0))
            except Exception:
                continue
        if window_start <= t <= timestamp:
            text = line.get('text') or getattr(line, 'text', '')
            if text:
                lines.append(text.strip())

    # Flatten the scene to a readable string
    scene_text = None
    if best_scene is not None:
        if isinstance(best_scene, dict):
            scene_text = best_scene.get('response') or best_scene.get('description') or str(best_scene)
        else:
            scene_text = getattr(best_scene, 'response', None) or getattr(best_scene, 'description', None) or str(best_scene)

    return {
        "scene":      scene_text or "No visual context available.",
        "transcript": " ".join(lines) if lines else "No dialogue in this window.",
        "timestamp":  timestamp,
    }
