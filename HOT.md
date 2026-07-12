---
project: drone-recon
updated: 2026-07-12
---
# HOT

## Now
Ran active-learning loop end-to-end on real scraped video: extracted frame 256 from 422_24.05.26.mp4, auto-detected bus (conf 0.83) on a UAZ vehicle, pushed to CVAT (task id=5), owner corrected class to military_vehicle in UI, cvat_pull.py retrieved updated annotation with unchanged coordinates.

## Last done
- Executed ingest_frame.py: extract → detect → map → overlay → push pipeline
- Frame 256 from 422_24.05.26.mp4 (vehicle detection, YOLO confidence 0.83)
- CVAT task id=5 created and pushed with auto-labeled frame
- Owner hand-corrected class: vehicle → military_vehicle in CVAT UI
- cvat_pull.py verified pull: updated class, bbox coordinates preserved
- Confirmed round-trip data integrity (Phase 0.3 + 0.4 seamless)
- Identified YOLO11n limitation: poor detection of small high-altitude drone objects (false positives: bird/train/clock on HUD)

## Next
Custom military-model training or first fine-tune cycle on golden set (23 frames insufficient; need to grow); keep golden set and auto-labeled train pool separate.

## Blockers
None.

## Open questions
- Drone FC for GPS logs? (Betaflight / ArduPilot / other)
- Target detection classes for fine-tuned model?
- Deploy: VPS or Beelink + tunnel?
- How many frames needed for golden set to train robust military-vehicle classifier?

## Reminders
- YOLO11n (COCO nano) struggles with small objects at drone altitude → confirms need for custom model with SPEC
- Test artifacts (task id=5, data/labeling/labels_test1) are separate from golden/ and production train pool
- `.env` must contain `ANTHROPIC_API_KEY`, `BOT_TOKEN`, `DETECTOR_URL`, `TG_API_ID`, `TG_API_HASH`
- `mcp/` shadows PyPI `mcp` — always use importlib outside mcp/
- Bot fallback: Claude fails → plain summary, never crashes
- `requires_detector` marker: skip detector-dependent tests with `-m "not requires_detector"`
- cv_toolkit frame extraction complete: 916 frames ready for labeling
- SPEC_v001.md: Pi5 refs are design intent for edge inference, separate from dev-server workspace (Pi5→Beelink SER5)
- infra/cvat-server/ is gitignored (vendored CVAT clone)
- CVAT_HOST=192.168.72.191 in infra .env
- Grounding DINO model wrapper deferred (heavy GPU deps); Phase 0.2 only defines/consumes raw-output contract
- CVAT category_id offset: +1 only on cvat_push.py path; taxonomy.yaml (0-5) and coco_export.py untouched
- .env now properly gitignored; git history contains secrets (filter-repo cleanup deferred as owner's decision)
- direnv now set up (.envrc); user can load .env into interactive shell without Claude reading it
- Sandbox fix: uvicorn run via '&'+disown was dying with bash session; resolved with Bash run_in_background:true

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