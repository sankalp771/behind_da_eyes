"""
BehindTheEyes — Dynamic Character Engine

No hardcoded profiles. Gemma 4 generates everything from:
- Its own training knowledge of the show & character
- The actual scene context from VideoDB at that timestamp
- The transcript of what was just said

Works for any show: anime, web series, drama, sitcom — anything.
"""
import json
import re
import urllib.parse
import urllib.request


WIKI_API = "https://en.wikipedia.org/w/api.php"


def _slugify_key(name: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return key or "character"


def _dedupe_characters(characters: list) -> list:
    seen = set()
    cleaned = []
    for item in characters:
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        norm = re.sub(r"\s+", " ", name.lower())
        if norm in seen:
            continue
        seen.add(norm)
        cleaned.append({
            "key": item.get("key") or _slugify_key(name),
            "name": name,
            "role": str(item.get("role") or "Character").strip(),
        })
    return cleaned[:10]


def _wiki_get(params: dict) -> dict:
    query = urllib.parse.urlencode({
        "format": "json",
        "formatversion": "2",
        **params,
    })
    req = urllib.request.Request(
        f"{WIKI_API}?{query}",
        headers={"User-Agent": "BehindTheEyes/0.1 (character lookup)"},
    )
    with urllib.request.urlopen(req, timeout=8) as response:
        return json.loads(response.read().decode("utf-8"))


def _strip_wiki_markup(text: str) -> str:
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^/]*/>", "", text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"\{\{.*?\}\}", "", text)
    text = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"''+", "", text)
    text = re.sub(r"&nbsp;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _name_from_cast_line(line: str) -> dict | None:
    clean = _strip_wiki_markup(line.lstrip("*#;: ").strip())
    if not clean or len(clean) < 4:
        return None

    actor = ""
    character_part = ""
    match = re.search(r"\bas\b\s+(.+)", clean, flags=re.IGNORECASE)
    if match:
        actor = clean[:match.start()].strip(" -–—,:")
        character_part = match.group(1)
    elif re.match(r"^[A-Z][A-Za-z .'\-]+(\s+[A-Z][A-Za-z .'\-]+){0,4}\s+[–-]\s+", clean):
        character_part = re.split(r"\s+[–-]\s+", clean, maxsplit=1)[0]
    else:
        return None

    name = re.split(r"\s*(?:,|;|:|\s+-\s+|\s+–\s+|\s+—\s+|\(|\[)", character_part, maxsplit=1)[0]
    name = re.sub(r"\s+also\s+known\s+as\s+.*$", "", name, flags=re.IGNORECASE)
    name = name.strip(" .-–—")

    if not name or len(name) > 70:
        return None
    if re.search(r"\b(season|episode|series|film|television|web series)\b", name, flags=re.IGNORECASE):
        return None

    role = f"Played by {actor}" if actor else "Character"
    return {"key": _slugify_key(name), "name": name, "role": role}


def _extract_characters_from_wikitext(wikitext: str) -> list:
    characters = []
    lines = [line.strip() for line in wikitext.splitlines()]

    # Many TV pages keep the primary cast in a wikitable where rows are:
    # | Character name
    # | [[Actor name]]
    for i, line in enumerate(lines[:-1]):
        if not line.startswith("|") or line.startswith("|-") or line.startswith("!"):
            continue
        if any(token in line.lower() for token in ("colspan", "rowspan", "style=", "width:")):
            continue

        raw_name = line.lstrip("|").strip()
        next_line = lines[i + 1].lstrip("|").strip()
        if not next_line or next_line.startswith(("colspan", "rowspan")):
            continue
        if "{{C" in next_line or "Season" in next_line:
            continue

        name = _strip_wiki_markup(raw_name).strip(" .-–—")
        actor = _strip_wiki_markup(next_line).strip(" .-–—")
        if not name or len(name) > 70:
            continue
        if re.search(r"\b(character|portrayed by|season|main|guest|recurring)\b", name, re.IGNORECASE):
            continue

        characters.append({
            "key": _slugify_key(name),
            "name": name,
            "role": f"Played by {actor}" if actor else "Character",
        })

    for line in lines:
        if not line.startswith(("*", "#", ";")):
            continue
        item = _name_from_cast_line(line)
        if item:
            characters.append(item)
    return _dedupe_characters(characters)


def fetch_wikipedia_characters(show_title: str) -> list:
    """
    Best-effort Wikipedia cast lookup. This is intentionally deterministic:
    find the likely show page, inspect Cast/Characters sections, then parse
    "Actor as Character" style list items.
    """
    search_terms = [
        f"{show_title} web series characters",
        f"{show_title} television series cast",
        f"{show_title} TV series",
        show_title,
    ]

    page_title = None
    for term in search_terms:
        data = _wiki_get({
            "action": "query",
            "list": "search",
            "srsearch": term,
            "srlimit": 5,
        })
        results = data.get("query", {}).get("search", [])
        if results:
            page_title = results[0].get("title")
            if page_title:
                break

    if not page_title:
        return []

    sections_data = _wiki_get({
        "action": "parse",
        "page": page_title,
        "prop": "sections",
    })
    sections = sections_data.get("parse", {}).get("sections", [])
    preferred_sections = [
        s for s in sections
        if re.search(r"\b(cast|characters?|cast and characters?)\b", s.get("line", ""), re.IGNORECASE)
    ]

    section_indexes = [s.get("index") for s in preferred_sections[:3] if s.get("index")]
    if not section_indexes:
        section_indexes = [None]

    for section in section_indexes:
        params = {"action": "parse", "page": page_title, "prop": "wikitext"}
        if section is not None:
            params["section"] = section
        parsed = _wiki_get(params)
        wikitext = parsed.get("parse", {}).get("wikitext", "")
        characters = _extract_characters_from_wikitext(wikitext)
        if characters:
            return characters

    return []


def _parse_json_from_output(text: str) -> list:
    """Extract JSON array from Gemma 4 output even if it adds surrounding text."""
    # Try direct parse
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    # Find JSON array in output
    match = re.search(r'\[.*?\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return []


def generate_character_list(coll, show_title: str, transcript: str = "") -> list:
    """
    Generate the cast list for any show using Gemma 4's world knowledge.
    The show_title is the PRIMARY source — NOT the transcript.
    Transcript is only used as a supplement when it actually matches the show.
    """

    wiki_characters = []
    try:
        wiki_characters = fetch_wikipedia_characters(show_title)
    except Exception:
        wiki_characters = []

    # Ask Gemma too. It can fill gaps for pages without clean cast sections,
    # but Wikipedia is preferred when it returns parseable names.
    prompt = f"""List the main characters from the show/series "{show_title}".

Return a JSON array in exactly this format (no other text, just the JSON array):
[
  {{"key": "snake_case_key", "name": "Full Character Name", "role": "brief role description"}}
]

Rules:
- Include the most important characters from "{show_title}"
- Use accurate names and roles from the actual show
- Maximum 10 characters, ordered by importance
- key must be lowercase snake_case
- Return ONLY the JSON array, nothing else"""

    model_characters = []
    try:
        result = coll.generate_text(prompt=prompt, model_name="ultra")
        output = result.get("output", "") if isinstance(result, dict) else str(result)
        model_characters = _parse_json_from_output(output)
    except Exception:
        model_characters = []

    model_characters = [
        c for c in model_characters
        if isinstance(c, dict) and c.get("key") and c.get("name")
    ]

    return _dedupe_characters(wiki_characters + model_characters)


def _clip_text(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text[:limit]


def build_style_guide_prompt(show_title: str, char_name: str, transcript_sample: str) -> str:
    return f"""Create a compact speaking-style guide for {char_name} from "{show_title}".

Use your knowledge of the show and, when useful, this transcript sample:
{_clip_text(transcript_sample, 6000)}

Return only this structure:
VOCAB:
- 4-6 words or phrases this character would naturally use
SENTENCE SHAPE:
- short notes on sentence length, rhythm, directness, language mix
ATTITUDE:
- short notes on confidence, aggression, warmth, humor, restraint
AVOID:
- 4 generic patterns that would sound unlike this character

Keep it specific and usable for rewriting. Do not invent catchphrases unless the character is known for them."""


def build_character_style_rewrite_prompt(
    show_title: str,
    char_name: str,
    question: str,
    scene: str,
    transcript: str,
    draft_response: str,
    style_guide: str,
) -> str:
    return f"""Rewrite this answer so it sounds more like {char_name} from "{show_title}".

STYLE GUIDE:
{style_guide}

CURRENT SCENE:
{_clip_text(scene, 1600)}

RECENT DIALOGUE:
{_clip_text(transcript, 1600)}

USER ASKED:
"{question}"

DRAFT ANSWER:
{draft_response}

Rules:
- Preserve the exact intent and facts of the draft.
- Make the vocabulary, sentence rhythm, confidence level, and language mix feel like {char_name}.
- Stay natural for a live conversation, not a dramatic monologue.
- Do not add new plot facts.
- Do not quote copyrighted dialogue from the show.
- Do not mention style guides, rewriting, AI, or prompts.
- 3-5 sentences.

Return only the rewritten answer."""


def build_character_prompt(
    show_title: str,
    char_name: str,
    scene: str,
    transcript: str,
    question: str
) -> str:
    """
    Fully dynamic prompt. Uses Gemma 4's own knowledge of the show + character
    combined with live scene/transcript context from VideoDB.
    No hardcoded profiles needed.
    """
    return f"""You are {char_name} from "{show_title}".

Draw on everything you know about {char_name} from your knowledge of "{show_title}":
- Your personality, way of speaking, accent, mannerisms
- Your relationships with the other characters in this scene
- Your current goals, fears, and what you are hiding
- Your history and why you are the way you are

WHAT IS HAPPENING AROUND YOU RIGHT NOW (from the scene):
{scene}

WHAT WAS JUST SAID (last ~60 seconds of dialogue):
{transcript}

SOMEONE WATCHING IS ASKING YOU:
"{question}"

---
Respond as {char_name} — directly to this person who can somehow hear your thoughts.
You know exactly where you are in your story. You know what just happened.
Be specific to THIS moment, not generic.
Sound like yourself — your dialect, your rhythm, your mindset.
4–6 sentences. No speeches. Just you, being real.
Do not start with your name. Do not say you are an AI. Just respond."""


def build_scene_prompt(
    show_title: str,
    scene: str,
    transcript: str,
    question: str
) -> str:
    """
    Scene companion mode — like watching with someone who has seen it all.
    """
    return f"""You have watched every episode of "{show_title}" multiple times.
You know this show inside out — every character's arc, every plot twist, every theme.

You are sitting next to someone who is watching this right now.
They just paused and asked you something.

WHAT IS ON SCREEN RIGHT NOW:
{scene}

WHAT WAS JUST SAID:
{transcript}

THEY ASKED:
"{question}"

---
Answer like that friend — genuinely engaged, specific, no generic summaries.
You can explain:
- What is actually happening vs. what appears to be happening
- What each character is really thinking or hiding
- Why this moment matters in the larger story
- What the viewer might be missing (subtext, callbacks, foreshadowing)
Be conversational, warm, occasionally excited when it is a great moment.
5–7 sentences. Real conversation."""
