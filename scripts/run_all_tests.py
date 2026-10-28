"""Runs every test that needs no running server, and prints one summary.

Run:  python -m scripts.run_all_tests              (fast checks only)
      python -m scripts.run_all_tests --with-llm   (also the accuracy test, needs Ollama)"""
import re
import subprocess
import sys

CHECKS = [
    ("Guardrails", "scripts.test_guardrails"),
    ("Companion safety", "scripts.test_companion"),
    ("Memory", "scripts.test_memory"),
    ("Voice helpers", "scripts.test_voice"),
    ("Emotion logic", "scripts.test_emotion"),
    ("Public mode", "scripts.test_public_mode"),
    ("Topic file cleaning", "scripts.test_knowledge"),
]
if "--with-llm" in sys.argv:
    CHECKS.append(("Presentation accuracy + attacks", "scripts.evaluate"))

all_ok = True
print(f"{'Test':34} Result")
print("-" * 52)
for name, module in CHECKS:
    run = subprocess.run([sys.executable, "-m", module], capture_output=True, text=True)
    match = re.search(r"Score:\s*(\d+)/(\d+)", run.stdout)
    if run.returncode != 0 or not match:
        all_ok = False
        print(f"{name:34} ERROR (could not run)")
        print("   " + (run.stderr.strip().splitlines() or ["no output"])[-1])
        continue
    got, total = int(match.group(1)), int(match.group(2))
    ok = got == total
    all_ok &= ok
    print(f"{name:34} {'PASS' if ok else 'FAIL'}  {got}/{total}")
    if not ok:
        for line in run.stdout.splitlines():
            if line.startswith("FAIL"):
                print("   " + line)

print("-" * 52)
print("ALL TESTS PASSED" if all_ok else "SOME TESTS FAILED")
sys.exit(0 if all_ok else 1)