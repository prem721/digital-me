# Security and privacy notes

## What protects the project
| Protection | Where |
|---|---|
| Owner login (JWT, 8 hours) for every private endpoint; fails closed if no password is set | `app/auth.py` |
| Input filter: length limit, empty check, known prompt-injection phrases | `app/guardrails.py` |
| Output filter: blocks leaked instructions, masks long ID-like numbers | `app/guardrails.py` |
| Visitors can only search `public` data (filtered in the vector search) | `app/rag.py` |
| Rate limits (questions, login attempts, voice, camera) | `app/ratelimit.py` |
| At most 2 questions use the language model at once; others get a polite "busy" | `app/main.py` |
| Crisis check before anything else in companion mode; those messages are not saved | `app/safety.py` |
| Long-term memory refuses sensitive topics; you can list and delete every memory | `app/memory_rules.py` |
| Camera frames are never saved; only a short label is sent, held 30 seconds | `scripts/emotion_camera.py` |
| Voice recordings are deleted right after transcription; replies after an hour | `app/voice.py` |
| Voice service listens only on 127.0.0.1 and needs a secret token | `digital-me-voice/server.py` |
| Public mode: only 3 paths exist, no docs page | `app/public_mode.py` |
| Audit log records events without private message text | `app/audit.py` |

## What it does NOT protect against
- **Clever prompt injection.** The phrase filter catches known tricks only. The strongest protection is that
  private data is never given to the visitor flow at all.
- **Anything you write in `data/public`.** Questions can surface it. Do not put secrets there.
- **Visitor questions are logged** (text up to 200 characters and the IP) in `logs/audit.jsonl`.
  Behind a tunnel the IP may show as 127.0.0.1. The visitor page says questions may be logged.
- **Data at rest is not encrypted:** `memory.db`, `data/private`, the voice sample, and your avatar file are
  plain files on your disk. Use disk encryption (BitLocker) and keep the project outside cloud-synced folders.
- **Rate limits and logs live on one machine** and reset when the server restarts.
- **HTTPS and hashed passwords:** local use does not need them. A tunnel provides HTTPS for visitors, but the
  owner password is stored as plain text in `.env`, so never run companion mode over the public internet.
- **Face emotion is a weak guess**, and the voice clone and avatar can be misused if the files leak.

## Before sharing publicly
- [ ] Reviewed every file in `data/public`
- [ ] Started with `PUBLIC_MODE=1` and confirmed `/docs` and `/avatar` return "Not found"
- [ ] `.env`, `data/private`, `reference/my_voice.wav` are not uploaded anywhere (check `.gitignore` before any git push)
- [ ] Strong `OWNER_PASSWORD`; new `JWT_SECRET` if it was ever shared
- [ ] Ready to stop the tunnel when done