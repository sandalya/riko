# drone-recon — ML Pipeline Roadmap

**Project:** drone-recon — reconnaissance agent for analyzing drone video
**Goal:** fine-tune YOLO11n on military/tactical classes from FPV/recon drone footage, with maximum automation of data collection and labeling, and human-in-the-loop verification.
**Constraints:** single GPU or CPU server, limited resources, human verification required.
**Stack:** YOLO11n (COCO pretrained) + FastAPI detector + MCP Server + Claude Agent.

> Use this document as the source-of-truth context for CC or Claude Web prompts. Each phase is self-contained; paste the relevant phase as context when delegating a build step.

---

## Problems being solved

| # | Problem | Phase that addresses it |
|---|---------|-------------------------|
| 1 | Model doesn't know required classes (COCO-only) | Phase 0 (taxonomy) + Phase 5 (fine-tune) |
| 2 | No dataset collection pipeline | Phase 1 |
| 3 | Auto-labeling fails on new classes | Phase 2 (open-vocabulary detection) |
| 4 | No human verification UI | Phase 3 |
| 5 | Video quality (blur, artifacts, low-res) | Phase 1 (quality_filter) |
| 6 | Class imbalance | Phase 4 |
| 7 | No eval metrics (mAP, per-class P/R) | Phase 5 (do EARLY) |

---

## Phase 0 — Foundation (1–2 weeks)

**The most important decisions happen here. Do not skip to training.**

### 0.1 Define taxonomy — start SMALL

The classic trap: an ambitious taxonomy at the start kills the project, because every class needs hundreds-to-thousands of examples. Start with 6–8 classes max:

```
v0 classes (6–8 maximum):
- person            # already in COCO, transfer over
- military_vehicle  # broad class (tank/BMP/BTR all together)
- pickup_truck      # civilian/technical vehicle
- fpv_drone
- artillery         # optional
- structure         # trench / shelter / position
```

Merging `tank/BMP/BTR` into one `military_vehicle` is a deliberate compromise. Split later when there's data. Coarse taxonomy = cheaper labeling = faster first working cycle.

### 0.2 Eval-first: build the golden test set NOW

Before any training, hand-label a frozen golden test set:
- 100–200 frames, carefully manually labeled
- Frozen — never enters training
- This is the single objective measure of progress

Without it, every later phase is blind work.

### Phase 0 deliverables
- [ ] `taxonomy.yaml` (v0, 6–8 classes, class IDs locked)
- [ ] `golden_test/` — 100–200 hand-labeled frames, frozen
- [ ] Decision recorded: which classes are merged and why

---

## Phase 1 — Data collection pipeline (2–3 weeks)

Architecture — each stage is a separate step, NOT a monolith:

```
TG scraper → frame_extractor → quality_filter → auto_label → human_verify → yolo_export
```

### 1.1 frame_extractor

Do not take every frame. FPV video at 30fps → adjacent frames are near-identical (causes train/val leakage + wasted labeling). Sample:
- 1 frame / 1–2 sec, OR
- scene-change detection (histogram/SSIM diff between frames > threshold)

### 1.2 quality_filter (solves Problem #5)

Auto-reject garbage BEFORE labeling:
- **Blur:** variance of Laplacian < threshold → drop (fast motion)
- **Contrast:** std-dev of brightness
- Analog-signal artifacts are harder — start with blur+contrast, covers ~80%

> Do NOT filter out ALL noise — the model must see realistic FPV noise, otherwise it fails in production. Filter only the unreadable.

### Phase 1 deliverables
- [ ] `frame_extractor.py` (scene-change or interval sampling)
- [ ] `quality_filter.py` (Laplacian blur + contrast thresholds, configurable)
- [ ] Pipeline runs end-to-end on one batch of scraped video → folder of candidate frames

---

## Phase 2 — Auto-labeling (Problem #3 — the key problem)

YOLO11n-COCO is useless for new classes — correct. The approach is **open-vocabulary detection** to bootstrap.

### 2.1 Grounding DINO

Text-prompt detection ("military vehicle", "drone", "soldier"). No training needed, works zero-shot. Sufficient for bbox.

### 2.2 + SAM2 (optional)

If precise masks/bbox needed: Grounding DINO gives rough bbox → SAM2 refines. For bbox-only YOLO, SAM2 can be skipped initially.

### 2.3 Confidence routing

```
Frame → Grounding DINO (text prompts) → bbox + confidence
  ├─ conf > 0.5  → auto-accept (fast verification queue)
  ├─ 0.25–0.5    → human review (full verification)
  └─ conf < 0.25 → discard or manual labeling
```

### 2.4 Resource reality

Grounding DINO on CPU is very slow. Realistic options:
- **Batch overnight** on your GPU (one pass over each new batch of video)
- **Rented GPU hourly** (Vast.ai / RunPod) for auto-labeling only — a few dollars per batch
- **LLM-with-vision** (Claude / GPT-4V) — expensive at scale, but good for complex/rare classes where Grounding DINO struggles. Use selectively, not on the whole dataset.

### Phase 2 deliverables
- [ ] `auto_label.py` (Grounding DINO wrapper, text-prompt config per class)
- [ ] Confidence-routing logic → 3 queues (auto-accept / review / discard)
- [ ] Decision recorded: where auto-labeling runs (local GPU / rented / hybrid)

---

## Phase 3 — Human verification (Problem #4)

Do not write a UI from scratch — use ready tools.

### 3.1 Label Studio (recommended)

Open-source, self-hosted. The smartest choice:
- Import pre-annotations from Grounding DINO; human only corrects
- Native YOLO export
- Run on the server, review via browser

Alternative if you want more control: **CVAT**, but heavier.

### 3.2 Telegram verification bot

Tempting (fits your ecosystem), BUT: bbox correction in Telegram is awkward. Telegram is only good for binary "correct/incorrect" (accept/reject whole frame), not for drawing boxes.

**Hybrid approach:**
- **TG-bot:** fast triage (accept/reject) for high-conf auto-labels — Ksyu swipes on phone
- **Label Studio:** precise correction for hard frames

This respects the "work for a real user" principle — fast triage scales, full labeling only where needed.

### Phase 3 deliverables
- [ ] Label Studio running on server, YOLO import/export wired
- [ ] (Optional) TG triage bot: accept/reject for high-conf queue
- [ ] Verified frames → clean YOLO-format dataset

---

## Phase 4 — Class balance (Problem #6)

`person` will dominate; `fpv_drone`/`structure` will be rare. Strategies by priority:

1. **Targeted collection** — don't balance artificially first; deliberately hunt video with rare classes (FPV/drone TG channels). The most honest method.
2. **Oversampling rare classes** — Ultralytics supports class weights / image repetition for images with rare classes.
3. **Copy-paste augmentation** — paste cut-out rare objects onto new backgrounds. Works for drones against sky.
4. **Loss weighting** — less reliable for detection than classification, but available.

> Don't chase perfect balance — the real combat distribution is also imbalanced. Target: enough examples for the class to be learned (minimum ~200–300 instances per class for a decent start), not 50/50.

### Phase 4 deliverables
- [ ] Per-class instance counts tracked (dashboard or simple script)
- [ ] Oversampling / copy-paste config for rare classes
- [ ] Targeted-collection list: which TG channels feed which rare classes

---

## Phase 5 — Eval (Problem #7 — do EARLY, not at the end)

Your pytest regression tests are infrastructure, not a quality metric. Add real ML metrics.

### 5.1 Per-class metrics on the frozen golden set

```
- mAP@50, mAP@50-95 (overall + per class)
- precision/recall per class separately
- confusion matrix (what gets confused with what)
```

Ultralytics produces this out of the box (`model.val()` on your val split).

### 5.2 Model registry

- Frozen golden test set never enters training
- Each model version → one row in a comparison table (version, mAP, per-class recall, date)
- Integrate into the memory system: `MODEL_REGISTRY.md` with version history

This gives an objective "v3 > v2" instead of gut feeling.

### Phase 5 deliverables
- [ ] `eval.py` (Ultralytics val on golden set, per-class output)
- [ ] `MODEL_REGISTRY.md` (version, mAP@50, mAP@50-95, per-class recall, date)
- [ ] First baseline number recorded (even if bad)

---

## The loop that ties it all together

**Active learning cycle:**

```
1. Train model on current dataset
2. Run on NEW video
3. Frames where the model is UNCERTAIN (conf ~0.3–0.6) → priority for human labeling
4. Labeled → into dataset → retrain
5. Eval on golden set → register version
```

This is maximum automation: the model itself indicates what to label next (uncertainty sampling). The human doesn't review thousands of easy frames — only the hard ones. Each cycle the model improves, and its own auto-labeling gets more accurate, reducing manual work.

---

## Realistic execution order (as a course project)

1. **Taxonomy v0 (6 classes) + golden test set — week one, most important**
2. frame_extractor + quality_filter — simple, immediate result
3. Grounding DINO auto-labeling on one batch of video
4. Label Studio + manual verification → first 500–1000 frames
5. First YOLO11n fine-tune → eval on golden → baseline number
6. Active learning loop

### Biggest risk

Getting stuck in infrastructure (yet another scraper, yet another pipeline step) instead of getting the first mAP number. The "work for work's sake" anti-pattern is real here — the goal of the first month is *one trained model with measured quality*, even bad quality. **A bad metric beats no metric.**

---

## Suggested repo structure (cv_toolkit/)

```
cv_toolkit/
├── taxonomy.yaml              # class definitions, locked IDs
├── pipeline/
│   ├── frame_extractor.py     # Phase 1
│   ├── quality_filter.py      # Phase 1
│   ├── auto_label.py          # Phase 2 (Grounding DINO)
│   └── yolo_export.py         # Phase 3 → YOLO format
├── eval/
│   ├── eval.py                # Phase 5 (Ultralytics val)
│   └── MODEL_REGISTRY.md      # version history
├── golden_test/               # frozen, never trained on
├── datasets/
│   ├── raw_frames/
│   ├── review_queue/
│   └── verified/
└── configs/
    ├── grounding_dino.yaml    # text prompts per class
    └── train.yaml             # YOLO11n fine-tune config
```
