---
project: drone-recon
updated: 2026-06-28
---
# HOT

## Done
scraper/ module — TG channel video scraper with 5-stage filter pipeline, all imports OK.

## Last done
- `scraper/config.py` — channels, priority, size/duration/quality thresholds, Haiku prompt, paths
- `scraper/client.py` — Telethon TelegramClient, `get_channel_videos()`
- `scraper/downloader.py` — `download_video()` via `message.download_media()`
- `scraper/filter.py` — `is_size_ok`, `is_duration_ok`, `is_quality_ok` (blur+brightness), `compute_phash`, `is_duplicate`
- `scraper/haiku_filter.py` — `classify_frame()` async, Claude Haiku vision, base64 middle frame, fallback "unsure"
- `scraper/main.py` — CLI, 5-stage pipeline, priority-sorted channels, stats summary
- Installed: telethon 1.44.0, imagehash 4.3.2
- Import verified: `from scraper.main import main` ✅
- Earlier: 28/28 eval tests green

## How to resume
```bash
# Terminal 1 — detector (required for detector/COCO/video tests + bot)
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/uvicorn detector.main:app --port 8000

# Terminal 2 — bot
venv/bin/python3 main.py

# CLI agent
venv/bin/python agent/main.py --image data/input/photo_20260627_234103.jpg

# Tests
venv/bin/pytest tests/ -v                          # 28 tests (detector on :8000)
venv/bin/pytest -m "not requires_detector" -v      # 12 tests, no detector needed
```

## Next
- Live test bot in TG: send real photo → verify Claude report arrives
- Phase 4: collect real GPX log from drone, test correlate end-to-end
- Deploy: VPS or Beelink + tunnel

## Notes
- `.env` must contain `ANTHROPIC_API_KEY`, `BOT_TOKEN`, `DETECTOR_URL`
- `mcp/` shadows PyPI `mcp` — always use importlib outside mcp/
- Bot fallback: Claude fails → plain summary, never crashes
- `requires_detector` marker: skip detector-dependent tests with `-m "not requires_detector"`

## Phase Status

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 0** | Detector `/detect` + `/detect_video` | ✅ Done |
| **Phase 1** | CLAUDE.md, CC configured | ✅ Done |
| **Bot→Detector** | TG video/photo → JSON → TG reply | ✅ Live tested |
| **Eval** | pytest 28 tests, COCO+video+GPS+agent | ✅ Done |
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
