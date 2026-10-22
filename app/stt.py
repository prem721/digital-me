"""Speech-to-text with faster-whisper (free, runs on your CPU).

Audio is decoded here with PyAV directly, so it works across PyAV versions.
(faster-whisper's own decoder breaks with newer PyAV releases.)"""
import numpy as np

MODEL_SIZE = "base"   # "tiny" is faster and less accurate, "small" is slower and better
SAMPLE_RATE = 16000

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel  # imported late so the server starts fast

        # First use downloads the model once, then it works offline
        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def load_audio(path: str) -> np.ndarray:
    """Decode any audio file to 16 kHz mono float32, which is what Whisper expects."""
    import av

    resampler = av.AudioResampler(format="s16", layout="mono", rate=SAMPLE_RATE)
    chunks = []

    def collect(frames):
        if frames is None:
            return
        if not isinstance(frames, (list, tuple)):
            frames = [frames]
        for frame in frames:
            chunks.append(frame.to_ndarray().reshape(-1))

    with av.open(path) as container:
        audio_streams = [s for s in container.streams if s.type == "audio"]
        if not audio_streams:
            raise ValueError("No audio found in this file.")
        for frame in container.decode(audio_streams[0]):
            collect(resampler.resample(frame))
        collect(resampler.resample(None))  # flush what is left in the resampler

    if not chunks:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(chunks).astype(np.float32) / 32768.0


def transcribe(path: str) -> str:
    audio = load_audio(path)
    if audio.size == 0:
        return ""
    segments, _info = _get_model().transcribe(audio, beam_size=1, vad_filter=False)
    return " ".join(seg.text.strip() for seg in segments).strip()