from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from app.audit import log_event
from app.auth import auth_configured, create_token, require_owner, verify_password
from app.pipeline import run_presentation
from app.rag import ingest_public
from app.ratelimit import rate_limit

app = FastAPI(title="Digital Me", version="0.3.0")


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


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@app.get("/health")
def health():
    return {"status": "ok"}


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
