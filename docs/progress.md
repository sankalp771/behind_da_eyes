# CharacterOS — Progress Report

_Last updated: 2026-05-17_

## Project Summary
An interactive AI experience where users pause any video, ask a character or the scene a question, and get a rich, knowledgeable, in-character text response — powered by VideoDB's transcript + scene indexing + Gemma 4.

**Hackathon scope (decided):** Text response only. No voice/image/video generation for the demo.

**Stack:** FastAPI · VideoDB SDK (hackathon branch) · Gemma 4 (`generate_text ultra`) · React + Vite

---

## Key IDs (Death Note Ep 6 — Test Case)

| Asset | ID |
|---|---|
| Video (full episode, Archive.org) | `m-z-019e30a2-7ff1-7e51-9b19-653edfda6fb7` |
| Scene Index (60s intervals, GEMMA_4_31B) | `be853dd0ff31d3b0` |
| Voice Reference (YT clip, parked) | `a-z-019e349e-79ac-7b21-806b-b199f4cd4b11` |
| Last Sandbox (parked) | `bx-8c107f88f78344fa` |

All IDs live in `backend/config.json`.

---

## Phase Status

### Phase 0 — Setup [DONE]
- Python venv, FastAPI, VideoDB hackathon SDK installed
- `.env` with `VIDEO_DB_API_KEY`
- Sandbox creation verified via smoke test

### Phase 1 — Ingest Pipeline [DONE]
- Full Death Note Ep 6 uploaded from Archive.org
- **Transcript indexed** (Whisper, word-level) across full 22-minute episode
- **Scene indexed** with `GEMMA_4_31B` at 60-second intervals → 22 frames analysed
  - Each frame returns: characters visible, emotional states, tension level, body language
- Voice reference audio uploaded and parked (not used in text-only demo)

### Phase 2 — Character Brain [DONE + ENHANCED]
- `get_context_at_timestamp(video, scene_index_id, timestamp, window=60)`
  - Retrieves the correct 60s scene chunk from the index
  - Retrieves windowed transcript (last 60s of dialogue)
- `generate_character_monologue()` → replaced by full prompt system (see Phase 4 backend work)
- Validated at multiple timestamps including the Naomi Misora scene (~20:00)

### Phase 3 — Video Composition [PARKED for hackathon]
- `compose_response_video()` built in `videodb_utils.py`
- FLUX image gen + OmniVoice voice cloning + Timeline compositor all implemented
- Blocked by: OmniVoice job duration > sandbox timeout; voice reference clip has background music
- **Decision: skip for this hackathon. Text-only demo is the product.**
- Code remains in place for post-hackathon iteration

### Phase 4 — Frontend UI [DONE]
Full single-screen React app with 4 states:

| State | What shows |
|---|---|
| `idle` | Player with `?` button overlaid top-right |
| `modal` | Ask modal with mode toggle, character dropdown, timestamp input, question textarea |
| `processing` | Pulsing overlay on player: "[Character] is thinking..." |
| `playing` | Response card appears above player with character name + mode badge |

**Features built:**
- VideoDB stream URL input → loads into iframe player
- `?` button rendered in a `pointer-events: none` overlay above the iframe (always visible)
- **Character dropdown** — populated live from `/api/characters` endpoint
- **Mode toggle**: Character mode / Scene mode
- **Character profile editor** for custom characters (any series)
- Response card: gold border for character responses, blue border for scene responses
- Vite proxy configured: `/api/*` → `http://localhost:8000`

### Phase 4 — Backend Character System [DONE — major upgrade]

**New file: `characters.py`**
- Full psychological profiles for 7 Death Note characters:
  - Light Yagami, L, Ryuk, Misa Amane, Near, Soichiro Yagami, Naomi Misora
  - Each profile includes: inner mindset, relationships, secrets, speech style, how they see others
- `SERIES_REGISTRY` dict — extensible to any series (AOT, Code Geass, etc.)
- Two prompt modes:
  - **Character mode** — character speaks as themselves with full self-knowledge; natural, not cinematic
  - **Scene mode** — omniscient companion who's already seen everything; explains context, subtext, motivations, foreshadowing

**Updated `main.py`**
- `POST /api/ask` — accepts `mode`, `character_key`, `series_key`, `custom_character_name/description`
- `GET /api/characters?series_key=death_note` — returns character list for frontend dropdown
- `GET /api/series` — returns available series
- `GET /api/health`
- Generic: character is never hardcoded; any character from any series can be used

### Phase 5 — Integration [IN PROGRESS]
- Vite proxy wired, backend running, frontend hitting `/api/ask` correctly
- Response text displays in card above player
- Timestamp capture: manual input in modal (external players don't fire postMessage)
  - When using VideoDB's official player URL, postMessage auto-capture will work
- Next: test full loop end-to-end with a real VideoDB player URL

### Phase 6 — Polish [NOT STARTED]

---

## Two Core Product Modes

### Character Mode
> "You're watching a show and the character can actually talk back to you."

The character knows:
- Their full backstory and secrets
- Their relationships with every other character
- What's happening in the current scene
- What was said in the last 60 seconds
- What you just asked them

They respond in their own voice — not a dramatic speech, just *them*.

### Scene Mode
> "You're watching it with someone who's already seen it."

The companion knows:
- What's actually happening vs. what appears to be happening
- What every character is really thinking
- The thematic significance of this moment
- What led here and where it's going
- What the viewer might be missing

---

## Known Issues & Decisions

| Item | Status |
|---|---|
| OmniVoice timeout (>600s) | Parked — text-only for hackathon |
| Voice ref has background music | Parked |
| Scene index failed at 10s intervals on 22-min video | Fixed — use 60s intervals |
| Timeline stream URL can't be re-uploaded as audio | Open — not needed for text demo |
| Timestamp always 0:00 for external players | Workaround — manual editable input in modal |

---

## File Map

```
characteros/
├── backend/
│   ├── .env                      # API key
│   ├── config.json               # Live IDs (video, scene index, voice ref, sandbox)
│   ├── main.py                   # FastAPI app — /api/ask, /api/characters, /api/series
│   ├── characters.py             # Character profiles + prompt builders (scene/character mode)
│   ├── videodb_utils.py          # get_context_at_timestamp, compose_response_video, poll_job
│   ├── ingest2.py                # Full ingest pipeline (upload → index → voice ref)
│   ├── retry_scene_index.py      # Re-runs scene index on existing video
│   ├── get_light_voice.py        # YT clip → voice ref audio
│   ├── test_phase2.py            # Tests Character Brain at any timestamp
│   ├── test_phase3.py            # Tests FLUX + OmniVoice composition (parked)
│   └── show_index.py             # Prints transcript + scene index samples
├── docs/
│   └── progress.md               # This file
└── frontend/
    ├── vite.config.js             # Proxy: /api → localhost:8000
    ├── .env                       # VITE_PLAYER_URL default
    └── src/
        ├── index.css              # Global dark theme + CSS variables
        ├── App.css                # All component styles
        └── App.jsx                # Full UI — 4 states, mode toggle, char dropdown, response card
```

---

## Immediate Next Steps
1. End-to-end test: paste a real player URL → ask L about Light → verify response quality
2. Test Scene mode at the Naomi scene (~20:00)
3. Add more series to `SERIES_REGISTRY` (e.g. Attack on Titan) for demo breadth
4. Phase 5 polish: error handling, loading states, mobile layout check
