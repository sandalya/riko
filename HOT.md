---
project: drone-recon
updated: 2026-07-22
---
# HOT

## Now
Built chkp-sumd: host-side systemd broker that allows checkpoint finalization (Anthropic call + apply_warm_ops + backlog + commit/push) to run outside the sandbox, enabling access to ANTHROPIC_API_KEY. Verified with mock round-trip and one live run.

## Last done
- Extracted run_checkpoint_finalize() from old do_checkpoint() into reusable module
- Implemented chkp-sumd.py as unix socket listener with secret-free validation
- Updated chkp.py do_checkpoint() to hand off via socket after pre-flight checks
- Added CHKP_ANTHROPIC_KEY to dedicated sumd.env file
- Wired client-side request via chkp_sum_client.py
- Verified mock and live round-trip; broker validated and executed checkpoint

## Next
Confirm the live chkp run committed and pushed correctly to origin. Decide whether to push meta repo commit (65c86da).

## Blockers
None.

## Open questions
- Should homework submission ship with sandbox.enabled=true (intent) or false (actually-working)?
- Is there an existing CVAT MCP package to restore, or was the dangling .mcp.json a local experiment?

## Reminders
- chkp-sumd files in meta/chkp/: chkp-sumd.py, chkp_sum_client.py, chkp-sumd.config.json, chkp-sumd.service, dedicated ~/.config/chkp/sumd.env
- systemd --user service (sumd) enabled+running, linger already on
- chkp-pushd.py (git push broker) also systemd --user, separate from sumd
- YOLO11n (COCO nano) auto-labeling: only 5/40 frames initially had detector-mapped boxes, but manual review showed auto frame *selection* (confidence ranking) works better than raw box *quality* — most frames legitimately needed added boxes (military_vehicle class unknown to base model)
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
- Claude Code module-3 homework: Path A (from scratch, drone-recon is the real project). Levels 1–3 closed (permissions + sandbox + network). Level 4 (devcontainer) intentionally skipped (solo project, no onboarding need). .claude/settings.local.json untracked and gitignored.