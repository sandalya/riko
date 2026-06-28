"""Download video attachments from Telegram messages."""
from __future__ import annotations

import logging
from pathlib import Path

from telethon import TelegramClient
from telethon.tl.types import Message

log = logging.getLogger("scraper.downloader")


async def download_video(
    client: TelegramClient,
    message: Message,
    dest_dir: str | Path,
) -> Path | None:
    """Download message video to dest_dir. Returns path or None on error."""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    try:
        path = await message.download_media(file=str(dest))
        return Path(path) if path else None
    except Exception as exc:
        log.error(f"Download failed for msg {message.id}: {exc}")
        return None
