"""Claude Haiku vision filter — classifies a video frame for military/recon relevance."""
from __future__ import annotations

import asyncio
import base64
import logging

import anthropic
import cv2

from scraper.config import HAIKU_MODEL, HAIKU_PROMPT

log = logging.getLogger("scraper.haiku_filter")


def _extract_middle_frame_jpg(video_path: str) -> bytes | None:
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, total // 2)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    _, buf = cv2.imencode(".jpg", frame)
    return buf.tobytes()


def _call_haiku(video_path: str) -> str:
    jpg = _extract_middle_frame_jpg(video_path)
    if jpg is None:
        return "unsure"

    b64 = base64.b64encode(jpg).decode()
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": b64,
                    },
                },
                {"type": "text", "text": HAIKU_PROMPT},
            ],
        }],
    )
    answer = response.content[0].text.strip().lower().split()[0]
    return answer if answer in {"yes", "no", "unsure"} else "unsure"


async def classify_frame(video_path: str) -> str:
    """Classify a video frame via Claude Haiku vision. Returns 'yes'/'no'/'unsure'."""
    try:
        return await asyncio.to_thread(_call_haiku, video_path)
    except Exception as exc:
        log.error(f"Haiku classify error for {video_path}: {exc}")
        return "unsure"
