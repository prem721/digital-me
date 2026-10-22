"""Checks for long-term memory storage and the rules that gate it. No LLM needed.

Run:  python -m scripts.test_memory
"""
import pathlib
import tempfile

import app.memory as m
from app.memory_rules import batch_is_sensitive, clean_facts, is_sensitive, parse_extraction

m.DB_FILE = pathlib.Path(tempfile.mkdtemp()) / "test_memory.db"  # never touches your real data

passed = total = 0


def check(ok: bool, label: str):
    global passed, total
    total += 1
    passed += bool(ok)
    print(("PASS  " if ok else "FAIL  ") + label)


# --- storage ---
m.add_message("s1", "user", "hi")
m.add_message("s1", "assistant", "hello")
m.add_message("s2", "user", "other session")
rows = m.unsummarized("s1")
check(len(rows) == 2, "unsummarized returns the session's messages")
m.mark_summarized([r["id"] for r in rows])
check(m.unsummarized("s1") == [], "marked messages are no longer pending")
check(len(m.recent_messages("s1")) == 2, "short-term history still available after summarizing")

sid = m.add_summary("s1", "We talked about planning a project.")
fid = m.add_fact("I am building a project called Digital Me")
check(fid is not None and m.add_fact("I am building a project called Digital Me") is None,
      "duplicate facts are not stored twice")
listing = m.list_memory()
check(len(listing["facts"]) == 1 and len(listing["summaries"]) == 1, "list_memory shows both")
check(m.delete_fact(fid) and not m.delete_fact(fid), "delete fact works once")
check(m.delete_summary(sid), "delete summary works")
counts = m.clear_everything()
check(counts["messages"] == 3, "clear_everything removes all messages")

# --- gating rules ---
check(is_sensitive("I have been feeling anxious and depressed"), "sensitive topic detected")
check(not is_sensitive("I want to finish my RAG project this week"), "normal topic allowed")
check(batch_is_sensitive(["hi", "my therapist said something"]), "batch with sensitive message is gated")
check(not batch_is_sensitive(["hi", "working on FastAPI today"]), "normal batch allowed")

facts = clean_facts(["I prefer coding at night", "I take medication daily", "ok", 5, "x" * 300])
check(facts == ["I prefer coding at night"], "clean_facts drops sensitive, short, long, non-string")

check(parse_extraction('{"summary": "A", "facts": ["b"]}') == {"summary": "A", "facts": ["b"]},
      "parse plain JSON")
check(parse_extraction('Sure! {"summary": "A", "facts": []} Hope it helps')["summary"] == "A",
      "parse JSON with extra text around it")
check(parse_extraction("not json at all") == {"summary": "", "facts": []}, "bad output gives empty result")

print(f"\nScore: {passed}/{total}")