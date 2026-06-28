---
project: drone-recon
updated: 2026-06-28
---
# HOT

## Done
Eval framework done — 8/8 tests green, CLAUDE.md updated, memory rules translated to English.

## Last done
- `tests/conftest.py` — fixtures: detector_url, fixtures_dir, golden_dir
- `tests/fixtures/person_street.jpg` — real photo with person
- `tests/fixtures/empty_black.jpg` — 100×100 black frame (PIL)
- `tests/golden/person_street.json` — baseline: min 1 detection, person >= 0.70
- `tests/test_detector_api.py` — 5 API tests (health, schema, 404, 422, black frame)
- `tests/test_detector_quality.py` — 3 regression tests (confidence, golden, bbox)
- `CLAUDE.md` — added `## Eval / Testing` section
- `COLD.md` — translated to English
- Git commits: `633a7f4`, `e4a9221`

## How to resume
```bash
# Terminal 1 — detector
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/uvicorn detector.main:app --port 8000

# Terminal 2 — bot
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/python3 main.py

# Run tests (detector must be on port 8000)
venv/bin/pytest tests/ -v
```

## Next
Phase 2 — MCP Server: mcp/server.py with 4 tools:
- `detect_objects`
- `analyze_video`
- `parse_gps_log`
- `correlate_detections_gps`

## Notes
- `pytest tests/ -v` requires detector on port 8000
- golden baseline: person >= 0.70 confidence (`tests/golden/person_street.json`)

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
              (future: via MCP Server → Claude Agent → report)
```

## Blockers
None.

## Open Questions
- Drone FC for GPS logs? (Betaflight / ArduPilot / other)
- Target detection classes for fine-tuned model?
- Deploy: VPS or Beelink + tunnel?
