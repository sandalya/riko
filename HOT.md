---
project: drone-recon
updated: 2026-06-28
---
# HOT

## Done
Phase 2 — MCP Server done. mcp/server.py with 4 tools, import verified OK.

## Last done
- `mcp/server.py` — 4 tools: detect_objects, analyze_video, parse_gps_log, correlate_detections_gps
- `mcp/__init__.py` — empty package marker
- `mcp/requirements.txt` — fastmcp, httpx, gpxpy
- Installed: fastmcp 3.4.2, gpxpy 1.6.2
- Smoke tested: detect_objects returns person 0.776, parse_gps_log raises ValueError on missing file
- Import verified: `venv/bin/python -c "import mcp.server; print('OK')"` ✅

## How to resume
```bash
# Terminal 1 — detector
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/uvicorn detector.main:app --port 8000

# Terminal 2 — bot
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/python3 main.py

# Run MCP server (when needed by agent)
venv/bin/python mcp/server.py

# Run tests (detector must be on port 8000)
venv/bin/pytest tests/ -v
```

## Next
Phase 3 — Claude Agent (agent/main.py):
- System prompt: recon analyst role
- Call MCP tools: detect_objects → parse_gps_log → correlate_detections_gps
- Output: structured report with object table + threat levels

## Notes
- `pytest tests/ -v` requires detector on port 8000
- golden baseline: person >= 0.70 confidence (`tests/golden/person_street.json`)
- mcp/ directory shadows PyPI mcp package — fastmcp import is deferred to `__main__` block with sys.path fix

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
