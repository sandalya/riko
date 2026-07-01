---
project: drone-recon
updated: 2026-07-03
---
# HOT

## Now
Phase 0.1 complete: installed CVAT self-hosted (docker, core-only), configured project with 6 frozen taxonomy labels, verified via REST API. Ready for auto-labeling phase.

## Last done
- Installed CVAT self-hosted (docker, apt-repo) on port 8081, dropped ClickHouse/Vector/Grafana
- Created drone-recon project with 6 frozen taxonomy labels in exact order
- Verified labels via REST API (not just UI)
- Committed infra changes to repo (3f8a30b)
- RAM profile: 5.6Gi used / 5.5Gi available

## Next
Phase 0.2: Build auto-labeler → COCO exporter (cv_toolkit/labeling/coco_export.py), map taxonomy, unit test on ~5-frame fixture.

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
| **Phase 0.2** | Auto-labeler + COCO exporter | 🔄 In Progress |
| **Phase 4** | GPS Level 1 + deploy | ⬜ Pending |