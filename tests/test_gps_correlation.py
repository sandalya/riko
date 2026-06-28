"""Integration tests for GPS parsing and frame correlation (no detector needed)."""
import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
GPX_PATH = str(FIXTURES / "sample.gpx")
VIDEO_JSON_PATH = FIXTURES / "sample_video_detections.json"


# ---------------------------------------------------------------------------
# parse_gps_log
# ---------------------------------------------------------------------------

def test_parse_gps_log(mcp_server):
    points = mcp_server.parse_gps_log(GPX_PATH)
    assert len(points) == 10
    for pt in points:
        assert "lat" in pt
        assert "lon" in pt
        assert "time" in pt
        assert "ele" in pt
    assert points[0]["lat"] == pytest.approx(48.0, abs=1e-6)


def test_parse_gps_missing_file(mcp_server):
    with pytest.raises(ValueError, match="GPS file not found"):
        mcp_server.parse_gps_log("/nonexistent/path/file.gpx")


# ---------------------------------------------------------------------------
# correlate_detections_gps
# ---------------------------------------------------------------------------

def test_correlate_basic(mcp_server):
    detections_json = VIDEO_JSON_PATH.read_text()
    result = mcp_server.correlate_detections_gps(detections_json, GPX_PATH)

    assert len(result) == 3
    for item in result:
        assert "frame_time" in item
        assert "lat" in item
        assert "lon" in item
        assert "detections" in item


def test_correlate_nearest_point(mcp_server):
    detections_json = VIDEO_JSON_PATH.read_text()
    result = mcp_server.correlate_detections_gps(detections_json, GPX_PATH)

    # frame_time=0.0 → GPS t=0 → lat=48.0000
    assert result[0]["frame_time"] == 0.0
    assert result[0]["lat"] == pytest.approx(48.0000, abs=1e-4)

    # frame_time=2.0 → GPS t=2 → lat=48.0002
    assert result[1]["frame_time"] == 2.0
    assert result[1]["lat"] == pytest.approx(48.0002, abs=1e-4)


def test_correlate_offset(mcp_server):
    detections_json = VIDEO_JSON_PATH.read_text()
    # offset=1.0: frame_time=0.0 is treated as t=1 → lat=48.0001
    result = mcp_server.correlate_detections_gps(detections_json, GPX_PATH, offset_seconds=1.0)

    assert result[0]["frame_time"] == 0.0
    assert result[0]["lat"] == pytest.approx(48.0001, abs=1e-4)
