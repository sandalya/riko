from contextlib import asynccontextmanager
from pathlib import Path

import cv2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ultralytics import YOLO

from detector.config import (
    CONFIDENCE_THRESHOLD,
    DEVICE,
    IOU_THRESHOLD,
    IMAGE_SIZE,
    MODEL_PATH,
)

model: YOLO | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    model_path = Path(MODEL_PATH)
    if not model_path.exists():
        raise RuntimeError(f"Model not found: {model_path}")
    model = YOLO(str(model_path))
    model.to(DEVICE)
    yield
    model = None


app = FastAPI(title="Drone Recon Detector", lifespan=lifespan)


# --- Pydantic schemas ---

class DetectRequest(BaseModel):
    image_path: str


class Detection(BaseModel):
    cls: str
    confidence: float
    bbox: list[float]  # [x1, y1, x2, y2]


class DetectResponse(BaseModel):
    image_path: str
    detections: list[Detection]


class DetectVideoRequest(BaseModel):
    video_path: str
    every_n_frames: int = 30


class FrameDetections(BaseModel):
    frame_time: float  # seconds
    detections: list[Detection]


class DetectVideoResponse(BaseModel):
    video_path: str
    fps: float
    timeline: list[FrameDetections]


# --- Helpers ---

def _run_inference(image) -> list[Detection]:
    results = model.predict(
        source=image,
        conf=CONFIDENCE_THRESHOLD,
        iou=IOU_THRESHOLD,
        imgsz=IMAGE_SIZE,
        verbose=False,
    )
    detections: list[Detection] = []
    for result in results:
        names = result.names
        for box in result.boxes:
            detections.append(Detection(
                cls=names[int(box.cls)],
                confidence=round(float(box.conf), 4),
                bbox=[round(v, 2) for v in box.xyxy[0].tolist()],
            ))
    return detections


# --- Endpoints ---

@app.post("/detect", response_model=DetectResponse)
def detect(req: DetectRequest):
    path = Path(req.image_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {req.image_path}")
    if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}:
        raise HTTPException(status_code=422, detail="Unsupported image format")

    try:
        detections = _run_inference(str(path))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference error: {exc}") from exc

    return DetectResponse(image_path=req.image_path, detections=detections)


@app.post("/detect_video", response_model=DetectVideoResponse)
def detect_video(req: DetectVideoRequest):
    path = Path(req.video_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Video not found: {req.video_path}")
    if req.every_n_frames < 1:
        raise HTTPException(status_code=422, detail="every_n_frames must be >= 1")

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise HTTPException(status_code=422, detail="Cannot open video file")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    timeline: list[FrameDetections] = []
    frame_idx = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % req.every_n_frames == 0:
                try:
                    detections = _run_inference(frame)
                except Exception as exc:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Inference error at frame {frame_idx}: {exc}",
                    ) from exc
                timeline.append(FrameDetections(
                    frame_time=round(frame_idx / fps, 3),
                    detections=detections,
                ))
            frame_idx += 1
    finally:
        cap.release()

    return DetectVideoResponse(
        video_path=req.video_path,
        fps=round(fps, 2),
        timeline=timeline,
    )
