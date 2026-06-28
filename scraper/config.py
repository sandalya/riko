CHANNELS = ["escadrone", "DPSUkr", "voyna18", "ssternenko"]
PRIORITY = {"escadrone": 3, "DPSUkr": 2, "voyna18": 2, "ssternenko": 1}

# Download filters
MIN_SIZE_MB = 1.0
MAX_SIZE_MB = 50.0
MIN_DURATION_SEC = 3
MAX_DURATION_SEC = 120

# Quality filters
BLUR_THRESHOLD = 100.0      # Laplacian variance — below = blurry
BRIGHTNESS_MIN = 20         # too dark
BRIGHTNESS_MAX = 235        # too bright/overexposed

# Haiku filter
HAIKU_MODEL = "claude-haiku-4-5-20251001"
HAIKU_PROMPT = """Look at this frame from a video. Does it show any of the following:
- military vehicle (truck, APC, tank, car in field/road)
- person in military/field context
- drone footage (aerial view, top-down or oblique)
- explosion or strike

Answer with exactly one word: yes, no, or unsure."""

# Paths (relative to project root)
RAW_DIR      = "data/scraper/raw"
APPROVED_DIR = "data/scraper/approved"
REJECTED_DIR = "data/scraper/rejected"
REVIEW_DIR   = "data/scraper/review"
HASHES_FILE  = "data/scraper/hashes.json"
SESSION_FILE = "data/scraper/tg_session"
