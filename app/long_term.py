"""Searchable index of long-term memory (summaries and facts) using Chroma."""
from app.rag import _chroma

_index = _chroma.get_or_create_collection("companion_memory", metadata={"hnsw:space": "cosine"})
MEMORY_MAX_DISTANCE = 0.8


def index_item(kind: str, item_id: int, text: str) -> None:
    _index.upsert(ids=[f"{kind}-{item_id}"], documents=[text], metadatas=[{"kind": kind}])


def remove_item(kind: str, item_id: int) -> None:
    _index.delete(ids=[f"{kind}-{item_id}"])


def clear_index() -> None:
    ids = _index.get()["ids"]
    if ids:
        _index.delete(ids=ids)


def search_memory(query: str, k: int = 3) -> list[str]:
    if _index.count() == 0:
        return []
    result = _index.query(query_texts=[query], n_results=min(k, _index.count()))
    return [
        doc
        for doc, dist in zip(result["documents"][0], result["distances"][0])
        if dist <= MEMORY_MAX_DISTANCE
    ]