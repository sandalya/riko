---
project: drone-recon
updated: 2026-07-06
---
# HOT

## Now
Completed Phase 0.3 + 0.4: built cvat_push.py (creates CVAT task, uploads frames + COCO via cvat-sdk) and cvat_pull.py (exports task annotations as Ultralytics YOLO format). Fixed critical bug: CVAT rejects category_id=0, added shift_category_ids() offset (+1) only on upload path. Ran full round-trip smoke test with real TG video, confirmed annotations round-trip correctly. Also discovered and fixed security issue: .env was committed to git, now gitignored (commit c606300).

## Last done
- Implemented cvat_push.py: task creation, frame upload, COCO import with category_id offset fix
- Implemented cvat_pull.py: task export, COCO parsing, Ultralytics YOLO dataset format generation
- Fixed CVAT COCO importer bug: category_id=0 rejection → shift_category_ids() with +1 offset (upload path only)
- End-to-end smoke test: downloaded real TG video, extracted frame 69, pushed hand-annotated box to CVAT (task id=3), owner corrected in UI, pulled back and verified coordinates changed
- Discovered .env committed to git since project start (2 commits), added to .gitignore (commit c606300)
- Added cvat-sdk to requirements.txt
- Verified 27/27 non-detector tests green (8 new: test_coco_export.py + test_cvat_pull.py with real CVAT export zip fixture)
- Phase 0 (end-to-end labeling pipeline seam) now complete

## Next
Phase 1.1: hand-label a frozen golden/val set (~100–150 frames spanning easy classes: vehicle, military_vehicle, structure) from scratch in CVAT—this is the one place auto-labeling is forbidden. Freeze into immutable `golden/` dir, never mixed into train pool.

## Blockers
None.

## Open questions
- Drone FC for GPS logs? (Betaflight / ArduPilot / other)
- Target detection classes for fine-tuned model?
- Deploy: VPS or Beelink + tunnel?

## Reminders
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

## How to resume
```bash
# Terminal 1 — detector
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/uvicorn detector.main:app --port 8000

# Terminal 2 — bot
venv/bin/python3 main.py

# Frame extraction (if needed)
venv/bin/python cv_toolkit/frame_extractor.py --input <video_path> --output <frames_dir>

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