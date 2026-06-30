# drone-recon — Incremental Active-Learning Loop (Concept)

Version: 0.1 | Status: Concept locked | Date: 2026-06-29
Owner: Sasha | Project: drone-recon
Doc language: English (per project convention). Chat: Ukrainian.

---

## Purpose of this document

Lock the *concept* for how we build a military-object detection dataset and model
with **minimum human time** and **maximum useful automation**. This is the "why" and
"shape". The step-by-step build plan for Sonnet CC is a separate document.

Core constraint from owner: **never spend a week labeling blind only to discover the
direction was wrong.** Work in short sessions (15-30 min of human time each), where
every session ends with a number that says "right direction / wrong direction".

---

## The honest framing (read this first)

There is **no fully-automatic labeling** that produces a combat-grade model without
human input on military objects. Confidence: ~90%. Public quality datasets for this
domain are scarce, and errors are costly. The real question is **not** "automate or not"
— it is **"where do we spend the scarce human minutes so each one teaches the model the
most".**

The answer is an **incremental active-learning loop**: the model itself tells you which
frames are worth your attention, and you only touch those.

---

## Taxonomy v0 (locked — context for this doc)

6 classes, IDs frozen (reordering breaks existing annotations):

| ID | Class | Meaning |
|----|-------|---------|
| 0 | `pidar` | person / soldier in field context |
| 1 | `military_vehicle` | heavy: tank, BMP, BTR, SPG, IFV |
| 2 | `vehicle` | light: pickup, quad, motorcycle, bukhanka |
| 3 | `fpv_drone` | drone visible in frame |
| 4 | `artillery` | guns, mortars, MLRS |
| 5 | `structure` | trench, shelter, fortified position |

---

## What we reuse from the past (and what we don't)

**Reuse:**
- `docs/drone-recon-SPEC_v001.md` — architecture context.
- `CV_Roadmap` (Drive) — direction, the "four phases / rule of three" working method.
- `docs/drone-recon-ml-pipeline-roadmap_v001.md` — Opus phase roadmap (Phase 0-5).
- Existing built pieces: TG scraper (`scraper/`, 5-stage), frame_extractor
  (`cv_toolkit/pipeline/frame_extractor.py`, scene-change mode, 916 frames extracted),
  taxonomy.yaml, cv_toolkit/ folder structure, MODEL_REGISTRY.md.

**Do NOT reuse (checked on Drive 2026-06-29):**
- The 2023 Colab `bmp/tank` experiment — YOLOv8 API is outdated vs YOLO11; only 2 classes.
- The `train/labels/` folder on Drive — it is the third-party "Construction Site Safety"
  Roboflow dataset (people, helmets, vests, excavators), NOT hand-labeled military frames.
  Wrong domain. Confidence this is correct: ~90%.
- Conclusion: there is **no salvageable hand-labeled military dataset** from the past.
  We seed fresh under the v0 taxonomy. The economic saving from old `bmp/tank` boxes
  would have been minimal anyway (re-mapping + re-verification needed regardless).

---

## The three techniques we combine (best of 1-3)

We are not picking one. We use each where it is strongest.

**Technique 1 — Pre-labeled public datasets as a foundation (confidence ~85%)**
Before labeling anything ourselves, pull what is already labeled (Roboflow Universe
military/drone-view sets, academic sets). Imperfect and not our taxonomy. Human work
here is **curation, not drawing**: filter junk, map foreign classes → our 6. Hours,
not weeks. Best for cold-starting classes that have public coverage (`vehicle`,
`structure`, partly `military_vehicle`).

**Technique 2 — Auto-labeling via open-vocabulary model + human verification (confidence ~65%)**
Run frames through a vocabulary-free detector (Grounding DINO / YOLO-World) driven by
text prompts ("tank", "antenna", "soldier"). It produces **draft boxes**. The human only
**accepts / edits / rejects** — reviewing a ready box is 2-3 s vs 15-20 s to draw from
scratch (5-7x human-time saving). Caveat: on small / camouflaged / domain-specific objects
(EW/REB, antennas, specific hardware) these models degrade hard — confidence drops to ~40%.
Good on `vehicle` / `structure`; doubtful on `pidar` / specialized gear. **This is exactly
what the first cycle must test empirically — do not trust it on faith.**

**Technique 3 — Active learning, the main weapon against pointless work (confidence ~80%)**
Do not label everything. Train on a small set → run model over a new pool →
**the model itself flags the frames where it is uncertain** (low confidence, conflicting
predictions) → human labels ONLY those. Frames the model is already confident on add
nothing — skip them. Mathematically reduces labeling volume by multiples at equal accuracy.
Human time goes where it actually moves the metric.

*(Technique 4 — self-training / pseudo-labeling — deferred. Risk of the model locking in
its own errors. Only after a decent baseline exists. Not now. Confidence ~55%.)*

---

## The loop (one cycle)

The human **never labels blind**. Each session is short and ends with a number.

1. **Seed (once, at start)** — ~50 frames from the TG stream. Auto-labeler (Technique 2)
   puts draft boxes under the 6 classes. Human accepts/edits/rejects in a simple UI in
   ~20 min. This is the only "from scratch" session.

2. **Train** — model fine-tunes on whatever exists (50 first, more later). Fast on the
   local RTX 3080 Ti.

3. **Metric** — model runs on a **frozen val/golden set**; output is per-class mAP.
   *This is the "right direction / wrong direction" signal.* If `vehicle` climbs but
   `pidar` is flat, you know exactly where the next session should go.

4. **Active learning (Technique 3)** — model runs over a fresh pool and **auto-selects
   the ~50 most useful frames** (uncertain / conflicting). Human fixes ONLY those.
   Everything else is left untouched.

5. → back to step 2. Each cycle: better model, and it selects what to show you more
   sharply than the last.

```
TG scraper ──> frame_extractor ──> auto-labeler (draft boxes)
                                          │
                                          ▼
            active-learning selector ─> ~50 most useful frames
                                          │
                                          ▼
                          human verify UI  (15-20 min)
                                          │
                                          ▼
                          train ──> mAP on frozen golden set
                                          │
                                   (signal: direction?)
                                          │
                                          └──> next cycle
```

---

## Why this matches the owner's requirements

- **First result after the very first session**, not after a week.
- Human work always goes where the marginal gain is highest (active learning), never
  "everything in a row".
- Every cycle produces a number → direction is visible → you can stop or change course
  at any cycle boundary.
- Techniques 1-3 combined: #1 (public datasets) for cold-starting covered classes;
  #2 (auto-label) for draft boxes; #3 (active learning) as the main dosing valve for
  human time.

---

## Where we are honestly NOT sure (must be verified in cycle 1, not believed)

- **Will the open-vocab model extract the specific classes** (`pidar`, EW/REB, antennas)?
  Near-certain yes on `vehicle`/`structure`. On specialized classes ~40%. Cycle 1 shows it.
- **How many cycles to a decent model** — unknown. Could be 5, could be 20. Depends on how
  clean the TG data is after filtering. Literature rough orientation: 300-500 quality
  instances per class to start, a few thousand for combat quality — but this is very rough
  (~50% confidence).
- **TG data quality** — propaganda, dupes, low-res, crops. How much survives filtering is
  unknown.
- **Legal/ethical framing** of real-conflict footage for a course project — owner's
  responsibility, not assessed here.

---

## Golden rule for the build

Every cycle must be **shippable and measurable on its own**. If a cycle does not end with
a per-class mAP delta on the frozen golden set, the cycle is malformed. Never let the
pipeline drift into "label more, measure later".

---

## Next artifact

`drone-recon-active-learning-PLAN_v001.md` — the step-by-step build plan for Sonnet CC:
module structure, build order, done-criteria per step, integration points into existing
`cv_toolkit/` + `scraper/`.
