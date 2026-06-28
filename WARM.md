

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
status: done, 28/28 green
```

```bash
venv/bin/pytest tests/ -v                        # 28 tests (detector on :8000)
venv/bin/pytest -m "not requires_detector" -v    # 12 tests, no detector needed
```

| File | Tests | Needs detector |
|------|-------|----------------|
| `test_detector_api.py` | 5 | yes |
| `test_detector_quality.py` | 3 | yes |
| `test_coco_fixtures.py` | 6 | yes (`requires_detector`) |
| `test_video_fixtures.py` | 4 | 3 yes + 1 no |
| `test_agent.py` | 5 | no (mock) |
| `test_gps_correlation.py` | 5 | no |

Fixtures:
- Images: `person_street.jpg`, `empty_black.jpg`, `tests/fixtures/images/coco_*.jpg` (6 COCO val2017)
- Videos: `tests/fixtures/videos/{people_walking,road_traffic,mixed_scene}.mp4` (5s each)
- GPS: `tests/fixtures/sample.gpx` (10 synthetic trackpoints)

Golden: `tests/golden/` — person_street, coco_* (6), video_* (3)
conftest: `mcp_server` fixture (importlib); `detector_url`, `fixtures_dir`, `golden_dir`; sys.path includes project root
pytest.ini: `requires_detector` marker registered

## Scraper

```yaml
last_touched: 2026-06-28
status: done, import verified, not yet run on real TG
```

```bash
# First run (interactive TG auth):
venv/bin/python scraper/main.py --channels escadrone --limit 50 --no-haiku

# With Haiku vision filter:
venv/bin/python scraper/main.py --channels escadrone DPSUkr --limit 100
```

Pipeline: metadata filter → download raw/ → quality (blur/brightness) → phash dedup → Haiku vision → approved/ | review/ | rejected/

Config: `scraper/config.py` — channels, thresholds, paths
`.env` needs: `TG_API_ID`, `TG_API_HASH`
Session: `data/scraper/tg_session` (created on first run, interactive)
Hashes: `data/scraper/hashes.json` (persists across runs)

Key fix: `is_duration_ok(0) → True` — TG metadata often returns duration=0 for unknown

## cv_toolkit

```yaml
last_touched: 2026-06-29
tags: [labeling, frame-extraction, preparation]
status: active
```

Framework for dataset curation and annotation:
- `frame_extractor.py` — extract frames from 6 FPV videos → 916 frames output
- Golden test set: manual labeling of 100–200 frames (Phase 0.2)
- Integration with Grounding DINO for auto-labeling pipeline
- Taxonomy v0 locked: 6 object classes
