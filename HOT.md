---
project: drone-recon
updated: 2026-06-27
---
# HOT

## Now
CLAUDE.md and HOT.md updated with full project context from SPEC.

## Last done
- CLAUDE.md created with complete project architecture and phase breakdown
- HOT.md updated with phase status table and full context
- Reviewed bot receiver (working), detector skeleton, and git+checkpoint setup

## Next
1. Install detector dependencies (`pip install ultralytics fastapi uvicorn`)
2. Add `detector/config.py` with `MODEL_PATH = "models/yolo11n.pt"`
3. Download `yolo11n.pt` into `detector/models/`
4. Implement `POST /detect` endpoint in `detector/main.py`
5. Test on a sample image from `data/input`

## Phase Status

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 0** | Folder structure + Detector `/detect` endpoint + git | 🟡 In progress |
| **Phase 1** | CLAUDE.md refined, CC configured | ✅ Done |
| **Phase 2** | MCP Server + 4 tools | ⬜ Pending |
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

- Detector inference is next critical milestone — install deps and test on real photo from `data/input`
- Phase 0 completion unblocks Phase 1 (MCP server design)
