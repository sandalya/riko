"""Regression tests for COCO val2017 fixtures — verifies detector output stability.

Run with detector on port 8000:
    venv/bin/pytest tests/test_coco_fixtures.py -v

Skip without detector:
    venv/bin/pytest tests/ -m "not requires_detector"
"""
import json

import httpx
import pytest

COCO_NAMES = [
    "coco_person_01",
    "coco_truck_01",
    "coco_mixed_01",
    "coco_person_02",
    "coco_vehicle_01",
    "coco_empty_01",
]


@pytest.mark.requires_detector
@pytest.mark.parametrize("name", COCO_NAMES)
def test_coco_regression(detector_url, fixtures_dir, golden_dir, name):
    golden = json.loads((golden_dir / f"{name}.json").read_text())
    image_path = str((fixtures_dir / "images" / f"{name}.jpg").resolve())

    r = httpx.post(f"{detector_url}/detect", json={"image_path": image_path}, timeout=30)
    assert r.status_code == 200, f"Detector returned {r.status_code}: {r.text}"
    actual = r.json()

    g_dets = golden["detections"]
    a_dets = actual["detections"]

    assert len(a_dets) == len(g_dets), (
        f"{name}: expected {len(g_dets)} detections, got {len(a_dets)}\n"
        f"  golden classes: {[d['cls'] for d in g_dets]}\n"
        f"  actual classes: {[d['cls'] for d in a_dets]}"
    )

    for i, (g, a) in enumerate(zip(g_dets, a_dets)):
        assert a["cls"] == g["cls"], (
            f"{name}[{i}]: class mismatch — expected '{g['cls']}', got '{a['cls']}'"
        )
        assert abs(a["confidence"] - g["confidence"]) <= 0.05, (
            f"{name}[{i}] '{g['cls']}': confidence {a['confidence']:.4f} "
            f"differs from golden {g['confidence']:.4f} by more than 0.05"
        )
        for j, (ab, gb) in enumerate(zip(a["bbox"], g["bbox"])):
            assert abs(ab - gb) <= 5, (
                f"{name}[{i}] '{g['cls']}' bbox[{j}]: {ab:.2f} differs from golden {gb:.2f} by more than 5px"
            )
