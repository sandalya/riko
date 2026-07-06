"""Convert auto-labeler raw output into taxonomy-mapped COCO JSON.

Raw input format (produced by the open-vocab auto-labeler, e.g. Grounding DINO
driven by cv_toolkit/configs/grounding_dino.yaml text prompts):

{
  "images": [
    {
      "file_name": "frame_000001.jpg",
      "width": 640,
      "height": 480,
      "detections": [
        {"label": "BMP infantry fighting vehicle", "confidence": 0.71,
         "bbox": [x1, y1, x2, y2]}
      ]
    }
  ]
}

`label` is the prompt phrase that fired (from grounding_dino.yaml). Each prompt
phrase belongs to exactly one taxonomy class — this module inverts that config
to map phrase -> class name, then class name -> frozen taxonomy ID (taxonomy.yaml).
Labels that don't match any known prompt are dropped (logged, not "unknown").

Usage:
  python -m cv_toolkit.labeling.coco_export \
      --raw <raw_detections.json> \
      --output <coco.json> \
      [--taxonomy taxonomy.yaml] [--prompts cv_toolkit/configs/grounding_dino.yaml]
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_TAXONOMY_PATH = _PROJECT_ROOT / "taxonomy.yaml"
DEFAULT_PROMPTS_PATH = _PROJECT_ROOT / "cv_toolkit" / "configs" / "grounding_dino.yaml"


def load_taxonomy(path: Path = DEFAULT_TAXONOMY_PATH) -> dict[int, str]:
    """Return {id: class_name}, in the frozen order from taxonomy.yaml."""
    data = yaml.safe_load(path.read_text())
    return dict(sorted(data["classes"].items()))


def load_prompt_to_class(path: Path = DEFAULT_PROMPTS_PATH) -> dict[str, str]:
    """Invert grounding_dino.yaml: {prompt phrase (lowercased) -> class name}."""
    data = yaml.safe_load(path.read_text())
    mapping: dict[str, str] = {}
    for class_name, prompts in data["prompts"].items():
        for prompt in prompts:
            mapping[prompt.strip().lower()] = class_name
    return mapping


def _xyxy_to_xywh(bbox: list[float]) -> list[float]:
    x1, y1, x2, y2 = bbox
    return [x1, y1, x2 - x1, y2 - y1]


def build_coco(
    raw: dict[str, Any],
    prompt_to_class: dict[str, str],
    taxonomy: dict[int, str],
) -> tuple[dict[str, Any], list[str]]:
    """Build a COCO dict from raw auto-labeler output.

    Returns (coco_dict, dropped_labels) — dropped_labels lists raw labels that
    didn't match any known prompt (unmatched detections are excluded from output).
    """
    class_to_id = {name: cls_id for cls_id, name in taxonomy.items()}
    categories = [{"id": cls_id, "name": name} for cls_id, name in taxonomy.items()]

    images: list[dict[str, Any]] = []
    annotations: list[dict[str, Any]] = []
    dropped: list[str] = []
    ann_id = 1

    for image_id, image in enumerate(raw["images"], start=1):
        images.append({
            "id": image_id,
            "file_name": image["file_name"],
            "width": image["width"],
            "height": image["height"],
        })

        for det in image.get("detections", []):
            label = det["label"].strip().lower()
            class_name = prompt_to_class.get(label)
            if class_name is None:
                dropped.append(det["label"])
                log.warning("Dropping unmatched label %r (no prompt match)", det["label"])
                continue

            bbox = _xyxy_to_xywh(det["bbox"])
            annotations.append({
                "id": ann_id,
                "image_id": image_id,
                "category_id": class_to_id[class_name],
                "bbox": bbox,
                "area": bbox[2] * bbox[3],
                "score": det["confidence"],
                "iscrowd": 0,
            })
            ann_id += 1

    coco = {
        "images": images,
        "annotations": annotations,
        "categories": categories,
    }
    return coco, dropped


def shift_category_ids(coco: dict[str, Any], offset: int) -> dict[str, Any]:
    """Return a copy of `coco` with all category ids shifted by `offset`.

    CVAT's COCO importer rejects category_id == 0 ("annotation has no label") —
    COCO tooling conventionally reserves id 0. Our frozen taxonomy.yaml IDs start
    at 0 (they're the source of truth for training), so the CVAT ingestion bridge
    (cvat_push.py) shifts by +1 only for the upload; taxonomy IDs are untouched
    everywhere else.
    """
    shifted = json.loads(json.dumps(coco))  # deep copy
    for cat in shifted["categories"]:
        cat["id"] += offset
    for ann in shifted["annotations"]:
        ann["category_id"] += offset
    return shifted


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", required=True, help="Raw auto-labeler output JSON")
    parser.add_argument("--output", required=True, help="Output COCO JSON path")
    parser.add_argument("--taxonomy", default=str(DEFAULT_TAXONOMY_PATH))
    parser.add_argument("--prompts", default=str(DEFAULT_PROMPTS_PATH))
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    raw = json.loads(Path(args.raw).read_text())
    taxonomy = load_taxonomy(Path(args.taxonomy))
    prompt_to_class = load_prompt_to_class(Path(args.prompts))

    coco, dropped = build_coco(raw, prompt_to_class, taxonomy)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(coco, indent=2))

    print(f"{len(coco['images'])} images, {len(coco['annotations'])} annotations written")
    if dropped:
        print(f"Dropped {len(dropped)} unmatched labels: {sorted(set(dropped))}", file=sys.stderr)
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
