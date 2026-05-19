from flask import Flask, render_template, jsonify, Response, request
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
import threading

# ── Make src/ and project root importable ─────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "src"))
from config import (BASE_DIR, JOB_DATA_DIR, JOB_REPORTS_DIR, RESUMES_DIR,
                    COVER_DIR as COVER_LETTERS_DIR, DOC_MANIFEST_DIR,
                    DIGEST_DIR, INTERVIEW_DIR, TRACKER_FILE, LOG_FILE)
from utils import parse_report_text

app = Flask(__name__)

PYTHON_EXE = sys.executable


# ── Data helpers ───────────────────────────────────────────────
def load_applications():
    if not os.path.exists(TRACKER_FILE):
        return []
    with open(TRACKER_FILE, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_applications(apps):
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(apps, f, indent=2, ensure_ascii=False)


def load_latest_jobs():
    if not os.path.exists(JOB_DATA_DIR):
        return []
    files = [f for f in os.listdir(JOB_DATA_DIR) if f.startswith("jobs_")]
    if not files:
        return []
    latest = sorted(files)[-1]
    with open(os.path.join(JOB_DATA_DIR, latest), "r", encoding="utf-8") as f:
        return json.load(f)


def load_latest_digest():
    if not os.path.exists(DIGEST_DIR):
        return None
    files = [f for f in os.listdir(DIGEST_DIR) if f.endswith(".txt")]
    if not files:
        return None
    latest = sorted(files)[-1]
    with open(os.path.join(DIGEST_DIR, latest), "r", encoding="utf-8") as f:
        return f.read()


def load_latest_report():
    if not os.path.exists(JOB_REPORTS_DIR):
        return []
    files = [f for f in os.listdir(JOB_REPORTS_DIR) if f.startswith("report_")]
    if not files:
        return []
    latest = sorted(files)[-1]
    with open(os.path.join(JOB_REPORTS_DIR, latest), "r", encoding="utf-8") as f:
        content = f.read()
    return parse_report_text(content)


def get_pipeline_status():
    status = {
        "last_run": "Never",
        "next_run": "7:00 AM daily",
        "jobs_found": 0,
        "docs_generated": 0
    }

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines):
            if "Daily pipeline complete" in line:
                try:
                    ts = line.split("]")[0].replace("[", "").strip()
                    status["last_run"] = ts
                except:
                    pass
                break

    if os.path.exists(JOB_DATA_DIR):
        files = [f for f in os.listdir(JOB_DATA_DIR) if f.startswith("jobs_")]
        if files:
            latest = sorted(files)[-1]
            jobs = load_latest_jobs()
            status["jobs_found"] = len(jobs)

    if os.path.exists(RESUMES_DIR):
        today = datetime.now().strftime("%Y%m%d")
        docs = [f for f in os.listdir(RESUMES_DIR) if today in f]
        status["docs_generated"] = len(docs)

    return status


def get_followups():
    apps = load_applications()
    today = datetime.now().strftime("%Y-%m-%d")
    upcoming = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    return [a for a in apps if
            a.get("follow_up_date", "9999") <= upcoming and
            a["status"] not in ["Offer Accepted", "Offer Declined", "Rejected", "Withdrawn"]]


def list_files(directory, prefix=""):
    if not os.path.exists(directory):
        return []
    files = []
    for f in os.listdir(directory):
        if f.endswith(".txt") and (not prefix or f.startswith(prefix)):
            filepath = os.path.join(directory, f)
            stat = os.stat(filepath)
            files.append({
                "name": f,
                "size": f"{stat.st_size // 1024}KB",
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                "_mtime": stat.st_mtime
            })
    files.sort(key=lambda x: x["_mtime"], reverse=True)
    for f in files:
        del f["_mtime"]
    return files


# ── Routes ─────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/dashboard")
def dashboard():
    apps = load_applications()
    jobs = load_latest_report()
    followups = get_followups()
    status = get_pipeline_status()
    digest = load_latest_digest()

    yes_jobs = [j for j in jobs if "YES" in str(j.get("verdict", "")).upper()]
    maybe_jobs = [j for j in jobs if "MAYBE" in str(j.get("verdict", "")).upper()]
    no_jobs = [j for j in jobs if "NO" in str(j.get("verdict", "")).upper()
               and "MAYBE" not in str(j.get("verdict", "")).upper()]

    active_apps = [a for a in apps if a["status"] not in
                   ["Offer Accepted", "Offer Declined", "Rejected", "Withdrawn"]]

    status_counts = {}
    for app_item in apps:
        s = app_item["status"]
        status_counts[s] = status_counts.get(s, 0) + 1

    return jsonify({
        "pipeline_status": status,
        "jobs": {
            "yes": yes_jobs,
            "maybe": maybe_jobs,
            "no": no_jobs,
            "total": len(jobs)
        },
        "applications": {
            "total": len(apps),
            "active": len(active_apps),
            "status_counts": status_counts,
            "list": apps
        },
        "followups": followups,
        "digest": digest
    })


@app.route("/api/jobs")
def get_jobs():
    jobs = load_latest_jobs()
    report_jobs = load_latest_report()
    score_map = {j["company"]: j for j in report_jobs}
    for job in jobs:
        if job["company"] in score_map:
            job["score"] = score_map[job["company"]].get("score", "?")
            job["verdict"] = score_map[job["company"]].get("verdict", "?")
            job["salary"] = score_map[job["company"]].get("salary", "")
    return jsonify(jobs)


@app.route("/api/applications", methods=["GET"])
def get_applications():
    return jsonify(load_applications())


@app.route("/api/applications", methods=["POST"])
def add_application():
    data = request.json
    apps = load_applications()
    app_entry = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "company": data.get("company", ""),
        "title": data.get("title", ""),
        "url": data.get("url", ""),
        "source": data.get("source", ""),
        "date_applied": data.get("date_applied", datetime.now().strftime("%Y-%m-%d")),
        "resume_version": data.get("resume_version", "master"),
        "cover_letter": data.get("cover_letter", False),
        "status": "Applied",
        "notes": data.get("notes", ""),
        "follow_up_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "history": [{"date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                     "event": "Application submitted"}]
    }
    apps.append(app_entry)
    save_applications(apps)
    return jsonify({"success": True, "application": app_entry})


@app.route("/api/applications/<app_id>", methods=["PUT"])
def update_application(app_id):
    data = request.json
    apps = load_applications()
    for app_item in apps:
        if app_item["id"] == app_id:
            new_status = data.get("status", app_item["status"])
            app_item["status"] = new_status
            app_item["notes"] = data.get("notes", app_item.get("notes", ""))
            if "follow_up_date" in data:
                app_item["follow_up_date"] = data["follow_up_date"]
            app_item.setdefault("history", []).append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "event": new_status,
                "notes": data.get("notes", "")
            })
            save_applications(apps)
            return jsonify({"success": True})
    return jsonify({"success": False, "error": "Not found"}), 404

@app.route("/api/applications/<app_id>", methods=["DELETE"])
def delete_application(app_id):
    apps = load_applications()
    apps = [a for a in apps if a["id"] != app_id]
    save_applications(apps)
    return jsonify({"success": True})

@app.route("/api/documents")
def get_documents():
    return jsonify({
        "resumes": list_files(RESUMES_DIR),
        "cover_letters": list_files(COVER_LETTERS_DIR),
        "doc_manifest": list_files(DOC_MANIFEST_DIR),
        "interview_prep": list_files(INTERVIEW_DIR),
        "digests": list_files(DIGEST_DIR)
    })


@app.route("/api/documents/<doc_type>/<filename>")
def get_document(doc_type, filename):
    dirs = {
        "resumes": RESUMES_DIR,
        "cover_letters": COVER_LETTERS_DIR,
        "doc_manifest": DOC_MANIFEST_DIR,
        "interview_prep": INTERVIEW_DIR,
        "digests": DIGEST_DIR,
        "job_reports": JOB_REPORTS_DIR
    }
    directory = dirs.get(doc_type)
    if not directory:
        return jsonify({"error": "Invalid document type"}), 400

    filepath = os.path.join(directory, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return jsonify({"filename": filename, "content": content})


@app.route("/api/run/<script>")
def run_script(script):
    scripts = {
        "scout": "src/scout.py",
        "pipeline": "src/analyze.py",
        "stage3": "src/generate_docs.py",
        "digest": "src/digest.py"
    }

    script_labels = {
        "scout": "Scout Jobs",
        "pipeline": "Analyze Jobs",
        "stage3": "Generate Docs",
        "digest": "Refresh Digest"
    }

    if script not in scripts:
        return jsonify({"error": "Unknown script"}), 400

    script_file = scripts[script]

    def generate():
        process = subprocess.Popen(
            [PYTHON_EXE, script_file],
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )

        yield f"data: Starting {script_file}...\n\n"

        for line in process.stdout:
            line = line.rstrip()
            if line:
                yield f"data: {line}\n\n"

        process.wait()
        if process.returncode == 0:
            yield f"data: \n\n"
            yield f"data: ✓ {script_file} completed successfully\n\n"
        else:
            yield f"data: \n\n"
            yield f"data: ✗ {script_file} finished with errors\n\n"
        yield "data: __DONE__\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no"})


@app.route("/api/log")
def get_log():
    if not os.path.exists(LOG_FILE):
        return jsonify({"log": "No log file found yet."})
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return jsonify({"log": "".join(lines[-100:])})


@app.route("/api/analyze_job", methods=["POST"])
def analyze_job_manual():
    """Manual single-job analysis — calls the same analyze_job() used by the pipeline."""
    data = request.json
    job = {
        "title":       data.get("title", ""),
        "company":     data.get("company", ""),
        "location":    data.get("location", "Remote"),
        "url":         data.get("url", ""),
        "source":      "Manual Entry",
        "description": data.get("description", ""),
        "salary_min":  0,
        "tags":        [],
    }

    def generate():
        yield f"data: Analyzing {job['title']} @ {job['company']}...\n\n"
        try:
            from analyze import analyze_job, strip_think_tags
            result = analyze_job(job)
            result = strip_think_tags(str(result))

            # Save to reports folder
            timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_co     = job["company"].replace(" ", "_").replace("/", "-")[:25]
            filename    = os.path.join(JOB_REPORTS_DIR, f"manual_{safe_co}_{timestamp}.txt")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"MANUAL JOB ANALYSIS\n")
                f.write(f"Title: {job['title']}\n")
                f.write(f"Company: {job['company']}\n")
                f.write(f"URL: {job['url']}\n")
                f.write(f"Analyzed: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write("=" * 60 + "\n\n")
                f.write(result)

            yield "data: ---RESULT---\n\n"
            for line in result.split("\n"):
                yield f"data: {line}\n\n"
            yield f"data: \nSaved to: {os.path.basename(filename)}\n\n"
        except Exception as e:
            yield f"data: Error: {e}\n\n"
        yield "data: __DONE__\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/analyze_and_generate", methods=["POST"])
@app.route("/api/force_generate", methods=["POST"])
def analyze_and_generate():
    """Score job then generate resume + cover letter — calls src modules directly."""
    data  = request.json
    force = request.path.endswith("force_generate") or data.get("force", False)
    job   = {
        "title":       data.get("title", ""),
        "company":     data.get("company", ""),
        "location":    data.get("location", "Remote"),
        "url":         data.get("url", ""),
        "source":      "Manual Entry",
        "description": data.get("description", ""),
        "salary_min":  0,
        "tags":        [],
    }

    def generate():
        try:
            from analyze import analyze_job, pre_score_job, strip_think_tags
            from tailor import run as tailor_run
            from cover  import run as cover_run

            # Step 1: pre-score
            yield "data: [1/3] Scoring job fit...\n\n"
            pre = pre_score_job(job)
            yield f"data: Pre-score: {pre}/10\n\n"
            if pre is not None and pre < 5 and not force:
                yield f"data: Score {pre}/10 below threshold — skipping doc generation.\n\n"
                yield "data: Use Force Generate to override.\n\n"
                yield "data: __DONE__\n\n"
                return

            # Step 2: full analysis
            yield "data: [2/3] Running full analysis...\n\n"
            result  = strip_think_tags(str(analyze_job(job)))
            timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_co    = job["company"].replace(" ", "_").replace("/", "-")[:25]

            report_file = os.path.join(JOB_REPORTS_DIR, f"manual_{safe_co}_{timestamp}.txt")
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(f"MANUAL JOB ANALYSIS\nTitle: {job['title']}\n"
                        f"Company: {job['company']}\nURL: {job['url']}\n"
                        f"Analyzed: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                        + "=" * 60 + "\n\n" + result)

            for line in result.split("\n"):
                if any(k in line for k in ["FIT SCORE", "WORTH APPLYING"]):
                    yield f"data: {line.strip()}\n\n"

            # Step 3: docs — generate for the submitted job specifically
            yield "data: [3/3] Generating resume + cover letter...\n\n"
            from tailor import tailor_resume, MASTER_RESUME
            from cover  import write_cover_letter, YOUR_INFO
            import os as _os
            _profile = f"{BASE_DIR}\\data\\james_profile.md"
            background = open(_profile, "r", encoding="utf-8").read() if _os.path.exists(_profile) else ""

            job_for_tailor = {
                "title":                job["title"],
                "company":              job["company"],
                "url":                  job["url"],
                "key_requirements":     job["description"][:1500],
                "application_strategy": "Emphasize the most relevant experience for this specific role",
            }
            tailored = tailor_resume(job_for_tailor, MASTER_RESUME)

            job_for_cover = {
                "title":            job["title"],
                "company":          job["company"],
                "url":              job["url"],
                "tone":             "professional",
                "key_requirements": job["description"][:1500],
                "key_angle":        "Connect the candidate's most relevant experience directly to this role's key requirements",
                "hiring_manager":   "Hiring Manager",
            }
            cover = write_cover_letter(job_for_cover, background, YOUR_INFO)

            doc_ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_co = job["company"].replace(" ", "_").replace("/", "-")[:25]
            resume_file = os.path.join(RESUMES_DIR, f"resume_{safe_co}_{doc_ts}.txt")
            cover_file  = os.path.join(COVER_LETTERS_DIR, f"cover_{safe_co}_{doc_ts}.txt")
            with open(resume_file, "w", encoding="utf-8") as f:
                f.write(f"TAILORED RESUME: {job['title']} @ {job['company']}\n"
                        f"URL: {job['url']}\n" + "=" * 60 + "\n\n" + tailored)
            with open(cover_file, "w", encoding="utf-8") as f:
                f.write(f"COVER LETTER: {job['title']} @ {job['company']}\n"
                        f"URL: {job['url']}\n" + "=" * 60 + "\n\n" + cover)

            yield f"data: Resume: {os.path.basename(resume_file)}\n\n"
            yield f"data: Cover:  {os.path.basename(cover_file)}\n\n"
            yield f"data: \nDone. Report + docs saved for {job['company']}.\n\n"
        except Exception as e:
            yield f"data: Error: {e}\n\n"
        yield "data: __DONE__\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

if __name__ == "__main__":
    print("Starting AI Job Search Dashboard...")
    print("Open your browser to: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    app.run(debug=False, host="127.0.0.1", port=5000)
