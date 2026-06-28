"""Regression tests for video fixtures — verifies detect_video output stability.

Run with detector on port 8000:
    venv/bin/pytest tests/test_video_fixtures.py -v

Skip detector tests:
    venv/bin/pytest tests/ -m "not requires_detector"
"""
import json
from pathlib import Path

import httpx
import pytest

VIDEO_NAMES = [
    "people_walking",
    "road_traffic",
    "mixed_scene",
]

GOLDEN_DIR = Path(__file__).parent / "golden"


def test_video_golden_files_exist():
    for name in VIDEO_NAMES:
        path = GOLDEN_DIR / f"video_{name}.json"
        assert path.exists(), f"Missing golden file: {path}"
        data = json.loads(path.read_text())
        assert "timeline" in data, f"{path.name}: missing 'timeline' key"


@pytest.mark.requires_detector
@pytest.mark.parametrize("name", VIDEO_NAMES)
def test_video_regression(detector_url, fixtures_dir, golden_dir, name):
    golden = json.loads((golden_dir / f"video_{name}.json").read_text())
    video_path = str((fixtures_dir / "videos" / f"{name}.mp4").resolve())

    r = httpx.post(
        f"{detector_url}/detect_video",
        json={"video_path": video_path, "every_n_frames": 15},
        timeout=120,
    )
    assert r.status_code == 200, f"Detector returned {r.status_code}: {r.text}"
    actual = r.json()

    g_timeline = golden["timeline"]
    a_timeline = actual["timeline"]

    assert len(a_timeline) == len(g_timeline), (
        f"{name}: expected {len(g_timeline)} frames, got {len(a_timeline)}"
    )

    for fi, (g_frame, a_frame) in enumerate(zip(g_timeline, a_timeline)):
        g_dets = g_frame["detections"]
        a_dets = a_frame["detections"]
        t = g_frame["frame_time"]

        assert len(a_dets) == len(g_dets), (
            f"{name} frame t={t}s: expected {len(g_dets)} detections, got {len(a_dets)}\n"
            f"  golden: {[d['cls'] for d in g_dets]}\n"
            f"  actual: {[d['cls'] for d in a_dets]}"
        )

        for i, (g, a) in enumerate(zip(g_dets, a_dets)):
            assert a["cls"] == g["cls"], (
                f"{name} frame t={t}s det[{i}]: class mismatch — "
                f"expected '{g['cls']}', got '{a['cls']}'"
            )
            assert abs(a["confidence"] - g["confidence"]) <= 0.05, (
                f"{name} frame t={t}s det[{i}] '{g['cls']}': "
                f"confidence {a['confidence']:.4f} differs from golden {g['confidence']:.4f} by more than 0.05"
            )
