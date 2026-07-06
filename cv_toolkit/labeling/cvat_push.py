"""Push frames + COCO annotations into a CVAT task (Phase 0.3 — ingestion bridge).

Creates a task under the drone-recon CVAT project and uploads frame images plus
the coco_export.py (0.2) output in one call, so opening the task in the browser
shows pre-placed boxes on the correct frames. CVAT never runs inference itself —
boxes are computed offline and imported.

Auth: CVAT_HOST (optional, defaults to the Beelink server) / CVAT_USER /
CVAT_PASSWORD from .env.

Usage:
  python -m cv_toolkit.labeling.cvat_push \
      --frames <frames_dir> --coco <coco.json> --task-name cycle0 [--project-id 1]
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from cvat_sdk import make_client
from cvat_sdk.core.client import Client
from cvat_sdk.core.proxies.tasks import ResourceType, Task
from dotenv import load_dotenv

from cv_toolkit.labeling.coco_export import shift_category_ids

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}
DEFAULT_PROJECT_ID = 1
DEFAULT_HOST = "http://192.168.72.191:8081"
ANNOTATION_FORMAT = "COCO 1.0"

# CVAT's COCO importer rejects category_id == 0 ("annotation has no label").
# taxonomy.yaml IDs (0-5) stay the source of truth everywhere else; this shift
# applies only to the file actually uploaded to CVAT.
CVAT_CATEGORY_ID_OFFSET = 1


@contextmanager
def _cvat_ready_coco(coco_path: Path):
    """Yield a path to a COCO file with category ids shifted for CVAT import."""
    coco = json.loads(coco_path.read_text())
    shifted = shift_category_ids(coco, CVAT_CATEGORY_ID_OFFSET)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", prefix="cvat_coco_", delete=False
    ) as f:
        json.dump(shifted, f)
        tmp_path = Path(f.name)
    try:
        yield tmp_path
    finally:
        tmp_path.unlink(missing_ok=True)


def collect_frames(frames_dir: Path) -> list[Path]:
    frames = sorted(p for p in frames_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    if not frames:
        raise FileNotFoundError(f"No images found in {frames_dir}")
    return frames


def push_task(
    client: Client,
    project_id: int,
    task_name: str,
    frames: list[Path],
    coco_path: Path,
) -> Task:
    spec = {"name": task_name, "project_id": project_id}
    return client.tasks.create_from_data(
        spec=spec,
        resources=[str(p) for p in frames],
        resource_type=ResourceType.LOCAL,
        annotation_path=str(coco_path),
        annotation_format=ANNOTATION_FORMAT,
    )


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", required=True, help="Directory of frame images")
    parser.add_argument("--coco", required=True, help="COCO JSON from coco_export.py")
    parser.add_argument("--task-name", required=True)
    parser.add_argument("--project-id", type=int, default=DEFAULT_PROJECT_ID)
    parser.add_argument("--host", default=os.environ.get("CVAT_HOST", DEFAULT_HOST))
    args = parser.parse_args()

    frames = collect_frames(Path(args.frames))

    with _cvat_ready_coco(Path(args.coco)) as cvat_coco_path:
        with make_client(
            args.host,
            credentials=(os.environ["CVAT_USER"], os.environ["CVAT_PASSWORD"]),
        ) as client:
            task = push_task(
                client=client,
                project_id=args.project_id,
                task_name=args.task_name,
                frames=frames,
                coco_path=cvat_coco_path,
            )

    print(f"Task created: id={task.id} name={task.name!r} frames={len(frames)}")
    print(f"Open: {args.host}/tasks/{task.id}")


if __name__ == "__main__":
    main()
