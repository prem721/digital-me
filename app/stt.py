"""Speech-to-text with faster-whisper (free, runs on your CPU)."""
MODEL_SIZE = "base"   # "tiny" is faster and less accurate, "small" is slower and better

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel  # imported late so the server starts fast

        # First use downloads the model once, then it works offline
        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def transcribe(path: str) -> str:
    segments, _info = _get_model().transcribe(path, beam_size=1, vad_filter=False)
    return " ".join(seg.text.strip() for seg in segments).strip()