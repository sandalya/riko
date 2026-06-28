"""Regression / quality tests for the detector service."""
import json
import httpx
import pytest


def _detect(detector_url: str, image_path: str) -> dict:
    r = httpx.post(
        f"{detector_url}/detect",
        json={"image_path": image_path},
        timeout=30,
    )
    assert r.status_code == 200, f"Unexpected status {r.status_code}: {r.text}"
    return r.json()


def test_person_street_confidence(detector_url, fixtures_dir):
    path = str((fixtures_dir / "person_street.jpg").resolve())
    body = _detect(detector_url, path)
    persons = [d for d in body["detections"] if d["cls"] == "person"]
    assert persons, "No 'person' detections found"
    assert any(p["confidence"] >= 0.70 for p in persons), (
        f"No person with confidence >= 0.70; got {[p['confidence'] for p in persons]}"
    )


def test_golden_baseline(detector_url, fixtures_dir, golden_dir):
    golden = json.loads((golden_dir / "person_street.json").read_text())
    path = str((fixtures_dir / "person_street.jpg").resolve())
    body = _detect(detector_url, path)
    detections = body["detections"]

    assert len(detections) >= golden["min_detections"], (
        f"Expected >= {golden['min_detections']} detections, got {len(detections)}"
    )
    for check in golden["checks"]:
        matching = [d for d in detections if d["cls"] == check["cls"]]
        assert matching, f"No detection with cls='{check['cls']}'"
        assert any(d["confidence"] >= check["min_confidence"] for d in matching), (
            f"No '{check['cls']}' with confidence >= {check['min_confidence']}; "
            f"got {[d['confidence'] for d in matching]}"
        )


def test_bbox_reasonable(detector_url, fixtures_dir):
    path = str((fixtures_dir / "person_street.jpg").resolve())
    body = _detect(detector_url, path)
    for det in body["detections"]:
        x1, y1, x2, y2 = det["bbox"]
        assert x1 >= 0, f"x1 negative: {x1}"
        assert y1 >= 0, f"y1 negative: {y1}"
        assert x1 < x2, f"x1 >= x2: {x1} >= {x2}"
        assert y1 < y2, f"y1 >= y2: {y1} >= {y2}"
