# Digital Me (Milestone 1: Presentation mode, text only)

## Setup (Windows, PowerShell)

```powershell
cd digital-me
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and replace `your-key-here` with an API key from the
[Anthropic Console](https://console.anthropic.com/settings/keys). Keep this key
private; `.env` is excluded from Git. The app loads this project-root `.env`
when it starts and sends chat requests to Claude using the Anthropic API.

If the key is missing, `/presentation/chat` reports a clear configuration
error. Restart the server after changing `.env`.

If PowerShell blocks activation, run once:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## Add your data

Edit `data/public/about_me.md` with your real skills, projects, hobbies, and how you talk.
Anything in `data/private/` is NOT used by presentation mode (reserved for companion mode later).

## Run

```powershell
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs, then:

1. `POST /ingest` (loads your public files into the vector DB; the first run downloads a small embedding model)
2. `POST /presentation/chat` with `{"question": "What are your skills?"}`

Re-run `/ingest` whenever you edit your files.

## Folder layout

```
digital-me/
  app/
    main.py   # FastAPI routes
    rag.py    # chunking, embeddings store, retrieval, LLM answer
  data/
    public/   # visible to presentation mode
    private/  # companion mode only (later)
  requirements.txt
  .env.example
```

## Next milestones

2. Test questions + "I don't know" behavior check
3. Auth (owner vs visitor) and guardrails
4. Companion mode + memory
5. Voice (Whisper, voice cloning)
6. Emotion detection
7. Lip sync / avatar
