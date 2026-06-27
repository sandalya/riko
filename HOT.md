---
project: drone-recon
updated: 2026-06-27
---
# HOT

## Now

Detector Service is next. Telegram bot is done (receives media → `data/input`).  
Goal: get `POST /detect` working on a test image end-to-end.

---

## Phase Status

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 0** | Folder structure + Detector `/detect` endpoint + git | 🟡 In progress |
| **Phase 1** | CLAUDE.md refined, CC configured | ✅ Done |
| **Phase 2** | MCP Server + 4 tools | ⬜ Pending |
| **Phase 3** | Claude Agent + report generation | ⬜ Pending |
| **Phase 4** | Web/Telegram output + GPS Level 1 + deploy | ⬜ Pending |

---

## Last Done

- `bot/client.py` — Telegram receiver, saves photo/video/doc to `data/input` with timestamps
- `detector/main.py` — FastAPI skeleton added
- CLAUDE.md and HOT.md updated with full architecture from SPEC

---

## Next

1. Install detector dependencies (`pip install ultralytics fastapi uvicorn`)
2. Add `detector/config.py` with `MODEL_PATH = "models/yolo11n.pt"`
3. Download `yolo11n.pt` into `detector/models/`
4. Implement `POST /detect` endpoint in `detector/main.py`
5. Test on a sample image from `data/input`

---

## Architecture Reminder (3 blocks)

```
[Input] → [Detector/FastAPI] → [MCP Server] → [Claude Agent] → [Report]
```

- Model swap: change only `detector/config.py → MODEL_PATH`
- Geolocation PoC: GPS timestamp correlation (Level 1)
- MCP tools: `detect_objects`, `analyze_video`, `parse_gps_log`, `correlate_detections_gps`

---

## Blockers

None.

## Open Questions

- Which drone FC provides GPS logs? (Betaflight / ArduPilot / other)
- Target detection classes for fine-tuned model?
- Final output: Telegram bot or web UI?
- Deploy: VPS or Beelink + tunnel?

## Active Branches

None.
