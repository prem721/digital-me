"""Runs in its own process so Windows speech never conflicts with the web server's threads.
Usage (internal): python -m app.tts_worker OUTPUT.wav   (text is read from stdin)"""
import sys


def main() -> None:
    import pyttsx3

    sys.stdin.reconfigure(encoding="utf-8")
    text = sys.stdin.read()
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    engine.save_to_file(text, sys.argv[1])
    engine.runAndWait()


if __name__ == "__main__":
    main()