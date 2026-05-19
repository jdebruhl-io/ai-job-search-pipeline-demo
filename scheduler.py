import schedule
import time
import subprocess
import sys
import os
from datetime import datetime

BASE_DIR = "C:\\ai-agents\\ai-job-search-pipeline"
LOG_FILE  = f"{BASE_DIR}\\logs\\scheduler.log"


def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")


def stream_subprocess(cmd, timeout, step_name, env=None):
    start_time = datetime.now()
    log(f"[START] {step_name} started at {start_time.strftime('%H:%M:%S')}")

    try:
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
            if line and any(x in line for x in [
                "[", "Score", "SCORE", "FIT", "WORTH", "YES", "MAYBE", "NO",
                "Step", "Digest", "ERROR", "Error", "error",
                "complete", "Complete", "failed", "Failed", "saved", "Saved",
                "BLOCKED", "processed", "Analyzing", "Loading", "Found",
                "Report", "Documents", "Generated", "Manifest"
            ]):
                log(f"  {line}")

        process.wait(timeout=timeout)
        elapsed = (datetime.now() - start_time).total_seconds()

        if process.returncode == 0:
            log(f"[DONE] {step_name} completed in {elapsed:.0f}s")
            return True
        else:
            stderr_out = process.stderr.read()[-500:] if process.stderr else ""
            log(f"[FAIL] {step_name} failed (exit {process.returncode}) after {elapsed:.0f}s")
            if stderr_out:
                log(f"  stderr: {stderr_out}")
            return False

    except subprocess.TimeoutExpired:
        process.kill()
        elapsed = (datetime.now() - start_time).total_seconds()
        log(f"[TIMEOUT] {step_name} timed out after {elapsed:.0f}s")
        return False
    except Exception as e:
        log(f"[ERROR] {step_name} exception: {e}")
        return False


def run_pipeline():
    pipeline_start = datetime.now()
    python_exe = sys.executable

    log("=" * 60)
    log("=== Starting daily job search pipeline ===")
    log(f"=== Pipeline start: {pipeline_start.strftime('%Y-%m-%d %H:%M:%S')} ===")
    log("=" * 60)

    # -- Step 1: Scout ----------------------------------------
    log("-" * 40)
    log("Step 1: Running job scout...")
    ok = stream_subprocess([python_exe, "src/scout.py"], timeout=120, step_name="Step 1 [Scout]")
    if not ok:
        log("[ABORT] Pipeline aborted at Step 1")
        return

    # -- Step 2: Analyze Jobs ---------------------------------
    log("-" * 40)
    log("Step 2: Analyzing jobs...")
    ok = stream_subprocess([python_exe, "src/analyze.py"], timeout=3600, step_name="Step 2 [Analyze Jobs]")
    if not ok:
        log("[ABORT] Pipeline aborted at Step 2")
        return

    # -- Step 3: Generate Docs --------------------------------
    # NOTE: Disabled from daily automation - hallucinated resumes
    # are not safe to send. Run manually via Flask dashboard only
    # when a specific high-scoring job needs clean verified docs.
    # log("-" * 40)
    # log("Step 3: Generating docs...")
    # ok = stream_subprocess([python_exe, "src/generate_docs.py"], timeout=7200, step_name="Step 3 [Generate Docs]")
    # if not ok:
    #     log("[WARN] Generate Docs failed but continuing to digest...")

    # -- Step 4: Refresh Digest -------------------------------
    log("-" * 40)
    log("Step 4: Refreshing digest...")
    ok = stream_subprocess([python_exe, "src/digest.py"], timeout=60, step_name="Step 4 [Refresh Digest]")
    if not ok:
        log("[WARN] Digest failed")

    # -- Pipeline complete ------------------------------------
    elapsed = (datetime.now() - pipeline_start).total_seconds()
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    log("=" * 60)
    log(f"=== Daily pipeline complete. Total runtime: {minutes}m {seconds}s ===")
    log("=== Check results folder for today's output. ===")
    log("=" * 60)


def run_scheduler():
    log("Scheduler started")
    log("Pipeline will run daily at 07:00 AM")
    log("Press Ctrl+C to stop")

    schedule.every().day.at("07:00").do(run_pipeline)

    run_pipeline()

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    run_scheduler()
