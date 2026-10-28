"""Memory Update Logic: decides what (if anything) from recent chats becomes long-term memory."""
import ollama

from app.long_term import index_item
from app.memory import add_fact, add_summary, mark_summarized, unsummarized
from app.memory_rules import (
    EXTRACT_PROMPT,
    batch_is_sensitive,
    clean_facts,
    is_sensitive,
    parse_extraction,
)
from app.rag import KEEP_ALIVE, MODEL

SUMMARY_EVERY = 12       # summarize after this many unsummarized messages
MAX_TRANSCRIPT_CHARS = 6000


def _extract(transcript: str) -> dict:
    try:
        response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": EXTRACT_PROMPT},
                {"role": "user", "content": transcript},
            ],
            format="json",
            options={"temperature": 0.2, "num_predict": 300},
            keep_alive=KEEP_ALIVE,
        )
        return parse_extraction(response["message"]["content"])
    except Exception:
        return {"summary": "", "facts": []}


def update_memory(session_id: str, force: bool = False) -> dict:
    """Summarize a session's new messages into long-term memory (gated and filtered)."""
    rows = unsummarized(session_id)
    if not rows or (not force and len(rows) < SUMMARY_EVERY):
        return {"processed": 0, "saved_summary": None, "saved_facts": [], "skipped": None}

    ids = [r["id"] for r in rows]
    user_texts = [r["content"] for r in rows if r["role"] == "user"]

    # Gate: sensitive batches are never turned into long-term memory
    if batch_is_sensitive(user_texts):
        mark_summarized(ids)
        return {"processed": len(ids), "saved_summary": None, "saved_facts": [],
                "skipped": "sensitive_topic"}

    transcript = "\n".join(
        f"{'Me' if r['role'] == 'user' else 'Companion'}: {r['content']}" for r in rows
    )[-MAX_TRANSCRIPT_CHARS:]
    data = _extract(transcript)

    saved_summary = None
    summary = data["summary"]
    if summary and not is_sensitive(summary):
        sid = add_summary(session_id, summary)
        index_item("sum", sid, summary)
        saved_summary = summary

    saved_facts = []
    for fact in clean_facts(data["facts"]):
        fid = add_fact(fact)
        if fid is not None:
            index_item("fact", fid, fact)
            saved_facts.append(fact)

    mark_summarized(ids)
    return {"processed": len(ids), "saved_summary": saved_summary,
            "saved_facts": saved_facts, "skipped": None}