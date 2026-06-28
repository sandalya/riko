"""Agent eval tests — verify prompt building and report structure. No real API calls."""
from unittest.mock import MagicMock, patch

from bot.client import _build_prompt, _call_claude, _system_prompt

FAKE_DETECTIONS = {
    "image_path": "/tmp/test.jpg",
    "detections": [{"cls": "person", "confidence": 0.776, "bbox": [409, 122, 584, 517]}],
}

FAKE_REPORT = """\
| Object | Confidence | BBox | Frame/Time | GPS Coords | Threat Level |
|--------|------------|------|------------|------------|--------------|
| person | 77.6% | [409, 122, 584, 517] | image | N/A | Medium |

### Summary
One person detected with medium confidence. Overall threat level: **Medium**.
"""


def test_build_prompt_contains_detections():
    prompt = _build_prompt(FAKE_DETECTIONS, "image")
    assert "person" in prompt
    assert "0.776" in prompt


def test_build_prompt_video_label():
    video_detections = {"video_path": "/tmp/v.mp4", "fps": 25.0, "timeline": []}
    prompt = _build_prompt(video_detections, "video")
    assert "Video detections" in prompt


def test_system_prompt_loaded():
    sp = _system_prompt()
    assert len(sp) > 0
    assert "Threat Level" in sp
    assert "recon" in sp.lower()


def test_report_structure():
    mock_client = MagicMock()
    mock_client.messages.create.return_value.content = [MagicMock(text=FAKE_REPORT)]

    with patch("bot.client.anthropic.Anthropic", return_value=mock_client):
        result = _call_claude(FAKE_DETECTIONS, "image")

    assert "person" in result
    assert "Medium" in result


def test_report_has_table():
    assert "|" in FAKE_REPORT
    assert "Threat Level" in FAKE_REPORT
    assert "Summary" in FAKE_REPORT
