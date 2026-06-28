# WARM — stable context

## Detector Service

```yaml
last_touched: 2026-06-28
status: done, live
port: 8000
model: yolo11n.pt (COCO, 80 classes)
```

Endpoints:
- `POST /detect` — `{image_path}` → `{detections: [{cls, confidence, bbox}]}`
- `POST /detect_video` — `{video_path, every_n_frames}` → `{fps, timeline: [{frame_time, detections}]}`

Start: `venv/bin/uvicorn detector.main:app --port 8000`
Model swap: only `detector/config.py → MODEL_PATH`

## Telegram Bot

```yaml
last_touched: 2026-06-27
status: done, live tested
```

- Receives photo/video → saves to `data/input/`
- Calls detector → saves JSON to `data/output/`
- Sends JSON file back to TG with summary
- Start: `venv/bin/python3 main.py` (from project root)

Config: `.env` → `BOT_TOKEN`, `DETECTOR_URL` (default: http://localhost:8000)

## MCP Server

```yaml
last_touched: 2026-06-28
status: done
```

Tools in `mcp/server.py` (imported directly, no subprocess):
- `detect_objects(image_path)` — calls POST /detect
- `analyze_video(video_path, every_n_frames=30)` — calls POST /detect_video
- `parse_gps_log(gps_path)` → `[{time, lat, lon, ele}]`
- `correlate_detections_gps(detections_json, gps_path, offset_seconds=0.0)` → `[{frame_time, lat, lon, detections}]`

Note: `mcp/` shadows PyPI `mcp` package. Agent loads server.py via `importlib.util.spec_from_file_location`.

## Claude Agent

```yaml
last_touched: 2026-06-28
status: done, live tested
model: claude-sonnet-4-6
```

```bash
# .env is loaded automatically via load_dotenv()
venv/bin/python agent/main.py --image <path>
venv/bin/python agent/main.py --video <path> [--gps <path>] [--every-n-frames 30] [--offset 0.0]
```

System prompt: `agent/prompts/recon_analyst.md`
Output: markdown table (Object / Confidence / BBox / Frame+Time / GPS Coords / Threat Level) + Summary

Live test result: `photo_20260627_234103.jpg` → person 77.6% → Threat Level: Medium ✅

## Eval Framework

```yaml
last_touched: 2026-06-28
status: done, 8/8 green
```

```bash
venv/bin/pytest tests/ -v          # all tests (detector must be on port 8000)
```

Fixtures: `tests/fixtures/person_street.jpg`, `empty_black.jpg`
Golden: `tests/golden/person_street.json` — person >= 0.70
