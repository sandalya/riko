# Session Log — drone-recon

### [2026-06-27 23:50] Action: Full checkpoint after live test
- Why: Зафіксувати перший успішний end-to-end тест
- Result: HOT/WARM/COLD оновлено, пам'ять записана
- Next: Відео тест або Phase 2 MCP Server

### [2026-06-27 23:41] Action: Live test — TG photo → detector → JSON reply
- Why: Перевірити що весь ланцюг реально працює (не тільки в коді)
- Result: person 77.6% bbox [409,122,584,517] — знайдено коректно. JSON повернено в TG.
- Next: Тест відео, потім Phase 2

### [2026-06-27 23:30] Action: Wire bot → detector
- Why: Ціль сесії — кинути фото/відео в TG, отримати JSON з bboxes
- Result: bot/client.py переписано, core/config.py розширено, integration test OK
- Next: Live test з реальним TG

### [2026-06-27 22:44] Action: Verify Phase 0
- Why: Не починати нову фазу без підтвердження попередньої
- Result: /detect повертає реальний inference (bus 94%, persons 88%). Порт 8000 живий.
- Next: Wire bot → detector

### [2026-06-28 00:00] Action: create eval framework
- Why: need regression coverage for detector API before adding new features
- Result: 8 tests, 8 passed — API contract (5) + quality regression (3)
- Next: wire into CI or pre-commit hook

### [2026-06-28 00:10] Action: checkpoint
- Why: зафіксувати стан після додавання eval framework
- Result: HOT/WARM оновлені, 8 тестів зелені, commit 633a7f4
- Next: Phase 2 — MCP Server (mcp/server.py, 4 tools)

### [2026-06-28 00:20] Action: checkpoint
- Why: explicit chkp — зафіксувати eval framework як завершений етап
- Result: HOT/WARM/COLD оновлені, COLD перекладено на English, всі 8 тестів green
- Next: Phase 2 — MCP Server: mcp/server.py with 4 tools
