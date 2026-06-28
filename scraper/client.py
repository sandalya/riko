"""Telethon client — connects to Telegram and fetches channel video messages."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import Message

from scraper.config import SESSION_FILE

load_dotenv(Path(__file__).parent.parent / ".env")

_API_ID   = int(os.getenv("TG_API_ID", "0"))
_API_HASH = os.getenv("TG_API_HASH", "")


def make_client() -> TelegramClient:
    session_path = str(Path(SESSION_FILE).resolve())
    return TelegramClient(session_path, _API_ID, _API_HASH)


async def get_channel_videos(client: TelegramClient, channel: str, limit: int) -> list[Message]:
    """Return messages that have a video attachment, newest first."""
    videos: list[Message] = []
    async for msg in client.iter_messages(channel, limit=limit):
        if msg.video is not None:
            videos.append(msg)
    return videos
