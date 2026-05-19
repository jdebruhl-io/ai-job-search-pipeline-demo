"""
config.py — Central configuration for ai-job-search-pipeline
All paths, thresholds, and model settings live here.
Update this file when moving to a new machine or changing settings.
"""
import os

# ── Base paths ────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
SRC_DIR      = os.path.join(BASE_DIR, "src")
RESULTS_DIR  = os.path.join(BASE_DIR, "results")
LOGS_DIR     = os.path.join(BASE_DIR, "logs")
DATA_DIR     = os.path.join(BASE_DIR, "data")

# ── Results subdirectories ────────────────────────────────────
JOB_DATA_DIR     = os.path.join(RESULTS_DIR, "01.0_job_data")
JOB_REPORTS_DIR  = os.path.join(RESULTS_DIR, "02.0_job_reports")
RESUMES_DIR      = os.path.join(RESULTS_DIR, "03.0_resumes")
COVER_DIR        = os.path.join(RESULTS_DIR, "03.1_cover_letters")
DOC_MANIFEST_DIR = os.path.join(RESULTS_DIR, "03.2_doc_manifest")
DIGEST_DIR       = os.path.join(RESULTS_DIR, "04.0_digests")
INTERVIEW_DIR    = os.path.join(RESULTS_DIR, "interview_prep")

# ── Key files ─────────────────────────────────────────────────
TRACKER_FILE = os.path.join(RESULTS_DIR, "applications.json")
LOG_FILE     = os.path.join(LOGS_DIR, "scheduler.log")
PROFILE_PATH = os.path.join(DATA_DIR, "james_profile.md")

# ── LLM settings ─────────────────────────────────────────────
LLM_MODEL    = "ollama/qwen3:14b"
LLM_BASE_URL = "http://localhost:11434"

# ── Pipeline settings ─────────────────────────────────────────
SCORE_THRESHOLD  = float(os.environ.get("SCORE_THRESHOLD_OVERRIDE", "7.0"))
SCHEDULE_TIME    = "07:00"  # Daily run time (24hr format)

# ── Step timeouts (seconds) ───────────────────────────────────
SCOUT_TIMEOUT    = 120
ANALYZE_TIMEOUT  = 3600   # 1 hour
GENERATE_TIMEOUT = 7200   # 2 hours
DIGEST_TIMEOUT   = 60

# ── Candidate settings ────────────────────────────────────────
CANDIDATE_NAME     = "James T Debruhl"
CANDIDATE_LOCATION = "Jacksonville, FL"
TARGET_SALARY_MIN  = 100000
TARGET_SALARY_MAX  = 160000
PREVIOUS_RATE_HR   = 62

# ── Blocklist ─────────────────────────────────────────────────
# Companies to skip document generation for
# Format: ("match_term", "reason")
BLOCKLIST = [
    ("bridgewater",      "NY/CT hybrid required - not relocating"),
    ("naval facilities", "federal government - paused for now"),
    ("naval air",        "federal government - paused for now"),
    ("army national guard", "federal government - paused for now"),
    ("air national guard",  "federal government - paused for now"),
    ("federal aviation", "federal government - paused for now"),
    ("gls germany",      "German company - EUR salary, EU work authorization likely required"),
]

# ── Flask settings ────────────────────────────────────────────
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000
