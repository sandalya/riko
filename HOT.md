---
project: drone-recon
updated: 2026-07-12
---
# HOT

## Now
Fixed requirements.txt to track all ~18 direct third-party dependencies (reconciled against pip freeze); backfilled logs/session.md with 11 missing entries from git history (2026-06-28 onwards); committed previously uncommitted work (bot/client.py CVAT push flow, cv_toolkit/pipeline/ingest_frame.py CLI, data/labeling frames); set up direnv (.envrc) for shell integration; expanded .gitignore to exclude stray char-device entries.

## Last done
- Reconciled requirements.txt against actual imports and pip freeze exact versions (~18 direct deps now tracked)
- Backfilled logs/session.md with 11 missing entries pulled from git log since 2026-06-28
- Committed bot/client.py CVAT push flow: video handler ranks frames by confidence, sends top-8 as TG media group with inline push/skip keyboard, handle_cvat_callback pushes multi-frame COCO via cvat_sdk
- Committed cv_toolkit/pipeline/ingest_frame.py: single-frame CLI (extract → detect → map → overlay → push to CVAT)
- Committed data/labeling/ frames to repository
- Set up direnv (.envrc with dotenv_if_exists .env) for user's shell environment
- Excluded stray char-device untracked entries via .gitignore update

## Next
Phase 1.1: hand-label a frozen golden/val set (~100–150 frames spanning easy classes: vehicle, military_vehicle, structure) from scratch in CVAT—freeze into immutable `golden/` dir, never mixed into auto-labeled train pool.

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
- direnv now set up (.envrc); user can load .env into interactive shell without Claude reading it

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