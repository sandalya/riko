---
project: drone-recon
updated: 2026-06-28
---
# HOT

## Done
Eval suite: 28/28 green. COCO + video regression tests + golden baselines complete.

## Last done
- `[eval]` 6 COCO val2017 images → `tests/fixtures/images/` + golden JSONs in `tests/golden/coco_*.json`
- `[eval]` `tests/test_coco_fixtures.py` — 6 parametrized regression tests (cls, confidence ±0.05, bbox ±5px)
- `[eval]` `pytest.ini` — `requires_detector` marker registered
- `[eval]` 3 video clips (5s each, yt-dlp + ffmpeg via imageio-ffmpeg) → `tests/fixtures/videos/`
- `[eval]` golden video baselines → `tests/golden/video_*.json`
- `[eval]` `tests/test_video_fixtures.py` — 4 tests: golden exist + 3 parametrized (frames, cls, confidence ±0.05)
- Total: 28/28 tests ✅

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
