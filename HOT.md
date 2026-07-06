---
project: drone-recon
updated: 2026-07-06
---
# HOT

## Now
Completed Phase 0.2: built cv_toolkit/labeling/coco_export.py to convert auto-labeler raw output (label + confidence + bbox) into taxonomy-mapped COCO JSON, inverting grounding_dino.yaml prompts for class mapping.

## Last done
- Implemented `coco_export.py` — inverts `cv_toolkit/configs/grounding_dino.yaml` prompt lists (phrase → class name) and maps via `taxonomy.yaml`
- Converts xyxy → xywh bbox format
- Drops unmatched labels with logging
- Added 5-frame fixture and 6 unit tests (all green)
- Updated requirements.txt with PyYAML
- Verified 25/25 existing non-detector tests still pass

## Next
Phase 0.3: CVAT ingestion bridge — `cv_toolkit/labeling/cvat_push.py` (cvat-sdk). Creates a task under project `drone-recon`, uploads frame images + the 0.2 COCO file. Exit: opening the task in browser shows pre-placed boxes on the correct frames.

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
venv/bin/pytest tests/ -v                       # 28 tests (detector on :8000)
venv/bin/pytest -m "not requires_detector" -v   # 12 tests, no detector needed

# CVAT labeling (Phase 0.1 ready)
CVAT_HOST=192.168.72.191 — access via http://192.168.72.191:8081
```

## Phase Status

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 0** | Detector `/detect` + `/detect_video` | ✅ Done |
| **Phase 1** | CLAUDE.md, CC configured | ✅ Done |
| **Bot→Detector** | TG video/photo → JSON → TG reply | ✅ Live tested |
| **Eval** | pytest 28 tests, COCO+video+GPS+agent | ✅ Done |
| **Phase 2** | MCP Server + 4 tools | ✅ Done |
| **Phase 3** | Claude Agent + bot wired | ✅ Done |
| **Phase 0.1** | CVAT self-hosted + taxonomy config | ✅ Done |
| **Phase 0.2** | Auto-labeler → COCO exporter | ✅ Done |
| **Phase 0.3** | CVAT ingestion bridge (cvat_push.py) | 🔄 Next |
| **Phase 4** | GPS Level 1 + deploy | ⬜ Pending |