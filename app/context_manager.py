"""Context Manager: gathers everything the prompt may need, from every source."""
import re

from app.config import ROOT
from app.long_term import search_memory
from app.memory import recent_messages
from app.rag import MAX_DISTANCE, _chroma, chunk_text, retrieve

PRIVATE_DIR = ROOT / "data" / "private"
STYLE_FILE = "style_samples.md"      # how I talk (examples, not searched)
PROFILE_FILE = "personality.md"      # who I am (always included)
PRIVATE_MAX_DISTANCE = 0.85
STYLE_MAX_CHARS = 2000
PROFILE_MAX_CHARS = 1500

private_collection = _chroma.get_or_create_collection(
    "private_me", metadata={"hnsw:space": "cosine"}
)


def _read_clean(path) -> str:
    text = path.read_text(encoding="utf-8")
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL).strip()  # drop template comments


def ingest_private() -> int:
    """Rebuild the private collection from data/private (owner only)."""
    existing = private_collection.get()["ids"]
    if existing:
        private_collection.delete(ids=existing)

    count = 0
    for path in sorted(PRIVATE_DIR.glob("*")):
        if path.suffix.lower() not in {".md", ".txt"} or path.name in {STYLE_FILE, PROFILE_FILE}:
            continue
        chunks = [c for c in chunk_text(_read_clean(path)) if len(c) > 40]
        if not chunks:
            continue
        private_collection.add(
            ids=[f"{path.name}-{i}" for i in range(len(chunks))],
            documents=chunks,
            metadatas=[{"source": path.name, "visibility": "private"}] * len(chunks),
        )
        count += len(chunks)
    return count


def _load_file(name: str, limit: int, empty: str) -> str:
    path = PRIVATE_DIR / name
    if not path.exists():
        return empty
    return _read_clean(path)[:limit] or empty


def _retrieve_private(question: str, k: int = 3) -> list[str]:
    if private_collection.count() == 0:
        return []
    result = private_collection.query(query_texts=[question], n_results=k)
    return [
        doc
        for doc, dist in zip(result["documents"][0], result["distances"][0])
        if dist <= PRIVATE_MAX_DISTANCE
    ]


def build_context(message: str, session_id: str) -> dict:
    return {
        "profile": _load_file(PROFILE_FILE, PROFILE_MAX_CHARS, "(no profile written yet)"),
        "style": _load_file(STYLE_FILE, STYLE_MAX_CHARS, "(no style examples yet)"),
        "personal": _retrieve_private(message),
        "public": [h["text"] for h in retrieve(message, k=2) if h["distance"] <= MAX_DISTANCE],
        "long_term": search_memory(message),
        "history": recent_messages(session_id),
    }