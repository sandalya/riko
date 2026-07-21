

# WARM — stable context

## Detector Service

```yaml
last_touched: 2026-07-06
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
last_touched: 2026-07-06
status: done, agent wired
```

- Receives photo/video → detector → Claude agent → markdown report in TG + JSON attachment
- Fallback to plain summary if Claude fails (never crashes)
- Start: `venv/bin/python3 main.py` (from project root)

Config: `.env` → `BOT_TOKEN`, `DETECTOR_URL`, `ANTHROPIC_API_KEY`

## MCP Server

```yaml
last_touched: 2026-07-06
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
last_touched: 2026-07-06
status: done, model updated to claude-sonnet-5
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
last_touched: 2026-07-06
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
last_touched: 2026-07-06
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
last_touched: 2026-07-14
tags: [labeling, frame-extraction, preparation]
status: active — Phase 0.3 + 0.4 complete (cvat_push.py, cvat_pull.py, category_id offset fix, ingest_frame.py single-frame CLI); Phase 1.1 (auto-labeling pipeline, golden/train_pool split, batch provenance tracking) in progress
```

Framework for dataset curation and annotation:
- `frame_extractor.py` — extract frames from 6 FPV videos → 916 frames output
- **Phase 0.1 (DONE)**: CVAT self-hosted (docker, core-only, port 8081) + drone-recon project + 6 frozen taxonomy labels (verified via REST API)
- **Phase 0.2 (DONE)**: `cv_toolkit/labeling/coco_export.py` — auto-labeler raw output (prompt-derived label + score + bbox) → taxonomy-mapped COCO. Inverts `cv_toolkit/configs/grounding_dino.yaml` prompts instead of a separate mapping file. Unmatched labels dropped+logged. 6 unit tests on 5-frame fixture, all green.
- **Phase 0.3 + 0.4 (DONE)**: `cv_toolkit/labeling/cvat_push.py` (cvat-sdk) — creates CVAT task, uploads frames, imports COCO. Fixed critical bug: CVAT rejects category_id=0 → added shift_category_ids() with +1 offset (upload path only, taxonomy.yaml untouched). `cv_toolkit/labeling/cvat_pull.py` — exports task annotations as Ultralytics YOLO format, extracts per-frame labels. `cv_toolkit/labeling/ingest_frame.py` — single-frame CLI for active-learning integration: extract → detect → map → overlay → push. Full round-trip smoke test passed: real TG video (422_24.05.26.mp4 frame 256) → auto-detected bus conf 0.83 → CVAT (task id=5) → owner corrected class vehicle→military_vehicle in UI → cvat_pull.py verified updated annotation with unchanged coordinates.
- **Phase 1.1 (IN PROGRESS)**: Auto-labeling batch pipeline + golden/train_pool data split:
  - `cv_toolkit/pipeline/auto_ingest_batch.py` — batch script: runs detector across 5 random videos from `data/scraper/approved/`, ranks frames per video by confidence (same logic as bot/client.py video handler), takes top-8 frames/video, pushes as one CVAT task with pre-placed YOLO→taxonomy boxes. Auto-v0-round1 (task id=7, 40 frames): owner reviewed all frames in CVAT, corrected 1 frame, pulled 11/40 frames with boxes (6 pidar + 5 military_vehicle). Result: auto frame *selection* (confidence ranking) works better than raw box *quality* — most frames legitimately needed added boxes (military_vehicle class unknown to YOLO11n).
  - **Data architecture**: golden = anything human-reviewed regardless of origin (manual-from-scratch or auto-suggested-then-corrected); train_pool = raw unreviewed detector output, never auto-merged into golden.
  - **Golden dataset structure (2026-07-14)**: batch_001/ (23 frames, manual round 1), batch_002/ (72 frames, manual round 2), batch_003/ (11 labeled frames from auto-v0-round1) = 106 total frames, 214 boxes. Future batches: batch_004/, batch_005/, etc. Data/golden/labels/ stays flat (unique vlcsnap/video-stem filenames, no collisions) regardless of batch.
  - **data/golden/provenance.json**: source metadata (manual, auto_reviewed) + CVAT task id/name per batch. Provenance.json is source of truth for batch origin, not directory structure.
  - **data/train_pool/{raw,labels,manifest.json}**: unreviewed detector snapshots. Auto_ingest_batch.py persists raw per-frame detections (with confidence) there before CVAT push, so future runs get an unreviewed record independent of whether sent for review.
  - Continue growing golden set toward target (~100–150 frames total); once satisfied, freeze immutable golden/val dir, never mixed into train pool. Easy classes only: pidar/military_vehicle/structure (6-class taxonomy v0 locked).
- **Golden dataset (2026-07-13)**: Round 1 (batch_001, 23 frames) completed and hand-labeled in CVAT task id=4. Round 2 (batch_002, 72 frames) hand-labeled in CVAT task id=6. Combined golden set now 95 frames, 203 boxes total (112 pidar + 91 military_vehicle). Both batch outputs live flat in data/golden/labels/ (unique vlcsnap timestamp filenames, no collisions). Continue growing toward target (~100–150 frames total). Once satisfied, freeze immutable golden/val dir, never mixed into train pool. Easy classes only: pidar/military_vehicle/structure (6-class taxonomy v0 locked).
- Integration with Grounding DINO for auto-labeling pipeline itself (the actual model wrapper) still not built — deferred; Phase 0.2 only defines/consumes the raw-output contract
- Tests: 8 new (test_coco_export.py + test_cvat_pull.py with real CVAT export zip fixture); 27/27 non-detector tests green. cvat-sdk added to requirements.txt.
- YOLO11n (COCO nano) limitation identified: poor detection of small high-altitude drone objects; false positives observed (bird/train/clock on HUD). Confirms need for custom military-vehicle model fine-tune cycle on golden set.

CVAT infra (gitignored): `infra/cvat-server/` (vendored clone), `CVAT_HOST=192.168.72.191:8081` in `.env`

## Git push broker (chkp-pushd)

```yaml
last_touched: 2026-07-21
tags: [sandbox, git, broker, fallback]
status: active — systemd --user service enabled+running, fallback integration wired
```

Host-side systemd --user service providing git push broker for sandboxed agent when direct push is blocked.

**Files** (meta/chkp/):
- `chkp-pushd.py` — unix socket listener, validates allowlist + pinned URL + ff-only
- `chkp_push_client.py` — in-agent client, request_push(repo_id, ref) → POST to broker socket
- `chkp-pushd.config.json` — allowlist (drone-recon repo_id=0)
- systemd service file (installed locally, not in git)

**Integration**:
- `chkp.py git_commit_push()` now falls back to broker if direct push blocked
- `.claude/settings.json` added: `allowFileSystemAccess: [meta/chkp/, ...]` + `allowAllUnixSockets: true`

**Verified**:
- `chkp-pushd.py --test` passes
- In-session client.request_push(0, "main") succeeds
- Unknown repo_id allowlist rejection works

**Next**: Monitor in practice once sandbox.enabled flipped on with network isolation. Add trudovik repo_id to config when needed.
