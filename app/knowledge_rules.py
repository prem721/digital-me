"""Cleans your topic files before they are stored for search. Pure Python, easy to test."""
import re

MIN_REAL_CHARS = 40   # a chunk needs at least this much real text (not headings or templates)


def strip_templates(text: str) -> str:
    """Remove <!-- comments --> and template lines written as (...) so they are never searched."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("(") and stripped.endswith(")"):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def has_real_content(chunk: str) -> bool:
    """False for chunks that are only headings or empty."""
    body = "\n".join(l for l in chunk.splitlines() if not l.strip().startswith("#"))
    return len(body.strip()) >= MIN_REAL_CHARS


def label_chunk(stem: str, chunk: str) -> str:
    """Prefix the topic name so 'What are your skills?' lands on chunks from skills.md."""
    return f"[{stem}] {chunk}"


# ---- topic-aware ranking (the search model alone often ranks broad chunks too high) ----
TOPIC_PATTERNS = {
    "skills": r"\bskills?\b|\bskilled\b|\btech stack\b|\bprogramming languages?\b|\bwhat can you do\b",
    "projects": r"\bprojects?\b|\bportfolio\b|\bwhat have you (built|made)\b",
    "education": r"\bstudy(ing)?\b|\beducation\b|\bcollege\b|\buniversity\b|\bdegree\b|\bgraduat",
    "hobbies": r"\bhobb(y|ies)\b|\bfree time\b|\binterests?\b|\bfor fun\b",
    "goals": r"\bgoals?\b|\bfuture\b|\bbecome\b|\bplans?\b|\bambition",
    "communication": r"\bcommunicat|\bhow do you (talk|speak|explain)\b",
}


def detect_topics(question: str) -> list[str]:
    """Which of your topic files the question is clearly about (may be several, or none)."""
    return [name for name, pattern in TOPIC_PATTERNS.items() if re.search(pattern, question, re.IGNORECASE)]


def apply_topic_boost(hits: list[dict], topics: list[str], boost: float) -> list[dict]:
    """Lower the distance of chunks from the matching topic file, then sort best first."""
    boosted = []
    for hit in hits:
        stem = hit["source"].rsplit(".", 1)[0]
        distance = hit["distance"] - boost if stem in topics else hit["distance"]
        boosted.append({**hit, "distance": distance})
    return sorted(boosted, key=lambda h: h["distance"])


def select_context(hits: list[dict], max_chunks: int, max_chars: int) -> list[dict]:
    """Keep the best chunks while staying under a size budget (less text = faster answers)."""
    chosen, total = [], 0
    for hit in hits:
        if len(chosen) >= max_chunks:
            break
        if chosen and total + len(hit["text"]) > max_chars:
            continue
        chosen.append(hit)
        total += len(hit["text"])
    return chosen