"""Telegram receiver — saves video/photo, runs detector, sends Claude recon report."""
import asyncio
import json
import logging
import time
from pathlib import Path

import anthropic
import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from core.config import (
    AGENT_PROMPT_PATH,
    ANTHROPIC_API_KEY,
    DATA_INPUT_DIR,
    DATA_OUTPUT_DIR,
    DETECTOR_URL,
)

log = logging.getLogger("bot.client")

MODEL = "claude-sonnet-4-6"
_SYSTEM_PROMPT: str | None = None


def _system_prompt() -> str:
    global _SYSTEM_PROMPT
    if _SYSTEM_PROMPT is None:
        _SYSTEM_PROMPT = AGENT_PROMPT_PATH.read_text(encoding="utf-8")
    return _SYSTEM_PROMPT


def _ts() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

async def _run_detector(endpoint: str, payload: dict) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{DETECTOR_URL}{endpoint}", json=payload)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        log.error(f"Detector error: {exc}")
        return None


# ---------------------------------------------------------------------------
# Claude Agent
# ---------------------------------------------------------------------------

def _build_prompt(detections: dict, media_type: str) -> str:
    section = "Video detections" if media_type == "video" else "Image detections"
    body = json.dumps(detections, indent=2)
    return f"## {section}\n\n```json\n{body}\n```\n\nProduce the reconnaissance report."


def _call_claude(detections: dict, media_type: str) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=_system_prompt(),
        messages=[{"role": "user", "content": _build_prompt(detections, media_type)}],
    )
    return response.content[0].text


async def _run_agent(detections: dict, media_type: str) -> str | None:
    try:
        return await asyncio.to_thread(_call_claude, detections, media_type)
    except Exception as exc:
        log.error(f"Agent error: {exc}")
        return None


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def handle_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    await msg.reply_text("⏳ Отримано фото, запускаю детектор + агент...")

    photo = msg.photo[-1]
    file = await ctx.bot.get_file(photo.file_id)
    filename = f"photo_{_ts()}.jpg"
    dest = DATA_INPUT_DIR / filename
    await file.download_to_drive(str(dest))
    log.info(f"Saved photo: {dest}")

    result = await _run_detector("/detect", {"image_path": str(dest)})
    if result is None:
        await msg.reply_text("❌ Детектор недоступний. Перевір чи запущений сервіс на порту 8000.")
        return

    DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_OUTPUT_DIR / f"{Path(filename).stem}_detections.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    report = await _run_agent(result, "image")
    if report:
        await msg.reply_text(report)
    else:
        total = len(result.get("detections", []))
        await msg.reply_text(f"✅ Готово: {total} об'єктів знайдено (звіт агента недоступний)")

    await msg.reply_document(
        document=out_path.open("rb"),
        filename=out_path.name,
        caption="JSON detections",
    )
    log.info(f"Sent report + detections: {out_path}")


async def handle_video(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    await msg.reply_text("⏳ Отримано відео, запускаю детектор + агент...")

    video = msg.video or msg.video_note
    file = await ctx.bot.get_file(video.file_id)
    ext = ".mp4"
    if hasattr(video, "file_name") and video.file_name:
        ext = Path(video.file_name).suffix or ext
    filename = f"video_{_ts()}{ext}"
    dest = DATA_INPUT_DIR / filename
    await file.download_to_drive(str(dest))
    log.info(f"Saved video: {dest}")

    result = await _run_detector("/detect_video", {"video_path": str(dest), "every_n_frames": 15})
    if result is None:
        await msg.reply_text("❌ Детектор недоступний. Перевір чи запущений сервіс на порту 8000.")
        return

    DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_OUTPUT_DIR / f"{Path(filename).stem}_detections.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    report = await _run_agent(result, "video")
    if report:
        await msg.reply_text(report)
    else:
        total = sum(len(f["detections"]) for f in result.get("timeline", []))
        frames = len(result.get("timeline", []))
        await msg.reply_text(
            f"✅ Готово: {frames} кадрів, {total} об'єктів (звіт агента недоступний)"
        )

    await msg.reply_document(
        document=out_path.open("rb"),
        filename=out_path.name,
        caption="JSON detections",
    )
    log.info(f"Sent report + detections: {out_path}")


async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    doc = update.message.document
    file = await ctx.bot.get_file(doc.file_id)
    orig = doc.file_name or "file"
    ext = Path(orig).suffix or ""
    stem = Path(orig).stem
    filename = f"doc_{_ts()}_{stem}{ext}"
    dest = DATA_INPUT_DIR / filename
    await file.download_to_drive(str(dest))
    log.info(f"Saved document: {dest}")
    await msg.reply_text(f"✅ Збережено: {filename}")


def setup_handlers(app: Application):
    app.add_handler(MessageHandler(filters.VIDEO | filters.VIDEO_NOTE, handle_video))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    log.info("Handlers налаштовано")
