"""Tells you exactly why the cloned voice is (or is not) being used.

Run:  python -m scripts.check_voice
Your token is never printed, only its length."""
import json
import urllib.error
import urllib.request

from app.config import VOICE_SERVICE_TOKEN, VOICE_SERVICE_URL
from app.voice_rules import is_local_url

print("1. Settings in digital-me\\.env")
print("   VOICE_SERVICE_URL   :", VOICE_SERVICE_URL or "(MISSING)")
print("   VOICE_SERVICE_TOKEN :", f"set, {len(VOICE_SERVICE_TOKEN)} characters" if VOICE_SERVICE_TOKEN else "(MISSING)")
if not VOICE_SERVICE_URL or not VOICE_SERVICE_TOKEN:
    print("\nFIX: add both lines to the .env inside the digital-me folder, save, and restart the main server:")
    print("     VOICE_SERVICE_URL=http://127.0.0.1:8100")
    print("     VOICE_SERVICE_TOKEN=<the token from the voice folder's .env>")
    raise SystemExit(1)
if not is_local_url(VOICE_SERVICE_URL):
    print("\nFIX: the URL must look exactly like http://127.0.0.1:8100 (http, not https; no spaces).")
    raise SystemExit(1)

base = VOICE_SERVICE_URL.rstrip("/")

print("\n2. Is the voice service running?")
try:
    with urllib.request.urlopen(base + "/health", timeout=5) as r:
        print("   Reachable:", r.read().decode())
except Exception as e:
    print("   NOT reachable:", e)
    print("\nFIX: start it in its own terminal, inside the voice folder with its (.venv) active:")
    print("     uvicorn server:app --host 127.0.0.1 --port 8100")
    raise SystemExit(1)

print("\n3. Asking it to speak (can take a minute on a CPU)...")
request = urllib.request.Request(
    base + "/speak",
    data=json.dumps({"text": "This is a test of my cloned voice."}).encode("utf-8"),
    headers={"Content-Type": "application/json", "X-Voice-Token": VOICE_SERVICE_TOKEN},
    method="POST",
)
try:
    with urllib.request.urlopen(request, timeout=180) as r:
        data = r.read()
except urllib.error.HTTPError as e:
    body = e.read().decode(errors="replace")[:300]
    print(f"   The service answered with error {e.code}: {body}")
    if e.code == 401:
        print("\nFIX: the token does not match. Both .env files must hold the exact same token")
        print("     (the voice service's token length is shown in its own .env). Restart both servers after editing.")
    elif e.code == 503:
        print("\nFIX: no reference voice. In the voice folder run: python prepare_reference.py sample.m4a")
    else:
        print("\nLook at the voice service terminal for the full error and send me the last 10 lines.")
    raise SystemExit(1)
except Exception as e:
    print("   Failed:", e)
    print("\nIf this says timed out, the first run is still loading the model. Wait and run this again.")
    raise SystemExit(1)

print(f"   Got {len(data)} bytes of audio.")
print("\nOK: the main app can use your cloned voice. Restart the main server, then try voice-chat again.")