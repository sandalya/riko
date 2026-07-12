"""Extract a single frame from a video, run detector, preview bboxes, push to CVAT.

Workflow:
  1. Extract exact frame N from video
  2. Run detector (optional — graceful if offline)
  3. Draw bbox overlay → save preview image
  4. Print detection table (pixel + percentage coords)
  5. Prompt: push frame + pre-annotations to CVAT? [y/n]

YOLO→taxonomy mapping (best-effort; Sasha corrects in CVAT):
  person                       → pidar (0)
  car / truck / bus / van      → vehicle (2)
  motorcycle / bicycle         → vehicle (2)
  Everything else is dropped — military_vehicle / artillery / structure
  must be drawn from scratch in CVAT.

Usage:
  python -m cv_toolkit.pipeline.ingest_frame \\
      --video data/input/flight.mp4 \\
      --frame 150 \\
      --task golden_cycle1

  # preview only, no CVAT push:
  python -m cv_toolkit.pipeline.ingest_frame --video ... --frame 150 --no-push

  # skip detector entirely, push empty frame for manual labeling:
  python -m cv_toolkit.pipeline.ingest_frame --video ... --frame 150 --no-detect
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from dotenv import load_dotenv

# ── project root ──────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from cv_toolkit.labeling.cvat_push import push_task, CVAT_CATEGORY_ID_OFFSET, DEFAULT_HOST, DEFAULT_PROJECT_ID
from cv_toolkit.labeling.coco_export import shift_category_ids

# ── constants ─────────────────────────────────────────────────────────────────
DETECTOR_URL = "http://127.0.0.1:8000/detect"

TAXONOMY = {
    0: "pidar",
    1: "military_vehicle",
    2: "vehicle",
    3: "fpv_drone",
    4: "artillery",
    5: "structure",
}

# YOLO COCO label → taxonomy id  (best-effort; incomplete is fine)
YOLO_TO_TAXONOMY: dict[str, int] = {
    "person":     0,  # pidar
    "car":        2,  # vehicle
    "truck":      2,
    "bus":        2,
    "van":        2,
    "motorcycle": 2,
    "bicycle":    2,
}

# BGR colors per taxonomy class for overlay
CLASS_COLORS: dict[int, tuple[int, int, int]] = {
    0: (0, 200, 255),    # pidar       — orange-ish
    1: (0, 0, 220),      # mil_vehicle — red
    2: (50, 220, 50),    # vehicle     — green
    3: (255, 180, 0),    # fpv_drone   — cyan-ish
    4: (0, 100, 255),    # artillery   — deep orange
    5: (200, 0, 200),    # structure   — purple
}
DEFAULT_COLOR = (180, 180, 180)

FRAMES_DIR = _ROOT / "data" / "labeling" / "frames"
PREVIEWS_DIR = _ROOT / "data" / "labeling" / "previews"
COCO_DIR = _ROOT / "data" / "labeling" / "coco"


# ── frame extraction ──────────────────────────────────────────────────────────

def extract_frame(video_path: Path, frame_idx: int) -> tuple[np.ndarray, float, float]:
    """Return (frame_bgr, fps, timestamp_sec). Raises on error."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_idx < 0 or frame_idx >= total:
        cap.release()
        raise ValueError(f"Frame {frame_idx} out of range [0, {total - 1}]")

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise RuntimeError(f"Failed to read frame {frame_idx}")

    return frame, fps, frame_idx / fps


# ── detector ──────────────────────────────────────────────────────────────────

def run_detector(image_path: Path) -> list[dict]:
    """POST to detector /detect. Returns list of {cls, confidence, bbox:[x1,y1,x2,y2]}.
    Returns [] if detector is offline (graceful degradation)."""
    payload = json.dumps({"image_path": str(image_path)}).encode()
    req = urllib.request.Request(
        DETECTOR_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("detections", [])
    except (urllib.error.URLError, OSError):
        return []


# ── mapping + overlay ─────────────────────────────────────────────────────────

def map_detections(raw_detections: list[dict]) -> list[dict]:
    """Filter + map YOLO COCO labels → taxonomy ids. Drops unmapped classes."""
    mapped = []
    for det in raw_detections:
        tax_id = YOLO_TO_TAXONOMY.get(det["cls"].lower())
        if tax_id is None:
            continue
        mapped.append({
            "taxonomy_id": tax_id,
            "label": TAXONOMY[tax_id],
            "yolo_cls": det["cls"],
            "confidence": det["confidence"],
            "bbox_xyxy": det["bbox"],  # [x1, y1, x2, y2] pixels
        })
    return mapped


def draw_overlay(frame: np.ndarray, detections: list[dict]) -> np.ndarray:
    vis = frame.copy()
    h, w = vis.shape[:2]
    for det in detections:
        x1, y1, x2, y2 = [int(v) for v in det["bbox_xyxy"]]
        color = CLASS_COLORS.get(det["taxonomy_id"], DEFAULT_COLOR)
        cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
        label = f"{det['label']} {det['confidence']:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(vis, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
        cv2.putText(vis, label, (x1 + 2, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)
    return vis


# ── COCO builder ──────────────────────────────────────────────────────────────

def build_coco_single(
    frame_name: str,
    width: int,
    height: int,
    detections: list[dict],
) -> dict:
    """Build minimal COCO JSON for a single frame."""
    categories = [{"id": tid, "name": name} for tid, name in TAXONOMY.items()]
    images = [{"id": 1, "file_name": frame_name, "width": width, "height": height}]
    annotations = []
    for ann_id, det in enumerate(detections, start=1):
        x1, y1, x2, y2 = det["bbox_xyxy"]
        bw, bh = x2 - x1, y2 - y1
        annotations.append({
            "id": ann_id,
            "image_id": 1,
            "category_id": det["taxonomy_id"],
            "bbox": [round(x1, 1), round(y1, 1), round(bw, 1), round(bh, 1)],
            "area": round(bw * bh, 1),
            "score": det["confidence"],
            "iscrowd": 0,
        })
    return {"images": images, "annotations": annotations, "categories": categories}


def build_coco_multi(
    frames: list[tuple[str, int, int, list[dict]]],
) -> dict:
    """Build COCO JSON for multiple frames.

    Args:
        frames: list of (file_name, width, height, detections)
    """
    categories = [{"id": tid, "name": name} for tid, name in TAXONOMY.items()]
    images = []
    annotations = []
    ann_id = 1
    for img_id, (fname, w, h, detections) in enumerate(frames, start=1):
        images.append({"id": img_id, "file_name": fname, "width": w, "height": h})
        for det in detections:
            x1, y1, x2, y2 = det["bbox_xyxy"]
            bw, bh = x2 - x1, y2 - y1
            annotations.append({
                "id": ann_id,
                "image_id": img_id,
                "category_id": det["taxonomy_id"],
                "bbox": [round(x1, 1), round(y1, 1), round(bw, 1), round(bh, 1)],
                "area": round(bw * bh, 1),
                "score": det["confidence"],
                "iscrowd": 0,
            })
            ann_id += 1
    return {"images": images, "annotations": annotations, "categories": categories}


# ── print helpers ─────────────────────────────────────────────────────────────

def print_table(detections: list[dict], width: int, height: int) -> None:
    if not detections:
        print("  (no detections mapped to taxonomy)")
        return
    header = f"  {'#':<3} {'label':<18} {'conf':<6} {'bbox % (x,y,w,h)'}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for i, det in enumerate(detections):
        x1, y1, x2, y2 = det["bbox_xyxy"]
        bw, bh = x2 - x1, y2 - y1
        pct = f"({x1/width*100:.1f}, {y1/height*100:.1f}, {bw/width*100:.1f}, {bh/height*100:.1f})"
        print(f"  {i:<3} {det['label']:<18} {det['confidence']:<6.2f} {pct}")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    load_dotenv(_ROOT / ".env")

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--frame", required=True, type=int, help="Frame index (0-based)")
    parser.add_argument("--task", default=None, help="CVAT task name (default: auto)")
    parser.add_argument("--project-id", type=int, default=DEFAULT_PROJECT_ID)
    parser.add_argument("--host", default=os.environ.get("CVAT_HOST", DEFAULT_HOST))
    parser.add_argument("--no-push", action="store_true", help="Preview only, skip CVAT push")
    parser.add_argument("--no-detect", action="store_true", help="Skip detector, push empty frame")
    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        print(f"ERROR: video not found: {video_path}", file=sys.stderr)
        sys.exit(1)

    # ── 1. extract frame ──
    print(f"\n[1/4] Extracting frame {args.frame} from {video_path.name} ...")
    frame, fps, ts = extract_frame(video_path, args.frame)
    h, w = frame.shape[:2]
    print(f"      {w}×{h} px  |  fps={fps:.1f}  |  t={ts:.2f}s  |  frame={args.frame}")

    stem = f"{video_path.stem}_f{args.frame:06d}"
    frame_path = FRAMES_DIR / f"{stem}.jpg"
    cv2.imwrite(str(frame_path), frame)
    print(f"      Saved: {frame_path}")

    # ── 2. detector ──
    detections: list[dict] = []
    if not args.no_detect:
        print(f"\n[2/4] Running detector ...")
        raw = run_detector(frame_path)
        if not raw:
            print("      Detector offline or no detections — continuing without pre-annotations")
        else:
            detections = map_detections(raw)
            dropped = len(raw) - len(detections)
            print(f"      {len(raw)} raw detections → {len(detections)} mapped  ({dropped} dropped, no taxonomy match)")
    else:
        print(f"\n[2/4] Detector skipped (--no-detect)")

    # ── 3. preview ──
    print(f"\n[3/4] Generating preview ...")
    preview = draw_overlay(frame, detections)
    preview_path = PREVIEWS_DIR / f"preview_{stem}.jpg"
    cv2.imwrite(str(preview_path), preview)
    print(f"      Saved: {preview_path}")
    print(f"\n  Detections:")
    print_table(detections, w, h)

    # ── 4. push ──
    if args.no_push:
        print(f"\n[4/4] --no-push: skipping CVAT upload.")
        print(f"\nDone.")
        return

    print(f"\n[4/4] Push to CVAT?")
    print(f"      Host:    {args.host}")
    task_name = args.task or f"ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"      Task:    {task_name}")
    print(f"      Frames:  1  |  Annotations: {len(detections)}")
    answer = input("      [y/n]: ").strip().lower()
    if answer != "y":
        print("      Skipped.")
        return

    coco = build_coco_single(frame_path.name, w, h, detections)
    coco_shifted = shift_category_ids(coco, CVAT_CATEGORY_ID_OFFSET)
    coco_path = COCO_DIR / f"{stem}.json"
    coco_path.write_text(json.dumps(coco_shifted, indent=2))

    from cvat_sdk import make_client
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", prefix="cvat_", delete=False) as tf:
        json.dump(coco_shifted, tf)
        tmp_coco = Path(tf.name)

    try:
        with make_client(
            args.host,
            credentials=(os.environ["CVAT_USER"], os.environ["CVAT_PASSWORD"]),
        ) as client:
            task = push_task(
                client=client,
                project_id=args.project_id,
                task_name=task_name,
                frames=[frame_path],
                coco_path=tmp_coco,
            )
        print(f"\n  ✓ Task created: id={task.id}  name={task.name!r}")
        print(f"  ✓ Open: {args.host}/tasks/{task.id}")
    finally:
        tmp_coco.unlink(missing_ok=True)

    print(f"\nDone.")


if __name__ == "__main__":
    main()
