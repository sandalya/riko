"""API-level tests for the detector service.

Requires the detector running: uvicorn detector.main:app --port 8000
"""
import httpx
import pytest


def test_health(detector_url):
    r = httpx.get(f"{detector_url}/docs", timeout=5)
    assert r.status_code == 200


def test_detect_valid_image(detector_url, fixtures_dir):
    path = str((fixtures_dir / "person_street.jpg").resolve())
    r = httpx.post(f"{detector_url}/detect", json={"image_path": path}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert "image_path" in body
    assert "detections" in body
    assert isinstance(body["detections"], list)


def test_detect_missing_file(detector_url):
    r = httpx.post(
        f"{detector_url}/detect",
        json={"image_path": "/nonexistent/path/image.jpg"},
        timeout=10,
    )
    assert r.status_code == 404


def test_detect_wrong_format(detector_url, tmp_path):
    txt_file = tmp_path / "not_an_image.txt"
    txt_file.write_text("this is not an image")
    r = httpx.post(
        f"{detector_url}/detect",
        json={"image_path": str(txt_file)},
        timeout=10,
    )
    assert r.status_code == 422


def test_detect_black_frame(detector_url, fixtures_dir):
    path = str((fixtures_dir / "empty_black.jpg").resolve())
    r = httpx.post(f"{detector_url}/detect", json={"image_path": path}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert "detections" in body
    assert isinstance(body["detections"], list)
