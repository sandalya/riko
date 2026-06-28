"""MCP server — drone-recon detector tools.

Run as MCP server:
    venv/bin/python mcp/server.py

Tools can also be called directly as Python functions (no MCP transport needed).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import gpxpy
import httpx

DETECTOR_URL = "http://localhost:8000"


# ---------------------------------------------------------------------------
# Tool 1
# ---------------------------------------------------------------------------

def detect_objects(image_path: str) -> dict:
    """Detect objects in a single image via the detector service."""
    r = httpx.post(
        f"{DETECTOR_URL}/detect",
        json={"image_path": image_path},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Tool 2
# ---------------------------------------------------------------------------

def analyze_video(video_path: str, every_n_frames: int = 30) -> dict:
    """Run detection on a video file, sampling every N frames."""
    r = httpx.post(
        f"{DETECTOR_URL}/detect_video",
        json={"video_path": video_path, "every_n_frames": every_n_frames},
        timeout=300,
    )
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Tool 3
# ---------------------------------------------------------------------------

def parse_gps_log(gps_path: str) -> list[dict]:
    """Parse a GPX file and return a list of {time, lat, lon, ele} points."""
    path = Path(gps_path)
    if not path.exists():
        raise ValueError(f"GPS file not found: {gps_path}")

    with path.open() as f:
        gpx = gpxpy.parse(f)

    points: list[dict] = []
    for track in gpx.tracks:
        for segment in track.segments:
            for pt in segment.points:
                points.append({
                    "time": pt.time.isoformat() if pt.time else None,
                    "lat": pt.latitude,
                    "lon": pt.longitude,
                    "ele": pt.elevation,
                })
    return points


# ---------------------------------------------------------------------------
# Tool 4
# ---------------------------------------------------------------------------

def correlate_detections_gps(
    detections_json: str,
    gps_path: str,
    offset_seconds: float = 0.0,
) -> list[dict]:
    """Match video detections to GPS coordinates by frame timestamp.

    detections_json — JSON string of a DetectVideoResponse (fps + timeline).
    offset_seconds  — shift applied to frame_time before GPS matching.
    Returns list of {frame_time, lat, lon, detections}.
    """
    data = json.loads(detections_json)
    gps_points = parse_gps_log(gps_path)
    if not gps_points:
        raise ValueError("GPS log is empty")

    # Build (elapsed_seconds_from_start, lat, lon) index
    timed: list[tuple[float, float, float]] = []
    t0: datetime | None = None
    for pt in gps_points:
        if pt["time"] is None:
            continue
        t = datetime.fromisoformat(pt["time"])
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        if t0 is None:
            t0 = t
        timed.append(((t - t0).total_seconds(), pt["lat"], pt["lon"]))

    def nearest_gps(frame_sec: float) -> tuple[float | None, float | None]:
        if not timed:
            return None, None
        target = frame_sec + offset_seconds
        _, lat, lon = min(timed, key=lambda x: abs(x[0] - target))
        return lat, lon

    result: list[dict] = []
    for frame in data.get("timeline", []):
        lat, lon = nearest_gps(frame["frame_time"])
        result.append({
            "frame_time": frame["frame_time"],
            "lat": lat,
            "lon": lon,
            "detections": frame["detections"],
        })
    return result


# ---------------------------------------------------------------------------
# MCP transport — only when run directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    # Our mcp/ directory shadows the installed mcp package.
    # Remove it from sys.path and sys.modules so fastmcp can find mcp.types.
    _root = str(Path(__file__).parent.parent.resolve())
    sys.path = [p for p in sys.path if p not in ("", _root)]
    for _key in list(sys.modules):
        if _key == "mcp" or _key.startswith("mcp."):
            del sys.modules[_key]

    from fastmcp import FastMCP

    server = FastMCP("drone-recon-detector")
    server.tool()(detect_objects)
    server.tool()(analyze_video)
    server.tool()(parse_gps_log)
    server.tool()(correlate_detections_gps)
    server.run()
