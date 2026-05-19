"""
pipeline_test.py — Single job pipeline test
Bypasses job_scout.py and injects one known job directly into the pipeline.
Tests Steps 2, 3, and 4 end-to-end with a single job.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import os
import subprocess
import re
from datetime import datetime

BASE_DIR = "C:\\ai-agents\\ai-job-search-pipeline"
RESULTS_DIR = f"{BASE_DIR}\\results"
JOB_DATA_DIR = f"{RESULTS_DIR}\\01.0_job_data"
PYTHON_EXE = sys.executable
TEST_THRESHOLD = 1.0  # Override for test only — normal value is 7.0

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def strip_think_tags(text):
    """Remove <think>...</think> blocks from LLM output."""
    import re
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

# ── Inject single test job ─────────────────────────────────────
TEST_JOB = {
    "title": "Technical Solutions Architect II - Network Security",
    "company": "World Wide Technology",
    "location": "Remote",
    "url": "https://jobicy.com/jobs/142242-technical-solutions-architect-ii-network-security",
    "source": "Jobicy",
    "description": """World Wide Technology is seeking a Technical Solutions Architect II specializing in Network Security.

Role Overview:
Design and implement enterprise network security solutions for clients across multiple industries. Act as a trusted advisor on network security architecture, zero trust frameworks, and SASE implementations.

Key Responsibilities:
- Design and architect enterprise-grade network security solutions including NGFW, segmentation, Zero Trust, and SASE frameworks
- Work with clients to assess current security posture and recommend improvements
- Integrate SIEM/SOAR platforms into security architectures
- Design hybrid and multi-cloud security architectures (AWS, Azure, GCP)
- Lead technical workshops and present security roadmaps to executive stakeholders
- Develop multi-vendor security solutions across Palo Alto, Check Point, Fortinet, Cisco, and others
- Produce architecture documentation, compliance reports, and security assessments

Requirements:
- 7+ years network security experience
- Strong knowledge of Zero Trust and SASE frameworks
- Experience with SIEM/SOAR platform integration
- Hybrid/multi-cloud security architecture experience
- Excellent communication and documentation skills
- CCIE Security, CISSP, or equivalent preferred

Salary: $128,000 - $160,000 annually
Location: Remote""",
    "salary_min": 128000,
    "tags": ["network security", "zero trust", "SASE", "SIEM", "architect"]
}

def run_step(cmd, step_name, timeout=3600, env=None):
    """Run a subprocess and stream output, stripping think tags."""
    log(f"[START] {step_name}")
    start = datetime.now()

    process = subprocess.Popen(
        cmd,
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=env
    )

    for line in process.stdout:
        line = line.rstrip()
        if line:
            # Strip think tags from output lines
            cleaned = strip_think_tags(line)
            if cleaned:
                print(f"  {cleaned}", flush=True)

    process.wait(timeout=timeout)
    elapsed = (datetime.now() - start).total_seconds()

    if process.returncode == 0:
        log(f"[DONE] {step_name} completed in {elapsed:.0f}s")
        return True
    else:
        err = process.stderr.read()[-300:] if process.stderr else ""
        log(f"[FAIL] {step_name} failed in {elapsed:.0f}s: {err}")
        return False


def main():
    log("=" * 50)
    log("PIPELINE TEST — Single Job")
    log(f"Job: {TEST_JOB['title']} @ {TEST_JOB['company']}")
    log("=" * 50)

    # Write test job to a temp jobs file so pipeline.py picks it up
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_jobs_file = os.path.join(JOB_DATA_DIR, f"jobs_{timestamp}.json")

    with open(test_jobs_file, "w", encoding="utf-8") as f:
        json.dump([TEST_JOB], f, indent=2, ensure_ascii=False)

    log(f"Test job written to: {os.path.basename(test_jobs_file)}")
    log("")

    # Step 2 — Analyze
    log("─" * 40)
    ok = run_step([PYTHON_EXE, "src/analyze.py"], "Step 2: Analyze Jobs")
    if not ok:
        log("Step 2 failed — aborting test")
        return

    # Step 3 — Generate Docs (with test threshold override via env var)
    log("─" * 40)
    env = os.environ.copy()
    env["SCORE_THRESHOLD_OVERRIDE"] = str(TEST_THRESHOLD)
    ok = run_step([PYTHON_EXE, "src/generate_docs.py"], "Step 3: Generate Docs", timeout=3600, env=env)
    if not ok:
        log("Step 3 failed — continuing to digest anyway")

    # Step 4 — Digest
    log("─" * 40)
    run_step([PYTHON_EXE, "src/digest.py"], "Step 4: Refresh Digest", timeout=60)

    log("=" * 50)
    log("TEST COMPLETE — check results folders for output")
    log("=" * 50)


if __name__ == "__main__":
    main()


