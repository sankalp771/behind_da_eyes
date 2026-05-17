# CharacterOS

> Pause any anime. Ask a character. They'll talk back.

CharacterOS is an interactive viewing experience built on [VideoDB](https://videodb.io). Upload any anime episode, pause it at any moment, and ask a character a question — or ask the scene itself what's happening. The AI responds with full knowledge of who the character is, what's happening on screen right now, and what was said in the last minute.

It's like watching anime with someone who's already seen it.

---

## Demo

**Two modes:**

- **Character mode** — select a character from the episode (Light Yagami, L, Ryuk, Misa, Near...). They respond as themselves — with their full psychology, secrets, and relationships — directly to you.
- **Scene mode** — a knowledgeable companion explains what's actually happening: subtext, character motivations, what you might be missing, themes.

**Tested on:** Death Note Episode 6 — *Unraveling*

---

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- [VideoDB API key](https://videodb.io) (hackathon sandbox key)

### Backend

```bash
cd characteros/backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install videodb fastapi uvicorn python-dotenv pydantic

cp .env.example .env
# Add your VIDEO_DB_API_KEY to .env

uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd characteros/frontend
npm install
npm run dev
```

Open `http://localhost:5173`

### Ingest a new video

```bash
cd characteros/backend
python ingest2.py
```

This uploads the episode, indexes the transcript (Whisper) and scenes (GEMMA_4_31B at 60s intervals), and saves all IDs to `config.json`.

---

## VideoDB APIs Used

| API | Purpose |
|---|---|
| `coll.upload(url=...)` | Upload full anime episode from URL |
| `video.index_spoken_words()` | Whisper transcript across full episode |
| `video.index_scenes(...)` | Visual scene analysis with GEMMA_4_31B at 60s intervals |
| `video.get_transcript()` | Retrieve dialogue for a timestamp window |
| `video.get_scene_index(id)` | Retrieve scene descriptions for context |
| `coll.generate_text(prompt, model_name="ultra")` | Gemma 4 text generation for character responses |

---

## Architecture

```
User pauses video at timestamp T
         │
         ▼
  POST /api/ask  {timestamp, question, mode, character_key}
         │
         ├── get_context_at_timestamp(video, scene_index_id, T, window=60)
         │     ├── scene bucket from 60s scene index
         │     └── transcript lines from last 60s
         │
         ├── build_character_prompt() or build_scene_prompt()
         │     └── full character profile + scene + transcript + question
         │
         └── coll.generate_text(prompt, model_name="ultra")
                   │
                   ▼
         Response displayed in card above player
```

---

## Adding a New Series

In `backend/characters.py`:

```python
SERIES_REGISTRY["attack_on_titan"] = {
    "name": "Attack on Titan",
    "series_context": "...",
    "characters": {
        "eren_yeager": {
            "name": "Eren Yeager",
            "role": "Protagonist",
            "series": "Attack on Titan",
            "profile": "You are Eren Yeager..."
        }
    }
}
```

The frontend `/api/characters?series_key=attack_on_titan` will automatically serve the character list.

---

## Project Structure

```
characteros/
├── backend/
│   ├── main.py           # FastAPI — /api/ask, /api/characters, /api/series
│   ├── characters.py     # Character profiles + prompt builders
│   ├── videodb_utils.py  # Context retrieval + composition utilities
│   ├── ingest2.py        # Ingest pipeline (upload → index)
│   ├── config.json       # Live video/scene index IDs
│   └── .env.example
├── docs/
│   └── progress.md       # Full build log
└── frontend/
    ├── vite.config.js    # Proxy /api → :8000
    └── src/
        ├── App.jsx       # Full UI
        └── App.css       # Styles
```

---

Built for the **VideoDB Hackathon** · May 2026
