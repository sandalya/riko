# CLAUDE.md — drone-recon

## Rules

1. **Language**: Always respond to the user in Ukrainian. Code and documentation must be written in English.

---

## Project Context

Drone reconnaissance agent. CV + agentic pipeline.  
Full spec: `docs/drone-recon-SPEC_v001.md`

**Vision:** Replace manual video review with an AI agent that detects, localizes, and analyzes objects of interest autonomously.

---

## Architecture — Three Blocks

```
[Input: video + GPS log]
         ↓
  [Detector Service]  ←── YOLO model (swappable via detector/config.py)
         ↓
   [MCP Server]       ←── tools: detect, analyze_video, parse_gps, correlate
         ↓
  [Claude Agent]      ←── system prompt: recon analyst
         ↓
  [Output: report]    ←── objects + timestamps + coordinates + threat level
```

Each block is independently replaceable.

### Block 1 — Detector Service (`detector/`)
- FastAPI service. Accepts image/video path, returns JSON detections.
- Default model: `yolo11n.pt` (COCO). Future: custom military/tactical model.
- Endpoints: `POST /detect`, `POST /detect_video`

### Block 2 — MCP Server (`mcp/`)
- Bridge between Detector and Claude Agent.
- Tools: `detect_objects`, `analyze_video`, `parse_gps_log`, `correlate_detections_gps`

### Block 3 — Claude Agent (`agent/`)
- Reasoning layer. Calls detector tools, cross-references GPS, generates report.
- System prompt role: recon analyst. Output: structured table + threat levels.

---

## Geolocation Levels

- **Level 1 (PoC)** — GPS timestamp correlation: frame_time → GPX log → coordinates
- **Level 2 (future)** — Visual georeferencing: altitude + camera angle + FOV
- **Level 3 (future)** — Full GIS, map overlay, multi-flight clustering

**Current target: Level 1 only.**

---

## File Structure

```
drone-recon/
├── CLAUDE.md               ← CC instructions
├── docs/
│   └── drone-recon-SPEC_v001.md
├── logs/
│   ├── session.md          ← append-only action log
│   └── errors.md
├── detector/
│   ├── main.py             ← FastAPI app
│   ├── config.py           ← MODEL_PATH lives here
│   └── models/             ← .pt model files
├── mcp/
│   ├── server.py
│   └── tools/
├── agent/
│   ├── prompts/
│   └── main.py
├── bot/
│   └── client.py           ← Telegram receiver (DONE)
├── data/
│   ├── input/              ← raw video and images
│   ├── output/             ← generated reports
│   └── gps/                ← GPX logs
└── tests/
```

---

## Logging Rule (MANDATORY)

After every significant action, append to `logs/session.md`:

```
### [YYYY-MM-DD HH:MM] Action: <what>
- Why: <reason>
- Result: <outcome>
- Next: <next step>
```

Never delete from `logs/session.md`. Append only.

---

## Git Discipline

Commit after every logical unit of work.  
Format: `[block] short description`  
Examples: `[detector] add video endpoint`, `[mcp] add gps parse tool`, `[agent] add report template`

---

## Model Swapping

The YOLO model path is always in `detector/config.py` → `MODEL_PATH`.  
Never hardcode model paths elsewhere.  
Swap `yolo11n.pt` → `military_v2.pt` by changing only `config.py`.

---

## Token / Cost Notes

- Keep all docs and prompts in English (Cyrillic ~1.5–2x more tokens)
- Use YOLO nano model for development (fast, low resource)
- Switch to larger model only when accuracy becomes bottleneck
