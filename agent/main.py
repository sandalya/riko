"""Drone recon agent — calls detector tools and generates a structured report via Claude.

Usage:
    python agent/main.py --image <path> [--gps <path>]
    python agent/main.py --video <path> [--gps <path>] [--every-n-frames 30] [--offset 0.0]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import anthropic

MODEL = "claude-sonnet-4-6"

# Load mcp/server.py by explicit path — avoids the PyPI `mcp` package shadowing
# our local mcp/ directory when agent/main.py is run as a script (sys.path[0] = agent/).
_MCP_SERVER_PATH = Path(__file__).parent.parent / "mcp" / "server.py"
_mcp_server: ModuleType | None = None


def _mcp() -> ModuleType:
    global _mcp_server
    if _mcp_server is None:
        spec = importlib.util.spec_from_file_location("_drone_recon_mcp_server", _MCP_SERVER_PATH)
        _mcp_server = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_mcp_server)
    return _mcp_server
_PROMPT_PATH = Path(__file__).parent / "prompts" / "recon_analyst.md"
SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Prompt builder (importable without side effects — used in smoke tests)
# ---------------------------------------------------------------------------

def build_report_prompt(
    detections_data: dict,
    gps_correlated: list[dict] | None = None,
    gps_log: list[dict] | None = None,
) -> str:
    """Return the user message string to send to the recon analyst."""
    parts: list[str] = []

    if gps_correlated is not None:
        parts.append("## Video detections with GPS correlation")
        parts.append(f"```json\n{json.dumps(gps_correlated, indent=2)}\n```")
    elif "timeline" in detections_data:
        parts.append("## Video detections (no GPS available)")
        parts.append(f"```json\n{json.dumps(detections_data, indent=2)}\n```")
    else:
        parts.append("## Image detections")
        parts.append(f"```json\n{json.dumps(detections_data, indent=2)}\n```")
        if gps_log:
            parts.append("## GPS log (first points)")
            parts.append(f"```json\n{json.dumps(gps_log[:5], indent=2)}\n```")

    parts.append("\nProduce the reconnaissance report.")
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Pipeline runners
# ---------------------------------------------------------------------------

def _run_image(image_path: str, gps_path: str | None) -> str:
    srv = _mcp()
    detections = srv.detect_objects(image_path)
    gps = srv.parse_gps_log(gps_path) if gps_path else None
    return build_report_prompt(detections, gps_log=gps)


def _run_video(
    video_path: str,
    gps_path: str | None,
    every_n_frames: int,
    offset: float,
) -> str:
    srv = _mcp()
    detections = srv.analyze_video(video_path, every_n_frames=every_n_frames)

    if gps_path:
        correlated = srv.correlate_detections_gps(
            json.dumps(detections),
            gps_path,
            offset_seconds=offset,
        )
        return build_report_prompt(detections, gps_correlated=correlated)

    return build_report_prompt(detections)


# ---------------------------------------------------------------------------
# Claude call
# ---------------------------------------------------------------------------

def generate_report(user_message: str) -> str:
    """Send the prompt to Claude and return the report text."""
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Drone recon agent — generates a structured intelligence report from media."
    )
    media = parser.add_mutually_exclusive_group(required=True)
    media.add_argument("--image", metavar="PATH", help="Path to image file")
    media.add_argument("--video", metavar="PATH", help="Path to video file")
    parser.add_argument("--gps", metavar="PATH", help="Path to GPX log file")
    parser.add_argument(
        "--every-n-frames", type=int, default=30, metavar="N",
        help="Sample every N frames for video analysis (default: 30)",
    )
    parser.add_argument(
        "--offset", type=float, default=0.0, metavar="SEC",
        help="GPS time offset in seconds relative to video start (default: 0.0)",
    )
    args = parser.parse_args()

    if args.image:
        user_message = _run_image(args.image, args.gps)
    else:
        user_message = _run_video(args.video, args.gps, args.every_n_frames, args.offset)

    report = generate_report(user_message)
    print(report)


if __name__ == "__main__":
    main()
