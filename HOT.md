---
project: drone-recon
updated: 2026-07-14
---
# HOT

## Now
Parked eval-pipeline design discussion. Captured full architecture for model regression testing (locked eval set, freeze_eval_set.py, auto_ingest guard, run_eval.py) — no code written yet.

## Last done
- Documented eval pipeline architecture: locked eval video set (10–20 videos), ground-truth labeling in CVAT, per-model result JSON snapshots
- Defined three-piece implementation plan: freeze_eval_set.py, auto_ingest_batch.py guard, run_eval.py
- Identified open decisions: IoU threshold, false-positive scoring outside golden classes, mAP inclusion

## Next
Resume eval pipeline design: decide IoU threshold, false-positive scoring outside golden classes, then implement freeze_eval_set.py / auto_ingest guard / run_eval.py.

## Blockers
None.

## Open questions
- How many frames needed for golden set to train robust military-vehicle classifier?
- Target detection classes for fine-tuned model?
- Drone FC for GPS logs (Betaflight / ArduPilot / other)?
- Deploy: VPS or Beelink + tunnel?
- **[EVAL PIPELINE]** IoU threshold for detection match (ground truth vs. detector output)?
- **[EVAL PIPELINE]** How to score false positives outside golden classes (pidar, military_vehicle)?
- **[EVAL PIPELINE]** Include mAP metric alongside precision/recall?

## Eval pipeline design (parked, not started)

Discussed 2026-07-14, not yet implemented — resume here. Goal: after each detector model update, run a fixed benchmark to see if it improved/regressed, comparably across runs.

Decisions made:
- Eval video set must be **locked**, not grown freely — a growing set breaks comparability between model versions (can't tell "model got worse" from "eval set got harder"). Can still expand later, but only as an explicit new version (eval_set_v2), never silent drift.
- Size: ~10–20 videos, sampled from `data/scraper/approved/`.
- Scope: detection metrics only for now (precision/recall per class: `pidar`, `military_vehicle`), not full pipeline/agent eval.
- Ground truth: hand-labeled by owner in CVAT, same workflow as `data/golden/` (see `cv_toolkit/labeling/cvat_push.py` / `cvat_pull.py`).

Proposed structure (not built yet):
```
data/eval/
├── manifest.json   ← locked: video filename + sha256 hash + date frozen + eval_set version
├── raw/            ← extracted frames, frozen (same pattern as data/golden/raw/batch_*)
├── labels/         ← YOLO .txt ground truth pulled from CVAT
└── results/        ← one JSON per eval run (date + model tag), so runs diff against each other
```

Planned pieces (none written yet):
1. `cv_toolkit/eval/freeze_eval_set.py` — one-time: sample N videos (seeded), write manifest.json with sha256 hashes, extract frames into `raw/` with no pre-placed boxes (owner labels from scratch, avoids detector bias in ground truth).
2. Guard in `cv_toolkit/pipeline/auto_ingest_batch.py` (and any future manual video-picking) — read `data/eval/manifest.json`, exclude those filenames from train/auto-label candidate pools. **Critical**: without this, eval videos could leak into training and invalidate the whole benchmark.
3. `cv_toolkit/eval/run_eval.py --model-tag <name>` — run current detector over `data/eval/raw/`, IoU-match against `data/eval/labels/`, compute precision/recall per class, write `data/eval/results/<date>_<model-tag>.json`.

Still to decide when we resume:
- IoU threshold for counting a detection as a "match" against ground truth.
- How to score false positives that fall outside the two golden classes (ignore vs. penalize).
- Whether to eventually add mAP alongside precision/recall.

## Reminders
- YOLO11n (COCO nano) auto-labeling: only 5/40 frames initially had detector-mapped boxes, but manual review showed auto frame *selection* (confidence ranking) works better than raw box *quality* for this domain — most frames legitimately needed added boxes (military_vehicle class unknown to base model)
- YOLO11n struggles with small objects at drone altitude → confirms need for custom model fine-tune
- Data architecture: golden/labels/ stays flat (unique vlcsnap/video-stem filenames, no collisions); provenance.json is source of truth for batch origin, not directory structure
- Golden batches: batch_001/ (23 frames, manual), batch_002/ (72 frames, manual), batch_003/ (11 frames, auto-reviewed). Combined: 106 frames, 214 boxes
- Train_pool: raw unreviewed detector snapshots, independent of CVAT push status — future runs get an unreviewed record
- CVAT tasks: id=4 (round1 manual), id=6 (round2 manual), id=7 (auto-v0-round1, 40 frames reviewed)
- `.env` must contain `ANTHROPIC_API_KEY`, `BOT_TOKEN`, `DETECTOR_URL`, `TG_API_ID`, `TG_API_HASH`, `CVAT_HOST`
- `mcp/` shadows PyPI `mcp` — always use importlib outside mcp/
- Bot fallback: Claude fails → plain summary, never crashes
- `requires_detector` marker: skip detector-dependent tests with `-m "not requires_detector"`
- cv_toolkit frame extraction complete: 916 frames ready for labeling
- SPEC_v001.md: Pi5 refs are design intent for edge inference, separate from dev-server workspace
- infra/cvat-server/ is gitignored (vendored CVAT clone)
- CVAT_HOST=192.168.72.191:8081 in infra .env
- Grounding DINO model wrapper deferred; Phase 0.2 only defines/consumes raw-output contract
- CVAT category_id offset: +1 only on cvat_push.py path; taxonomy.yaml and coco_export.py untouched
- direnv set up (.envrc); user can load .env into interactive shell

## How to resume
```bash
# Terminal 1 — detector
cd /home/sashok/.openclaw/workspace/drone-recon
venv/bin/uvicorn detector.main:app --port 8000

# Terminal 2 — bot
venv/bin/python3 main.py

# Auto-labeling batch run
venv/bin/python cv_toolkit/pipeline/auto_ingest_batch.py --num-videos 5 --top-frames 8 --task-name auto-v0-round2

# Frame extraction (if needed)
venv/bin/python cv_toolkit/frame_extractor.py --input <video_path> --output <frames_dir>

# CVAT ingestion (Phase 0.3/0.4)
venv/bin/python cv_toolkit/labeling/ingest_frame.py --frame <path> --task-id <id>

# Tests
venv/bin/pytest tests/ -v                       # 27+ tests (detector on :8000)
venv/bin/pytest -m "not requires_detector" -v   # tests without detector dependency

# CVAT labeling (Phase 0 ready, Phase 1.1 next)
CVAT_HOST=192.168.72.191:8081 — access via http://192.168.72.191:8081
```

## Phase Status

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 0** | Detector `/detect` + `/detect_video` | ✅ Done |
| **Phase 1** | CLAUDE.md, CC configured | ✅ Done |
| **Bot→Detector** | TG video/photo → JSON → TG reply | ✅ Live tested |
| **Eval** | pytest 27+ tests, COCO+video+GPS+agent | ✅ Done |
| **Phase 2** | MCP Server + 4 tools | ✅ Done |
| **Phase 3** | Claude Agent + bot wired | ✅ Done |
| **Phase 0.1** | CVAT self-hosted + taxonomy config | ✅ Done |
| **Phase 0.2** | Auto-labeler → COCO exporter | ✅ Done |
| **Phase 0.3 + 0.4** | CVAT ingestion (cvat_push.py) + export (cvat_pull.py) | ✅ Done |
| **Phase 1.1** | Hand-label golden/val set + auto-labeling pipeline + data split | 🔄 In progress |
| **Phase 4 — Eval Pipeline** | Locked eval set + freeze/run/diff scripts | ⬜ Pending (design parked, resume next) |
| **Phase 5** | GPS Level 1 + deploy | ⬜ Pending |