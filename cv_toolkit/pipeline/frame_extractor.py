"""Extract frames from video files for dataset building.

Two modes:
  interval   — one frame every N seconds (fast, uniform coverage)
  scene      — save when histogram diff to last saved frame > threshold (smarter, fewer duplicates)

Usage:
  python cv_toolkit/pipeline/frame_extractor.py \
      --input data/scraper/approved/ \
      --output cv_toolkit/datasets/raw_frames/ \
      --mode scene --interval 1.0 --scene-threshold 0.4
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

BLUR_MIN = 80.0
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def _blur(frame: np.ndarray) -> float:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _hist(frame: np.ndarray) -> np.ndarray:
    """Normalized HSV hue+saturation histogram."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
    cv2.normalize(h, h)
    return h


def _hist_diff(h1: np.ndarray, h2: np.ndarray) -> float:
    """1 − correlation; 0.0 = identical, ~1.0 = completely different."""
    return 1.0 - float(cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL))


def _save(frame: np.ndarray, output_dir: Path, stem: str, idx: int) -> None:
    cv2.imwrite(str(output_dir / f"{stem}_{idx:06d}.jpg"), frame)


def extract_interval(
    video_path: Path,
    output_dir: Path,
    every_n_sec: float = 1.0,
) -> tuple[int, int]:
    """One frame every `every_n_sec` seconds. Returns (extracted, skipped_blur)."""
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, int(fps * every_n_sec))
    stem = video_path.stem
    extracted = skipped_blur = save_idx = 0

    for pos in range(0, total, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        if not ret:
            continue
        if _blur(frame) < BLUR_MIN:
            skipped_blur += 1
        else:
            _save(frame, output_dir, stem, save_idx)
            extracted += 1
            save_idx += 1

    cap.release()
    return extracted, skipped_blur


def extract_scene_change(
    video_path: Path,
    output_dir: Path,
    threshold: float = 0.4,
) -> tuple[int, int]:
    """Save frame when histogram diff to the last saved frame exceeds threshold."""
    cap = cv2.VideoCapture(str(video_path))
    stem = video_path.stem
    extracted = skipped_blur = save_idx = 0
    ref_hist: np.ndarray | None = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        curr_hist = _hist(frame)
        if ref_hist is not None and _hist_diff(ref_hist, curr_hist) <= threshold:
            continue

        # Scene changed (or first frame) — apply blur gate
        if _blur(frame) < BLUR_MIN:
            skipped_blur += 1
            # Don't update ref_hist: keep comparing to last clean reference
        else:
            _save(frame, output_dir, stem, save_idx)
            extracted += 1
            save_idx += 1
            ref_hist = curr_hist

    cap.release()
    return extracted, skipped_blur


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract frames from video files.")
    parser.add_argument("--input", required=True, help="Video file or directory of videos")
    parser.add_argument("--output", required=True, help="Output directory for frames")
    parser.add_argument("--mode", choices=["interval", "scene"], default="scene")
    parser.add_argument("--interval", type=float, default=1.0, metavar="SEC",
                        help="Seconds between frames (interval mode, default: 1.0)")
    parser.add_argument("--scene-threshold", type=float, default=0.4, metavar="T",
                        help="Histogram diff threshold 0–1 (scene mode, default: 0.4)")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if input_path.is_file():
        videos = [input_path]
    elif input_path.is_dir():
        videos = sorted(
            p for p in input_path.iterdir()
            if p.suffix.lower() in VIDEO_EXTS
        )
    else:
        print(f"Input not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if not videos:
        print(f"No video files found in {input_path}", file=sys.stderr)
        sys.exit(1)

    total_extracted = total_skipped = 0

    for video in videos:
        if args.mode == "interval":
            extracted, skipped = extract_interval(video, output_dir, args.interval)
        else:
            extracted, skipped = extract_scene_change(video, output_dir, args.scene_threshold)

        print(f"{video.name} → {extracted} frames extracted, {skipped} skipped (blur)")
        total_extracted += extracted
        total_skipped += skipped

    if len(videos) > 1:
        print(f"\nTotal: {total_extracted} extracted, {total_skipped} skipped (blur)")
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    main()
