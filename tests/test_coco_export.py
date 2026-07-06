"""Unit tests for cv_toolkit/labeling/coco_export.py (Phase 0.2).

No detector/GPU needed — pure data transform, runs against a 5-frame fixture.
"""
import json

import pytest

from cv_toolkit.labeling.coco_export import (
    build_coco,
    load_prompt_to_class,
    load_taxonomy,
)


@pytest.fixture(scope="module")
def raw(fixtures_dir):
    return json.loads((fixtures_dir / "labeling" / "raw_detections_5frame.json").read_text())


@pytest.fixture(scope="module")
def taxonomy():
    return load_taxonomy()


@pytest.fixture(scope="module")
def prompt_to_class():
    return load_prompt_to_class()


def test_taxonomy_has_six_frozen_classes(taxonomy):
    assert taxonomy == {
        0: "pidar",
        1: "military_vehicle",
        2: "vehicle",
        3: "fpv_drone",
        4: "artillery",
        5: "structure",
    }


def test_coco_categories_match_taxonomy_ids(raw, prompt_to_class, taxonomy):
    coco, _ = build_coco(raw, prompt_to_class, taxonomy)
    categories = {c["id"]: c["name"] for c in coco["categories"]}
    assert categories == taxonomy


def test_coco_images_count(raw, prompt_to_class, taxonomy):
    coco, _ = build_coco(raw, prompt_to_class, taxonomy)
    assert len(coco["images"]) == 5


def test_matched_detections_mapped_to_correct_class(raw, prompt_to_class, taxonomy):
    coco, dropped = build_coco(raw, prompt_to_class, taxonomy)

    by_image = {}
    for ann in coco["annotations"]:
        by_image.setdefault(ann["image_id"], []).append(ann)

    # frame 1: soldier -> pidar (0), civilian car -> vehicle (2)
    assert {a["category_id"] for a in by_image[1]} == {0, 2}
    # frame 2: BMP -> military_vehicle (1)
    assert by_image[2][0]["category_id"] == 1
    # frame 4: FPV drone -> fpv_drone (3); "dog" unmatched, dropped
    assert [a["category_id"] for a in by_image[4]] == [3]
    # frame 5: trench -> structure (5)
    assert by_image[5][0]["category_id"] == 5

    assert dropped == ["dog"]


def test_bbox_converted_xyxy_to_xywh(raw, prompt_to_class, taxonomy):
    coco, _ = build_coco(raw, prompt_to_class, taxonomy)
    # frame 1, soldier: xyxy [100, 50, 180, 220] -> xywh [100, 50, 80, 170]
    ann = next(a for a in coco["annotations"] if a["image_id"] == 1 and a["category_id"] == 0)
    assert ann["bbox"] == [100.0, 50.0, 80.0, 170.0]
    assert ann["area"] == pytest.approx(80.0 * 170.0)


def test_empty_detections_frame_produces_no_annotations(raw, prompt_to_class, taxonomy):
    coco, _ = build_coco(raw, prompt_to_class, taxonomy)
    assert not any(a["image_id"] == 3 for a in coco["annotations"])
