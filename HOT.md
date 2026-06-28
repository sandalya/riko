---
project: drone-recon
updated: 2026-06-28
---
# HOT

## Done
Eval suite expanded to 18/18 green. Agent wired into bot. chkp documented in CLAUDE.md.

## Last done
- `[bot]` `bot/client.py` — Claude agent wired: photo/video → _run_agent() → markdown report in TG + JSON attachment
- `[bot]` `core/config.py` — ANTHROPIC_API_KEY, AGENT_PROMPT_PATH added
- `[eval]` `tests/test_agent.py` — 5 tests: prompt builder, system prompt, mock Claude call
- `[eval]` `tests/test_gps_correlation.py` — 5 tests: parse_gps_log, missing file, correlate basic/nearest/offset
- `[eval]` `tests/fixtures/sample.gpx` — 10 synthetic trackpoints, 1s apart, lat 48.0000→48.0009
- `[eval]` `tests/fixtures/sample_video_detections.json` — 3 frames (person, truck, empty)
- `[eval]` `tests/conftest.py` — mcp_server session fixture (importlib), sys.path fix
- `[meta]` `CLAUDE.md` — chkp section added after Git Discipline
- Total: 18/18 tests green ✅

## How to resume
```bash
# Terminal 1 — detector (required for detector tests + bot)
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/uvicorn detector.main:app --port 8000

# Terminal 2 — bot
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/python3 main.py

# CLI agent (standalone)
venv/bin/python agent/main.py --image data/input/photo_20260627_234103.jpg

# Full test suite (detector must be on port 8000)
venv/bin/pytest tests/ -v

# GPS-only tests (no detector needed)
venv/bin/pytest tests/test_agent.py tests/test_gps_correlation.py -v
```

## Next
- Live test bot in TG: send real photo → verify Claude report arrives
- Phase 4: collect real GPX log from drone, test correlate end-to-end
- Deploy: VPS or Beelink + tunnel

## Notes
- `.env` must contain `ANTHROPIC_API_KEY`, `BOT_TOKEN`, `DETECTOR_URL`
- `mcp/` shadows PyPI `mcp` — use importlib everywhere outside mcp/; never `from mcp.server import`
- Bot fallback: if Claude fails → plain summary sent, bot never crashes
- golden baseline: person >= 0.70 (`tests/golden/person_street.json`)

## Phase Status

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 0** | Detector `/detect` + `/detect_video` | ✅ Done |
| **Phase 1** | CLAUDE.md, CC configured | ✅ Done |
| **Bot→Detector** | TG video/photo → JSON → TG reply | ✅ Live tested |
| **Eval** | pytest 18 tests, agent+GPS+detector | ✅ Done |
| **Phase 2** | MCP Server + 4 tools | ✅ Done |
| **Phase 3** | Claude Agent + bot wired | ✅ Done |
| **Phase 4** | GPS Level 1 + deploy | ⬜ Pending |

## Architecture

```
[TG Bot] ──► [Detector FastAPI :8000]
                      │
              [mcp/server.py tools]
                      │
              [Claude Agent claude-sonnet-4-6]
                      │
              [Markdown recon report → TG reply]
```

## Open Questions
- Drone FC for GPS logs? (Betaflight / ArduPilot / other)
- Target detection classes for fine-tuned model?
- Deploy: VPS or Beelink + tunnel?
