"""Checks which paths exist in public mode. No server needed.

Run:  python -m scripts.test_public_mode
"""
from app.public_mode import is_allowed_in_public_mode

passed = total = 0


def check(ok: bool, label: str):
    global passed, total
    total += 1
    passed += bool(ok)
    print(("PASS  " if ok else "FAIL  ") + label)


for path in ["/", "/health", "/presentation/chat"]:
    check(is_allowed_in_public_mode(path), f"public path allowed: {path}")

for path in [
    "/docs", "/redoc", "/openapi.json", "/auth/login", "/ingest", "/companion/chat",
    "/companion/memory", "/companion/emotion", "/voice/transcribe", "/voice/audio/abc.wav",
    "/avatar", "/avatar/model", "//ingest", "/presentation/chat/", "/presentation/../ingest",
    "/presentation", "", "/HEALTH",
]:
    check(not is_allowed_in_public_mode(path), f"blocked in public mode: {path!r}")

print(f"\nScore: {passed}/{total}")