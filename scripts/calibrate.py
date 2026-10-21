"""Shows the distance of the best matches for any question, so you can pick MAX_DISTANCE.

Run:  python -m scripts.calibrate
"""
from app.rag import MAX_DISTANCE, ingest_public, retrieve

QUESTIONS = [
    # Questions your files DO answer (edit to match your content)
    "What are your skills?",
    "Tell me about your projects",
    "What do you do in your free time?",
    # Questions your files do NOT answer
    "What is your favorite movie?",
    "What is the capital of France?",
    "How much salary do you want?",
]

print("Re-ingesting data/public ...", ingest_public(), "chunks\n")
print(f"Current MAX_DISTANCE = {MAX_DISTANCE}\n")
for q in QUESTIONS:
    hits = retrieve(q, k=1)
    if hits:
        print(f"{hits[0]['distance']:.3f}  {q}   (best chunk from {hits[0]['source']})")
    else:
        print(f"-----  {q}   (no data)")
print("\nGood setting: put MAX_DISTANCE between the largest distance of questions you CAN answer")
print("and the smallest distance of questions you can NOT answer.")
