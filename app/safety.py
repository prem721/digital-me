"""Mood hints and crisis detection for companion mode (no heavy imports, easy to test)."""
import re

# EDIT these numbers for the country you live in.
CRISIS_REPLY = (
    "I'm really glad you told me, and I'm taking it seriously. You don't have to carry this alone, "
    "and I'm not the right support for this moment, so please reach a real person right now.\n\n"
    "If you might act on these thoughts or you are in immediate danger, call your local emergency "
    "number (112 in India) or go to the nearest hospital, and tell someone near you.\n"
    "In India you can also call Tele-MANAS at 14416. In other countries, findahelpline.com lists "
    "support lines by country.\n\n"
    "If a friend, family member, or mentor is nearby, please go to them or call them now. "
    "I'm here with you while you do that."
)

CRISIS_PATTERNS = [
    r"\bkill(ing)? (myself|my self)\b",
    r"\bend(ing)? (my life|it all)\b",
    r"\btake my own life\b",
    r"\bsuicid",
    r"\bwant to die\b",
    r"\bwish i (was|were) dead\b",
    r"\bdon'?t want to (live|be alive|exist|be here)\b",
    r"\b(hurt|hurting|harm|harming|cut|cutting) (myself|my self)\b",
    r"\bself[- ]?harm",
    r"\bno reason to (live|go on)\b",
    r"\bbetter off (dead|without me)\b",
    r"\bcan'?t go on\b",
]
_CRISIS_RE = [re.compile(p, re.IGNORECASE) for p in CRISIS_PATTERNS]


def is_crisis(text: str) -> bool:
    """Keyword check. It can miss indirect wording, so it is a safety net, not a diagnosis."""
    return any(p.search(text) for p in _CRISIS_RE)


MOOD_WORDS = {
    "lonely": ["lonely", "alone", "nobody", "no one", "isolated", "miss my"],
    "sad": ["sad", "down", "low", "depressed", "crying", "cry", "hopeless", "empty", "hurt"],
    "stressed": ["stress", "anxious", "anxiety", "overwhelmed", "pressure", "exam", "deadline",
                 "worried", "panic", "burnout"],
    "angry": ["angry", "annoyed", "furious", "irritated", "frustrated", "hate"],
    "happy": ["happy", "excited", "awesome", "amazing", "yay", "proud", "good news",
              "celebrate", "selected", "i won", "great day"],
}


def detect_mood(text: str) -> str:
    """Very simple word-count mood hint. Replaced later by face and voice emotion signals."""
    lowered = text.lower()
    scores = {
        mood: sum(1 for w in words if re.search(rf"\b{re.escape(w)}", lowered))
        for mood, words in MOOD_WORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "neutral"