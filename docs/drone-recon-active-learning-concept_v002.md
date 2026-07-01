# drone-recon — Incremental Active-Learning Loop (Build Plan)

Version: 0.1 | Status: Ready for CC | Date: 2026-07-01
Companion to: `drone-recon-active-learning-concept_v001.md` (read that first for the "why")
Target executor: Claude Code (Sonnet) | Owner: Sasha | Project: drone-recon (Ríko)
Doc language: English (project convention). Chat: Ukrainian.

---

## How to use this document (CC, read first)

- This is the step-by-step build plan for the concept locked in
  `drone-recon-active-learning-concept_v001.md`. The concept holds the rationale and the
  honesty about confidence levels — do not re-litigate it here, just build it.
- Build **phase by phase**. Each phase has an **exit criterion**. Do NOT start a phase
  until the previous phase's exit criterion is met and confirmed by the owner.
- **Golden rule (inherited from concept):** every phase ends with something shippable and
  measurable. If a phase cannot end with a demonstrable artifact or a number, it is
  malformed — stop and flag, do not drift into "build more, measure later".
- **Anti-scope — do NOT build (this is the "work for work's sake" trap):**
  - a custom labeling UI (CVAT is the UI),
  - CVAT Nuclio / serverless model integration (we auto-label offline, not inside CVAT),
  - self-training / pseudo-labeling (deferred until a real baseline exists).
  If you feel the pull to build any of these, flag it to the owner instead.
- **Always ask the owner before:** installing heavy infra, any change to a prod service,
  launching a long GPU job.
- Update `MODEL_REGISTRY.md` after every trained model. Keep all docs in English.
  Each phase exit is a natural `chkp` milestone.

---

## Machine topology (LOCKED)

| Box | Role |
|-----|------|
| **Beelink SER5** (`sashok-SER`, `192.168.72.191`, always-on) | The durable **data home** and the **CVAT self-hosted** review server. Also hosts the scraper and other always-on Ríko services. CPU-only — the CVAT community UI runs fine because we do **not** run models on this box (no Nuclio). Raw scraped video and the master dataset backup live here, so nothing is lost when the workstation is off. |
| **GPU workstation (RTX 3080 Ti)** — on-demand, available whenever a cycle is run | All GPU-heavy steps: triage, frame extraction, auto-labeling (Grounding DINO / YOLO-World / Florence-2), active-learning inference, and training. Holds the **working copy** of the dataset during a session (local disk = fast training I/O). |

### Data transport (LOCKED — no branches)

Everything moves over the **LAN**; nothing touches the cloud (privacy + one less moving part).
Two transports, each with one clear job:

1. **CVAT REST API — the review round-trip.** The `cvat_push` / `cvat_pull` modules (0.3 / 0.4)
   already talk to CVAT over its API: they upload frames + draft boxes into a task and download
   reviewed YOLO labels back. CVAT ingests its own copy of the images, so review works in the
   browser even when the workstation is off. **No filesystem share is needed for the label
   round-trip — it is already handled by these modules.**
2. **`rsync` over SSH — bulk media between the two boxes.** Reuses the existing SSH setup: no
   new service, no persistent mount that can drop mid-training.
   - **Session start:** workstation pulls the videos/frames it needs from Beelink.
   - **Session end:** workstation pushes the updated dataset (frames + reviewed labels +
     weights) back to Beelink as the durable backup.

**Authority rule (prevents stale copies):** Beelink is authoritative for raw video and is the
backup of record; the workstation is authoritative for the dataset **only during an active
session**. Flow is one-directional at each stage, so there is never a merge conflict as long as
you do not label on both boxes at once (you won't). `run_cycle` (2.3) wraps the pull at the
start and the push-back at the end.

### Known port conflict

`:8080` on Beelink is **web VSCode (code-server)** —
`http://192.168.72.191:8080/?folder=/home/sashok`. CVAT's default nginx also wants `:8080`.
Install CVAT on **`:8081`**.

---

## Taxonomy v0 (LOCKED — IDs frozen, never reorder; reordering breaks all annotations)

| ID | Class | Meaning |
|----|-------|---------|
| 0 | `pidar` | person / soldier in field context |
| 1 | `military_vehicle` | heavy: tank, BMP, BTR, SPG, IFV |
| 2 | `vehicle` | light: pickup, quad, motorcycle, bukhanka |
| 3 | `fpv_drone` | drone visible in frame |
| 4 | `artillery` | guns, mortars, MLRS |
| 5 | `structure` | trench, shelter, fortified position |

`vehicle`, `military_vehicle`, `structure` = **easy classes** (open-vocab covers them well).
`pidar`, `fpv_drone` (in flight), `artillery` = **hard classes** — enter the loop LATER.

---

## The seam (core architecture decision — internalize this)

CVAT does **not** detect anything live. Boxes are computed **offline** by our own
auto-labeler, exported to COCO, and **imported** into a CVAT task. CVAT is purely the
review + edit surface. This is what makes the "yes / no / fix" cycle real rather than
magic: the boxes are already on the frames before the human opens the task.

Two supported import paths (both without Nuclio — prefer whichever keeps our existing
auto-labeler as the source of truth):
1. **Upload annotations** — push a COCO / CVAT-XML / YOLO file onto an existing task.
2. **CVAT CLI/SDK** — `cvat-cli auto-annotate <task_id> --function-file <model.py>`.

Label matching (open-vocab class name → our 6 taxonomy IDs) is configured **once** at the
CVAT project level (e.g. model's `car` → task's `vehicle`).

**Round-trip:** frames + draft boxes → CVAT task → human review → export YOLO → train.

Use exact install/CLI commands from the current official CVAT docs at build time — do not
hardcode from memory, versions drift.

---

## Phase 0 — CVAT up + one video end-to-end (prove the seam)

Goal: eliminate all doubt that pre-annotated review is real. **No training, no triage.**
One video, full round-trip. This phase is the PoC of the loop *mechanics*, not the model.

### 0.1 Install CVAT self-hosted on Beelink
- Follow current official self-hosted (community) install (Docker Compose).
- **Check Beelink resource headroom first** (CVAT stack = postgres + redis + server + ui)
  against the existing Ríko services; report before proceeding.
- Put CVAT on **`:8081`** (`:8080` is web VSCode / code-server).
- Create Project `drone-recon` with the **6 labels in frozen taxonomy order**. One admin user.
- **Done:** CVAT reachable on LAN at the chosen port; project exists with exactly 6 labels
  in the correct order; admin login works.

### 0.2 Auto-labeler → COCO exporter (taxonomy-mapped)
- New module: `cv_toolkit/labeling/coco_export.py`.
- Input: existing auto-labeler raw output (open-vocab boxes + scores + prompt-derived label).
- Output: valid COCO JSON whose `categories` are exactly the 6 taxonomy classes/IDs.
- Mapping table (open-vocab label → taxonomy ID) lives in config (`taxonomy.yaml` or a new
  `label_mapping.yaml`). Unmatched labels are **dropped** for now (logged, not "unknown").
- **Done:** COCO file validates; category IDs == taxonomy IDs; unit test on a ~5-frame fixture.

### 0.3 CVAT ingestion bridge
- New module: `cv_toolkit/labeling/cvat_push.py` using `cvat-sdk`.
- Creates a task under project `drone-recon`, uploads frame images + the 0.2 COCO file.
- **Done:** `python -m cv_toolkit.labeling.cvat_push --frames <dir> --coco <file>
  --task-name cycle0` creates a task; opening it in the browser shows **pre-placed boxes
  on the correct frames**.

### 0.4 Review + export round-trip
- New module: `cv_toolkit/labeling/cvat_pull.py` — pull reviewed annotations back as YOLO
  (Ultralytics format) into a local `labels/` dir.
- **Done:** reviewed labels on disk in YOLO format; a box edited in CVAT shows changed
  coords in the export (round-trip proven).

**Phase 0 exit:** owner runs one real TG video through 0.2 → 0.4 and confirms (a) draft
boxes appeared pre-placed in CVAT, (b) the YOLO export is valid. The "is this real?"
question is answered by holding the artifact.

---

## Phase 1 — Golden set + first train + first mAP

Goal: the first honest direction signal.

### 1.1 Hand-label frozen golden/val set
- ~100–150 frames spanning the **easy classes** (`vehicle`, `military_vehicle`, `structure`).
- Labeled **from scratch by the human in CVAT** — this is the single from-scratch session
  and the one place auto-labeling is forbidden.
- Freeze: copy to an immutable, versioned `golden/` dir. **Never mixed into the train pool.**
- **Done:** `golden/` with images + YOLO labels; per-class instance counts documented.

### 1.2 Training harness (YOLO11n fine-tune) — GPU box
- New: `train/train.py`. Fine-tune YOLO11n from the reviewed seed (~50 frames from Phase 0).
- Reuse the config from the existing FastAPI YOLO11n detector service where possible.
- Log the run (weights path, config, git SHA) to `MODEL_REGISTRY.md`.
- **Done:** trained weights file + registry entry.

### 1.3 Eval harness — per-class mAP on frozen golden
- Extend the existing pytest eval framework (28 tests): new `tests/eval/test_golden_map.py`
  (or a CLI) computing **per-class mAP (mAP50 and mAP50-95)** against `golden/`.
- Store the per-model result in `MODEL_REGISTRY.md`.
- **Done:** running it prints a per-class mAP table; the number is recorded.

**Phase 1 exit:** a first per-class mAP number exists on the frozen golden set. The loop
now has a "right direction / wrong direction" signal.

---

## Phase 2 — Close the active-learning loop

Goal: one command drives a full cycle; each cycle produces a per-class mAP delta.

### 2.1 Active-learning selector (uncertainty)
- New: `cv_toolkit/active/selector.py`.
- Run the current model over a fresh unlabeled pool (batch inference on GPU box; reuse the
  detector service). Score each frame's **uncertainty** (e.g. low mean/margin box
  confidence, count of low-confidence boxes, class conflicts). Rank; select top-N (~50).
- **Done:** selector emits a ranked frame list + scores; unit test on a fixture.

### 2.2 Wire selector → auto-label → CVAT (reuse 0.2 / 0.3)
- Chain: selected frames → draft boxes (0.2) → review-ready CVAT task (0.3).
- **Done:** one command produces a CVAT task containing the N most-useful frames, pre-boxed.

### 2.3 Cycle runner + per-cycle mAP delta
- New: `cv_toolkit/active/run_cycle.py` (runs on the GPU workstation). Orchestrates:
  **rsync-pull data from Beelink** → select → auto-label → push to CVAT →
  **[pause for human review]** → pull reviewed labels (CVAT API) → train → eval →
  log **Δ per-class mAP** vs the previous model → **rsync-push updated dataset + weights
  back to Beelink**.
- **Done:** `run_cycle --pool <dir>` runs the automated portions, pauses at the human review
  gate, resumes on pull, ends with a Δ mAP logged to the registry, and leaves a fresh backup
  on Beelink.

**Phase 2 exit:** a single command runs a full cycle end-to-end; every cycle logs a
per-class mAP delta. The loop — not any single model — is the deliverable.

---

## Phase 3 — Video-triage (upstream gate) — ONLY after Phase 2

Goal: stop feeding junk videos into `frame_extractor`. This is the layer missing from the
concept — a coarse gate that decides *which videos deserve extraction at all*, distinct
from the frame-level active-learning selection (which decides *which frames to review*).

### 3.1 Whole-video perceptual-hash dedup
- New: `cv_toolkit/triage/video_dedup.py`. Aggregate a sampled-frame perceptual hash per
  video; flag near-duplicate videos across the pool (TG is full of re-uploads).
- **Done:** dedup report; duplicate videos skipped before extraction.

### 3.2 Object-density scorer (sparse sample)
- New: `cv_toolkit/triage/density.py`. Sparse-sample each video (every Nth frame), run the
  detector, compute the fraction of sampled frames containing ≥1 taxonomy class above a
  confidence threshold. Videos below threshold **skip** `frame_extractor`.
- **Done:** per-video density score; gate wired **before**
  `cv_toolkit/pipeline/frame_extractor.py`; measure and log the junk-cut %.

### 3.3 (Optional) Local VLM relevance classifier
- New: `cv_toolkit/triage/vlm_relevance.py` using Florence-2 or Moondream2.
- Per-clip semantic yes/no ("contains ground military objects / FPV POV") — catches cases
  density misses (e.g. a museum tank, or a talking-head with a distant vehicle). Run on the
  GPU box; Beelink CPU is too slow for throughput here.
- **Done:** a relevance flag per video + a short comparison note vs density-only.

### 3.4 Channel prior in scraper queue
- Prioritize/weight the scraper queue by channel signal (e.g. `@escadrone` high).
- **Done:** queue orders by channel prior.

**Phase 3 exit:** `frame_extractor` receives only above-threshold videos; junk-cut %
measured and logged.

---

## Phase 4 — Evolution (deferred, per-cycle experiments — not a blocking phase)

- **Cycle-1 empirical test (from the concept, do not skip):** run Florence-2 vs
  Grounding DINO on the **same 50 seed frames**; count human edits per model. Fewer edits =
  the better pre-labeler for this domain. This settles empirically whether open-vocab
  extracts the hard classes, rather than trusting it on faith.
- **Cycle ~3–5:** once our own model is decent, swap it in as the pre-labeler in place of
  Grounding DINO — boxes arrive already in our taxonomy, so fewer edits per frame. This is
  **not** self-training: the human still verifies every selected frame.
- **Hard classes** (`pidar`, `fpv_drone` in flight, `artillery`) enter the loop only after
  the easy classes are stable on the golden set. Active learning will naturally surface
  hard-class frames as "uncertain", steering human minutes there without manual planning.

---

## Module map (integration with existing code)

**Existing → role in this plan**
- `scraper/` (5-stage) — source videos; Phase 3 triage sits at its output.
- `cv_toolkit/pipeline/frame_extractor.py` (scene-change) — frames; gated by Phase 3.
- existing auto-labeler (Grounding DINO / YOLO-World) — gets the 0.2 COCO exporter.
- `taxonomy.yaml` — the 6-class source of truth + label-mapping base.
- FastAPI YOLO11n detector service — the detector reused for density (3.2) and
  active-learning inference (2.1).
- MCP server / Ríko bot — unchanged; downstream consumer of the final model.
- pytest eval framework (28 tests) — extended by 1.3.
- `MODEL_REGISTRY.md` — per-model mAP log.

**New modules**
- `cv_toolkit/labeling/coco_export.py` (0.2)
- `cv_toolkit/labeling/cvat_push.py` (0.3)
- `cv_toolkit/labeling/cvat_pull.py` (0.4)
- `cv_toolkit/active/selector.py` (2.1)
- `cv_toolkit/active/run_cycle.py` (2.3)
- `cv_toolkit/triage/video_dedup.py` (3.1)
- `cv_toolkit/triage/density.py` (3.2)
- `cv_toolkit/triage/vlm_relevance.py` (3.3, optional)
- `train/train.py` (1.2)
- `tests/eval/test_golden_map.py` (1.3)

---

## Interfaces / data contracts (keep stable across the pipeline)

- **Frame ID:** `<video_id>_<frame_idx>`, stable across extract → label → train → eval.
- **COCO categories:** exactly the 6 taxonomy IDs/names, frozen order.
- **YOLO export:** class indices == taxonomy IDs (no re-mapping downstream).
- **Golden set:** immutable, versioned, never mixed into the train pool.

---

## Known unknowns (verify empirically — do not trust on faith)

- Does open-vocab actually extract `pidar` / specialized gear? ~40% confidence.
  → settled by the Phase 4 cycle-1 test; active learning surfaces these frames regardless.
- Cycles to a decent model: unknown (5–20). → the per-cycle mAP delta tells you live.
- TG data quality after filtering: unknown. → Phase 3 measures the junk-cut %.
- Beelink resource headroom for CVAT alongside Ríko services. → verify at 0.1.
- Legal/ethical framing of real-conflict footage for a course project — owner's call,
  out of scope for this plan.
