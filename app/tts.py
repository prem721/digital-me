"""Text-to-speech. Today: the built-in Windows voice (placeholder).
Milestone 5B replaces synthesize() with your cloned voice, and nothing else changes."""
import subprocess
import sys
import uuid

from app.config import ROOT
from app.voice_rules import delete_old_files, trim_for_speech

AUDIO_OUT_DIR = ROOT / "data" / "private" / "audio_out"


def synthesize(text: str) -> str:
    """Creates a .wav file and returns its file name (inside data/private/audio_out)."""
    AUDIO_OUT_DIR.mkdir(parents=True, exist_ok=True)
    delete_old_files(AUDIO_OUT_DIR)

    name = f"{uuid.uuid4().hex}.wav"
    out_path = AUDIO_OUT_DIR / name
    subprocess.run(
        [sys.executable, "-m", "app.tts_worker", str(out_path)],
        input=trim_for_speech(text),
        encoding="utf-8",
        cwd=ROOT,
        timeout=60,
        check=True,
        capture_output=True,
    )
    if not out_path.exists():
        raise RuntimeError("The speech engine did not create an audio file.")
    return name