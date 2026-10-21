import json
import time

from app.config import ROOT

LOG_FILE = ROOT / "logs" / "audit.jsonl"


def log_event(event: str, **fields) -> None:
    """Append one JSON line per event (who/what/when). Never log secrets here."""
    LOG_FILE.parent.mkdir(exist_ok=True)
    record = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "event": event, **fields}
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
