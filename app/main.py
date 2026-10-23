import re

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.audit import log_event
from app.auth import auth_configured, create_token, require_owner, verify_password
from app.companion import companion_chat, ingest_private
from app.long_term import clear_index, remove_item
from app.memory import (
    clear_everything,
    clear_history,
    delete_fact,
    delete_summary,
    list_memory,
)
from app.memory_update import update_memory
from app.pipeline import run_presentation
from app.rag import ingest_public
from app.ratelimit import rate_limit
from app.stt import transcribe
from app.tts import AUDIO_OUT_DIR, synthesize
from app.voice import save_upload
from app.voice_rules import is_valid_output_name

app = FastAPI(title="Digital Me", version="0.5.0")

SESSION_PATTERN = r"^[A-Za-z0-9_-]{1,50}$"


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


class LoginRequest(BaseModel):
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CompanionRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    session_id: str = Field(default="default", pattern=SESSION_PATTERN)


class CompanionResponse(BaseModel):
    reply: str
    mood: str
    crisis: bool


class EndSessionRequest(BaseModel):
    session_id: str = Field(default="default", pattern=SESSION_PATTERN)


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- Owner login ----------
@app.post(
    "/auth/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit(max_calls=5, window_seconds=60))],
)
def login(req: LoginRequest, request: Request):
    if not auth_configured():
        raise HTTPException(status_code=503, detail="Owner login is not configured.")
    if not verify_password(req.password):
        log_event("login_failed", ip=client_ip(request))
        raise HTTPException(status_code=401, detail="Wrong password.")
    log_event("login_ok", ip=client_ip(request))
    return {"access_token": create_token(), "token_type": "bearer"}


# ---------- Presentation mode (public visitors) ----------
@app.post("/ingest", dependencies=[Depends(require_owner)])
def ingest(request: Request):
    count = ingest_public()
    log_event("ingest", ip=client_ip(request), chunks=count)
    return {"chunks_stored": count}


@app.post(
    "/presentation/chat",
    response_model=ChatResponse,
    dependencies=[Depends(rate_limit(max_calls=20, window_seconds=60))],
)
def presentation_chat(req: ChatRequest, request: Request):
    return run_presentation(req.question, ip=client_ip(request))


# ---------- Companion mode (owner only) ----------
@app.post("/companion/ingest", dependencies=[Depends(require_owner)])
def companion_ingest(request: Request):
    count = ingest_private()
    log_event("companion_ingest", ip=client_ip(request), chunks=count)
    return {"private_chunks_stored": count}


@app.post(
    "/companion/chat",
    response_model=CompanionResponse,
    dependencies=[Depends(require_owner), Depends(rate_limit(max_calls=30, window_seconds=60))],
)
def companion_chat_endpoint(req: CompanionRequest, request: Request, background: BackgroundTasks):
    result = companion_chat(req.message, req.session_id)
    if not result["crisis"] and result["mood"] != "blocked":
        # Memory update runs after the reply is sent, so chat stays fast
        background.add_task(update_memory, req.session_id)
    # Privacy: never write what you said into the audit log, only metadata
    log_event("companion_chat", ip=client_ip(request), mood=result["mood"], crisis=result["crisis"])
    return result


@app.post("/companion/end-session", dependencies=[Depends(require_owner)])
def companion_end_session(req: EndSessionRequest, request: Request):
    """Summarize this session into long-term memory now."""
    result = update_memory(req.session_id, force=True)
    log_event("companion_end_session", ip=client_ip(request), processed=result["processed"])
    return result


# ---------- Memory controls (owner only) ----------
@app.get("/companion/memory", dependencies=[Depends(require_owner)])
def memory_list():
    return list_memory()


@app.delete("/companion/memory/fact/{fact_id}", dependencies=[Depends(require_owner)])
def memory_delete_fact(fact_id: int):
    if not delete_fact(fact_id):
        raise HTTPException(status_code=404, detail="No such fact.")
    remove_item("fact", fact_id)
    return {"deleted": True}


@app.delete("/companion/memory/summary/{summary_id}", dependencies=[Depends(require_owner)])
def memory_delete_summary(summary_id: int):
    if not delete_summary(summary_id):
        raise HTTPException(status_code=404, detail="No such summary.")
    remove_item("sum", summary_id)
    return {"deleted": True}


@app.delete("/companion/memory", dependencies=[Depends(require_owner)])
def memory_clear_all(request: Request, confirm: bool = False):
    """Deletes ALL messages, summaries, and facts. Requires ?confirm=true."""
    if not confirm:
        raise HTTPException(status_code=400, detail="Add ?confirm=true to delete everything.")
    counts = clear_everything()
    clear_index()
    log_event("companion_memory_cleared", ip=client_ip(request), **counts)
    return counts


@app.delete("/companion/history", dependencies=[Depends(require_owner)])
def companion_clear_history(request: Request, session_id: str = "default"):
    deleted = clear_history(session_id)
    log_event("companion_history_cleared", ip=client_ip(request), deleted=deleted)
    return {"deleted_messages": deleted}


# ---------- Voice (owner only) ----------
@app.post(
    "/voice/transcribe",
    dependencies=[Depends(require_owner), Depends(rate_limit(max_calls=10, window_seconds=60))],
)
def voice_transcribe(audio: UploadFile = File(...)):
    """Turn an audio file into text (nothing is stored)."""
    path = save_upload(audio)
    try:
        text = transcribe(str(path))
    finally:
        path.unlink(missing_ok=True)  # your recording is deleted right away
    return {"text": text}


@app.post(
    "/companion/voice-chat",
    dependencies=[Depends(require_owner), Depends(rate_limit(max_calls=10, window_seconds=60))],
)
def companion_voice_chat(
    request: Request,
    background: BackgroundTasks,
    audio: UploadFile = File(...),
    session_id: str = Form("default"),
):
    """Speak to the companion: audio in, text and spoken reply out."""
    if not re.match(SESSION_PATTERN, session_id):
        raise HTTPException(status_code=422, detail="Invalid session_id.")

    path = save_upload(audio)
    try:
        text = transcribe(str(path))
    finally:
        path.unlink(missing_ok=True)
    if not text:
        raise HTTPException(status_code=422, detail="I could not hear any speech in that audio.")

    result = companion_chat(text, session_id)  # same safety, guardrails, and memory as text chat

    try:
        audio_file, voice_engine = synthesize(result["reply"])
    except Exception:
        audio_file, voice_engine = None, None  # the text reply is still returned if speech fails

    if not result["crisis"] and result["mood"] != "blocked":
        background.add_task(update_memory, session_id)
    log_event("companion_voice_chat", ip=client_ip(request), mood=result["mood"],
              crisis=result["crisis"], voice=voice_engine)
    return {"transcript": text, **result, "audio_file": audio_file, "voice": voice_engine}


@app.get("/voice/audio/{filename}", dependencies=[Depends(require_owner)])
def voice_audio(filename: str):
    """Download a generated reply. Only files we created can be fetched."""
    if not is_valid_output_name(filename):
        raise HTTPException(status_code=404, detail="Not found.")
    path = AUDIO_OUT_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Not found (files are deleted after an hour).")
    return FileResponse(path, media_type="audio/wav", filename=filename)