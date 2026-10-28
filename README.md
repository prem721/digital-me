# Digital Me

A personal AI version of yourself with two modes.

| Mode | Who uses it | What it does |
|---|---|---|
| **Presentation** | Anyone (visitors, recruiters) | Answers questions about you from your public notes only. Page: `/` |
| **Companion** | Only you (owner login) | Talks like you: your private notes, memory, cloned voice, animated avatar, webcam mood. Page: `/avatar` |

Everything runs on your own computer. No paid API is needed.

## What it uses
FastAPI backend, Chroma vector database (RAG), Ollama local language model, faster-whisper (speech to text),
XTTS voice cloning (separate service), OpenCV + ONNX (webcam emotion), three.js + VRM (3D avatar).

## Two Python environments
| Project | Python | Folder |
|---|---|---|
| Main app | 3.13 | `digital-me` |
| Voice service | 3.11 | `digital-me-voice` (keep it outside OneDrive) |

## Running it each time
| Terminal | Folder | Command |
|---|---|---|
| 1 (main app) | `digital-me` | `.venv\Scripts\activate` then `uvicorn app.main:app` |
| 2 (voice) | `digital-me-voice` | `.venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8100` |
| 3 (optional, webcam) | `digital-me` | `python -m scripts.emotion_camera --preview` |
| Ollama | background app | starts automatically |

| Address | What |
|---|---|
| http://127.0.0.1:8000/ | Visitor page |
| http://127.0.0.1:8000/avatar | Companion with avatar (owner login) |
| http://127.0.0.1:8000/docs | Testing panel (private mode only) |

## Your data
- `data/public/*.md`: what visitors can learn. Write full sentences. Reload with **POST /ingest** after editing.
- `data/private/*.md`: personality, values, coping, writing style. Reload with **POST /companion/ingest**.
- `data/private/avatar.vrm`: your 3D character (optional; the 2D face is used without it).
- Secrets live in `.env` (never share or upload it): `OWNER_PASSWORD`, `JWT_SECRET`, `VOICE_SERVICE_URL`, `VOICE_SERVICE_TOKEN`.

## Tests
```
python -m scripts.run_all_tests              fast checks, no server needed
python -m scripts.run_all_tests --with-llm   adds the accuracy and attack test (needs Ollama)
python -m scripts.smoke_test                 end-to-end checks against the running server
python -m scripts.check_voice                explains why the cloned voice is or is not used
python -m scripts.debug_rag                  shows why a question is refused and where the time goes
```

## Sharing presentation mode with other people
Public mode removes every path except the visitor page, `/health` and `/presentation/chat`.
Companion mode, login, voice, memory, and the docs page do not exist in it.
1. Review `data/public` first: anything in it can be revealed by questions.
2. Stop the normal server. Start public mode in a new terminal:
   - Command Prompt: `set PUBLIC_MODE=1` then `uvicorn app.main:app --host 127.0.0.1 --port 8000`
   - PowerShell: `$env:PUBLIC_MODE="1"` then the same uvicorn command
   (Do not put PUBLIC_MODE in `.env`.)
3. Expose it with a tunnel such as Cloudflare Tunnel (check Cloudflare's current documentation for the command).
4. When finished, close the tunnel and the server.

Answers run on your laptop's CPU, so they are slow, your computer must stay on, and the limits in
`SECURITY.md` apply.

## Folder layout
```
digital-me/
  app/            backend code (main.py = all endpoints) and app/static/ pages
  scripts/        tests, calibration, webcam reader
  data/public/    visitor knowledge        data/private/  your private data (git-ignored)
  models/ logs/ chroma_db/   created automatically
digital-me-voice/ voice cloning service (own environment, reference/my_voice.wav is your voice sample)
```