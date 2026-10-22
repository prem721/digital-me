"""Checks for the voice helpers (no microphone, Whisper, or speech engine needed).

Run:  python -m scripts.test_voice
"""
import os
import pathlib
import tempfile
import time

from app.voice_rules import (
    MAX_SPEECH_CHARS,
    delete_old_files,
    is_allowed_audio,
    is_valid_output_name,
    trim_for_speech,
)

passed = total = 0


def check(ok: bool, label: str):
    global passed, total
    total += 1
    passed += bool(ok)
    print(("PASS  " if ok else "FAIL  ") + label)


for name in ["voice.wav", "note.M4A", "clip.mp3", "a.webm"]:
    check(is_allowed_audio(name), f"allowed audio: {name}")
for name in ["virus.exe", "notes.txt", "noextension", "", "audio.wav.exe"]:
    check(not is_allowed_audio(name), f"rejected upload: {name!r}")

good = "a" * 32 + ".wav"
check(is_valid_output_name(good), "valid generated file name")
for bad in ["../secret.wav", "..\\\\secret.wav", "abc.wav", "a" * 32 + ".mp3", "a" * 32 + ".wav/../x", ""]:
    check(not is_valid_output_name(bad), f"blocked download name: {bad!r}")

long_text = "word " * 400
check(len(trim_for_speech(long_text)) <= MAX_SPEECH_CHARS + 3, "long replies are trimmed before speaking")
check(trim_for_speech("Hello there") == "Hello there", "short replies unchanged")

d = pathlib.Path(tempfile.mkdtemp())
old, new = d / "old.wav", d / "new.wav"
old.write_bytes(b"x")
new.write_bytes(b"x")
os.utime(old, (time.time() - 7200, time.time() - 7200))
removed = delete_old_files(d, max_age_seconds=3600)
check(removed == 1 and not old.exists() and new.exists(), "old audio is deleted, new audio kept")

print(f"\nScore: {passed}/{total}")