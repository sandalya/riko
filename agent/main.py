"""Drone recon agent — calls detector tools and generates a structured report via Claude.

Usage:
    python agent/main.py --image <path> [--gps <path>]
    python agent/main.py --video <path> [--gps <path>] [--every-n-frames 30] [--offset 0.0]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import anthropic

MODEL = "claude-sonnet-4-6"
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
    from mcp.server import detect_objects, parse_gps_log

    detections = detect_objects(image_path)
    gps = parse_gps_log(gps_path) if gps_path else None
    return build_report_prompt(detections, gps_log=gps)


def _run_video(
    video_path: str,
    gps_path: str | None,
    every_n_frames: int,
    offset: float,
) -> str:
    from mcp.server import analyze_video, correlate_detections_gps

    detections = analyze_video(video_path, every_n_frames=every_n_frames)

    if gps_path:
        correlated = correlate_detections_gps(
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
