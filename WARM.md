# WARM — стабільний контекст

## Detector Service

```yaml
last_touched: 2026-06-28
status: done, live
port: 8000
model: yolo11n.pt (COCO, 80 classes)
```

Endpoints:
- `POST /detect` — JSON `{image_path}` → `{detections: [{cls, confidence, bbox}]}`
- `POST /detect_video` — JSON `{video_path, every_n_frames}` → `{fps, timeline: [{frame_time, detections}]}`

Запуск: `venv/bin/uvicorn detector.main:app --port 8000`
Model swap: тільки `detector/config.py → MODEL_PATH`

## Telegram Bot

```yaml
last_touched: 2026-06-27
status: done, live tested
```

- Отримує фото/відео → зберігає в `data/input/`
- Викликає детектор → зберігає JSON в `data/output/`
- Відправляє JSON файл назад в TG з summary
- Запуск: `venv/bin/python3 main.py` (з кореня проекту)

Конфіг: `.env` → `BOT_TOKEN`, `DETECTOR_URL` (default: http://localhost:8000)

## Eval Framework

```yaml
last_touched: 2026-06-28
status: done, 8/8 green
```

```bash
venv/bin/pytest tests/ -v                        # всі тести
pytest tests/test_detector_api.py -v             # API контракт
pytest tests/test_detector_quality.py -v         # якість / regression
```

- `tests/fixtures/person_street.jpg` — реальне фото з людиною (77.6% confidence)
- `tests/fixtures/empty_black.jpg` — 100×100 чорний кадр
- `tests/golden/person_street.json` — baseline regression
- Залежності: `venv/bin/pip install pytest httpx Pillow`
- Детектор має бути запущений на порту 8000 перед тестами

## Live Test Result (2026-06-27)

Фото з людиною у формі → `person` 77.6%, bbox `[409, 122, 584, 517]` (центр кадру).
Поточна модель: тільки COCO класи. `person` — так, `soldier`/`weapon` — ні (потрібен fine-tune).
