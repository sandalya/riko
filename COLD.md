# COLD — immutable project context

## Goal
Replace manual drone video review with an AI agent: detection → localization → report.

## Stack
- **Detector**: FastAPI + Ultralytics YOLO (Python 3.14, venv)
- **Bot**: python-telegram-bot v21
- **Agent**: Claude API (future)
- **MCP**: mcp SDK (future)

## Structure
```
drone-recon/
├── detector/main.py       — FastAPI detection service
├── detector/config.py     — MODEL_PATH (only place for model swap)
├── detector/models/       — .pt model files
├── bot/client.py          — TG handlers
├── core/config.py         — BOT_TOKEN, DETECTOR_URL, paths
├── main.py                — bot entry point
├── mcp/                   — MCP Server (Phase 2)
├── agent/                 — Claude Agent (Phase 3)
├── tests/                 — pytest eval framework
├── data/input/            — raw video/photos (not in git)
├── data/output/           — JSON results (not in git)
└── .env                   — BOT_TOKEN, ANTHROPIC_API_KEY, DETECTOR_URL
```

## Rules
- Model swap: only `detector/config.py` → `MODEL_PATH`
- Geolocation PoC: GPS timestamp correlation (Level 1)
- Logs: append-only `logs/session.md`
- Commits: `[block] short description`
- Tests: run `venv/bin/pytest tests/ -v` after every model swap or detector change
