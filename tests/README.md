# Detector Eval Framework

## Prerequisites

The detector service must be running on port 8000:

```bash
uvicorn detector.main:app --port 8000
```

Install test dependencies:

```bash
pip install -r tests/requirements.txt
```

## Running tests

```bash
# all tests
pytest tests/ -v

# API tests only
pytest tests/test_detector_api.py -v

# quality / regression tests only
pytest tests/test_detector_quality.py -v
```

## Structure

```
tests/
├── conftest.py                   # shared fixtures (detector_url, fixtures_dir, golden_dir)
├── fixtures/
│   ├── person_street.jpg         # real photo with a person (from data/input/)
│   └── empty_black.jpg           # 100x100 black frame (no detections expected)
├── golden/
│   └── person_street.json        # regression baseline: min detections + confidence checks
├── test_detector_api.py          # API contract tests
├── test_detector_quality.py      # detection quality / regression tests
└── requirements.txt
```

## Adding a new fixture

1. Drop the image into `tests/fixtures/`.
2. Run a detection manually and save the expected output to `tests/golden/<name>.json` with the schema:
   ```json
   {"min_detections": N, "checks": [{"cls": "...", "min_confidence": 0.XX}]}
   ```
3. Add a test in `test_detector_quality.py` that calls `test_golden_baseline` logic with your new golden file.
