# BehindTheEyes

Pause any show. Ask the characters. They talk back.

BehindTheEyes uses [VideoDB](https://videodb.io) to index any video — transcript + scene analysis — then lets you ask questions at any timestamp. Pick a character and they respond as themselves, with full knowledge of who they are and what's happening. Or ask the scene directly for context, subtext, and what you might be missing.

Works for any show: Death Note, Mirzapur, Young Sheldon, Breaking Bad — anything.

## screenshots : harshad mehta example
<img width="586" height="650" alt="Screenshot 2026-05-17 185748" src="https://github.com/user-attachments/assets/8b00a478-52ec-4784-8f39-bab144ad9e16" />
<img width="1234" height="822" alt="Screenshot 2026-05-17 191350" src="https://github.com/user-attachments/assets/ff55224f-24a6-408c-a7ac-7d5341b5f65d" />

---

## How It Works

1. Upload any episode to VideoDB (transcript + scene indexing)
2. Enter the show title — BehindTheEyes generates the character list dynamically using Gemma 4
3. Pause at any moment, pick a character, ask a question
4. The character responds as themselves — using the scene context + their full personality from the model's knowledge

**No hardcoded profiles.** Character knowledge comes from Gemma 4's understanding of the show, grounded by the actual scene description and transcript at that timestamp.

---

## Setup

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

### Ingest a New Video

```bash
cd characteros/backend
python ingest2.py
```

Uploads the episode, indexes transcript (Whisper) and scenes (GEMMA_4_31B), saves IDs to `config.json`.

---

## VideoDB APIs Used

| API | What it does in BehindTheEyes |
|---|---|
| `coll.upload(url=...)` | Upload any video from URL |
| `video.index_spoken_words()` | Full episode transcript via Whisper |
| `video.index_scenes(model, prompt, config)` | Scene-level visual analysis with Gemma 4 |
| `video.get_transcript()` | Retrieve dialogue at a specific timestamp window |
| `video.get_scene_index(id)` | Retrieve scene descriptions for visual context |
| `coll.generate_text(prompt, model_name)` | Dynamic character list generation + in-character responses |

---

## Architecture

```
User pauses video at timestamp T, picks a character
                    |
                    v
         POST /api/ask
         { timestamp, question, show_title, character_name, mode }
                    |
      +-------------+-------------+
      |                           |
  get_scene(T)              get_transcript(T, window=60s)
      |                           |
      +-------------+-------------+
                    |
          build_character_prompt()
          - Gemma 4's knowledge of the show + character
          - Scene description from VideoDB
          - Last 60s of dialogue from VideoDB
          - User's question
                    |
                    v
          coll.generate_text(prompt, model="ultra")
                    |
                    v
          Response card in UI
```

Two modes:
- **Character** — the character talks to you as themselves
- **Scene** — a knowledgeable companion explains what's happening

---

## Adding Support for a New Video

1. Change the video URL in `ingest2.py`
2. Run `python ingest2.py`
3. It saves the new `video_id` and `scene_index_id` to `config.json`
4. In the frontend, type the show title and hit "Set" — characters are generated automatically

---

## Project Structure

```
characteros/
├── backend/
│   ├── main.py           # FastAPI — /api/ask, /api/characters
│   ├── engine.py         # Dynamic prompt builders (character + scene mode)
│   ├── videodb_utils.py  # Scene alignment + transcript retrieval
│   ├── ingest2.py        # Upload + index pipeline
│   ├── config.json       # Active video + scene index IDs
│   └── .env.example
├── docs/
│   └── progress.md
└── frontend/
    ├── vite.config.js    # Proxy /api -> :8000
    └── src/
        ├── App.jsx       # Full UI — dynamic char list, mode toggle
        ├── App.css       # Dark theme, gold accents, responsive
        └── index.css     # CSS variables + reset
```

---

Built for the **VideoDB Hackathon** · May 2026
