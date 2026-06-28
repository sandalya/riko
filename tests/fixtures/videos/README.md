# Video Test Fixtures

Downloaded via yt-dlp, trimmed to 5 seconds with ffmpeg (imageio-ffmpeg static binary).
Detection run with `every_n_frames=15`.

| Filename | Source | Duration | Frames analysed | Total detections | Main objects |
|----------|--------|----------|-----------------|------------------|--------------|
| people_walking.mp4 | YouTube search: "people walking sidewalk security camera" | 5s | 11 | 111 | person×100, handbag×6, backpack×4 |
| road_traffic.mp4 | YouTube search: "road traffic dashcam cars trucks" | 5s | 11 | 24 | person×24 |
| mixed_scene.mp4 | YouTube search: "outdoor parking lot surveillance camera people cars" | 5s | 9 | 41 | car×39, truck×2 |

Golden JSON files: `tests/golden/video_<name>.json`

## Notes
- `road_traffic.mp4` actual content: crowded street scene — persons detected, no vehicles (COCO model limitation on this clip)
- `mixed_scene.mp4`: parking lot — car/truck detections as expected
- Model: yolo11n.pt (COCO 80 classes), every_n_frames=15
