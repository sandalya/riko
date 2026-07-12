"""Batch auto-labeling trial: run the detector over several videos, take each
video's top-N frames by confidence (same ranking bot/client.py uses), and push
them all into one CVAT task with pre-placed YOLO->taxonomy boxes.

Every candidate frame + its raw (unreviewed) detections is first saved to
data/train_pool/ — that's the permanent record of what the detector produced,
independent of review. Frames only join data/golden/ once a human has reviewed
them in CVAT and they're pulled back in (see cvat_pull.py); train_pool data is
never merged into golden automatically.

Usage:
  python -m cv_toolkit.pipeline.auto_ingest_batch \
      --videos-dir data/scraper/approved --count 5 --top-n 8 \
      --task-name auto-v0-round1
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

import cv2
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from cv_toolkit.labeling.cvat_push import push_task, CVAT_CATEGORY_ID_OFFSET, DEFAULT_HOST, DEFAULT_PROJECT_ID
from cv_toolkit.labeling.coco_export import shift_category_ids
from cv_toolkit.pipeline.ingest_frame import (
    TAXONOMY,
    YOLO_TO_TAXONOMY,
    build_coco_multi,
    map_detections,
)

DETECTOR_URL = "http://127.0.0.1:8000/detect_video"
MIN_CONFIDENCE = 0.35
EVERY_N_FRAMES = 15

TRAIN_POOL_DIR = _ROOT / "data" / "train_pool"
FRAMES_DIR = TRAIN_POOL_DIR / "raw"
LABELS_DIR = TRAIN_POOL_DIR / "labels"
MANIFEST_PATH = TRAIN_POOL_DIR / "manifest.json"


def run_detect_video(video_path: Path) -> dict | None:
    payload = json.dumps({"video_path": str(video_path), "every_n_frames": EVERY_N_FRAMES}).encode()
    req = urllib.request.Request(
        DETECTOR_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, OSError) as e:
        print(f"  ERROR: detector call failed for {video_path.name}: {e}", file=sys.stderr)
        return None


def top_frames_for_video(video_path: Path, top_n: int) -> list[tuple[int, list[dict]]]:
    """Return list of (frame_idx, raw_detections) for the top-N frames by confidence."""
    result = run_detect_video(video_path)
    if result is None:
        return []

    fps = result.get("fps", 25.0)
    timeline = result.get("timeline", [])
    frames_with_det = [
        f for f in timeline
        if any(d["confidence"] >= MIN_CONFIDENCE for d in f["detections"])
    ]
    if not frames_with_det:
        return []

    frames_with_det.sort(
        key=lambda f: sum(d["confidence"] for d in f["detections"] if d["confidence"] >= MIN_CONFIDENCE),
        reverse=True,
    )
    top = frames_with_det[:top_n]
    return [(round(f["frame_time"] * fps), f["detections"]) for f in top]


def extract_and_save(video_path: Path, frame_idx: int, stem: str) -> Path | None:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FRAMES_DIR / f"{stem}_f{frame_idx:06d}.jpg"
    cv2.imwrite(str(out_path), frame)
    return out_path


def save_train_pool_record(frame_name: str, mapped: list[dict], video_name: str) -> None:
    """Persist the detector's raw (unreviewed) output for one frame — this is the
    train_pool record, kept regardless of whether the frame is later sent to CVAT
    for review or promoted into golden."""
    LABELS_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "frame": frame_name,
        "source_video": video_name,
        "detections": mapped,  # includes confidence — needed to triage unreviewed data
    }
    out_path = LABELS_DIR / f"{Path(frame_name).stem}.json"
    out_path.write_text(json.dumps(record, indent=2))


def append_manifest(task_name: str, videos: list[str], frame_count: int, cvat_task_id: int | None) -> None:
    from datetime import datetime

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    if MANIFEST_PATH.exists():
        entries = json.loads(MANIFEST_PATH.read_text())
    entries.append({
        "batch": task_name,
        "created": datetime.now().isoformat(timespec="seconds"),
        "source_videos": videos,
        "frame_count": frame_count,
        "cvat_task_id": cvat_task_id,
        "reviewed": False,
    })
    MANIFEST_PATH.write_text(json.dumps(entries, indent=2))


def main() -> None:
    load_dotenv(_ROOT / ".env")

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--videos-dir", default="data/scraper/approved")
    parser.add_argument("--count", type=int, default=5, help="How many videos to sample")
    parser.add_argument("--top-n", type=int, default=8, help="Top-N frames per video by confidence")
    parser.add_argument("--task-name", required=True)
    parser.add_argument("--project-id", type=int, default=DEFAULT_PROJECT_ID)
    parser.add_argument("--host", default=os.environ.get("CVAT_HOST", DEFAULT_HOST))
    parser.add_argument("--seed", type=int, default=None, help="Random seed for video sampling")
    args = parser.parse_args()

    videos_dir = Path(args.videos_dir)
    all_videos = sorted(p for p in videos_dir.iterdir() if p.suffix.lower() == ".mp4")
    if len(all_videos) < args.count:
        print(f"ERROR: only {len(all_videos)} videos found in {videos_dir}, need {args.count}", file=sys.stderr)
        sys.exit(1)

    rng = random.Random(args.seed)
    chosen = rng.sample(all_videos, args.count)

    print(f"Selected {len(chosen)} videos:")
    for v in chosen:
        print(f"  - {v.name}")

    coco_frames: list[tuple[str, int, int, list[dict]]] = []

    for video_path in chosen:
        print(f"\n[{video_path.name}] running detector (every {EVERY_N_FRAMES} frames)...")
        top = top_frames_for_video(video_path, args.top_n)
        if not top:
            print("  no confident detections, skipping video")
            continue
        print(f"  {len(top)} frames selected (top by confidence)")

        stem = video_path.stem
        for frame_idx, raw_detections in top:
            frame_path = extract_and_save(video_path, frame_idx, stem)
            if frame_path is None:
                print(f"  WARN: failed to extract frame {frame_idx}")
                continue
            confident = [d for d in raw_detections if d["confidence"] >= MIN_CONFIDENCE]
            mapped = map_detections(confident)
            h, w = cv2.imread(str(frame_path)).shape[:2]
            coco_frames.append((frame_path.name, w, h, mapped))
            save_train_pool_record(frame_path.name, mapped, video_path.name)
            print(f"    frame={frame_idx:>6}  {len(mapped)} mapped boxes  -> {frame_path.name}")

    if not coco_frames:
        print("\nNo frames collected across all videos, nothing to push.")
        return

    print(f"\nTotal frames collected: {len(coco_frames)}")
    print(f"Raw (unreviewed) records saved to {LABELS_DIR}")

    coco = build_coco_multi(coco_frames)
    coco_shifted = shift_category_ids(coco, CVAT_CATEGORY_ID_OFFSET)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", prefix="cvat_auto_", delete=False) as tf:
        json.dump(coco_shifted, tf)
        tmp_coco = Path(tf.name)

    from cvat_sdk import make_client

    frames = [FRAMES_DIR / fname for fname, *_ in coco_frames]
    try:
        with make_client(
            args.host,
            credentials=(os.environ["CVAT_USER"], os.environ["CVAT_PASSWORD"]),
        ) as client:
            task = push_task(
                client=client,
                project_id=args.project_id,
                task_name=args.task_name,
                frames=frames,
                coco_path=tmp_coco,
            )
        print(f"\nTask created: id={task.id} name={task.name!r} frames={len(frames)}")
        print(f"Open: {args.host}/tasks/{task.id}")
        append_manifest(args.task_name, [v.name for v in chosen], len(frames), task.id)
    finally:
        tmp_coco.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
