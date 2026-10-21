import re

BLOCK_REPLY = (
    "I can only answer questions about Prem. "
    "Please ask about his skills, projects, education, or interests."
)

MAX_QUESTION_CHARS = 500

# Common prompt-injection phrases (a speed bump, NOT a complete defense)
INJECTION_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above|your|these)?\s*(instructions|rules|prompt)",
    r"disregard (all |any |the )?(previous|prior|above|your)?\s*(instructions|rules|prompt)",
    r"forget (all |any |your )?(previous |prior )?(instructions|rules)",
    r"(reveal|show|print|repeat|tell me|output) (me )?(your|the) (system )?(prompt|instructions|rules)",
    r"system prompt",
    r"you are now\b",
    r"\bdan\b.*\b(no rules|without rules|jailbreak)",
    r"developer mode",
    r"jailbreak",
    r"pretend (to be|you are)",
    r"override (your|the|all) (rules|instructions|safety)",
]
_INJECTION_RE = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

# Pieces of our own system prompt: if the answer contains them, it is leaking
LEAK_MARKERS = [
    "RULES:",
    "CONTEXT:",
    "digital version of Prem Kumar. A visitor",
    "Use ONLY facts written in",
]


def clean_input(text: str) -> str:
    # remove control characters, collapse whitespace
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def check_input(question: str) -> tuple[bool, str | None]:
    """Returns (allowed, reason_if_blocked)."""
    q = clean_input(question)
    if not q:
        return False, "empty"
    if len(q) > MAX_QUESTION_CHARS:
        return False, "too_long"
    for pattern in _INJECTION_RE:
        if pattern.search(q):
            return False, "injection_pattern"
    return True, None


def check_output(answer: str) -> tuple[str, str | None]:
    """Returns (safe_answer, reason_if_changed)."""
    lowered = answer.lower()
    for marker in LEAK_MARKERS:
        if marker.lower() in lowered:
            return BLOCK_REPLY, "prompt_leak"
    redacted = re.sub(r"\b\d{12,}\b", "[redacted]", answer)  # long ID/card-like numbers
    if redacted != answer:
        return redacted, "pii_redacted"
    return answer, None
