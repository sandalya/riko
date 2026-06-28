---
project: drone-recon
updated: 2026-06-29
---
# HOT

## Now
Taxonomy v0 locked (6 classes), frame_extractor completed — 916 frames extracted from 6 FPV videos. cv_toolkit/ folder structure created per Opus roadmap.

## Last done
- Finalized taxonomy v0 with 6 object classes
- Implemented frame_extractor — processed 6 FPV videos → 916 frames output
- Set up cv_toolkit/ directory structure
- Scraper verified working with ed_session

## Next
Phase 0.2: golden test set — manually label 100–200 frames from extracted frames, then prepare for Grounding DINO auto-labeling pipeline.

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
| **Phase 0.2** | Golden test set (100–200 frames) | 🔄 In Progress |
| **Phase 4** | GPS Level 1 + deploy | ⬜ Pending |
