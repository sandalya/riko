---
project: drone-recon
updated: 2026-07-21
---
# HOT

## Now
Built chkp-pushd: host-side systemd --user git push broker (unix socket, allowlist+pinned-url+ff-only) as fallback when sandboxed git push is blocked. Wired chkp.py git_commit_push() to fall back to chkp_push_client.request_push(); added sandbox filesystem allow + allowAllUnixSockets to .claude/settings.json.

## Last done
- Implemented chkp-pushd.py systemd --user service (unix socket broker for git push)
- Created chkp_push_client.py with fallback request logic (pinned URL, ff-only, allowlist)
- Configured chkp-pushd.config.json with drone-recon repo entry
- Added sandbox filesystem allow + allowAllUnixSockets to .claude/settings.json
- Verified broker with --test flag, in-session client call, and allowlist rejection
- Integrated fallback into chkp.py git_commit_push()

## Next
Monitor broker in practice once sandbox.enabled is flipped back on with network isolation. Add trudovik repo entry to chkp-pushd.config.json when needed.

## Blockers
None.

## Open questions
- Should homework submission ship with sandbox.enabled=true (intent) or false (actually-working)?
- Is there an existing CVAT MCP package to restore, or was the dangling .mcp.json a local experiment?

## Reminders
- chkp-pushd files in meta/chkp/ (chkp-pushd.py, chkp_push_client.py, chkp-pushd.config.json, repo_id=drone-recon only)
- systemd --user service enabled+running, linger already on
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
- Claude Code module-3 homework: Path A (from scratch, drone-recon is the real project). Levels 1–3 closed (permissions + sandbox + network). Level 4 (devcontainer) intentionally skipped (solo project, no onboarding need). .claude/settings.local.json untracked and gitignored.