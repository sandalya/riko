---
project: drone-recon
updated: 2026-07-02
---
# HOT

## Now
Updated Claude model from claude-sonnet-4-6 to claude-sonnet-5 in agent/main.py and bot/client.py as part of workspace-wide model version sweep.

## Last done
- Updated Claude model ID in agent/main.py
- Updated Claude model ID in bot/client.py
- Verified both files now reference claude-sonnet-5

## Next
Continue with other projects.

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