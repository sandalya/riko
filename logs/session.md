# Session Log

## 2026-06-27 — Project Initialization

- Project structure created: `detector/`, `mcp/`, `agent/`, `data/`, `tests/`, `logs/`
- Initial config defined in `detector/config.py`
- First git commit: `[init] project structure`

## 2026-06-27 — Detector API

- Created `detector/main.py`: FastAPI app with lifespan model loading (YOLO via ultralytics)
- `POST /detect` — accepts `image_path`, returns `{cls, confidence, bbox}` per object
- `POST /detect_video` — accepts `video_path` + `every_n_frames` (default 30), returns timeline `[{frame_time, detections}]`
- Model loaded once at startup from `MODEL_PATH` in `config.py`; error raised if file missing
- Commit: `[detector] add main.py`
