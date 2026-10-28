"""Checks for the cleaning of topic files. No server or models needed.

Run:  python -m scripts.test_knowledge
"""
from app.knowledge_rules import (
    apply_topic_boost, detect_topics, has_real_content, label_chunk, select_context, strip_templates,
)

passed = total = 0


def check(ok: bool, label: str):
    global passed, total
    total += 1
    passed += bool(ok)
    print(("PASS  " if ok else "FAIL  ") + label)


template = "# Projects\n\n(For each project write: its name, what it does, your role.)\n"
check(not has_real_content(strip_templates(template)), "template-only file has no real content")
check(not has_real_content("# Skills"), "a bare heading is not real content")

real = "# Skills\n\nI am skilled in Python and I have built a RAG chatbot with FastAPI."
check(has_real_content(strip_templates(real)), "a file with sentences counts as real content")
check("(" not in strip_templates("Hello there\n(Write something here)\nMore real text"), "placeholder lines are removed")
check("Hello there" in strip_templates("Hello there\n(Write something)") and
      "More real text" in strip_templates("Hello there\n(Write something)\nMore real text"),
      "real lines next to placeholders are kept")
check("secret" not in strip_templates("<!-- secret instructions -->\nI like cricket and chess."),
      "HTML comments are removed")
check(label_chunk("skills", "I know Python.") == "[skills] I know Python.", "chunks are labelled with their topic")
mixed = "# Goals\n\n(Add what you want to learn.)\n\nI want to become a software engineer working on AI products."
check(has_real_content(strip_templates(mixed)), "real sentence under a template still counts")


# --- topic-aware ranking ---
check(detect_topics("What are your skills?") == ["skills"], "topic: skills")
check(detect_topics("Tell me about your projects") == ["projects"], "topic: projects")
check(detect_topics("What are you studying?") == ["education"], "topic: education")
check(detect_topics("What do you do in your free time?") == ["hobbies"], "topic: hobbies")
check(detect_topics("What are your goals?") == ["goals"], "topic: goals")
check(detect_topics("What is the weather today?") == [], "no topic for unrelated questions")

hits = [  # the real numbers from a run: the generic hobbies chunk ranked first
    {"text": "h" * 300, "source": "hobbies.md", "distance": 0.522},
    {"text": "g" * 300, "source": "goals.md", "distance": 0.537},
    {"text": "p" * 300, "source": "projects.md", "distance": 0.561},
    {"text": "s" * 300, "source": "skills.md", "distance": 0.601},
]
ranked = apply_topic_boost(hits, ["projects"], 0.15)
check(ranked[0]["source"] == "projects.md", "boost puts the matching topic file first")
check(apply_topic_boost(hits, [], 0.15)[0]["source"] == "hobbies.md", "no topic means no change in order")
check(hits[0]["distance"] == 0.522, "boost does not modify the original list")

check(len(select_context(ranked, max_chunks=3, max_chars=5000)) == 3, "at most 3 chunks are kept")
check(len(select_context(ranked, max_chunks=3, max_chars=700)) == 2, "size budget limits the chunks")
check(len(select_context([{"text": "x" * 2000, "source": "a.md", "distance": 0.1}], 3, 100)) == 1,
      "the best chunk is kept even if it is long")

print(f"\nScore: {passed}/{total}")