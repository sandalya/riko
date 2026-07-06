"""Unit test for cv_toolkit/labeling/cvat_pull.py (Phase 0.4).

Uses a real CVAT YOLO-export zip captured from the Phase 0 smoke test (task 3,
frame_000069 — pidar box corrected by hand in the CVAT UI) as a fixture, so no
live CVAT server is needed to test the extraction logic.
"""
from cv_toolkit.labeling.cvat_pull import extract_labels_from_zip


def test_extracts_only_label_txt_files(fixtures_dir, tmp_path):
    zip_path = fixtures_dir / "labeling" / "cvat_yolo_export_sample.zip"
    written = extract_labels_from_zip(zip_path, tmp_path)

    assert [p.name for p in written] == ["frame_000069.txt"]
    assert not (tmp_path / "data.yaml").exists()
    assert not (tmp_path / "train.txt").exists()


def test_label_content_matches_corrected_box(fixtures_dir, tmp_path):
    zip_path = fixtures_dir / "labeling" / "cvat_yolo_export_sample.zip"
    extract_labels_from_zip(zip_path, tmp_path)

    content = (tmp_path / "frame_000069.txt").read_text().strip()
    cls_id, cx, cy, w, h = content.split()
    assert cls_id == "0"  # pidar, taxonomy ID 0
    assert 0.0 < float(cx) < 1.0
    assert 0.0 < float(cy) < 1.0
