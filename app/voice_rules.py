"""Validation helpers for audio uploads and generated files. Pure Python, easy to test."""
import re
import time
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".webm", ".flac"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024   # 10 MB
MAX_SPEECH_CHARS = 300                # longer replies are trimmed before speaking (keeps cloning fast on a CPU)
OUTPUT_MAX_AGE_SECONDS = 3600         # generated audio is deleted after an hour

_OUTPUT_NAME_RE = re.compile(r"^[a-f0-9]{32}\.wav$")


def is_allowed_audio(filename: str) -> bool:
    return Path(filename or "").suffix.lower() in ALLOWED_EXTENSIONS


def is_valid_output_name(name: str) -> bool:
    """Only names we generated ourselves can be downloaded (blocks path tricks like ../)."""
    return bool(_OUTPUT_NAME_RE.match(name or ""))


def trim_for_speech(text: str) -> str:
    text = (text or "").strip()
    return text if len(text) <= MAX_SPEECH_CHARS else text[:MAX_SPEECH_CHARS].rsplit(" ", 1)[0] + "..."


def delete_old_files(directory: Path, max_age_seconds: int = OUTPUT_MAX_AGE_SECONDS) -> int:
    """Delete files older than max_age_seconds. Returns how many were removed."""
    if not directory.exists():
        return 0
    now = time.time()
    removed = 0
    for f in directory.iterdir():
        if f.is_file() and now - f.stat().st_mtime > max_age_seconds:
            f.unlink(missing_ok=True)
            removed += 1
    return removed


def is_local_url(url: str) -> bool:
    """Your reply text is only ever sent to a voice service running on this computer."""
    parsed = urlparse(url or "")
    return parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}