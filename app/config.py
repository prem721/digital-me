import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
# Load THIS project's .env only, and let it win over stray system variables
load_dotenv(ROOT / ".env", override=True)

OWNER_PASSWORD = os.getenv("OWNER_PASSWORD", "")
JWT_SECRET = os.getenv("JWT_SECRET", "")
TOKEN_HOURS = 8
