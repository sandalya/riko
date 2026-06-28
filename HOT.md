---
project: drone-recon
updated: 2026-06-28
---
# HOT

## Done
Claude Agent wired into Telegram bot. Photo/video → detector → Claude → markdown recon report in TG.

## Last done
- `bot/client.py` — `_run_agent(detections, media_type)` helper: builds prompt → `asyncio.to_thread(_call_claude)` → returns markdown report
- `bot/client.py` — `handle_photo` / `handle_video`: send Claude report as reply_text + JSON as document attachment
- `bot/client.py` — fallback to raw summary if Claude fails (bot never crashes)
- `core/config.py` — added `ANTHROPIC_API_KEY`, `AGENT_PROMPT_PATH`
- Smoke test: imports + `_build_prompt` + `_system_prompt()` OK ✅

## How to resume
```bash
# Terminal 1 — detector (required)
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/uvicorn detector.main:app --port 8000

# Terminal 2 — bot
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/python3 main.py

# CLI agent (standalone)
venv/bin/python agent/main.py --image data/input/photo_20260627_234103.jpg

# Tests (detector must be on port 8000)
venv/bin/pytest tests/ -v
```

## Next
- Live test bot with real photo/video → verify Claude report arrives in TG
- Phase 4: collect real GPX log, test correlate_detections_gps end-to-end
- Deploy: VPS or Beelink + tunnel

## Notes
- `.env` must contain `ANTHROPIC_API_KEY`, `BOT_TOKEN`, `DETECTOR_URL`
- `mcp/` shadows PyPI `mcp` pkg — agent uses importlib, bot uses direct `_build_prompt` (no import needed)
- Bot falls back to plain summary if Claude API fails — never crashes
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
