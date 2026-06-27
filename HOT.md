---
project: drone-recon
updated: 2026-06-27
---
# HOT

## Now
Live test passed. Full pipeline working: TG photo → bot → /detect → JSON reply.
Next: відео тест або Phase 2 MCP Server.

## Last done
- Verified Phase 0: /detect inference real (bus 94%, 4 persons)
- Wired bot/client.py: photo → /detect → JSON file → TG reply
- Wired bot/client.py: video → /detect_video → JSON file → TG reply
- Live test: реальне фото з людиною → person 77.6% bbox [409,122,584,517] ✅
- Fixed .gitignore: data/, __pycache__, *.pyc excluded
- Git commits: 563b521, 031b743

## How to resume
```bash
# Terminal 1 — detector (може вже крутитись, перевір: ps aux | grep uvicorn)
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/uvicorn detector.main:app --port 8000

# Terminal 2 — bot
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/python3 main.py
```

## Next
Option A: Тест з відео (щоб побачити timeline + timings)
Option B: Phase 2 — MCP Server (detect_objects, analyze_video, parse_gps_log, correlate_detections_gps)

## Phase Status

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 0** | Detector `/detect` + `/detect_video` endpoints | ✅ Done |
| **Phase 1** | CLAUDE.md, CC configured | ✅ Done |
| **Bot→Detector** | TG video/photo → JSON detections → TG reply | ✅ Live tested |
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
