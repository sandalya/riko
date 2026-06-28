---
project: drone-recon
updated: 2026-06-28
---
# HOT

## Done
Taxonomy v0 locked (6 classes). cv_toolkit/ folder structure created.

## Last done
- `taxonomy.yaml` — v0.1, 6 класів, class IDs locked (не переставляти!)
- `cv_toolkit/eval/MODEL_REGISTRY.md` — таблиця моделей, baseline: yolo11n-coco
- `cv_toolkit/configs/grounding_dino.yaml` — text prompts для авто-розмітки
- `cv_toolkit/configs/train.yaml` — placeholder для першого fine-tune
- `cv_toolkit/` папки: pipeline/, eval/, golden_test/, datasets/{raw_frames,review_queue,verified}/
- Раніше: scraper/ module, 28/28 eval tests green

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
- **Phase 0.2 — golden test set**: зібрати ~50 кадрів per class із scraper output, авто-розмітка Grounding DINO
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
