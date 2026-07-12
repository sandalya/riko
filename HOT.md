---
project: drone-recon
updated: 2026-07-13
---
# HOT

## Now
Reorganized golden round-1 raw frames into batch_001/ subdirectory (22 files, 100% rename detected by git); verified no code hardcodes the old path and committed the change to main.

## Last done
- Moved data/golden/raw/*.png → data/golden/raw/batch_001/
- Confirmed CVAT task stores server-side copies (no relinking needed)
- Verified cvat_pull.py uses Path(name).name (filename only, not full path)
- Staged as git renames and confirmed no history loss
- Committed (dc41804) and pushed to main

## Next
Continue growing the golden set beyond round 1 (currently 23 frames, 2 classes). Phase 1.1 (hand-label golden/val ~100–150 frames) is the active milestone; future batches will use batch_002, batch_003, etc. naming convention.

## Blockers
None.

## Open questions
- How many frames needed for golden set to train robust military-vehicle classifier?
- Target detection classes for fine-tuned model?
- Drone FC for GPS logs (Betaflight / ArduPilot / other)?
- Deploy: VPS or Beelink + tunnel?

## Reminders
- YOLO11n (COCO nano) struggles with small objects at drone altitude → confirms need for custom model
- Test artifacts (task id=5, data/labeling/labels_test1) are separate from golden/ and production train pool
- Golden batches follow naming: batch_001/, batch_002/, etc. under data/golden/raw/
- `.env` must contain `ANTHROPIC_API_KEY`, `BOT_TOKEN`, `DETECTOR_URL`, `TG_API_ID`, `TG_API_HASH`
- `mcp/` shadows PyPI `mcp` — always use importlib outside mcp/
- Bot fallback: Claude fails → plain summary, never crashes
- `requires_detector` marker: skip detector-dependent tests with `-m "not requires_detector"`
- cv_toolkit frame extraction complete: 916 frames ready for labeling
- SPEC_v001.md: Pi5 refs are design intent for edge inference, separate from dev-server workspace
- infra/cvat-server/ is gitignored (vendored CVAT clone)
- CVAT_HOST=192.168.72.191:8081 in infra .env
- Grounding DINO model wrapper deferred; Phase 0.2 only defines/consumes raw-output contract
- CVAT category_id offset: +1 only on cvat_push.py path; taxonomy.yaml and coco_export.py untouched
- direnv set up (.envrc); user can load .env into interactive shell

## How to resume
```bash
# Terminal 1 — detector
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/uvicorn detector.main:app --port 8000

# Terminal 2 — bot
venv/bin/python3 main.py

# Frame extraction (if needed)
venv/bin/python cv_toolkit/frame_extractor.py --input <video_path> --output <frames_dir>

# CVAT ingestion (Phase 0.3/0.4)
venv/bin/python cv_toolkit/labeling/ingest_frame.py --frame <path> --task-id <id>

# Tests
venv/bin/pytest tests/ -v                       # 27+ tests (detector on :8000)
venv/bin/pytest -m "not requires_detector" -v   # tests without detector dependency

# CVAT labeling (Phase 0 ready, Phase 1.1 next)
CVAT_HOST=192.168.72.191:8081 — access via http://192.168.72.191:8081
```

## Phase Status

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 0** | Detector `/detect` + `/detect_video` | ✅ Done |
| **Phase 1** | CLAUDE.md, CC configured | ✅ Done |
| **Bot→Detector** | TG video/photo → JSON → TG reply | ✅ Live tested |
| **Eval** | pytest 27+ tests, COCO+video+GPS+agent | ✅ Done |
| **Phase 2** | MCP Server + 4 tools | ✅ Done |
| **Phase 3** | Claude Agent + bot wired | ✅ Done |
| **Phase 0.1** | CVAT self-hosted + taxonomy config | ✅ Done |
| **Phase 0.2** | Auto-labeler → COCO exporter | ✅ Done |
| **Phase 0.3 + 0.4** | CVAT ingestion (cvat_push.py) + export (cvat_pull.py) | ✅ Done |
| **Phase 1.1** | Hand-label golden/val set (~100–150 frames) | 🔄 Next |
| **Phase 4** | GPS Level 1 + deploy | ⬜ Pending |