"""Latest webcam emotion reading (kept in memory only) and how it is combined with your words.
Pure Python, no camera or model imports, so it is easy to test."""
import math
import threading
import time

# Output order of the FER+ model
FER_LABELS = ["neutral", "happiness", "surprise", "sadness", "anger", "disgust", "fear", "contempt"]

LABEL_TO_MOOD = {
    "neutral": "neutral",
    "happiness": "happy",
    "surprise": "surprised",
    "sadness": "sad",
    "anger": "angry",
    "disgust": "annoyed",
    "fear": "stressed",
    "contempt": "annoyed",
}

TTL_SECONDS = 30       # a reading older than this is ignored (camera stopped, or no face)
MIN_CONFIDENCE = 0.5   # weaker readings are ignored

_lock = threading.Lock()
_latest = None  # (label, confidence, timestamp)


def softmax(values: list[float]) -> list[float]:
    top = max(values)
    exps = [math.exp(v - top) for v in values]
    total = sum(exps)
    return [e / total for e in exps]


def average_probs(readings: list[list[float]]) -> list[float]:
    n = len(readings)
    return [sum(r[i] for r in readings) / n for i in range(len(readings[0]))]


def top_label(probs: list[float]) -> tuple[str, float]:
    i = max(range(len(probs)), key=lambda k: probs[k])
    return FER_LABELS[i], probs[i]


def set_face_emotion(label: str, confidence: float, now: float | None = None) -> None:
    global _latest
    with _lock:
        _latest = (label, confidence, time.time() if now is None else now)


def get_face_emotion(now: float | None = None) -> dict | None:
    """The current reading, or None if there is none, it is stale, or it is too weak."""
    with _lock:
        latest = _latest
    if latest is None:
        return None
    label, confidence, stamp = latest
    current = time.time() if now is None else now
    if current - stamp > TTL_SECONDS or confidence < MIN_CONFIDENCE:
        return None
    return {
        "label": label,
        "confidence": round(confidence, 2),
        "mood": LABEL_TO_MOOD.get(label, "neutral"),
        "age_seconds": round(current - stamp, 1),  # how old this reading is
    }


def face_mood_name(face: dict | None) -> str | None:
    return face["mood"] if face else None


def combine_mood(text_mood: str, face: dict | None) -> str:
    """Your words win. The face only helps when your words show no clear mood."""
    if face is None or text_mood != "neutral" or face["mood"] == "neutral":
        return text_mood
    return (
        f"neutral in his words. The camera suggests he may look {face['mood']} "
        "(a weak signal: never state it as fact, and if you mention it, ask gently)"
    )