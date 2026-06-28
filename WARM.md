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
last_touched: 2026-06-28
status: done, agent wired
```

- Receives photo/video → detector → Claude agent → markdown report in TG + JSON attachment
- Fallback to plain summary if Claude fails (never crashes)
- Start: `venv/bin/python3 main.py` (from project root)

Config: `.env` → `BOT_TOKEN`, `DETECTOR_URL`, `ANTHROPIC_API_KEY`

## MCP Server

```yaml
last_touched: 2026-06-28
status: done
```

Tools in `mcp/server.py` (loaded via importlib, no subprocess):
- `detect_objects(image_path)` — POST /detect
- `analyze_video(video_path, every_n_frames=30)` — POST /detect_video
- `parse_gps_log(gps_path)` → `[{time, lat, lon, ele}]`
- `correlate_detections_gps(detections_json, gps_path, offset_seconds=0.0)` → `[{frame_time, lat, lon, detections}]`

Note: `mcp/` shadows PyPI `mcp`. Always load via `importlib.util.spec_from_file_location`.

## Claude Agent

```yaml
last_touched: 2026-06-28
status: done, live tested
model: claude-sonnet-4-6
```

```bash
venv/bin/python agent/main.py --image <path>
venv/bin/python agent/main.py --video <path> [--gps <path>] [--every-n-frames 30] [--offset 0.0]
```

System prompt: `agent/prompts/recon_analyst.md`
Output: markdown table (Object / Confidence / BBox / Frame+Time / GPS Coords / Threat Level) + Summary
Live test: `photo_20260627_234103.jpg` → person 77.6% → Threat Level: Medium ✅

## Eval Framework

```yaml
last_touched: 2026-06-28
status: done, 18/18 green
```

```bash
venv/bin/pytest tests/ -v                                          # all (detector on :8000)
venv/bin/pytest tests/test_agent.py tests/test_gps_correlation.py -v  # no detector needed
```

| File | Tests | Needs detector |
|------|-------|----------------|
| `test_detector_api.py` | 5 | yes |
| `test_detector_quality.py` | 3 | yes |
| `test_agent.py` | 5 | no (mock) |
| `test_gps_correlation.py` | 5 | no |

Fixtures: `person_street.jpg`, `empty_black.jpg`, `sample.gpx`, `sample_video_detections.json`
Golden: `tests/golden/person_street.json` — person >= 0.70
conftest: `mcp_server` fixture loads mcp/server.py via importlib; sys.path includes project root
