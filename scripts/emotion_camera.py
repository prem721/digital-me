"""Reads YOUR facial expression from the webcam and sends only a short label to the companion.
Frames are processed in memory and are never saved or uploaded.

1. Start the main server:   uvicorn app.main:app
2. In another terminal:      python -m scripts.emotion_camera --preview
Press q in the preview window (or Ctrl+C) to stop. The camera light shows when it is on."""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from collections import deque

from app.config import OWNER_PASSWORD, ROOT
from app.emotion import FER_LABELS, average_probs, softmax, top_label

BASE_URL = "http://127.0.0.1:8000"
MODEL_PATH = ROOT / "models" / "emotion-ferplus-8.onnx"
MODEL_URLS = [
    "https://huggingface.co/onnxmodelzoo/emotion-ferplus-8/resolve/main/emotion-ferplus-8.onnx",
    "https://github.com/onnx/models/raw/main/validated/vision/body_analysis/emotion_ferplus/model/emotion-ferplus-8.onnx",
]

ANALYZE_EVERY = 0.25   # seconds between frames that are analyzed
SEND_EVERY = 2.0       # seconds between updates sent to the app
WINDOW = 6             # readings averaged together to avoid flicker
MIN_FACE_PIXELS = 80
NO_FACE_RESET = 3.0    # forget old readings after this long without a face


def ensure_model() -> None:
    if MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 1_000_000:
        return
    MODEL_PATH.parent.mkdir(exist_ok=True)
    for url in MODEL_URLS:
        try:
            print("Downloading the emotion model (about 34 MB, one time)...")
            request = urllib.request.Request(url, headers={"User-Agent": "digital-me"})
            with urllib.request.urlopen(request, timeout=120) as response:
                MODEL_PATH.write_bytes(response.read())
            if MODEL_PATH.stat().st_size > 1_000_000:
                print("Model saved to", MODEL_PATH)
                return
        except Exception as error:
            print("  download failed:", error)
        MODEL_PATH.unlink(missing_ok=True)
    print("\nCould not download the model automatically.")
    print("Download 'emotion-ferplus-8.onnx' manually (search for it on Hugging Face or the ONNX Model Zoo)")
    print("and save it as:", MODEL_PATH)
    sys.exit(1)


def api(path: str, payload: dict | None = None, token: str | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(BASE_URL + path, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def login() -> str:
    if not OWNER_PASSWORD:
        print("OWNER_PASSWORD is missing in the .env file.")
        sys.exit(1)
    return api("/auth/login", {"password": OWNER_PASSWORD})["access_token"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="show the camera with the detected emotion")
    parser.add_argument("--camera", type=int, default=0, help="camera number (0 is the default webcam)")
    args = parser.parse_args()

    import cv2
    import numpy as np
    import onnxruntime as ort

    if not hasattr(cv2, "CascadeClassifier") or not hasattr(cv2, "data"):
        print("This OpenCV version has no built-in face detector. Install the 4.x line instead:")
        print('  python -m pip uninstall -y opencv-python')
        print('  python -m pip install "opencv-python<5"')
        sys.exit(1)

    ensure_model()
    session = ort.InferenceSession(str(MODEL_PATH), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    try:
        token = login()
    except Exception as error:
        print("Could not log in to the main app. Is it running (uvicorn app.main:app)?", error)
        sys.exit(1)

    camera = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
    if not camera.isOpened():
        print("Could not open the camera. Close other apps using it, and check Windows Settings >")
        print("Privacy & security > Camera > 'Let desktop apps access your camera'.")
        sys.exit(1)

    print("Camera on. Reading your expression (nothing is saved). Press q in the preview, or Ctrl+C, to stop.")
    recent: deque = deque(maxlen=WINDOW)
    last_face_time = last_sent = last_analyzed = 0.0
    shown = "no face"

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                time.sleep(0.2)
                continue
            now = time.time()

            if now - last_analyzed >= ANALYZE_EVERY:
                last_analyzed = now
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = cascade.detectMultiScale(
                    gray, scaleFactor=1.2, minNeighbors=5, minSize=(MIN_FACE_PIXELS, MIN_FACE_PIXELS)
                )
                if len(faces) > 0:
                    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])  # only the largest face
                    face = cv2.resize(gray[y : y + h, x : x + w], (64, 64))
                    model_input = face.astype(np.float32).reshape(1, 1, 64, 64)
                    logits = session.run(None, {input_name: model_input})[0][0]
                    recent.append(softmax([float(v) for v in logits]))
                    last_face_time = now
                    label, confidence = top_label(average_probs(list(recent)))
                    shown = f"{label} {confidence:.2f}"
                    if args.preview:
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 200, 0), 2)
                elif now - last_face_time > NO_FACE_RESET:
                    recent.clear()
                    shown = "no face"

            if recent and now - last_sent >= SEND_EVERY:
                last_sent = now
                label, confidence = top_label(average_probs(list(recent)))
                try:
                    api("/companion/emotion", {"label": label, "confidence": round(confidence, 3)}, token)
                except urllib.error.HTTPError as error:
                    if error.code == 401:  # login expired
                        token = login()
                except Exception:
                    print("Main app not reachable, will keep trying...")

            if args.preview:
                cv2.putText(frame, shown, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 200, 0), 2)
                cv2.imshow("Emotion preview (press q to quit)", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            else:
                time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Camera off.")


if __name__ == "__main__":
    main()