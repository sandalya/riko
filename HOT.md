---
project: drone-recon
updated: 2026-06-28
---
# HOT

## Done
Phase 3 complete + import conflict fixed. Full pipeline live: photo → detector → Claude → structured report.

## Last done
- `agent/main.py` importlib fix: mcp/server.py loaded by explicit path → no more PyPI mcp shadowing
- `agent/main.py` dotenv: `load_dotenv()` added — .env loaded automatically, no manual export needed
- Live test: `photo_20260627_234103.jpg` → person 77.6% → report with Threat Level: Medium ✅
- Commits: `bdc44f9` (Phase 3), `e3490b3` (importlib fix)

## How to resume
```bash
# Terminal 1 — detector
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/uvicorn detector.main:app --port 8000

# Terminal 2 — bot
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/python3 main.py

# Agent — .env is loaded automatically (ANTHROPIC_API_KEY must be in .env)
venv/bin/python agent/main.py --image data/input/photo_20260627_234103.jpg
venv/bin/python agent/main.py --video <path> --gps data/gps/<file>.gpx --offset 0.0

# Tests (detector must be on port 8000)
venv/bin/pytest tests/ -v
```

## Next
Phase 4 — GPS Level 1 + deploy:
- Collect real GPX log from drone flight
- Test `correlate_detections_gps` end-to-end with real video + GPX
- Wire agent into Telegram bot (replace JSON reply with Claude report)
- Deploy: VPS or Beelink + tunnel

## Notes
- `.env` must contain `ANTHROPIC_API_KEY`, `BOT_TOKEN`, `DETECTOR_URL`
- `mcp/` shadows PyPI `mcp` pkg — solved in agent via importlib, in mcp/server.py via sys.path cleanup in `__main__`
- golden baseline: person >= 0.70 (`tests/golden/person_street.json`)

## Phase Status

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 0** | Detector `/detect` + `/detect_video` | ✅ Done |
| **Phase 1** | CLAUDE.md, CC configured | ✅ Done |
| **Bot→Detector** | TG video/photo → JSON → TG reply | ✅ Live tested |
| **Eval** | pytest, 8 tests, golden baseline | ✅ Done |
| **Phase 2** | MCP Server + 4 tools | ✅ Done |
| **Phase 3** | Claude Agent + report generation | ✅ Done |
| **Phase 4** | GPS Level 1 + deploy | ⬜ Pending |

## Architecture

```
[TG Bot] ──► [Detector FastAPI :8000]
                      │
              [mcp/server.py tools]
                      │
              [Claude Agent claude-sonnet-4-6]
                      │
              [Structured recon report]
```

## Open Questions
- Drone FC for GPS logs? (Betaflight / ArduPilot / other)
- Target detection classes for fine-tuned model?
- Deploy: VPS or Beelink + tunnel?
