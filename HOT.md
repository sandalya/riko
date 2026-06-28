---
project: drone-recon
updated: 2026-06-28
---
# HOT

## Done
scraper/ module complete + duration filter fix. TG scraper pipeline ready to run with real credentials.

## Last done
- `scraper/` — 6 файлів: config, client, downloader, filter, haiku_filter, main
- `scraper/client.py` — load_dotenv з явним шляхом до .env (виправлено юзером)
- `scraper/filter.py` — `is_duration_ok(0) → True` (невідома тривалість з TG метаданих пропускається)
- Telethon 1.44.0, imagehash 4.3.2 встановлено
- Import verified ✅ | 28/28 eval tests green

## How to resume
```bash
# Terminal 1 — detector
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/uvicorn detector.main:app --port 8000

# Terminal 2 — bot
venv/bin/python3 main.py

# Scraper (потрібні TG_API_ID + TG_API_HASH в .env)
venv/bin/python scraper/main.py --channels escadrone --limit 50 --no-haiku

# Tests
venv/bin/pytest tests/ -v                       # 28 tests (detector on :8000)
venv/bin/pytest -m "not requires_detector" -v   # 12 tests, no detector needed
```

## Next
- Додати TG_API_ID + TG_API_HASH в .env і запустити scraper на реальному каналі
- Live test bot в TG: надіслати фото → отримати Claude report
- Phase 4: реальний GPX лог + deploy

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
