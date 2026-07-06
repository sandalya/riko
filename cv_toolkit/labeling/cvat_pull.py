"""Pull reviewed annotations from a CVAT task back as YOLO labels.

Phase 0.4 — closes the review round-trip: frames + draft boxes (0.2/0.3) go into
CVAT, a human reviews/corrects them in the browser, and this module pulls the
current state back out as Ultralytics YOLO .txt files. A box edited in CVAT
shows up here with the corrected coordinates — that's the round-trip proof.

Auth: CVAT_HOST (optional) / CVAT_USER / CVAT_PASSWORD from .env.

Usage:
  python -m cv_toolkit.labeling.cvat_pull --task-id 3 --output labels/
"""
from __future__ import annotations

import argparse
import os
import tempfile
import zipfile
from pathlib import Path

from cvat_sdk import make_client
from dotenv import load_dotenv

DEFAULT_HOST = "http://192.168.72.191:8081"
ANNOTATION_FORMAT = "Ultralytics YOLO Detection 1.0"


def extract_labels_from_zip(zip_path: Path, output_dir: Path) -> list[Path]:
    """Copy label .txt files out of a CVAT YOLO export zip into output_dir.

    Ignores data.yaml / train.txt / images — only the per-frame label files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with zipfile.ZipFile(zip_path) as zf:
        label_names = [
            n for n in zf.namelist()
            if n.startswith("labels/") and n.endswith(".txt")
        ]
        for name in label_names:
            dest = output_dir / Path(name).name
            dest.write_bytes(zf.read(name))
            written.append(dest)
    return written


def pull_labels(
    host: str,
    user: str,
    password: str,
    task_id: int,
    output_dir: Path,
) -> list[Path]:
    """Export task_id's current annotations as YOLO and extract labels into output_dir."""
    with make_client(host, credentials=(user, password)) as client:
        task = client.tasks.retrieve(task_id)
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / "export.zip"
            task.export_dataset(ANNOTATION_FORMAT, zip_path, include_images=False)
            return extract_labels_from_zip(zip_path, output_dir)


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", type=int, required=True)
    parser.add_argument("--output", required=True, help="Local directory for pulled YOLO labels")
    parser.add_argument("--host", default=os.environ.get("CVAT_HOST", DEFAULT_HOST))
    args = parser.parse_args()

    written = pull_labels(
        host=args.host,
        user=os.environ["CVAT_USER"],
        password=os.environ["CVAT_PASSWORD"],
        task_id=args.task_id,
        output_dir=Path(args.output),
    )
    print(f"Pulled {len(written)} label file(s) into {args.output}")
    for p in written:
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
