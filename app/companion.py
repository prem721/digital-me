"""Companion mode flow:
safety router -> input guardrails -> mood -> context manager -> prompt builder
-> LLM -> output guardrails -> save messages. (Memory update runs afterwards in the background.)"""
import ollama

from app.context_manager import build_context, ingest_private  # noqa: F401  (ingest_private re-exported)
from app.emotion import combine_mood, face_mood_name, get_face_emotion
from app.guardrails import check_input, check_output, clean_input
from app.memory import add_message
from app.prompt_builder import build_messages
from app.rag import KEEP_ALIVE, MODEL
from app.safety import CRISIS_REPLY, detect_mood, is_crisis

FALLBACK_REPLY = "Hmm, I lost my train of thought. Can you say that again?"


def companion_chat(message: str, session_id: str = "default") -> dict:
    message = clean_input(message)

    # 1. Safety router: serious distress gets a fixed caring reply. Nothing is saved.
    if is_crisis(message):
        return {"reply": CRISIS_REPLY, "mood": "crisis", "crisis": True}

    # 2. Input guardrails (length, injection phrases)
    allowed, reason = check_input(message)
    if not allowed:
        return {
            "reply": f"That message was blocked by the input filter ({reason}). Try rewording it.",
            "mood": "blocked",
            "crisis": False,
        }

    # 3. Mood hint: his words first, plus the webcam reading if the camera script is running
    mood = detect_mood(message)
    face = get_face_emotion()
    mood_hint = combine_mood(mood, face)

    # 4-5. Context manager + prompt builder
    ctx = build_context(message, session_id)
    messages = build_messages(ctx, mood_hint, message)

    # 6. LLM
    response = ollama.chat(
        model=MODEL,
        messages=messages,
        options={"temperature": 0.7, "num_predict": 250},
        keep_alive=KEEP_ALIVE,
    )

    # 7. Output guardrails
    reply, reason = check_output(response["message"]["content"].strip())
    if reason == "prompt_leak":
        reply = FALLBACK_REPLY

    # 8. Short-term memory
    add_message(session_id, "user", message)
    add_message(session_id, "assistant", reply)
    return {"reply": reply, "mood": mood, "crisis": False, "face": face_mood_name(face)}