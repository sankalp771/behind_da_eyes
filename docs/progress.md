# CharacterOS — Progress Report

## Project Summary
An interactive AI experience where users pause any anime video, ask a character a question, and get a real response — in that character's **cloned voice**, with a **generated image**, composed into a playable video clip.

**Stack:** FastAPI · VideoDB SDK · Gemma 4 (text) · FLUX (image) · OmniVoice (voice) · React (frontend TBD)

---

## Key IDs (Death Note Ep 6 — Test Case)

| Asset | ID |
|---|---|
| Video (full episode) | `m-z-019e30a2-7ff1-7e51-9b19-653edfda6fb7` |
| Scene Index (60s intervals, GEMMA_4_31B) | `be853dd0ff31d3b0` |
| Voice Reference Audio (YT clip) | `a-z-019e349e-79ac-7b21-806b-b199f4cd4b11` |
| Active Sandbox | `bx-8c107f88f78344fa` |

All saved in `backend/config.json`.

---

## Phase Status

### Phase 0 — Setup & Smoke Test [DONE]
- Python venv + FastAPI + VideoDB hackathon SDK installed
- `.env` configured with `VIDEO_DB_API_KEY`
- Sandbox creation (`SandboxTier.medium`) verified working

### Phase 1 — Ingest Pipeline [DONE]
- Full Death Note Ep 6 uploaded from Archive.org
- **Transcript indexed** (Whisper, word-level) across entire 22-min episode
- **Scene indexed** with `GEMMA_4_31B` at 60-second intervals (22 frames)
  - First attempt at 10s intervals failed (130+ frames hit sandbox limit)
  - Fixed by using 60s intervals — completed successfully
- **Voice reference** uploaded from YouTube clip (Light's early lines)
  - `voice_ref_text` = "Wait, on the off chance someone really dies. Would that make me a murderer?"
  - NOTE: This clip has background music — affects clone fidelity (fix planned)

### Phase 2 — Character Brain (Gemma 4 Text Generation) [DONE]
- `get_context_at_timestamp()` — fetches correct scene bucket + windowed transcript
- `generate_character_monologue()` — uses `coll.generate_text(model_name="ultra")`
- **Test at 96s** ("Why are you working with your father?"):
  - Response was in-character, calculated, used the scene context correctly
- **Test at 1200s** ("Why do you need to eliminate Naomi Misora asap?"):
  - Response correctly identified Naomi as a threat, cited her deductive skills
  - Sounded like Light, not a generic chatbot
- Phase 2 fully validated at multiple timestamps

### Phase 3 — Video Composition [IN PROGRESS]
- `compose_response_video()` implemented in `videodb_utils.py`
- FLUX image generation — working (Light Yagami cinematic image generated)
- OmniVoice voice cloning — timeout issue
  - Root cause: Default SDK timeout is 600s; OmniVoice takes longer on cold sandbox
  - Fix applied: `wait=False` + custom `poll_job()` with 1800s timeout
  - Both jobs now fire async/parallel
  - Currently running in background
- Voice quality: reference clip has background music — needs cleaner source
- Timeline composition (Image + Audio -> Stream URL) confirmed working in first successful run

### Phase 4 — Backend API Routes [NOT STARTED]
- FastAPI `/api/ask` route skeleton exists in `main.py`
- Needs wiring to `compose_response_video()`
- Character config: web scraper for fandom wikis + user input box fallback

### Phase 5 — Frontend (React + Vite) [NOT STARTED]
- Scaffold exists at `characteros/frontend/`
- Needs: custom video player, loading overlay, character input box

### Phase 6 — Polish & Demo [NOT STARTED]

---

## Known Issues & Fixes

| Issue | Fix Applied |
|---|---|
| Scene index timeout on full episode at 10s intervals | Use 60s intervals (22 frames vs 130+) |
| OmniVoice hits 600s SDK timeout | Custom 1800s async poll_job() |
| Voice ref clip has background music | Need clean isolated speech clip |
| Timeline stream URL cannot be re-uploaded as audio | Open — need alternate audio extraction |

---

## File Map

```
characteros/
├── backend/
│   ├── .env                    # API key
│   ├── config.json             # All live IDs for current test
│   ├── main.py                 # FastAPI app + /api/ask route
│   ├── videodb_utils.py        # get_context, compose_response_video, poll_job
│   ├── ingest2.py              # Full ingest pipeline
│   ├── retry_scene_index.py    # Re-runs scene index on existing video
│   ├── get_light_voice.py      # Uploads YT clip for voice ref
│   ├── test_phase2.py          # Tests Character Brain at any timestamp
│   ├── test_phase3.py          # Tests full composition (FLUX + OmniVoice)
│   └── show_index.py           # Prints transcript + scene index samples
├── docs/
│   └── progress.md             # This file
└── frontend/                   # React/Vite (scaffold only)
```

---

## Immediate Next Steps
1. Confirm test_phase3.py succeeds with 1800s timeout
2. Find clean voice reference for Light (no background music)
3. Phase 4 — finalize /api/ask, add /api/status polling endpoint
4. Phase 5 — build React video player UI
