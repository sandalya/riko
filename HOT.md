---
project: drone-recon
updated: 2026-07-17
---
# HOT

## Now
Security cleanup: rotated ANTHROPIC_API_KEY and BOT_TOKEN (were exposed when repo went public); cleaned .env from entire git history via git filter-repo; force-pushed rewritten history to GitHub (sandalya/riko). Confirmed TG_API_ID/HASH low-risk (session file was never committed).

## Last done
- Rotated ANTHROPIC_API_KEY in .env and Anthropic console
- Rotated BOT_TOKEN in .env and Telegram BotFather
- Ran `git filter-repo` to remove .env from full git history
- Force-pushed rewritten history to GitHub
- Verified TG_API_ID/HASH remain in .env (session file never committed, low risk)
- Repo is now public (sandalya/riko) with clean history

## Next
Resume eval pipeline: decide IoU threshold + false-positive scoring, then implement freeze_eval_set.py / auto_ingest guard / run_eval.py.

## Blockers
None.

## Open questions
- IoU threshold for detection match (ground truth vs. detector output)?
- How to score false positives outside golden classes (pidar, military_vehicle)?
- Include mAP metric alongside precision/recall?

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
- CVAT_HOST=192.168.72.191:8081 in infra .env
- Grounding DINO model wrapper deferred; Phase 0.2 only defines/consumes raw-output contract
- CVAT category_id offset: +1 only on cvat_push.py path; taxonomy.yaml and coco_export.py untouched
- direnv set up (.envrc); user can load .env into interactive shell
- Eval pipeline design parked 2026-07-14: locked eval_set_v0 (~10–20 videos), freeze_eval_set.py / auto_ingest guard / run_eval.py not yet built