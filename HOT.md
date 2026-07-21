---
project: drone-recon
updated: 2026-07-21
---
# HOT

## Now
Built production-ready Claude Code config for module-3 homework (Path A). Closed security levels 1–3: permissions deny (sudo, git push --force), sandbox filesystem denyRead (~/.ssh, ~/.aws/credentials, ~/.config/gcloud, **/.env), and network allowedDomains (anthropic, github, npm, pypi, telegram). Diagnosed and fixed a Claude Code sandbox regression (nested userns/CAP_SYS_ADMIN crash on latest channel 2.1.216) by pinning to stable 2.1.206. Untracked .claude/settings.local.json and added to .gitignore. Verified CVAT (non-MCP) workflow still works end-to-end via cvat_pull.py against task id=7.

## Last done
- Configured Claude Code sandbox with strict permissions (deny: sudo, git push --force; filesystem denyRead: ~/.ssh, ~/.aws/credentials, ~/.config/gcloud, **/.env)
- Set network allowedDomains to anthropic, github, npm, pypi, telegram
- Tested sandbox filesystem restrictions (child bash process got Permission denied on .env)
- Identified real Claude Code bug: latest channel (2.1.216) broke all bash execution due to nested userns/CAP_SYS_ADMIN crash
- Fixed by pinning Claude Code to stable version 2.1.206 in user settings.json
- Removed dangling .mcp.json reference (enabledMcpjsonServers:"cvat") from settings.local.json
- Untracked .claude/settings.local.json from git (git rm --cached) and added to .gitignore
- Verified CVAT non-MCP workflow: cvat_pull.py successfully pulled 11 labels from task id=7
- Drafted homework submission: project description, level breakdown (1–3 closed, 4 intentionally skipped), key security decisions

## Next
Optionally restore CVAT MCP server (.mcp.json, tracked in BACKLOG.md) — find/install an actual CVAT MCP package before recreating the config. Decide final sandbox.enabled value to ship in homework submission (true documents intent but doesn't run locally due to host nested-userns limitation; false is the actually-working state). Then resume eval pipeline: decide IoU threshold + false-positive scoring, implement freeze_eval_set.py / auto_ingest guard / run_eval.py.

## Blockers
None.

## Open questions
- Should homework submission ship with sandbox.enabled=true (intent) or false (actually-working)?
- Is there an existing CVAT MCP package to restore, or was the dangling .mcp.json a local experiment?

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
- Claude Code module-3 homework: Path A (from scratch, drone-recon is the real project). Levels 1–3 closed (permissions + sandbox + network). Level 4 (devcontainer) intentionally skipped (solo project, no onboarding need). .claude/settings.local.json untracked and gitignored.