---
project: drone-recon
updated: 2026-06-28
---
# HOT

## Now
Eval framework створено і всі 8 тестів зелені.
Next: Phase 2 — MCP Server (4 tools).

## Last done
- `tests/` — повний eval фреймворк:
  - `conftest.py` — фікстури detector_url, fixtures_dir, golden_dir
  - `fixtures/person_street.jpg` — реальне фото з людиною
  - `fixtures/empty_black.jpg` — 100×100 чорний кадр (PIL)
  - `golden/person_street.json` — baseline: min 1 detection, person ≥ 0.70
  - `test_detector_api.py` — 5 API тестів (health, schema, 404, 422, black)
  - `test_detector_quality.py` — 3 regression тести (confidence, golden, bbox)
- `CLAUDE.md` оновлено: секція `## Eval / Testing`
- Git commit: `633a7f4`

## How to resume
```bash
# Terminal 1 — detector
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/uvicorn detector.main:app --port 8000

# Terminal 2 — bot
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/python3 main.py

# Запустити тести
venv/bin/pytest tests/ -v
```

## Next
Phase 2 — MCP Server:
- `mcp/server.py` — 4 tools: `detect_objects`, `analyze_video`, `parse_gps_log`, `correlate_detections_gps`
- Підключити до Claude Agent (Phase 3)

## Phase Status

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 0** | Detector `/detect` + `/detect_video` endpoints | ✅ Done |
| **Phase 1** | CLAUDE.md, CC configured | ✅ Done |
| **Bot→Detector** | TG video/photo → JSON detections → TG reply | ✅ Live tested |
| **Eval** | pytest framework, 8 tests, golden baseline | ✅ Done |
| **Phase 2** | MCP Server + 4 tools | ⬜ Pending |
| **Phase 3** | Claude Agent + report generation | ⬜ Pending |
| **Phase 4** | GPS Level 1 + deploy | ⬜ Pending |

## Architecture

```
[TG Bot] ──► [Detector FastAPI :8000] ──► [JSON file] ──► [TG reply]
                      │
              (майбутнє: через MCP Server → Claude Agent → звіт)
```

## Blockers
None.

## Open Questions
- Drone FC для GPS логів? (Betaflight / ArduPilot / other)
- Target detection classes для fine-tuned моделі?
- Deploy: VPS чи Beelink + tunnel?
