# COLD — незмінний контекст проекту

## Мета
Замінити ручний перегляд відео з дрону на AI агента: детекція → локалізація → звіт.

## Стек
- **Detector**: FastAPI + Ultralytics YOLO (Python 3.14, venv)
- **Bot**: python-telegram-bot v21
- **Agent**: Claude API (майбутнє)
- **MCP**: mcp SDK (майбутнє)

## Структура
```
drone-recon/
├── detector/main.py       — FastAPI сервіс детекції
├── detector/config.py     — MODEL_PATH (єдине місце для swap моделі)
├── detector/models/       — .pt файли
├── bot/client.py          — TG handlers
├── core/config.py         — BOT_TOKEN, DETECTOR_URL, paths
├── main.py                — точка входу бота
├── mcp/                   — MCP Server (Phase 2)
├── agent/                 — Claude Agent (Phase 3)
├── data/input/            — вхідні відео/фото (не в git)
├── data/output/           — JSON результати (не в git)
└── .env                   — BOT_TOKEN, ANTHROPIC_API_KEY, DETECTOR_URL
```

## Правила
- Model swap: тільки `detector/config.py`
- Геолокація PoC: GPS timestamp correlation (Level 1)
- Логи: append-only `logs/session.md`
- Коміти: `[block] short description`
