"""Shows why a question is (or is not) answered, and where the time goes.

Run:  python -m scripts.debug_rag
Edit QUESTIONS below to test your own."""
import time

import ollama

from app.rag import (
    DATA_DIR, KEEP_ALIVE, MAX_DISTANCE, MODEL, answer_presentation, collection,
    ingest_public_detailed, retrieve, select_hits,
)
from app.knowledge_rules import has_real_content, strip_templates
from app.rag import chunk_text

QUESTIONS = [
    "What are your skills?",
    "Tell me about your projects",
    "What are you studying?",
    "What are your goals?",
    "What do you do in your free time?",
]


def field(response, name):
    try:
        return response[name]
    except Exception:
        return getattr(response, name, None)


print("== 1. Your topic files ==")
for path in sorted(DATA_DIR.glob("*")):
    if path.suffix.lower() not in {".md", ".txt"}:
        continue
    real = [c for c in chunk_text(strip_templates(path.read_text(encoding="utf-8"))) if has_real_content(c)]
    print(f"  {path.name:20} {'OK, ' + str(len(real)) + ' chunk(s) with real content' if real else 'NO REAL CONTENT (still a template). Write full sentences here.'}")

report = ingest_public_detailed()
print(f"\nReloaded: {report['chunks']} chunks stored. Collection now holds {collection.count()}.")
print(f"Distance limit (MAX_DISTANCE) = {MAX_DISTANCE}")

print("\n== 2. What the search finds for each question ==")
for q in QUESTIONS:
    started = time.time()
    hits = retrieve(q)
    took = time.time() - started
    print(f"\n  Q: {q}   (search took {took:.2f}s)")
    if not hits:
        print("     nothing stored at all, so it will always say 'I don't have that information'")
    for h in hits:
        mark = "within limit" if h["distance"] <= MAX_DISTANCE else "TOO FAR"
        preview = h["text"][:70].replace("\n", " ")
        print(f"     {h['distance']:.3f} {mark:12} {h['source']:18} {preview}")

print("\n== 2b. What the model is actually given (after the topic boost and size limit) ==")
for q in QUESTIONS:
    used = select_hits(q)
    names = ", ".join(f"{h['source']} ({h['distance']:.2f})" for h in used) or "nothing -> will say it has no information"
    print(f"  {q:40} -> {names}")

print("\n== 3. Speed of the language model ==")
first = ollama.chat(model=MODEL, messages=[{"role": "user", "content": "Reply with one short sentence about Python."}],
                    options={"num_predict": 40}, keep_alive=KEEP_ALIVE)
load = (field(first, "load_duration") or 0) / 1e9
evals = field(first, "eval_count") or 0
eval_time = (field(first, "eval_duration") or 1) / 1e9
speed = evals / eval_time if eval_time else 0
print(f"  model load time : {load:.1f}s   (large = the model was not in memory)")
print(f"  writing speed   : {speed:.1f} tokens per second")
if speed < 5:
    print("  -> slow CPU speed. Try MODEL = \"llama3.2:1b\" in app/rag.py, and close other heavy programs.")
if load > 5:
    print("  -> the model had to load. KEEP_ALIVE keeps it ready for the next questions.")

print("\n== 4. A full answer, timed ==")
for q in QUESTIONS[:2]:
    started = time.time()
    result = answer_presentation(q)
    print(f"  {time.time() - started:5.1f}s  Q: {q}")
    print(f"          A: {result['answer'][:200]}")
    stats = result.get("stats")
    if stats:
        print(f"          reading {stats['prompt_tokens']} tokens took {stats['prompt_seconds']}s; "
              f"writing {stats['answer_tokens']} tokens took {stats['answer_seconds']}s")