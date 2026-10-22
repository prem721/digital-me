"""Handles audio uploads safely."""
import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import ROOT
from app.voice_rules import MAX_UPLOAD_BYTES, delete_old_files, is_allowed_audio

AUDIO_IN_DIR = ROOT / "data" / "private" / "audio_in"


def save_upload(upload: UploadFile) -> Path:
    """Saves the upload to a temporary file. The caller must delete it when done."""
    if not is_allowed_audio(upload.filename or ""):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use .wav, .mp3, .m4a, .ogg, .webm, or .flac.",
        )
    data = upload.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Audio file is too large (limit 10 MB).")
    if not data:
        raise HTTPException(status_code=400, detail="The audio file is empty.")

    AUDIO_IN_DIR.mkdir(parents=True, exist_ok=True)
    delete_old_files(AUDIO_IN_DIR, max_age_seconds=3600)  # clean up anything left by a crash
    suffix = Path(upload.filename).suffix.lower()
    with tempfile.NamedTemporaryFile(dir=AUDIO_IN_DIR, suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        return Path(tmp.name)