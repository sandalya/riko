# Drone Recon Agent — Project SPEC
> Version: 0.1 | Status: Planning
> Last updated: 2026-06-27

---

## Vision

An agentic system that processes drone footage (video/images + GPS logs),
runs object detection, and generates structured tactical reconnaissance reports.

**Core value:** Replace manual video review with an AI agent that detects,
localizes, and analyzes objects of interest autonomously.

---

## Architecture Overview

```
[Input: video + GPS log]
         ↓
  [Detector Service]  ←── YOLO model (swappable)
         ↓
   [MCP Server]       ←── tools: detect, analyze_video, parse_gps
         ↓
  [Claude Agent]      ←── system prompt: recon analyst
         ↓
  [Output: report]    ←── objects + timestamps + coordinates + threat level
```

Each block is independently replaceable. The model inside Detector Service
can be swapped without touching anything else.

---

## Block 1 — Detector Service

**What it is:** Isolated FastAPI service. Accepts image path or video path,
returns JSON with detections.

**Key principle:** The model is a black box behind an HTTP interface.
Swap `yolo11n.pt` → `military_v2.pt` without changing anything else.

**Default model:** `yolo11n.pt` (COCO pretrained — person, car, truck, bus)
**Future model:** Custom fine-tuned on military/tactical classes

**Endpoint:**
```
POST /detect
Body: { "image_path": "string" }
Returns: { "detections": [{ "class", "confidence", "bbox", "frame_time" }] }

POST /detect_video  
Body: { "video_path": "string", "every_n_frames": 30 }
Returns: { "timeline": [{ "frame_time", "detections": [...] }] }
```

**Stack:** Python, FastAPI, Ultralytics YOLO11

---

## Block 2 — MCP Server

**What it is:** Bridge between Detector Service and Claude Agent.
Exposes detector capabilities as Claude tools.

**Tools exposed:**
- `detect_objects(image_path)` → single image detection
- `analyze_video(video_path, every_n_frames)` → full video timeline
- `parse_gps_log(gpx_path)` → returns list of `{timestamp, lat, lon, alt}`
- `correlate_detections_gps(timeline, gps_log)` → matches detections to coordinates

**Stack:** Python, MCP SDK (same pattern as Houdini MCP)

---

## Block 3 — Claude Agent

**What it is:** The reasoning layer. Decides what to analyze, how, and
generates the final report.

**System prompt role:** Recon analyst. Structured output. Threat assessment.

**Agent capabilities:**
- Call detector multiple times (compare frames, track object across time)
- Notice dynamics (object appeared then disappeared = suspicious)
- Cross-reference with GPS data for coordinates
- Generate structured report with threat levels

**Output format (report):**
```
## Recon Report — [mission_id] — [timestamp]

### Detected Objects
| Time | Object | Confidence | Coordinates | Threat |
|------|--------|------------|-------------|--------|
| 3:56 | vehicle/truck | 0.87 | 48.123, 37.456 | MEDIUM |

### Analysis
[Claude's reasoning about the scene]

### Recommendations
[Actionable items]
```

---

## Geolocation Strategy

**Level 1 (MVP) — GPS timestamp correlation:**
- Drone flight controller writes GPX log (Betaflight/ArduPilot)
- Detection at frame_time → lookup GPS log → get coordinates
- Relatively simple, very useful

**Level 2 (future) — Visual georeferencing:**
- No GPS required
- Uses: altitude + camera angle + FOV → calculate object position
- Needs calibrated drone data

**Level 3 (future) — Full GIS:**
- Map overlay, clustering across multiple flights
- Separate product scope

**For PoC: Level 1 only.**

---

## On-Device (Edge) Processing — Future Consideration

**Lightweight path (realistic):**
- YOLO runs on-board (Raspberry Pi 5 or Jetson Nano)
- Only bbox JSON streamed via radio link (much less bandwidth than video)
- Claude Agent analyzes stream on ground station in near-realtime

**Heavy path (later):**
- Full agent on Jetson Orin
- Different budget/weight class

**Not a first feature.**

---

## File Structure

```
drone-recon/
├── CLAUDE.md               ← CC instructions + logging rules
├── SPEC.md                 ← this file
├── logs/
│   ├── session.md          ← CC appends actions here (append only)
│   └── errors.md           ← errors and resolutions
├── detector/
│   ├── main.py             ← FastAPI app
│   ├── models/             ← .pt model files
│   └── requirements.txt
├── mcp/
│   ├── server.py           ← MCP server
│   └── tools/              ← individual tool implementations
├── agent/
│   ├── prompts/            ← system prompts
│   └── main.py
├── data/
│   ├── input/              ← raw video and images
│   ├── output/             ← generated reports
│   └── gps/                ← GPX logs
└── tests/
```

---

## CLAUDE.md Rules (to be placed in project root)

```markdown
# drone-recon — Claude Code Instructions

## Project context
Drone reconnaissance agent. CV + agentic pipeline.
See SPEC.md for full architecture.

## Logging rule (MANDATORY)
After every significant action, append to logs/session.md:
```
### [YYYY-MM-DD HH:MM] Action: <what>
- Why: <reason>
- Result: <outcome>
- Next: <next step>
```
Never delete from logs/session.md. Append only.

## Git discipline
Commit after every logical unit of work.
Commit message format: `[block] short description`
Examples: `[detector] add video endpoint`, `[mcp] add gps parse tool`

## Model swapping
The YOLO model path is always in detector/config.py → MODEL_PATH.
Never hardcode model paths elsewhere.

## Language
Code and comments: English.
Log entries: English.
```

---

## Phased Development Plan

### Phase 0 — Before course (now)
- [ ] Create folder structure
- [ ] Detector Service with default YOLO11n
- [ ] Basic `/detect` endpoint working on test image
- [ ] Git initialized, CLAUDE.md in place

### Phase 1 — Course Module 1-2
- [ ] CLAUDE.md refined with course learnings
- [ ] CC configured and working with project

### Phase 2 — Course Module 6 (MCP)
- [ ] MCP Server wrapping Detector
- [ ] All 4 tools implemented and tested

### Phase 3 — Course Module 8 (Agents)
- [ ] Claude Agent orchestrating full pipeline
- [ ] Report generation working end-to-end

### Phase 4 — Course Module 9 (Production)
- [ ] Web interface or Telegram bot
- [ ] GPS correlation (Level 1)
- [ ] Deploy (VPS or ngrok over Beelink)

---

## Token / Cost Notes

- Keep all docs and prompts in English (Cyrillic ~1.5-2x more tokens)
- Use YOLO nano model for development (fast inference, low resource)
- Switch to larger model only when accuracy becomes bottleneck

---

## Open Questions

- [ ] Which drone FC will provide GPS logs? (Betaflight/ArduPilot/other)
- [ ] What are the target detection classes for fine-tuned model?
- [ ] Telegram bot or web UI for final output?
- [ ] VPS provider or keep on Beelink + tunnel?
