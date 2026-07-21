# BACKLOG — drone-recon

## Restore CVAT MCP server config

`.mcp.json` (server `"cvat"`) is gone — it was gitignored, never committed, likely lost during the security cleanup / `git filter-repo` pass. No record of its `command`/`args` anywhere in the repo.

**Why:** `.claude/settings.local.json` had `enabledMcpjsonServers: ["cvat"]` pointing at this nonexistent file, which broke Claude Code's sandbox startup — `bwrap` tried to mount at a malformed fallback path `/home/.mcp.json` and crashed with `Permission denied`, blocking sandbox testing (Level 3 of the Claude Code Setup homework). Removed the dangling reference from `settings.local.json` for now (2026-07-21) to unblock sandbox.

**How to resume:** find/install an actual CVAT MCP server package (official or a custom wrapper) before recreating `.mcp.json`. The working non-MCP CVAT integration (`cv_toolkit/labeling/cvat_push.py`/`cvat_pull.py`, via `cvat_sdk`) uses `CVAT_HOST`/`CVAT_USER`/`CVAT_PASSWORD` env vars — reuse that as the likely env shape for the MCP server too.
