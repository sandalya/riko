"""Telegram receiver — зберігає відео, фото, документи в data/input/."""
import logging
import time
from pathlib import Path
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from core.config import DATA_INPUT_DIR

log = logging.getLogger("bot.client")


def _ts() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


async def handle_video(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    video = msg.video or msg.video_note
    file = await ctx.bot.get_file(video.file_id)
    ext = ".mp4"
    if hasattr(video, "file_name") and video.file_name:
        ext = Path(video.file_name).suffix or ext
    filename = f"video_{_ts()}{ext}"
    dest = DATA_INPUT_DIR / filename
    await file.download_to_drive(str(dest))
    log.info(f"Saved video: {dest}")
    await msg.reply_text(f"✅ Збережено: {filename}")


async def handle_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    photo = msg.photo[-1]
    file = await ctx.bot.get_file(photo.file_id)
    filename = f"photo_{_ts()}.jpg"
    dest = DATA_INPUT_DIR / filename
    await file.download_to_drive(str(dest))
    log.info(f"Saved photo: {dest}")
    await msg.reply_text(f"✅ Збережено: {filename}")


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
