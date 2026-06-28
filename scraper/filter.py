"""Size, quality, and deduplication filters for scraped videos."""
from __future__ import annotations

import cv2
import imagehash
import numpy as np
from PIL import Image

from scraper.config import (
    BLUR_THRESHOLD,
    BRIGHTNESS_MAX,
    BRIGHTNESS_MIN,
    MAX_DURATION_SEC,
    MAX_SIZE_MB,
    MIN_DURATION_SEC,
    MIN_SIZE_MB,
)


# ---------------------------------------------------------------------------
# Metadata filters (no I/O beyond the values already known)
# ---------------------------------------------------------------------------

def is_size_ok(size_bytes: int) -> bool:
    mb = size_bytes / (1024 * 1024)
    return MIN_SIZE_MB <= mb <= MAX_SIZE_MB


def is_duration_ok(duration_sec: int) -> bool:
    if duration_sec == 0:
        return True  # unknown duration — allow, will check after download
    return MIN_DURATION_SEC <= duration_sec <= MAX_DURATION_SEC


# ---------------------------------------------------------------------------
# Frame-level quality checks
# ---------------------------------------------------------------------------

def _extract_middle_frame(video_path: str) -> np.ndarray | None:
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, total // 2)
    ret, frame = cap.read()
    cap.release()
    return frame if ret else None


def compute_blur(frame: np.ndarray) -> float:
    """Laplacian variance — lower = blurrier."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def compute_brightness(frame: np.ndarray) -> float:
    """Mean pixel value of grayscale frame."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(gray.mean())


def is_quality_ok(video_path: str) -> tuple[bool, str]:
    """Extract middle frame and check blur + brightness. Returns (ok, reason)."""
    frame = _extract_middle_frame(video_path)
    if frame is None:
        return False, "cannot_read_frame"

    blur = compute_blur(frame)
    if blur < BLUR_THRESHOLD:
        return False, f"blurry({blur:.1f}<{BLUR_THRESHOLD})"

    brightness = compute_brightness(frame)
    if brightness < BRIGHTNESS_MIN:
        return False, f"too_dark({brightness:.1f}<{BRIGHTNESS_MIN})"
    if brightness > BRIGHTNESS_MAX:
        return False, f"too_bright({brightness:.1f}>{BRIGHTNESS_MAX})"

    return True, "ok"


# ---------------------------------------------------------------------------
# Perceptual hash deduplication
# ---------------------------------------------------------------------------

def compute_phash(video_path: str) -> str:
    """Perceptual hash of the middle frame. Returns empty string on failure."""
    frame = _extract_middle_frame(video_path)
    if frame is None:
        return ""
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    return str(imagehash.phash(img))


def is_duplicate(phash: str, known_hashes: dict) -> bool:
    """True if hamming distance to any known hash is < 8."""
    if not phash:
        return False
    h1 = imagehash.hex_to_hash(phash)
    for known in known_hashes:
        try:
            if h1 - imagehash.hex_to_hash(known) < 8:
                return True
        except Exception:
            continue
    return False
