"""Short-term messages + long-term summaries and facts, in a local SQLite file.
The file lives in data/private, which git ignores."""
import sqlite3
import time
from contextlib import closing

from app.config import ROOT

DB_FILE = ROOT / "data" / "private" / "memory.db"
HISTORY_TURNS = 10  # recent messages that go back into every prompt


def _connect() -> sqlite3.Connection:
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS messages ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, role TEXT, content TEXT, "
        "ts REAL, summarized INTEGER DEFAULT 0)"
    )
    cols = [r[1] for r in conn.execute("PRAGMA table_info(messages)")]
    if "summarized" not in cols:  # upgrade a database made by Milestone 4
        conn.execute("ALTER TABLE messages ADD COLUMN summarized INTEGER DEFAULT 0")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS summaries ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, text TEXT, ts REAL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS facts ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT UNIQUE, ts REAL)"
    )
    return conn


# ---------- short-term ----------
def add_message(session_id: str, role: str, content: str) -> None:
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO messages (session_id, role, content, ts) VALUES (?, ?, ?, ?)",
            (session_id, role, content, time.time()),
        )


def recent_messages(session_id: str, limit: int = HISTORY_TURNS) -> list[dict]:
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
    return [{"role": r, "content": c} for r, c in reversed(rows)]


def unsummarized(session_id: str) -> list[dict]:
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT id, role, content FROM messages WHERE session_id = ? AND summarized = 0 "
            "ORDER BY id",
            (session_id,),
        ).fetchall()
    return [{"id": i, "role": r, "content": c} for i, r, c in rows]


def mark_summarized(ids: list[int]) -> None:
    if not ids:
        return
    marks = ",".join("?" * len(ids))
    with closing(_connect()) as conn, conn:
        conn.execute(f"UPDATE messages SET summarized = 1 WHERE id IN ({marks})", ids)


def clear_history(session_id: str) -> int:
    with closing(_connect()) as conn, conn:
        return conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,)).rowcount


# ---------- long-term ----------
def add_summary(session_id: str, text: str) -> int:
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO summaries (session_id, text, ts) VALUES (?, ?, ?)",
            (session_id, text, time.time()),
        )
        return cur.lastrowid


def add_fact(text: str) -> int | None:
    """Returns the new id, or None if the same fact is already stored."""
    try:
        with closing(_connect()) as conn, conn:
            cur = conn.execute("INSERT INTO facts (text, ts) VALUES (?, ?)", (text, time.time()))
            return cur.lastrowid
    except sqlite3.IntegrityError:
        return None


def list_memory() -> dict:
    fmt = lambda ts: time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))
    with closing(_connect()) as conn:
        facts = conn.execute("SELECT id, text, ts FROM facts ORDER BY id").fetchall()
        sums = conn.execute("SELECT id, session_id, text, ts FROM summaries ORDER BY id").fetchall()
    return {
        "facts": [{"id": i, "text": t, "saved": fmt(ts)} for i, t, ts in facts],
        "summaries": [
            {"id": i, "session_id": s, "text": t, "saved": fmt(ts)} for i, s, t, ts in sums
        ],
    }


def delete_fact(fact_id: int) -> bool:
    with closing(_connect()) as conn, conn:
        return conn.execute("DELETE FROM facts WHERE id = ?", (fact_id,)).rowcount > 0


def delete_summary(summary_id: int) -> bool:
    with closing(_connect()) as conn, conn:
        return conn.execute("DELETE FROM summaries WHERE id = ?", (summary_id,)).rowcount > 0


def clear_everything() -> dict:
    with closing(_connect()) as conn, conn:
        counts = {
            "messages": conn.execute("DELETE FROM messages").rowcount,
            "summaries": conn.execute("DELETE FROM summaries").rowcount,
            "facts": conn.execute("DELETE FROM facts").rowcount,
        }
    return counts