# AI Job Search Pipeline

> **Demo Repository** — This is a cleaned, public demonstration version of a production system.
> Personal data, application history, and candidate-specific configuration have been replaced
> with example placeholders. The full production system runs privately.

An autonomous multi-agent job search system that runs locally at zero API cost.
Scouts job boards daily, scores every posting against your profile using a local LLM,
generates tailored resumes and cover letters for high-scoring jobs, and delivers a
morning digest — all without manual intervention.

## How It Works

```
Windows Task Scheduler (7:00 AM daily)
    └── scheduler.py (orchestrator)
         ├── Step 1: src/scout.py       — scrape job boards → 01.0_job_data/
         ├── Step 2: src/analyze.py     — score all jobs    → 02.0_job_reports/
         ├── Step 3: src/generate_docs.py — generate docs for top scorers
         │           ├── src/tailor.py  → 03.0_resumes/
         │           ├── src/cover.py   → 03.1_cover_letters/
         │           └── manifest       → 03.2_doc_manifest/
         └── Step 4: src/digest.py      — daily summary     → 04.0_digests/
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language model | Ollama / qwen3:14b (local) |
| Agent orchestration | CrewAI |
| Automation | Windows Task Scheduler + Python subprocess |
| Dashboard | Flask (localhost:5000) |
| Hardware | NVIDIA RTX 4070 Super |
| API cost | $0 — fully local |

## Project Structure

```
ai-job-search-pipeline/
├── app.py                  # Flask dashboard entry point
├── scheduler.py            # Pipeline orchestrator
├── config.py               # All settings in one place
├── requirements.txt
├── .gitignore
│
├── src/                    # Pipeline source modules
│   ├── scout.py            # Step 1: job board scraping
│   ├── analyze.py          # Step 2: LLM scoring
│   ├── generate_docs.py    # Step 3: resume + cover letter generation
│   ├── digest.py           # Step 4: daily summary
│   ├── tailor.py           # standalone: resume tailoring
│   ├── cover.py            # standalone: cover letter writing
│   ├── prep.py             # standalone: interview prep
│   ├── analyst.py          # standalone: single job analysis
│   ├── tracker.py          # standalone: application tracking CLI
│   └── show.py             # standalone: quick job list viewer
│
├── templates/              # Flask HTML templates
│   └── index.html
│
├── scripts/                # Windows automation helpers
│   ├── run_scheduler.bat   # Task Scheduler entry point
│   ├── launch_dashboard.bat
│   ├── launch_scheduler.vbs
│   └── tail_log.ps1        # Live log viewer
│
├── tests/                  # Test scripts
│   ├── pipeline_test.py    # Single-job end-to-end test
│   ├── test_ollama.py      # Ollama connectivity test
│   └── test_job.py
│
├── docs/                   # Documentation and diagrams
│   └── AI_Job_Search_System_Flowchart.*
│
├── data/                   # Candidate profile (gitignored)
│   └── james_profile.md
│
├── results/                # Generated output (gitignored)
│   ├── 01.0_job_data/
│   ├── 02.0_job_reports/
│   ├── 03.0_resumes/
│   ├── 03.1_cover_letters/
│   ├── 03.2_doc_manifest/
│   ├── 04.0_digests/
│   └── interview_prep/
│
└── logs/                   # Pipeline logs (gitignored)
    └── scheduler.log
```

## Setup

**Prerequisites:**
- Python 3.11+
- [Ollama](https://ollama.ai) with `qwen3:14b` pulled
- NVIDIA GPU recommended (runs on CPU but slowly)

```bash
# Clone and install
git clone https://github.com/yourusername/ai-job-search-pipeline
cd ai-job-search-pipeline
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Pull the model
ollama pull qwen3:14b

# Configure
# Copy data/candidate_profile_example.md to data/candidate_profile.md
# Edit it with your background, target roles, and compensation
# Edit config.py with your paths and settings
```

## Running

**Full automated pipeline (via Task Scheduler):**
```
scripts\run_scheduler.bat
```

**Dashboard:**
```
scripts\launch_dashboard.bat
# Opens http://localhost:5000
```

**Individual steps:**
```bash
python src/scout.py           # Step 1: scout jobs
python src/analyze.py         # Step 2: analyze and score
python src/generate_docs.py   # Step 3: generate documents
python src/digest.py          # Step 4: refresh digest
```

**Standalone tools:**
```bash
python src/tracker.py         # CLI application tracker
python src/prep.py            # Interview prep package
python src/analyst.py         # Single job analysis
```

**Run tests:**
```bash
python tests/pipeline_test.py   # Single-job end-to-end test
python tests/test_ollama.py     # Verify Ollama connection
```

## Configuration

All settings are in `config.py`:

- `SCORE_THRESHOLD` — minimum score to generate documents (default: 7.0)
- `BLOCKLIST` — companies to skip
- `LLM_MODEL` — Ollama model to use
- `SCHEDULE_TIME` — daily run time
- `TARGET_SALARY_MIN/MAX` — salary filter

## Built By

James T. Debruhl — Jacksonville, FL — 2026
