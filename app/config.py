import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
# Load THIS project's .env only, and let it win over stray system variables
load_dotenv(ROOT / ".env", override=True)

OWNER_PASSWORD = os.getenv("OWNER_PASSWORD", "")
JWT_SECRET = os.getenv("JWT_SECRET", "")
TOKEN_HOURS = 8

VOICE_SERVICE_URL = os.getenv("VOICE_SERVICE_URL", "")
VOICE_SERVICE_TOKEN = os.getenv("VOICE_SERVICE_TOKEN", "")

# Set by you in the terminal only when sharing publicly (do NOT put it in .env):
#   Command Prompt:  set PUBLIC_MODE=1        PowerShell:  $env:PUBLIC_MODE="1"
PUBLIC_MODE = os.getenv("PUBLIC_MODE", "").strip() == "1"