---
project: drone-recon
updated: 2026-06-27
---
# HOT

## Now
Phase 0 complete: dependencies installed, yolo11n.pt downloaded, /detect endpoint live and tested on real photo.

## Last done
- Installed detector dependencies (ultralytics, fastapi, uvicorn)
- Downloaded yolo11n.pt model into detector/models/
- Implemented POST /detect endpoint in detector/main.py
- Tested endpoint on sample image from data/input — inference working

## Next
Phase 2: Build MCP Server with 4 tools (detect_objects, analyze_video, parse_gps_log, correlate_detections_gps).

## Phase Status

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 0** | Folder structure + Detector `/detect` endpoint + git | ✅ Done |
| **Phase 1** | CLAUDE.md refined, CC configured | ✅ Done |
| **Phase 2** | MCP Server + 4 tools | 🟡 In progress |
| **Phase 3** | Claude Agent + report generation | ⬜ Pending |
| **Phase 4** | Web/Telegram output + GPS Level 1 + deploy | ⬜ Pending |

## Architecture Reminder (3 blocks)

```
[Input] → [Detector/FastAPI] → [MCP Server] → [Claude Agent] → [Report]
```

- Model swap: change only `detector/config.py → MODEL_PATH`
- Geolocation PoC: GPS timestamp correlation (Level 1)
- MCP tools: `detect_objects`, `analyze_video`, `parse_gps_log`, `correlate_detections_gps`

## Blockers

None.

## Open Questions

- Which drone FC provides GPS logs? (Betaflight / ArduPilot / other)
- Target detection classes for fine-tuned model?
- Final output: Telegram bot or web UI?
- Deploy: VPS or Beelink + tunnel?

## Reminders

- Phase 0 unlocked Phase 2 (MCP server design) — detector inference stable
- Fine-tune on drone dataset later; COCO model ready for integration testing
- uvicorn running on port 8000 in background