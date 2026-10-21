from app.audit import log_event
from app.guardrails import BLOCK_REPLY, check_input, check_output, clean_input
from app.rag import answer_presentation


def run_presentation(question: str, ip: str = "local") -> dict:
    """Full presentation-mode flow: input guardrail -> RAG+LLM -> output guardrail -> audit."""
    question = clean_input(question)

    allowed, reason = check_input(question)
    if not allowed:
        log_event("input_blocked", ip=ip, reason=reason, question=question[:200])
        return {"answer": BLOCK_REPLY, "sources": []}

    result = answer_presentation(question)

    safe_answer, reason = check_output(result["answer"])
    if reason:
        log_event("output_changed", ip=ip, reason=reason, question=question[:200])
    result["answer"] = safe_answer
    if reason == "prompt_leak":
        result["sources"] = []

    log_event("answered", ip=ip, question=question[:200], sources=result["sources"])
    return result
