import json
import os
from datetime import datetime, timedelta
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from config import JOB_REPORTS_DIR, JOB_DATA_DIR, TRACKER_FILE, DIGEST_DIR
from utils import parse_report_text


def ensure_dirs():
    os.makedirs(DIGEST_DIR, exist_ok=True)


def load_latest_report():
    files = [f for f in os.listdir(JOB_REPORTS_DIR) if f.startswith("report_")]
    if not files:
        return None, None
    latest = sorted(files)[-1]
    filepath = os.path.join(JOB_REPORTS_DIR, latest)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read(), latest


def load_latest_jobs():
    files = [f for f in os.listdir(JOB_DATA_DIR) if f.startswith("jobs_")]
    if not files:
        return []
    latest = sorted(files)[-1]
    filepath = os.path.join(JOB_DATA_DIR, latest)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_applications():
    if not os.path.exists(TRACKER_FILE):
        return []
    with open(TRACKER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_scores_from_report(report_text):
    return parse_report_text(report_text)


def get_followups():
    apps = load_applications()
    today = datetime.now().strftime("%Y-%m-%d")
    upcoming = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

    due = [a for a in apps if
           a.get("follow_up_date", "9999") <= upcoming and
           a["status"] not in ["Offer Accepted", "Offer Declined", "Rejected", "Withdrawn"]]

    return due, today


def run():
    ensure_dirs()
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    lines = []
    lines.append("=" * 60)
    lines.append(f"  DAILY JOB SEARCH DIGEST — {today}")
    lines.append("=" * 60)

    # Load and parse latest report
    report_text, report_file = load_latest_report()
    jobs = load_latest_jobs()

    if not report_text:
        lines.append("\nNo report found. Run pipeline first.")
    else:
        results = parse_scores_from_report(report_text)

        # YES jobs
        yes_jobs = [r for r in results if "YES" in r["verdict"].upper()]
        maybe_jobs = [r for r in results if "MAYBE" in r["verdict"].upper()]

        lines.append(f"\n[JOBS] JOBS ANALYZED TODAY: {len(results)}")
        lines.append(f"   Report: {report_file}")

        if yes_jobs:
            lines.append(f"\n[YES] YES — APPLY THESE ({len(yes_jobs)} jobs)")
            lines.append("-" * 60)
            for job in yes_jobs:
                lines.append(f"\n  {job['title']}")
                lines.append(f"  Company: {job['company']}")
                lines.append(f"  Score: {job['score']}")
                if job['salary']:
                    lines.append(f"  Est. Salary: {job['salary']}")
                if job['url']:
                    lines.append(f"  URL: {job['url']}")
        else:
            lines.append("\n[YES] YES jobs: None today")

        if maybe_jobs:
            lines.append(f"\n[MAYBE] MAYBE — Worth a look ({len(maybe_jobs)} jobs)")
            lines.append("-" * 60)
            for job in maybe_jobs:
                lines.append(f"  {job['score']} | {job['title']} @ {job['company']}")

    # Application tracker summary
    apps = load_applications()
    followups, today_str = get_followups()

    lines.append(f"\n[PIPELINE] APPLICATION PIPELINE")
    lines.append("-" * 60)
    lines.append(f"  Total applications: {len(apps)}")

    if apps:
        active = [a for a in apps if a["status"] not in
                  ["Offer Accepted", "Offer Declined", "Rejected", "Withdrawn"]]
        lines.append(f"  Active: {len(active)}")

        # Status breakdown
        statuses = {}
        for app in apps:
            s = app["status"]
            statuses[s] = statuses.get(s, 0) + 1
        for status, count in statuses.items():
            lines.append(f"    {count}x {status}")

    if followups:
        lines.append(f"\n[FOLLOWUP]  FOLLOW-UPS DUE (next 3 days)")
        lines.append("-" * 60)
        for app in followups:
            overdue = " <-- OVERDUE" if app.get("follow_up_date", "") <= today_str else ""
            lines.append(f"  {app['follow_up_date']}{overdue}")
            lines.append(f"  {app['company']} — {app['title']}")
            lines.append(f"  Status: {app['status']}")
    else:
        lines.append(f"\n>> No follow-ups due in next 3 days")

    lines.append(f"\n{'=' * 60}")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"{'=' * 60}\n")

    # Save digest
    digest_filename = f"{DIGEST_DIR}\\digest_{timestamp}.txt"
    digest_content = "\n".join(lines)

    with open(digest_filename, "w", encoding="utf-8") as f:
        f.write(digest_content)

    # Also print to console
    print(digest_content)
    print(f"Digest saved to: {digest_filename}")


if __name__ == "__main__":
    run()


