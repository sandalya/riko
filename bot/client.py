"""Telegram receiver — зберігає відео/фото, запускає детектор, повертає JSON."""
import json
import logging
import time
from pathlib import Path

import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from core.config import DATA_INPUT_DIR, DATA_OUTPUT_DIR, DETECTOR_URL

log = logging.getLogger("bot.client")


def _ts() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


async def _run_detector(endpoint: str, payload: dict) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{DETECTOR_URL}{endpoint}", json=payload)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        log.error(f"Detector error: {exc}")
        return None


async def handle_video(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    await msg.reply_text("⏳ Отримано відео, запускаю детектор...")

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

    total = sum(len(f["detections"]) for f in result.get("timeline", []))
    frames = len(result.get("timeline", []))
    summary = f"✅ Готово: {frames} кадрів проаналізовано, {total} об'єктів знайдено"

    await msg.reply_document(
        document=out_path.open("rb"),
        filename=out_path.name,
        caption=summary,
    )
    log.info(f"Sent detections: {out_path}")


async def handle_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    await msg.reply_text("⏳ Отримано фото, запускаю детектор...")

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

    total = len(result.get("detections", []))
    summary = f"✅ Готово: {total} об'єктів знайдено"

    await msg.reply_document(
        document=out_path.open("rb"),
        filename=out_path.name,
        caption=summary,
    )
    log.info(f"Sent detections: {out_path}")


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
