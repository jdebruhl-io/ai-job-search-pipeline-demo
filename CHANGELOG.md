# Changelog

All notable changes to ai-job-search-pipeline are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]
See [GitHub Issues](https://github.com/jdebruhl-io/ai-job-search-pipeline/issues) for planned work.

- #2 fix: duplicate job listings from scout - near-identical titles not deduplicated
- #3 investigate: score vs verdict mismatch from analyst agent
- known: Booz Allen Hamilton Workday description fetch returning empty for all BAH jobs —
  20 jobs per run analyzed as N/A; BAH detail API endpoint structure may have changed

---

## [1.3.0] - 2026-05-15

### Refactored (Phase 3)
- Removed hardcoded paths from all 9 `src/` modules — now imported from `config.py` (closes issue #4)
- Removed duplicate `BLOCKLIST` from `generate_docs.py` — single source of truth in `config.py`
- Removed embedded `MY_BACKGROUND` strings (~315 lines total) from `analyze.py`, `generate_docs.py`,
  `cover.py`, `tailor.py`, `prep.py` — all modules now load candidate profile from
  `data/james_profile.md` via `config.PROFILE_PATH`
- Replaced 4 independent report parser implementations in `analyze.py`, `generate_docs.py`,
  `digest.py`, and `app.py` with shared `utils.parse_report_text()` (closes issue #1)
- `app.py` path constants now imported from `config.py` instead of hardcoded strings;
  `BASE_DIR` now uses `os.path.abspath(__file__)` for portability

### Added
- `src/utils.py` — shared `parse_summary()` and `parse_report_text()` functions
- `tests/test_utils.py` — smoke tests for both utils functions

### Fixed (Phase 4–5)
- `scout.py`: HTML entities and tags now stripped from all job descriptions at normalization
  time via `_clean_desc()` in `_norm_job()` — previously Greenhouse, Remotive, and Jobicy
  descriptions arrived with raw `&lt;div&gt;` entities that the LLM had to parse around
- `analyze.py` salary penalty: MANDATORY language added so LLM actually subtracts 1.0 from
  the numeric FIT SCORE when salary is below $90k, not just notes it as a red flag
- `analyze.py`: removed two duplicate "Agile methodology" REWARD lines that were adding
  prompt noise and over-weighting that skill category

### Changed
- `scout.py` `RELEVANT_TITLE_TERMS`: added `"grc"`, `"compliance analyst"`,
  `"prompt engineer"` — roles that match James's background but were previously filtered
  before reaching the LLM

---

## [1.2.0] - 2026-05-15

### Fixed
- `app.py`: corrected `LOG_FILE` path from project root to `logs/scheduler.log`
  — dashboard was always showing "Last run: Never" and `/api/log` always
  returned "No log file found" even after a successful pipeline run
- `app.py` `/api/analyze_job`: removed crash on missing `pipeline.py` (renamed
  to `src/analyze.py` in v1.0.0); background now loaded from `data/james_profile.md`.
  Also fixed `james_profile.md` path which was missing the `data\` subdirectory —
  extended profile was silently empty on every manual analysis request
- `app.py` `/api/analyze_and_generate`: removed crash on missing `pipeline.py`
  and `resume_tailor.py` (both renamed in v1.0.0 restructure); background now
  loaded from `data/james_profile.md`, master resume imported from `src.tailor`
- `app.py` `/api/force_generate`: force flag was silently dropped — route set
  `data['force'] = True` on a local dict but `analyze_and_generate()` re-reads
  `request.json` independently. Both routes now handled via dual `@app.route`
  decorator; force detected via `request.path.endswith("force_generate")`
- `app.py`: removed 385-line dead code block and duplicate `@app.route`
  definitions for `/api/analyze_and_generate` and `/api/force_generate` that
  caused Flask to throw `AssertionError: View function mapping is overwriting
  an existing endpoint` on startup — dashboard could not start at all
- `app.py` `/api/analyze_and_generate`: doc generation now targets the
  submitted job instead of iterating the hardcoded `TARGET_JOBS` list in
  `tailor.run()` / `cover.run()`. Now calls `tailor_resume()` and
  `write_cover_letter()` directly with the submitted job and saves the
  resulting files to the correct results directories
- `requirements.txt`: added `feedparser` and `beautifulsoup4` — both were used
  in `scout.py` but missing from requirements (feedparser was silently
  auto-installed at runtime; beautifulsoup4 needed for LinkedIn guest scraper)

---

## [1.1.0] - 2026-05-11

### Fixed
- Removed undefined `analyze_and_generate_internal` reference in `app.py` 
  (caught by Pylance in VS Code) — `force_generate` route now calls 
  `analyze_and_generate()` directly
- Replaced box-drawing characters (`─`) with plain ASCII dashes in 
  `scheduler.py` to fix garbled log output (`â"€â"€â"€`)
- Replaced Unicode left-arrow (`←`) with ASCII `<--` in `digest.py` 
  to fix charmap encoding error on overdue follow-up display
- Added `flush=True` to all progress print statements in `analyze.py` 
  so `[Job X/51]` counter streams in real time to the log
- Fixed score summary parser in `analyze.py` to strip `*` before parsing 
  — eliminates `Score: ? | ?` lines in log output
- Applied `strip_think_tags()` to all LLM output in `analyze.py` and 
  `generate_docs.py` — eliminates Chinese `<think>` block text leaking 
  into reports

### Changed
- `scheduler.py` subprocess runner now streams stdout line-by-line in 
  real time instead of capturing at end — enables live log monitoring
- Step 3 (`generate_docs.py`) no longer re-scores jobs with a second LLM 
  call — now reads scores directly from Step 2 report. Eliminates duplicate 
  LLM processing and score inconsistency between digests

### Added
- `tail_log.ps1` — live log viewer with color coding, auto-closes when 
  pipeline completes (green=high scores, yellow=maybe, red=errors, cyan=steps)
- `[Job X/51]` progress counter now appears in real-time log stream
- `tests/pipeline_test.py` — single-job end-to-end test with env var 
  threshold override (`SCORE_THRESHOLD_OVERRIDE`) so production threshold 
  is never modified for testing
- `src/generate_docs.py` now reads `SCORE_THRESHOLD` from environment variable 
  with 7.0 as default — allows test override without code changes

---

## [1.0.0] - 2026-05-11 — Initial Release / Full Restructure

### Project Structure
- Moved project from flat `C:\ai-agents\` root into professional repo layout 
  at `C:\ai-agents\ai-job-search-pipeline\`
- Created standard directory structure: `src/`, `tests/`, `scripts/`, 
  `docs/`, `data/`, `logs/`, `templates/`, `results/`
- Added `config.py` — centralized settings (paths, thresholds, model, blocklist)
- Added `README.md` with full project documentation
- Added `requirements.txt`
- Added `.gitignore` (excludes venv, results, logs, personal data)
- Added `src/__init__.py` — makes src a proper Python package
- Added `CONVENTIONS.md` at workspace root documenting `_io` naming convention

### Files Renamed
| Old Name | New Name | Location |
|----------|----------|----------|
| `job_scout.py` | `scout.py` | `src/` |
| `pipeline.py` | `analyze.py` | `src/` |
| `stage3_pipeline.py` | `generate_docs.py` | `src/` |
| `daily_digest.py` | `digest.py` | `src/` |
| `resume_tailor.py` | `tailor.py` | `src/` |
| `cover_letter.py` | `cover.py` | `src/` |
| `interview_prep.py` | `prep.py` | `src/` |
| `job_analyst.py` | `analyst.py` | `src/` |
| `show_jobs.py` | `show.py` | `src/` |
| `tracker.py` | `tracker.py` | `src/` |

### Results Folder Renamed
| Old Name | New Name |
|----------|----------|
| `job_data/` | `01.0_job_data/` |
| `job_reports/` | `02.0_job_reports/` |
| `resumes/` | `03.0_resumes/` |
| `cover_letters/` | `03.1_cover_letters/` |
| `stage3_digest/` | `03.2_doc_manifest/` |
| `digests/` | `04.0_digests/` |

### Internal Changes
- All `[Stage3]` print messages renamed to `[Generate Docs]`
- All internal `run_scout()`, `run_pipeline()`, `run_stage3()` etc renamed to `run()`
- Dead `analyze_and_filter()` code block removed from `generate_docs.py` 
  (638 → 509 lines)
- Flask button labels updated: Scout Jobs / Analyze Jobs / Generate Docs / Refresh Digest
- `stage3_digest` concept renamed to `doc_manifest` throughout

### Git & GitHub
- Git repository initialized
- Connected to `https://github.com/jdebruhl-io/ai-job-search-pipeline`
- Initial commit: 35 files, 10,013 insertions
- GitHub Issues configured with labels: bug, enhancement, investigation, 
  refactor, documentation, question, wontfix

### Developer Tooling
- VS Code configured with Python interpreter pointing to `C:\ai-agents\venv`
- Extensions installed: Python, GitLens, Git History, GitHub Pull Requests, 
  Code Spell Checker, Notepad++ keymap
- PowerShell profile updated with full alias set

### PowerShell Aliases Added
| Alias | Command |
|-------|---------|
| `aiwork` | Activate venv + cd to project root |
| `aihelp` | Show all available commands |
| `reload` | Reload PowerShell profile without restarting |
| `scout` | Run Step 1 — Scout Jobs |
| `analyze` | Run Step 2 — Analyze Jobs |
| `gendocs` | Run Step 3 — Generate Docs |
| `digest` | Run Step 4 — Refresh Digest |
| `scheduler` | Run full pipeline orchestrator |
| `webui` | Start Flask dashboard + open Chrome |
| `tailor` | Standalone resume tailor |
| `covers` | Standalone cover letter writer |
| `prep` | Standalone interview prep |
| `analyst` | Standalone single job analysis |
| `track` | CLI application tracker |
| `show` | Quick job list viewer |
| `npp` | Open file in Notepad++ |

---

## [0.2.0] - 2026-05-06

### Fixed
- UTF-8 encoding added to all file write operations across pipeline
- `sys.stdout.reconfigure(encoding='utf-8')` added to all scripts

### Changed
- `scheduler.py` updated to stream subprocess output line-by-line in real time
- `run_scheduler.bat` updated to remove `pause` command that was causing 
  Task Scheduler to show task as perpetually "Running" after completion

### Added
- `launch_scheduler.vbs` — WScript launcher so Task Scheduler opens pipeline 
  window in user desktop session instead of invisible Session 0
- Task Scheduler action updated to use VBScript launcher
- `[Job X/N]` progress counter added to analyze step output

---

## [0.1.0] - 2026-04-28 — Initial Build

### Added
- Job scout scraping RemoteOK, Jobicy, USAJobs, Remotive
- Targeted company searches (Booz Allen, SAIC, Leidos, L3Harris)
- Analyst agent scoring jobs 1-10 using CrewAI + Ollama qwen3:14b
- Stage 3 document generation (resume + cover letter) for jobs scoring 7.0+
- Blocklist system with documented reasons per company
- Daily digest generator with YES/MAYBE/NO categorization
- Application tracker with 13 status states and follow-up reminders
- Flask web dashboard at localhost:5000 with real-time SSE log streaming
- Windows Task Scheduler automation at 7:00 AM daily
- Standalone tools: analyst, tailor, cover, prep, tracker, show
- Local LLM infrastructure: Ollama / qwen3:14b on RTX 4070 Super
- Zero API cost — fully local pipeline
