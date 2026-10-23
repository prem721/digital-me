"""Text-to-speech.
1) Your cloned voice, from the separate voice service (if it is configured and running).
2) Otherwise the built-in Windows voice as a fallback."""
import json
import subprocess
import sys
import urllib.error
import urllib.request
import uuid

from app.config import ROOT, VOICE_SERVICE_TOKEN, VOICE_SERVICE_URL
from app.voice_rules import delete_old_files, is_local_url, trim_for_speech

AUDIO_OUT_DIR = ROOT / "data" / "private" / "audio_out"
CLONE_TIMEOUT_SECONDS = 180  # cloning on a CPU can be slow


def _synthesize_cloned(text: str, out_path) -> bool:
    """Ask the local voice service. Returns False if it is not set up or not reachable."""
    if not (VOICE_SERVICE_URL and VOICE_SERVICE_TOKEN) or not is_local_url(VOICE_SERVICE_URL):
        return False
    request = urllib.request.Request(
        VOICE_SERVICE_URL.rstrip("/") + "/speak",
        data=json.dumps({"text": trim_for_speech(text)}).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Voice-Token": VOICE_SERVICE_TOKEN},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=CLONE_TIMEOUT_SECONDS) as response:
            data = response.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        return False
    if len(data) < 1000:  # not a real audio file
        return False
    out_path.write_bytes(data)
    return True


def _synthesize_windows(text: str, out_path) -> None:
    subprocess.run(
        [sys.executable, "-m", "app.tts_worker", str(out_path)],
        input=trim_for_speech(text),
        encoding="utf-8",
        cwd=ROOT,
        timeout=60,
        check=True,
        capture_output=True,
    )


def synthesize(text: str) -> tuple[str, str]:
    """Creates a .wav file in data/private/audio_out. Returns (file_name, "cloned" or "placeholder")."""
    AUDIO_OUT_DIR.mkdir(parents=True, exist_ok=True)
    delete_old_files(AUDIO_OUT_DIR)

    name = f"{uuid.uuid4().hex}.wav"
    out_path = AUDIO_OUT_DIR / name

    if _synthesize_cloned(text, out_path):
        return name, "cloned"

    _synthesize_windows(text, out_path)
    if not out_path.exists():
        raise RuntimeError("The speech engine did not create an audio file.")
    return name, "placeholder"