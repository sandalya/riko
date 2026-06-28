"""Конфігурація drone-recon бота."""
import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
DETECTOR_URL = os.getenv("DETECTOR_URL", "http://localhost:8000")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

AGENT_PROMPT_PATH = BASE_DIR / "agent" / "prompts" / "recon_analyst.md"

LOGS_DIR = BASE_DIR / "logs"
DATA_INPUT_DIR = BASE_DIR / "data" / "input"
DATA_OUTPUT_DIR = BASE_DIR / "data" / "output"
