"""Quick checks for crisis detection and mood hints. No LLM needed.

Run:  python -m scripts.test_companion
"""
from app.safety import CRISIS_REPLY, detect_mood, is_crisis

passed = total = 0


def check(ok: bool, label: str):
    global passed, total
    total += 1
    passed += ok
    print(("PASS  " if ok else "FAIL  ") + label)


for t in [
    "I want to die",
    "i don't want to live anymore",
    "sometimes I think about killing myself",
    "I feel like there is no reason to go on",
    "I keep thinking about self harm",
]:
    check(is_crisis(t), f"crisis detected: {t!r}")

for t in [
    "My exam is killing me",
    "I'm dying to try this new framework",
    "I feel lonely today",
    "Got selected for the internship!",
]:
    check(not is_crisis(t), f"not a crisis: {t!r}")

check(detect_mood("I feel so alone, nobody texts me") == "lonely", "mood lonely")
check(detect_mood("I'm stressed about the deadline and overwhelmed") == "stressed", "mood stressed")
check(detect_mood("So excited, I got selected, amazing day") == "happy", "mood happy")
check(detect_mood("What should I eat?") == "neutral", "mood neutral")
check("112" in CRISIS_REPLY and "14416" in CRISIS_REPLY, "crisis reply has help numbers")

print(f"\nScore: {passed}/{total}")