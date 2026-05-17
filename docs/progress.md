# BehindTheEyes Progress Report

_Last updated: 2026-05-17_

## Current Product

BehindTheEyes is a text-only companion for watching video. A user loads a video/player, enters the show or series title, picks a character, pauses at a timestamp, and asks either:

- a character, who answers in-character using model knowledge plus the current scene context
- a scene companion, who explains context, subtext, and what the viewer may be missing

The demo scope is deliberately text-only. Voice, generated video responses, and timeline composition are not part of the hackathon demo.

## What Works Now

- FastAPI backend with `/api/ask`, `/api/characters`, and `/api/health`
- React/Vite single-screen frontend
- Show-title based character generation through VideoDB `coll.generate_text`
- Scene/transcript grounding from the active VideoDB video and scene index
- Real scene lookup by `start`/`end` ranges in `video.get_scene_index(...)`
- Transcript window lookup from the last 60 seconds before the selected timestamp
- Character mode and scene mode
- YouTube watch links normalized to embeddable player links in the frontend
- Local file playback option in the frontend for demo viewing

## Active VideoDB Asset

The current backend is configured against a single indexed test asset:

| Asset | ID |
|---|---|
| Video | `m-z-019e30a2-7ff1-7e51-9b19-653edfda6fb7` |
| Scene Index | `be853dd0ff31d3b0` |

These IDs live in `backend/config.json`.

## Important Limitations

- The backend does not yet ingest a new URL or uploaded file from the UI.
- Loading a different YouTube/local video in the frontend only changes playback. Q&A still uses the active VideoDB IDs unless the backend config or request IDs are changed.
- Character generation is dynamic from show title, but it depends on model knowledge and prompt quality; it is not a fully verified character database.
- Scene index quality depends on the existing indexing interval and prompt. The current index is useful, but not a precise shot-by-shot cinematic timeline.
- External iframes do not reliably emit pause timestamps, so the timestamp remains manually editable.

## VideoDB APIs Used In The Demo

| API | Use |
|---|---|
| `coll.generate_text(...)` | Generate character lists and final text responses |
| `video.get_scene_index(scene_index_id)` | Retrieve visual scene descriptions |
| `video.get_transcript()` | Retrieve dialogue around the selected timestamp |

## Next Work

1. Add a backend ingest endpoint for URL and file upload using `coll.upload(url=...)` or `coll.upload(file_path=...)`.
2. After ingest, run `video.index_spoken_words(force=True)` and `video.index_scenes(...)`, then return `video_id`, `scene_index_id`, and a VideoDB player URL.
3. Wire the frontend Load/File controls to that ingest endpoint so playback and Q&A use the same asset.
4. Add an evidence/debug panel showing the exact scene range and transcript window used for each answer.
5. Keep pitch language aligned to the shipped text-only product unless voice/video generation is restored and demo-proven.
