"""Telegram channel video scraper with 5-stage filter pipeline.

Usage:
    python scraper/main.py --channels escadrone DPSUkr --limit 100
    python scraper/main.py --channels escadrone --limit 50 --no-haiku

Requires in .env:
    TG_API_ID=...
    TG_API_HASH=...
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import shutil
from collections import defaultdict
from pathlib import Path

from scraper.client import get_channel_videos, make_client
from scraper.config import (
    APPROVED_DIR,
    CHANNELS,
    HASHES_FILE,
    PRIORITY,
    RAW_DIR,
    REJECTED_DIR,
    REVIEW_DIR,
)
from scraper.downloader import download_video
from scraper.filter import (
    compute_phash,
    is_duration_ok,
    is_duplicate,
    is_quality_ok,
    is_size_ok,
)
from scraper.haiku_filter import classify_frame

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("scraper.main")

Outcome = str  # "approved" | "review" | "rejected"


def _load_hashes() -> dict:
    p = Path(HASHES_FILE)
    if p.exists():
        return json.loads(p.read_text())
    return {}


def _save_hashes(hashes: dict) -> None:
    p = Path(HASHES_FILE)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(hashes, indent=2))


def _move(src: Path, dest_dir: str) -> Path:
    d = Path(dest_dir)
    d.mkdir(parents=True, exist_ok=True)
    dest = d / src.name
    shutil.move(str(src), str(dest))
    return dest


async def _process_message(
    client,
    msg,
    channel: str,
    known_hashes: dict,
    use_haiku: bool,
) -> tuple[Outcome, str]:
    """Run the 5-stage pipeline for one message. Returns (outcome, log_line)."""
    video = msg.video
    size_bytes  = getattr(video, "size", 0)
    duration    = getattr(video, "duration", 0)
    size_mb     = size_bytes / (1024 * 1024)

    # Stage 1 — metadata filter
    if not is_size_ok(size_bytes):
        return "rejected", f"size={size_mb:.1f}MB out of range"
    if not is_duration_ok(duration):
        return "rejected", f"duration={duration}s out of range → rejected"

    # Stage 2 — download
    raw_path = await download_video(client, msg, RAW_DIR)
    if raw_path is None:
        return "rejected", "download_failed"

    tag = f"[{channel}] msg={msg.id} | size={size_mb:.1f}MB | dur={duration}s"

    # Stage 3 — quality filter
    ok, reason = is_quality_ok(str(raw_path))
    if not ok:
        _move(raw_path, REJECTED_DIR)
        return "rejected", f"{tag} | quality={reason} → rejected"

    # Stage 4 — dedup
    phash = compute_phash(str(raw_path))
    if is_duplicate(phash, known_hashes):
        _move(raw_path, REJECTED_DIR)
        return "rejected", f"{tag} | duplicate → rejected"

    # Stage 5 — Haiku vision filter
    haiku_result = "skip"
    if use_haiku:
        haiku_result = await classify_frame(str(raw_path))

    # Route outcome
    if use_haiku and haiku_result == "no":
        outcome = "rejected"
        dest_dir = REJECTED_DIR
    elif use_haiku and haiku_result == "unsure":
        outcome = "review"
        dest_dir = REVIEW_DIR
    else:
        outcome = "approved"
        dest_dir = APPROVED_DIR

    _move(raw_path, dest_dir)
    if phash:
        known_hashes[phash] = {"channel": channel, "msg_id": msg.id}

    line = f"{tag} | blur=ok | haiku={haiku_result} → {outcome}"
    return outcome, line


async def run(channels: list[str], limit: int, use_haiku: bool) -> None:
    known_hashes = _load_hashes()
    stats: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    async with make_client() as client:
        # Sort by priority descending
        ordered = sorted(channels, key=lambda c: PRIORITY.get(c, 0), reverse=True)

        for channel in ordered:
            log.info(f"Scanning @{channel} (limit={limit}) ...")
            try:
                messages = await get_channel_videos(client, channel, limit)
            except Exception as exc:
                log.error(f"Cannot fetch @{channel}: {exc}")
                continue

            log.info(f"@{channel}: {len(messages)} video messages found")
            stats[channel]["total"] = len(messages)

            for msg in messages:
                outcome, line = await _process_message(
                    client, msg, channel, known_hashes, use_haiku
                )
                stats[channel][outcome] += 1
                print(line)

    _save_hashes(known_hashes)

    print("\n── Stats ──")
    for ch, s in stats.items():
        total    = s.get("total", 0)
        approved = s.get("approved", 0)
        review   = s.get("review", 0)
        rejected = s.get("rejected", 0)
        print(f"  @{ch}: total={total} approved={approved} review={review} rejected={rejected}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Telegram channel video scraper")
    parser.add_argument(
        "--channels", nargs="+", default=CHANNELS, metavar="CHANNEL",
        help="Channel usernames to scrape (default: all from config)",
    )
    parser.add_argument(
        "--limit", type=int, default=100, metavar="N",
        help="Max messages to fetch per channel (default: 100)",
    )
    parser.add_argument(
        "--no-haiku", action="store_true",
        help="Skip Claude Haiku vision filter (for testing without API)",
    )
    args = parser.parse_args()
    asyncio.run(run(args.channels, args.limit, use_haiku=not args.no_haiku))


if __name__ == "__main__":
    main()
