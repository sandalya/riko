---
project: drone-recon
updated: 2026-06-27
---
# HOT

## Now
Bot wired to detector: video/photo → detector → JSON back to Telegram. Verified end-to-end.

## Last done
- Verified Phase 0: /detect returns real inference (bus 94%, 4 persons on test image)
- Added DETECTOR_URL + DATA_OUTPUT_DIR to core/config.py
- Rewrote bot/client.py: handle_video → /detect_video → sends JSON file back
- Rewrote bot/client.py: handle_photo → /detect → sends JSON file back
- Integration tested: bot→detector→JSON pipeline works
- Bot starts cleanly, all handlers connected

## Next
Live test: start bot + detector, send real video via Telegram, get JSON back.
Then: Phase 2 — MCP Server (detect_objects, analyze_video, parse_gps_log, correlate_detections_gps).

## Phase Status

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 0** | Folder structure + Detector `/detect` endpoint + git | ✅ Done |
| **Phase 1** | CLAUDE.md refined, CC configured | ✅ Done |
| **Bot→Detector** | video/photo in TG → JSON detections back | ✅ Done |
| **Phase 2** | MCP Server + 4 tools | ⬜ Pending |
| **Phase 3** | Claude Agent + report generation | ⬜ Pending |
| **Phase 4** | GPS Level 1 + deploy | ⬜ Pending |

## Architecture Reminder (3 blocks)

```
[Input] → [Detector/FastAPI] → [MCP Server] → [Claude Agent] → [Report]
                    ↑
              [Telegram Bot] (wired directly for basic CV output)
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

- Detector running on port 8000, uvicorn in background
- Bot requires `venv/bin/python3 main.py` from project root
- Both must run simultaneously for end-to-end to work
