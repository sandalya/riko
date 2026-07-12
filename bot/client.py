"""Telegram receiver — saves video/photo, runs detector, sends recon report + bbox previews."""
import asyncio
import json
import logging
import sys
import tempfile
import time
from pathlib import Path

import anthropic
import cv2
import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from core.config import (
    AGENT_PROMPT_PATH,
    ANTHROPIC_API_KEY,
    DATA_INPUT_DIR,
    DATA_OUTPUT_DIR,
    DETECTOR_URL,
)

# cv_toolkit helpers (shared with ingest_frame.py CLI)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cv_toolkit.pipeline.ingest_frame import (
    CLASS_COLORS,
    COCO_DIR,
    DEFAULT_COLOR,
    FRAMES_DIR,
    PREVIEWS_DIR,
    TAXONOMY,
    YOLO_TO_TAXONOMY,
    build_coco_multi,
    draw_overlay,
    extract_frame,
    map_detections,
)
from cv_toolkit.labeling.cvat_push import (
    CVAT_CATEGORY_ID_OFFSET,
    DEFAULT_HOST,
    DEFAULT_PROJECT_ID,
    push_task,
)
from cv_toolkit.labeling.coco_export import shift_category_ids

log = logging.getLogger("bot.client")

MODEL = "claude-sonnet-5"
_SYSTEM_PROMPT: str | None = None

# In-memory state: user_id → pending CVAT push payload
_pending_cvat: dict[int, dict] = {}

MAX_PREVIEW_FRAMES = 8   # TG media group limit is 10; keep headroom
MIN_CONFIDENCE = 0.35    # filter out very low-confidence noise


def _system_prompt() -> str:
    global _SYSTEM_PROMPT
    if _SYSTEM_PROMPT is None:
        _SYSTEM_PROMPT = AGENT_PROMPT_PATH.read_text(encoding="utf-8")
    return _SYSTEM_PROMPT


def _ts() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


# ── detector ──────────────────────────────────────────────────────────────────

async def _run_detector(endpoint: str, payload: dict) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{DETECTOR_URL}{endpoint}", json=payload)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        log.error(f"Detector error: {exc}")
        return None


# ── Claude Agent ──────────────────────────────────────────────────────────────

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


# ── frame preview helpers ─────────────────────────────────────────────────────

def _extract_preview(
    video_path: Path,
    frame_idx: int,
    raw_detections: list[dict],
) -> tuple[Path, Path, list[dict]] | None:
    """Extract frame, draw overlay, save. Returns (frame_path, preview_path, mapped_dets)."""
    try:
        frame, fps, _ = extract_frame(video_path, frame_idx)
    except Exception as exc:
        log.warning(f"Frame {frame_idx} extraction failed: {exc}")
        return None

    # All detections for overlay (show even unmapped, grey color)
    all_for_overlay = []
    for d in raw_detections:
        tax_id = YOLO_TO_TAXONOMY.get(d["cls"].lower())
        all_for_overlay.append({
            "taxonomy_id": tax_id if tax_id is not None else -1,
            "label": TAXONOMY.get(tax_id, d["cls"]) if tax_id is not None else d["cls"],
            "confidence": d["confidence"],
            "bbox_xyxy": d["bbox"],
        })

    # Taxonomy-mapped only (for COCO export)
    mapped = map_detections(raw_detections)

    stem = f"{video_path.stem}_f{frame_idx:06d}"
    frame_path = FRAMES_DIR / f"{stem}.jpg"
    preview_path = PREVIEWS_DIR / f"preview_{stem}.jpg"

    cv2.imwrite(str(frame_path), frame)
    preview = draw_overlay(frame, all_for_overlay)
    cv2.imwrite(str(preview_path), preview)

    return frame_path, preview_path, mapped


# ── handlers ──────────────────────────────────────────────────────────────────

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

    # Draw overlay on the photo and send it back
    raw_dets = result.get("detections", [])
    if raw_dets:
        try:
            frame = cv2.imread(str(dest))
            all_for_overlay = []
            for d in raw_dets:
                tax_id = YOLO_TO_TAXONOMY.get(d["cls"].lower())
                all_for_overlay.append({
                    "taxonomy_id": tax_id if tax_id is not None else -1,
                    "label": TAXONOMY.get(tax_id, d["cls"]) if tax_id is not None else d["cls"],
                    "confidence": d["confidence"],
                    "bbox_xyxy": d["bbox"],
                })
            preview = draw_overlay(frame, all_for_overlay)
            preview_path = PREVIEWS_DIR / f"preview_{Path(filename).stem}.jpg"
            cv2.imwrite(str(preview_path), preview)
            labels_str = ", ".join(
                f"{d['label']} {d['confidence']:.2f}" for d in all_for_overlay
            )
            await msg.reply_photo(photo=preview_path.open("rb"), caption=f"🎯 {labels_str}")
        except Exception as exc:
            log.error(f"Preview generation failed: {exc}")

    report = await _run_agent(result, "image")
    if report:
        await msg.reply_text(report)
    else:
        await msg.reply_text(f"✅ {len(raw_dets)} об'єктів знайдено")


async def handle_video(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user_id = update.effective_user.id

    await msg.reply_text("⏳ Завантажую відео...")

    video = msg.video or msg.video_note
    file = await ctx.bot.get_file(video.file_id)
    ext = ".mp4"
    if hasattr(video, "file_name") and video.file_name:
        ext = Path(video.file_name).suffix or ext
    filename = f"video_{_ts()}{ext}"
    dest = DATA_INPUT_DIR / filename
    await file.download_to_drive(str(dest))
    log.info(f"Saved video: {dest}")

    await msg.reply_text("🔍 Запускаю детектор...")

    result = await _run_detector("/detect_video", {"video_path": str(dest), "every_n_frames": 15})
    if result is None:
        await msg.reply_text("❌ Детектор недоступний. Перевір чи запущений сервіс на порту 8000.")
        return

    DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_OUTPUT_DIR / f"{Path(filename).stem}_detections.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    fps = result.get("fps", 25.0)
    timeline = result.get("timeline", [])

    # Filter frames: must have at least one detection above threshold
    frames_with_det = [
        f for f in timeline
        if any(d["confidence"] >= MIN_CONFIDENCE for d in f["detections"])
    ]

    if not frames_with_det:
        total = sum(len(f["detections"]) for f in timeline)
        await msg.reply_text(
            f"🔍 Детектор не знайшов впевнених об'єктів.\n"
            f"(Проаналізовано {len(timeline)} кадрів, {total} слабких детекцій нижче порогу {MIN_CONFIDENCE})"
        )
        return

    # Rank by total confidence, take top N
    frames_with_det.sort(
        key=lambda f: sum(d["confidence"] for d in f["detections"] if d["confidence"] >= MIN_CONFIDENCE),
        reverse=True,
    )
    top_frames = frames_with_det[:MAX_PREVIEW_FRAMES]

    await msg.reply_text(
        f"📸 Знайшов об'єкти у {len(frames_with_det)} кадрах → показую топ {len(top_frames)}..."
    )

    # Extract frames + draw overlays (in thread to avoid blocking)
    previews: list[tuple[int, Path, Path, list[dict]]] = []

    def _build_previews():
        for f_data in top_frames:
            frame_idx = round(f_data["frame_time"] * fps)
            result = _extract_preview(dest, frame_idx, f_data["detections"])
            if result is not None:
                fp, pp, mapped = result
                previews.append((frame_idx, fp, pp, mapped))

    await asyncio.to_thread(_build_previews)

    if not previews:
        await msg.reply_text("❌ Не вдалося витягнути кадри.")
        return

    # Send as media group (photo album)
    media = []
    for i, (fidx, fp, pp, mapped) in enumerate(previews):
        ts_sec = fidx / fps
        if mapped:
            det_str = " | ".join(f"{d['label']} {d['confidence']:.2f}" for d in mapped)
        else:
            # Show raw YOLO labels if nothing mapped to taxonomy
            raw_f = top_frames[i]
            det_str = " | ".join(
                f"{d['cls']} {d['confidence']:.2f}"
                for d in raw_f["detections"]
                if d["confidence"] >= MIN_CONFIDENCE
            )
        caption = f"#{i+1}  frame={fidx}  t={ts_sec:.1f}s\n{det_str}"
        if i == 0:
            caption = f"🎯 Топ кадри з детекціями\n\n{caption}"
        with pp.open("rb") as fh:
            media.append(InputMediaPhoto(media=fh.read(), caption=caption))

    await msg.reply_media_group(media=media)

    # Store pending state for CVAT push
    _pending_cvat[user_id] = {
        "video_path": dest,
        "previews": previews,  # list of (frame_idx, frame_path, preview_path, mapped_dets)
        "task_name": f"tg_{dest.stem[-12:]}",
    }

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            f"📤 Push {len(previews)} frames → CVAT",
            callback_data="cvat_push",
        ),
        InlineKeyboardButton("❌ Skip", callback_data="cvat_skip"),
    ]])
    await msg.reply_text(
        f"Відправити ці {len(previews)} кадрів у CVAT для лейблування?",
        reply_markup=keyboard,
    )


async def handle_cvat_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if query.data == "cvat_skip":
        await query.edit_message_text("❌ Пропущено.")
        _pending_cvat.pop(user_id, None)
        return

    pending = _pending_cvat.get(user_id)
    if not pending:
        await query.edit_message_text("❌ Немає збережених кадрів — надішли відео знову.")
        return

    await query.edit_message_text("⏳ Пушу в CVAT...")

    previews = pending["previews"]
    task_name = pending["task_name"]

    # Build multi-frame COCO
    coco_input = []
    frame_paths = []
    for frame_idx, fp, _pp, mapped in previews:
        img = cv2.imread(str(fp))
        if img is None:
            continue
        h, w = img.shape[:2]
        coco_input.append((fp.name, w, h, mapped))
        frame_paths.append(fp)

    if not frame_paths:
        await query.edit_message_text("❌ Кадри не знайдено на диску.")
        return

    coco = build_coco_multi(coco_input)
    coco_shifted = shift_category_ids(coco, CVAT_CATEGORY_ID_OFFSET)

    try:
        from cvat_sdk import make_client
        import os
        host = os.environ.get("CVAT_HOST", DEFAULT_HOST)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", prefix="cvat_bot_", delete=False
        ) as tf:
            json.dump(coco_shifted, tf)
            tmp_coco = Path(tf.name)

        try:
            with make_client(
                host,
                credentials=(os.environ["CVAT_USER"], os.environ["CVAT_PASSWORD"]),
            ) as client:
                task = await asyncio.to_thread(
                    push_task,
                    client,
                    DEFAULT_PROJECT_ID,
                    task_name,
                    frame_paths,
                    tmp_coco,
                )
        finally:
            tmp_coco.unlink(missing_ok=True)

        _pending_cvat.pop(user_id, None)
        await query.edit_message_text(
            f"✅ Готово!\n\n"
            f"Task: {task.name!r}  (id={task.id})\n"
            f"Frames: {len(frame_paths)}\n"
            f"🔗 {host}/tasks/{task.id}"
        )

    except Exception as exc:
        log.error(f"CVAT push failed: {exc}")
        await query.edit_message_text(f"❌ CVAT push failed: {exc}")


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
    app.add_handler(CallbackQueryHandler(handle_cvat_callback, pattern="^cvat_"))
    log.info("Handlers налаштовано")
