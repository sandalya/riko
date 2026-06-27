"""Конфігурація drone-recon бота."""
import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")

LOGS_DIR = BASE_DIR / "logs"
DATA_INPUT_DIR = BASE_DIR / "data" / "input"
