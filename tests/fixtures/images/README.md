# COCO val2017 Test Fixtures

Downloaded from http://images.cocodataset.org/val2017/

| Filename | COCO ID | Expected objects | Actual detections (yolo11n) |
|----------|---------|------------------|-----------------------------|
| coco_person_01.jpg | 000000397133 | person on street | person ×2 (0.91, 0.61), bowl ×2, oven ×2 |
| coco_truck_01.jpg | 000000037777 | truck on road | refrigerator 0.83, oven 0.81, orange ×4 |
| coco_mixed_01.jpg | 000000252219 | person + vehicle | person ×3 (0.94, 0.91, 0.90), umbrella 0.63 |
| coco_person_02.jpg | 000000087038 | person alone | person ×2 (0.83, 0.80), skateboard 0.76, bicycle 0.71 |
| coco_vehicle_01.jpg | 000000174482 | vehicles | bicycle 0.92, car ×4 (0.84, 0.82, 0.54, 0.52) |
| coco_empty_01.jpg | 000000403385 | open field / minimal | toilet 0.84, sink 0.81 |

Golden JSON files: `tests/golden/coco_*.json`

## Notes
- `coco_truck_01` actual scene: indoor kitchen/appliances — no vehicles detected by COCO-trained YOLO
- `coco_empty_01` actual scene: bathroom — not an open field; low object count still useful as a "few detections" case
- Model: yolo11n.pt (COCO 80 classes), confidence threshold from detector/config.py
