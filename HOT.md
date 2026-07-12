---
project: drone-recon
updated: 2026-07-14
---
# HOT

## Now
Added auto-labeling batch pipeline (cv_toolkit/pipeline/auto_ingest_batch.py) that detects across 5 random approved videos, ranks frames by confidence, pushes top-8/video to CVAT (task auto-v0-round1, id=7, 40 frames), and owner reviewed/corrected all 40. Established golden vs train_pool split: golden = human-reviewed (manual or auto-corrected); train_pool = raw unreviewed detector output. Moved 40 reviewed auto-frames into data/golden/raw/batch_003/ and added data/golden/provenance.json tracking batch source + CVAT task metadata.

## Last done
- Created cv_toolkit/pipeline/auto_ingest_batch.py — batch detection on 5 random videos from data/scraper/approved/, confidence-ranked frame selection (top-8/video), CVAT task creation (auto-v0-round1, id=7)
- Owner reviewed all 40 frames in CVAT task id=7, corrected 1 frame, pulled annotations (11/40 frames with boxes, 6 pidar + 5 military_vehicle)
- Reorganized golden set structure: batch_001 (23), batch_002 (72), batch_003 (11 labeled frames from auto-round1) → 106 total frames, 214 boxes
- Added data/golden/provenance.json: source metadata (manual vs auto_reviewed) + CVAT task id/name per batch
- Scaffolded data/train_pool/{raw,labels,manifest.json} for unreviewed detector snapshots
- Wired auto_ingest_batch.py to persist raw per-frame detections in train_pool before CVAT push
- Data architecture: golden = anything reviewed; train_pool = never auto-merged into golden

## Next
Continue growing golden set (target ~100–150 frames total); decide when to freeze golden/val split; run more auto_ingest_batch.py rounds into train_pool and selectively promote reviewed subsets into golden.

## Blockers
None.

## Open questions
- How many frames needed for golden set to train robust military-vehicle classifier?
- Target detection classes for fine-tuned model?
- Drone FC for GPS logs (Betaflight / ArduPilot / other)?
- Deploy: VPS or Beelink + tunnel?

## Reminders
- YOLO11n (COCO nano) auto-labeling: only 5/40 frames initially had detector-mapped boxes, but manual review showed auto frame *selection* (confidence ranking) works better than raw box *quality* for this domain — most frames legitimately needed added boxes (military_vehicle class unknown to base model)
- YOLO11n struggles with small objects at drone altitude → confirms need for custom model fine-tune
- Data architecture: golden/labels/ stays flat (unique vlcsnap/video-stem filenames, no collisions); provenance.json is source of truth for batch origin, not directory structure
- Golden batches: batch_001/ (23 frames, manual), batch_002/ (72 frames, manual), batch_003/ (11 frames, auto-reviewed). Combined: 106 frames, 214 boxes
- Train_pool: raw unreviewed detector snapshots, independent of CVAT push status — future runs get an unreviewed record
- CVAT tasks: id=4 (round1 manual), id=6 (round2 manual), id=7 (auto-v0-round1, 40 frames reviewed)
- `.env` must contain `ANTHROPIC_API_KEY`, `BOT_TOKEN`, `DETECTOR_URL`, `TG_API_ID`, `TG_API_HASH`, `CVAT_HOST`
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

# Auto-labeling batch run
venv/bin/python cv_toolkit/pipeline/auto_ingest_batch.py --num-videos 5 --top-frames 8 --task-name auto-v0-round2

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
| **Phase 1.1** | Hand-label golden/val set + auto-labeling pipeline + data split | 🔄 In progress |
| **Phase 4** | GPS Level 1 + deploy | ⬜ Pending |