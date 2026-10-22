"""Rules for what long-term memory may keep. Pure Python, easy to test."""
import json
import re

# If a chat batch touches these topics, NOTHING from it is saved to long-term memory.
SENSITIVE_RE = re.compile(
    r"(depress|anxi|suicid|self[- ]?harm|panic|therap|counsel|psychiatr|medicat|diagnos|"
    r"mental health|disorder|abus|assault|trauma|addict|overdos)",
    re.IGNORECASE,
)

EXTRACT_PROMPT = """You write private notes for a person's own journaling assistant.
Read the conversation and return ONLY a JSON object with exactly two keys:
  "summary": 1 to 3 short sentences about the topics discussed and any decisions or plans.
  "facts": a list of at most 3 short, lasting facts or preferences about the person
           (for example plans, projects, routines, likes). Use [] if there are none.
Do NOT include: health or mental-health details, one-off emotions or moods, secrets,
or private details about other people. Do not invent anything not said in the conversation."""


def is_sensitive(text: str) -> bool:
    return bool(SENSITIVE_RE.search(text))


def batch_is_sensitive(user_messages: list[str]) -> bool:
    return any(is_sensitive(m) for m in user_messages)


def parse_extraction(text: str) -> dict:
    """Parse the model's JSON reply, tolerating extra text around it."""
    data = None
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        match = re.search(r"\{.*\}", text or "", re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                data = None
    if not isinstance(data, dict):
        return {"summary": "", "facts": []}
    summary = data.get("summary", "")
    facts = data.get("facts", [])
    return {
        "summary": summary.strip() if isinstance(summary, str) else "",
        "facts": facts if isinstance(facts, list) else [],
    }


def clean_facts(raw_facts: list) -> list[str]:
    """Keep up to 3 short, non-sensitive fact strings."""
    kept = []
    for f in raw_facts:
        if not isinstance(f, str):
            continue
        f = f.strip()
        if 5 < len(f) <= 200 and not is_sensitive(f):
            kept.append(f)
    return kept[:3]