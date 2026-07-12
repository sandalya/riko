# Session Log — drone-recon

### [2026-07-06] Action: Active-learning loop Phase 0.2 — auto-labeler COCO exporter
- Why: `docs/drone-recon-active-learning-concept_v002.md` Phase 0.2 — convert open-vocab
  auto-labeler raw output (prompt-derived label + score + bbox) into valid COCO with
  taxonomy-mapped category IDs, so CVAT tasks can be pre-annotated (0.3).
- Result: `cv_toolkit/labeling/coco_export.py` — inverts existing
  `cv_toolkit/configs/grounding_dino.yaml` prompt lists (phrase → class name) instead of
  a redundant new mapping file; class name → frozen ID via `taxonomy.yaml`. Unmatched
  labels dropped + logged (not "unknown"). xyxy→xywh bbox conversion. CLI:
  `python -m cv_toolkit.labeling.coco_export --raw <raw.json> --output <coco.json>`.
  Added PyYAML to requirements.txt (was venv-only, undeclared). New 5-frame fixture
  `tests/fixtures/labeling/raw_detections_5frame.json` + `tests/test_coco_export.py`
  (6 tests: taxonomy frozen order, category ID mapping, bbox conversion, unmatched-label
  drop, empty-detections frame). 6/6 new + 25/25 existing (non-detector) tests green.
- Next: Phase 0.3 — `cv_toolkit/labeling/cvat_push.py` (cvat-sdk): create CVAT task,
  upload frames + this COCO file, verify pre-placed boxes show in browser.

### [2026-07-01 20:13] Action: Active-learning loop Phase 0.1 — CVAT self-hosted install
- Why: `docs/drone-recon-active-learning-concept_v002.md` Phase 0.1 — prove the review
  round-trip mechanics; CVAT is the review UI (no custom labeling UI, no Nuclio).
- Result: Docker installed via official apt repo (not curl script). CVAT (`cvat-ai/cvat`,
  develop branch) cloned into `infra/cvat-server/` (gitignored). `docker-compose.yml`
  locally slimmed to core-only: removed ClickHouse/Vector/Grafana analytics stack and
  their hard `depends_on` on `cvat_server` + all 7 workers, set `CVAT_ANALYTICS: 0`,
  remapped traefik port 8080→8081 (8080 taken by code-server). 14 containers up, no
  analytics containers. RAM after up: 5.6Gi used / 5.5Gi available of 11Gi — workable.
  Project `drone-recon` (id=1) created with the 6 frozen taxonomy labels in exact order
  (pidar, military_vehicle, vehicle, fpv_drone, artillery, structure) — verified via
  `GET /api/labels?project_id=1`, not just UI screenshot. Admin login (`sashok`) confirmed
  working via API.
- Next: Hard stop per doc — owner verifies in browser, then Phase 0.2 (auto-labeler →
  COCO exporter, `cv_toolkit/labeling/coco_export.py`).

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

### [2026-06-28 00:30] Action: Phase 2 — MCP Server
- Why: bridge between detector and future Claude Agent
- Result: mcp/server.py with 4 tools; import OK; detect_objects smoke test passed (person 0.776)
- Next: Phase 3 — Claude Agent (agent/main.py)

### [2026-06-28 00:45] Action: Phase 3 — Claude Agent
- Why: reasoning layer that calls detector tools and produces structured recon report
- Result: agent/main.py CLI + prompts/recon_analyst.md; anthropic 0.112.0 installed; smoke test OK
- Next: Phase 4 — GPS Level 1 + deploy (wire agent into bot, test with real GPX)

### [2026-06-28 01:00] Action: checkpoint
- Why: Phase 3 завершено + importlib фікс + dotenv auto-load
- Result: HOT/WARM/COLD оновлені; pipeline live: photo → person 77.6% → Threat Level Medium
- Next: Phase 4 — реальний GPX лог + wire agent в bot + deploy

### [2026-06-28 01:20] Action: wire Claude Agent into Telegram bot
- Why: replace raw JSON reply with structured recon report from Claude
- Result: bot/client.py — _run_agent() helper, asyncio.to_thread, fallback on error; core/config.py — ANTHROPIC_API_KEY + AGENT_PROMPT_PATH
- Next: live test bot with real photo; Phase 4 GPS + deploy

### [2026-06-28 02:00] Action: checkpoint
- Why: зафіксувати eval expansion + bot wiring + CLAUDE.md chkp docs
- Result: 18/18 tests green; HOT/WARM оновлені; агент в боті; GPS synthetic fixtures
- Next: live test bot в TG з реальним фото; Phase 4 GPS + deploy

### [2026-06-28 03:00] Action: checkpoint + push
- Why: зафіксувати eval expansion — COCO+video регресія, 28/28 тестів
- Result: HOT/WARM оновлені; 28 тестів green; пуш на remote
- Next: live test bot in TG; Phase 4 GPS + deploy

### [2026-06-28 03:30] Action: scraper/ module
- Why: automated TG channel scraping pipeline for drone recon footage collection
- Result: 6 files (config, client, downloader, filter, haiku_filter, main); all imports OK; telethon+imagehash installed
- Next: user adds TG_API_ID + TG_API_HASH to .env; test with --no-haiku on real channel

### [2026-06-28 04:00] Action: checkpoint + push
- Why: зафіксувати scraper module + duration fix перед тестом на реальних даних
- Result: HOT/WARM оновлені; scraper ready; duration=0 пропускається
- Next: додати TG_API_ID/TG_API_HASH в .env; запустити scraper; live test bot

### [2026-06-28 16:56–19:56] Action: eval suite expansion — COCO + video regression
- Why: покрити детектор регресійними тестами на реальних фікстурах, не тільки smoke-тестами
- Result: 6 COCO val2017 parametrized тестів + 3 video parametrized тести (golden baselines завантажені); 28/28 тестів green
- Next: scraper module для збору відео з TG-каналів

### [2026-06-28 20:30–21:13] Action: scraper/ — TG video scraper, 5-stage filter pipeline
- Why: автоматизований збір дрон-відео з TG-каналів для датасету
- Result: config/client/downloader/filter/haiku_filter/main (6 файлів); фікс duration=0 (TG часто не віддає тривалість) → allow unknown; scraper готовий, не тестований на реальних даних
- Next: taxonomy + frame extraction

### [2026-06-28 21:35–21:46] Action: cv_toolkit — taxonomy v0 + frame_extractor
- Why: зафіксувати номенклатуру класів і почати вирізати кадри з відео під лейблення
- Result: taxonomy v0 locked (6 класів, ID 0-5 frozen); frame_extractor.py (interval + scene-change modes); 916 кадрів з 6 FPV відео
- Next: custom labeling UI (backlog) або готове рішення (CVAT)

### [2026-06-30 23:34–23:52] Action: workspace Pi5→Beelink SER5 migration audit
- Why: аудит SPEC_v001.md під час міграції воркспейсу — перевірити, чи Pi5-референси це застаріла інфра чи навмисний архітектурний вибір
- Result: Pi5-референси в SPEC — це design intent для edge-інференсу (окремо від dev-server), залишено без змін; .gitignore розширено (виключено великі data-асети: scraper videos, raw frames, model weights)
- Next: English thinking language migration

### [2026-07-01 00:23] Action: English thinking language migration
- Why: розділити мову міркування (English, дешевші токени) і мову відповіді користувачу (українська)
- Result: PROMPT.md перекладено, CLAUDE.md Rule 1 оновлено з явним принципом
- Next: model update claude-sonnet-4-6 → claude-sonnet-5

### [2026-07-01 12:35] Action: model update to claude-sonnet-5
- Why: перейти на актуальну модель у agent/main.py та bot/client.py
- Result: обидва файли оновлені на claude-sonnet-5
- Next: Phase 0.1 — CVAT self-hosted install

### [2026-07-01 23:15–23:25] Action: Phase 0.1 — CVAT self-hosted install
- Why: потрібен labeling seam для active-learning loop (auto-label → human review → retrain)
- Result: CVAT встановлено (docker, core-only — без ClickHouse/Vector/Grafana), порт 8081, проєкт drone-recon з 6 замороженими taxonomy-лейблами, перевірено через REST API
- Next: Phase 0.2 — auto-labeler → COCO exporter

### [2026-07-06 20:26] Action: Phase 0.2 — cv_toolkit/labeling/coco_export.py
- Why: конвертувати сирий вивід auto-labeler'а (prompt-derived label + confidence + bbox) у taxonomy-mapped COCO JSON
- Result: інвертує cv_toolkit/configs/grounding_dino.yaml (phrase → class name) замість окремого mapping-файлу; unmatched labels dropped+logged; xyxy→xywh конверсія; 5-frame фікстура + 6 unit-тестів; PyYAML додано в requirements.txt; 25/25 non-detector тестів green
- Next: Phase 0.3+0.4 — CVAT push/pull

### [2026-07-06 22:04–22:05] Action: Phase 0.3+0.4 — cvat_push.py + cvat_pull.py; security fix .env
- Why: замкнути labeling seam end-to-end (push кадрів+анотацій у CVAT, pull назад після ручної корекції)
- Result: cvat_push.py (створення task, upload frames+COCO через cvat-sdk) і cvat_pull.py (export у Ultralytics YOLO формат) готові; знайдено і виправлено баг — CVAT відхиляє category_id=0 → shift_category_ids() з +1 офсетом тільки на upload-шляху (taxonomy.yaml 0-5 не чіпали); повний round-trip smoke test на реальному TG-відео (task id=3) пройдений; окремо знайдено і виправлено security-issue — .env був закомічений у git з початку проєкту (2 коміти), untracked + доданий у .gitignore (commit c606300) до цього чекпоінту; git-історія все ще містить секрети (filter-repo cleanup відкладено як рішення власника)
- Next: Phase 1.1 — hand-label golden/val set (~100-150 кадрів), заморозити окремо від auto-labeled train pool

### [2026-07-12] Action: backfill session.md (retroactive) + requirements.txt reconciliation
- Why: session.md не оновлювався з 2026-06-28, хоча HOT.md/WARM.md і git log фіксували роботу до 2026-07-06 включно (порушення append-only логування з CLAUDE.md); requirements.txt мав лише 4 пакети (>=), хоча в коді реально імпортується ~18 third-party залежностей
- Result: записи вище відновлені з git log (реальні дати/повідомлення комітів, не вигадані); requirements.txt переписаний на основі grep імпортів по коду + `venv/bin/pip freeze` (точні версії з робочого venv)
- Next: розглянути незакомічену роботу (bot/client.py CVAT push flow з боту, cv_toolkit/pipeline/ingest_frame.py, data/labeling/) — перевірити тестами і зачекпоїнтити; Phase 1.1 залишається офіційним наступним кроком за SPEC

### [2026-07-12] Action: Phase 1.1 round 1 — golden set hand-labeling workflow (23 frames)
- Why: обкатати golden/val labeling workflow; на відміну від auto-labeled train pool, тут кадри відбирає власник вручну з відео (без auto-selector), щоб eval лишався незалежним від auto-labeling пайплайну
- Result: власник нарізав 23 кадри з відео вручну в `data/golden/raw/`; cvat_push.py розширено — `--coco` тепер опціональний (можна заливати кадри без анотацій для розмічання з нуля); створено CVAT task `golden-v0-round1` (id=4, host 192.168.72.191:8081) без попередніх боксів; власник розмітив вручну 2 класи (pidar, military_vehicle) в CVAT UI; cvat_pull.py витягнув анотації в `data/golden/labels/` — 23/23 кадри мають боксі (жодного порожнього), 36 боксів total (17 pidar + 19 military_vehicle)
- Next: продовжити нарощувати golden set (наступні раунди кадрів/класів), потім заморозити фінальний golden/val split і почати перший fine-tune цикл

### [2026-07-12] Action: active-learning loop end-to-end smoke test (Phase 0.3/0.4 seam, no code changes)
- Why: перевірити, що весь ланцюг ingest_frame.py (extract → detect → map → overlay → push → CVAT review → pull) реально працює на справжньому скрейпнутому відео, окремо від golden set, без зачіпання auto-labeler-у чи fine-tune
- Result: детектор (`venv/bin/uvicorn detector.main:app --port 8000`) впав одразу після старту при запуску через `&`+`disown` у bash-сесії — процес вбивався разом з sandbox-сесією; фікс — піднімати через Bash `run_in_background: true`, тоді стабільний. Сканування кадрів кількох approved-відео (04.05.2026 mix, 25.05.2026 орки, 422_24.05.26, 29.04.2026 вартові) кроком 8-10 кадрів показало: YOLO11n nano на COCO майже не бачить дрібні об'єкти з висоти дрона (пусті детекції або хибні класи типу bird/train/clock на HUD-оверлеях) — очікувано для PoC-моделі, підтверджує потребу в custom military-моделі з SPEC. Знайдено робочий кадр: 422_24.05.26.mp4 frame=256 (t=10.24s) → detector дав `bus` conf=0.83 → mapped на `vehicle` (id=2). Push у CVAT (task id=5, active_learning_test1) з pre-placed боксом vehicle навколо УАЗа. Власник спершу лишив клас як є, pull повернув `2 ...` (vehicle) — координати збіглися з auto-боксом; потім власник виправив клас на `military_vehicle` в CVAT UI (УАЗ — фактично military transport, не light tactical `vehicle` за taxonomy.yaml), повторний pull дав `1 ...` (military_vehicle), координати без змін — підтверджує коректний round-trip людської корекції класу (аналогічно до task id=3 smoke test з Phase 0.3/0.4)
- Next: seam підтверджено робочим end-to-end на реальних даних; наступний великий крок — custom military-модель або fine-tune цикл на основі golden set (23 кадри поки замало, потрібно нарощувати); `data/labeling/labels_test1/` і `active_learning_test1` (task id=5) — тестові артефакти, не частина golden чи production train pool
