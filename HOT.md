---
project: drone-recon
updated: 2026-06-28
---
# HOT

## Done
Phase 3 — Claude Agent done. agent/main.py CLI, build_report_prompt importable, smoke test OK.

## Last done
- `agent/main.py` — CLI agent: --image/--video, --gps, --every-n-frames, --offset
- `agent/__init__.py` — empty package marker
- `agent/prompts/recon_analyst.md` — system prompt: role, table format, threat levels
- Installed: anthropic 0.112.0
- Model: claude-sonnet-4-6
- Smoke test: `from agent.main import build_report_prompt` ✅
- Prompt output verified: correct markdown structure for image/video/GPS inputs

## How to resume
```bash
# Terminal 1 — detector
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/uvicorn detector.main:app --port 8000

# Terminal 2 — bot
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/python3 main.py

# Run agent (requires ANTHROPIC_API_KEY in .env or env)
venv/bin/python agent/main.py --image data/input/photo_20260627_234103.jpg
venv/bin/python agent/main.py --video <path> --gps data/gps/<file>.gpx

# Run tests (detector must be on port 8000)
venv/bin/pytest tests/ -v
```

## Next
Phase 4 — GPS Level 1 + deploy:
- Test full pipeline end-to-end with real GPX log
- Wire agent into Telegram bot (replace JSON reply with Claude report)
- Deploy: choose VPS or Beelink + tunnel

## Notes
- `pytest tests/ -v` requires detector on port 8000
- golden baseline: person >= 0.70 confidence (`tests/golden/person_street.json`)
- mcp/ directory shadows PyPI mcp package — fastmcp import deferred to `__main__` with sys.path fix
- agent uses direct mcp.server function imports (no subprocess), deferred inside pipeline runners

## Phase Status

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 0** | Detector `/detect` + `/detect_video` endpoints | ✅ Done |
| **Phase 1** | CLAUDE.md, CC configured | ✅ Done |
| **Bot→Detector** | TG video/photo → JSON detections → TG reply | ✅ Live tested |
| **Eval** | pytest framework, 8 tests, golden baseline | ✅ Done |
| **Phase 2** | MCP Server + 4 tools | ✅ Done |
| **Phase 3** | Claude Agent + report generation | ✅ Done |
| **Phase 4** | GPS Level 1 + deploy | ⬜ Pending |

## Architecture

```
[TG Bot] ──► [Detector FastAPI :8000] ──► [JSON file] ──► [TG reply]
                      │
              (future: via MCP Server → Claude Agent → report)
```

## Blockers
None.

## Open Questions
- Drone FC for GPS logs? (Betaflight / ArduPilot / other)
- Target detection classes for fine-tuned model?
- Deploy: VPS or Beelink + tunnel?
