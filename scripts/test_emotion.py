"""Checks for the emotion logic. No camera or model needed.

Run:  python -m scripts.test_emotion
"""
from app.emotion import (
    FER_LABELS,
    TTL_SECONDS,
    average_probs,
    combine_mood,
    face_mood_name,
    get_face_emotion,
    set_face_emotion,
    softmax,
    top_label,
)

passed = total = 0


def check(ok: bool, label: str):
    global passed, total
    total += 1
    passed += bool(ok)
    print(("PASS  " if ok else "FAIL  ") + label)


probs = softmax([0.1, 3.0, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0])
check(abs(sum(probs) - 1.0) < 1e-9, "softmax sums to 1")
check(top_label(probs)[0] == "happiness", "top label picks the strongest score")
avg = average_probs([[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]])
check(abs(avg[0] - 2 / 3) < 1e-9, "average of readings")
check(len(FER_LABELS) == 8, "model has 8 labels")

check(get_face_emotion(now=0) is None, "no reading at the start")
set_face_emotion("sadness", 0.8, now=100)
face = get_face_emotion(now=110)
check(face is not None and face["mood"] == "sad", "fresh reading is returned and mapped to a mood")
check(face is not None and face["age_seconds"] == 10.0, "reading reports its age")
check(get_face_emotion(now=100 + TTL_SECONDS + 1) is None, "old reading expires")
set_face_emotion("happiness", 0.3, now=200)
check(get_face_emotion(now=201) is None, "weak reading is ignored")

sad = {"label": "sadness", "confidence": 0.8, "mood": "sad"}
neutral_face = {"label": "neutral", "confidence": 0.9, "mood": "neutral"}
check(combine_mood("happy", sad) == "happy", "his words win over the face")
check(combine_mood("neutral", None) == "neutral", "no camera keeps the text mood")
check(combine_mood("neutral", neutral_face) == "neutral", "neutral face changes nothing")
hint = combine_mood("neutral", sad)
check("may look sad" in hint and "weak signal" in hint, "neutral words plus sad face gives a gentle hint")
check(face_mood_name(None) is None and face_mood_name(sad) == "sad", "face_mood_name helper")

print(f"\nScore: {passed}/{total}")
print("All tests passed!" if passed == total else "Some tests failed.")