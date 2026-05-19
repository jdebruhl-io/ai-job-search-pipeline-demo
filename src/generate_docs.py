from crewai import Agent, Task, Crew, LLM
import json
import os
from datetime import datetime
import sys
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from config import (JOB_DATA_DIR, JOB_REPORTS_DIR, RESUMES_DIR, COVER_DIR,
                    DOC_MANIFEST_DIR, DIGEST_DIR, PROFILE_PATH,
                    LLM_MODEL, LLM_BASE_URL, BLOCKLIST, SCORE_THRESHOLD)
from utils import parse_report_text

COVER_LETTERS_DIR = COVER_DIR  # local alias used throughout this file

llm = LLM(model=LLM_MODEL, base_url=LLM_BASE_URL)

import re

def strip_think_tags(text):
    """Remove <think>...</think> blocks from qwen3 output."""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

def is_blocked(company_name):
    """Check if a company is on the blocklist"""
    company_lower = company_name.lower()
    for term, reason in BLOCKLIST:
        if term.lower() in company_lower:
            print(f"  [Blocklist] Skipping {company_name} â€” {reason}")
            return True
    return False

MASTER_RESUME = """
===AGENT NOTES - DO NOT INCLUDE IN RESUME OUTPUT===
Current target compensation: $62/hr (~$124k annually)
Use this to assess role fit and salary alignment only.
Do not print this section in the tailored resume.
====================================================

James T Debruhl
Jacksonville, FL 32259
LinkedIn: linkedin.com/in/james-debruhl-b017aa66
Security Clearance: Eligible

SUMMARY:
Senior Network Security Analyst with 10+ years of experience in firewall
compliance, information security metrics, and infrastructure operations
across major financial institutions. Expertise in Palo Alto and Check Point
firewall rule analysis, compliance automation, and CISO-level reporting.
Proven ability to design SQL/VBA-driven pipelines that process 25,000+
firewall rules at enterprise scale. Currently expanding into AI engineering
â€” building local multi-agent systems with CrewAI and Ollama for security
workflow automation. Strong background in Cisco networking, governance,
risk assessment, and cross-functional stakeholder coordination.

EXPERIENCE:

Citibank (Contract - Matrix/Motion Recruitment) | Oct 2022 - Oct 2025 | Jacksonville, FL
Senior Network Security Analyst
- Designed and automated SQL and VBA-driven reporting pipelines to support
  CISO metrics, IS governance, and compliance tracking across global firewall
  infrastructure
- Produced monthly and ad-hoc Information Security reports using Cognos,
  Excel, and SQL datasets for executive management decision-making
- Built interactive Excel dashboards and visualizations for IS risk, firewall
  compliance, and connectivity metrics supporting executive visibility
- Performed firewall rule cleanup and compliance checks on Palo Alto and
  Check Point firewalls using scripts and structured analysis
- Responded to audit-related efforts to ensure firewall policy compliance
  with regulatory standards
- Partnered with IS program owners, technology teams, and risk management
  to gather data inputs, resolve data quality issues, and refine reporting

Bank of America (Contract - The Select Group/Cisco) | Jun 2016 - Oct 2022 | Jacksonville, FL
Network Engineer
- Remotely coordinated banking center network upgrades using Cisco CLI/IOS
- Analyzed 25,000+ firewall security rules using SQL and VBA automation
- Executed change orders on Cisco routers and switches for ATM network upgrades
- Maintained firewall security rules per enterprise standards and lifecycle

Gutter Helmet of North Florida | 2014 - 2019 | Jacksonville, FL
IT Consultant
- Managed all IT responsibilities at branch SOHO office
- Established and maintained Office 365 Exchange environment
- Implemented security monitoring system

EDUCATION:
St. Johns River State College | Orange Park, FL
AS Computer Network Engineering Technology (2013-2015)
Dean's List | NetRiders CCNA Finalist & Top Achiever (2015)

CERTIFICATIONS: CCNA (2016) | Network+ (2015) | A+ (2014)

AI/AUTOMATION PROJECTS (2026):
- Built local multi-agent AI system using CrewAI + Ollama on RTX 4070 Super
- Developed automated job market intelligence pipeline with Python
- Running and optimizing LLMs locally for security workflow automation
"""

EXTENDED_PROFILE = ""
if os.path.exists(PROFILE_PATH):
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        EXTENDED_PROFILE = f.read()

if SCORE_THRESHOLD != 7.0:
    print(f"[Generate Docs] TEST MODE: threshold overridden to {SCORE_THRESHOLD} (normal: 7.0)", flush=True)

def load_latest_jobs():
    files = [f for f in os.listdir(JOB_DATA_DIR) if f.startswith("jobs_")]
    if not files:
        print("No job files found. Run scout first.")
        return []
    latest = sorted(files)[-1]
    with open(os.path.join(JOB_DATA_DIR, latest), "r", encoding="utf-8") as f:
        return json.load(f)

def load_scores_from_report():
    """Read Step 2 report. Returns dict keyed by 'title|company' -> job dict."""
    files = [f for f in os.listdir(JOB_REPORTS_DIR) if f.startswith("report_")]
    if not files:
        print("[Generate Docs] No report found. Run Analyze Jobs first.")
        return {}
    latest = sorted(files)[-1]
    print(f"[Generate Docs] Reading scores from: {latest}")
    with open(os.path.join(JOB_REPORTS_DIR, latest), "r", encoding="utf-8") as f:
        text = f.read()

    scores = {}
    for job in parse_report_text(text):
        key = f"{job['title'].lower()}|{job['company'].lower()}"
        try:
            score_f = float(job["score"].split("/")[0])
        except (ValueError, AttributeError):
            score_f = 0.0
        scores[key] = {
            "key":             key,
            "title":           job["title"],
            "company":         job["company"],
            "score":           score_f,
            "verdict":         job["verdict"] if job["verdict"] != "?" else "NO",
            "url":             job["url"],
            "salary_estimate": job["salary"],
            "top_requirement": job["top_requirement"],
            "apply_angle":     job["apply_angle"],
            "biggest_gap":     job["biggest_gap"],
        }

    print(f"[Generate Docs] Loaded scores for {len(scores)} jobs from Step 2 report")
    return scores

def merge_jobs_with_scores(jobs, scores):
    """Merge scout job data with Step 2 scores. Returns (all_scored, high_scorers)."""
    all_scored = []
    for job in jobs:
        key = f"{job['title'].lower().strip()}|{job['company'].lower().strip()}"
        score_data = scores.get(key, {})
        merged = {
            **job,
            "score": score_data.get("score", 0.0),
            "verdict": score_data.get("verdict", "NO"),
            "top_requirement": score_data.get("top_requirement", ""),
            "apply_angle": score_data.get("apply_angle", ""),
            "biggest_gap": score_data.get("biggest_gap", ""),
            "salary_estimate": score_data.get("salary_estimate", "")
        }
        all_scored.append(merged)

    high_scorers = [j for j in all_scored if j["score"] >= SCORE_THRESHOLD]
    print(f"[Generate Docs] {len(high_scorers)} jobs scored {SCORE_THRESHOLD}+ â€” proceeding to document generation")
    return all_scored, high_scorers

def tailor_resume_for_job(job):
    """Generate tailored resume for a specific job"""
    print(f"  [Tailor] Writing resume for {job['company']}...")

    tailor = Agent(
        role="Expert Resume Writer",
        goal="Rewrite resume to maximize interview chances for a specific role",
        backstory="""Professional resume writer specializing in cybersecurity
        and network engineering. You reframe real experience truthfully to
        match job requirements. You never invent experience.""",
        llm=llm,
        verbose=False
    )

    task = Task(
        description=f"""Tailor this resume for the job below.

JOB: {job['title']} at {job['company']}
KEY REQUIREMENT: {job['top_requirement']}
APPLY ANGLE: {job['apply_angle']}
DESCRIPTION: {job['description'][:1000]}

MASTER RESUME:
{MASTER_RESUME}

EXTENDED CANDIDATE PROFILE:
{EXTENDED_PROFILE}

Rewrite the resume optimizing for this specific role.
Keep all facts accurate. Reorder skills to put most relevant first.
Rewrite summary to mirror the job language.
Output complete resume only, no commentary.""",
        expected_output="Complete tailored resume",
        agent=tailor
    )

    crew = Crew(agents=[tailor], tasks=[task], verbose=False)
    return strip_think_tags(str(crew.kickoff()))

def write_cover_letter_for_job(job):
    """Generate cover letter for a specific job"""
    print(f"  [Writer] Writing cover letter for {job['company']}...")

    writer = Agent(
        role="Professional Cover Letter Writer",
        goal="Write compelling cover letters that get candidates interviews",
        backstory="""Expert cover letter writer for cybersecurity and network
        engineering roles. You write confident, specific letters that open
        with impact. Never generic. Never hollow phrases.""",
        llm=llm,
        verbose=False
    )

    task = Task(
        description=f"""Write a cover letter for this application.

JOB: {job['title']} at {job['company']}
APPLY ANGLE: {job['apply_angle']}
KEY REQUIREMENT: {job['top_requirement']}
DESCRIPTION: {job['description'][:1000]}

CANDIDATE PROFILE:
{EXTENDED_PROFILE}

Requirements:
- Open with impact, not "I am writing to apply"
- 4 paragraphs max, under 400 words
- Reference Citibank and Bank of America specifically
- Mention clearance eligibility
- End with confident call to action
- Never use: "passionate", "leverage", "team player", "great fit"

Output complete letter with header and signature.""",
        expected_output="Complete cover letter ready to send",
        agent=writer
    )

    crew = Crew(agents=[writer], tasks=[task], verbose=False)
    return strip_think_tags(str(crew.kickoff()))

def save_documents(job, resume, cover_letter, timestamp):
    """Save resume and cover letter for a job"""
    safe_company = job['company'].replace(" ", "_").replace("/", "-")[:25]

    resume_file = f"{RESUMES_DIR}\\resume_{safe_company}_{timestamp}.txt"
    with open(resume_file, "w", encoding="utf-8") as f:
        f.write(f"TAILORED RESUME: {job['title']} @ {job['company']}\n")
        f.write(f"Score: {job['score']}/10 | {job['verdict']}\n")
        f.write(f"URL: {job['url']}\n")
        f.write("=" * 60 + "\n\n")
        f.write(resume)

    cover_file = f"{COVER_LETTERS_DIR}\\cover_{safe_company}_{timestamp}.txt"
    with open(cover_file, "w", encoding="utf-8") as f:
        f.write(f"COVER LETTER: {job['title']} @ {job['company']}\n")
        f.write(f"Score: {job['score']}/10 | {job['verdict']}\n")
        f.write(f"URL: {job['url']}\n")
        f.write("=" * 60 + "\n\n")
        f.write(cover_letter)

    return resume_file, cover_file

def generate_doc_manifest(all_jobs, high_scorers, documents):
    """Generate manifest of documents generated this run (Step 3 output)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    today = datetime.now().strftime("%Y-%m-%d")

    lines = []
    lines.append("=" * 60)
    lines.append(f"  DOCUMENT MANIFEST -- {today}")
    lines.append(f"  Step 3: Generate Docs")
    lines.append("=" * 60)
    lines.append(f"\nJobs from Step 2 report: {len(all_jobs)}")
    lines.append(f"Docs generated (score >= {SCORE_THRESHOLD}): {len(high_scorers)}")

    if high_scorers:
        lines.append(f"\n[GENERATED] READY TO APPLY -- Documents Generated")
        lines.append("-" * 60)
        for job in high_scorers:
            if is_blocked(job['company']):
                continue
            doc = documents.get(job['company'], {})
            lines.append(f"\n  {job['title']}")
            lines.append(f"  Company: {job['company']}")
            lines.append(f"  Score: {job['score']}/10 | {job['verdict']}")
            lines.append(f"  Est. Salary: {job['salary_estimate']}")
            lines.append(f"  URL: {job['url']}")
            if doc.get('resume'):
                lines.append(f"  Resume: {os.path.basename(doc['resume'])}")
            if doc.get('cover'):
                lines.append(f"  Cover: {os.path.basename(doc['cover'])}")

    blocked_jobs = [j for j in high_scorers if is_blocked(j['company'])]
    if blocked_jobs:
        lines.append(f"\n[BLOCKED] BLOCKED -- Skipped document generation")
        lines.append("-" * 60)
        for job in blocked_jobs:
            reason = next((r for t, r in BLOCKLIST if t.lower() in job['company'].lower()), "")
            lines.append(f"  {job['score']}/10 | {job['title']} @ {job['company']}")
            lines.append(f"  Reason: {reason}")

    below = [j for j in all_jobs if j['score'] < SCORE_THRESHOLD]
    if below:
        lines.append(f"\n[BELOW THRESHOLD] score < {SCORE_THRESHOLD} -- No docs generated")
        lines.append("-" * 60)
        for job in sorted(below, key=lambda x: x['score'], reverse=True):
            lines.append(f"  {job['score']}/10 | {job['title']} @ {job['company']}")

    lines.append(f"\n{'=' * 60}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"{'=' * 60}\n")

    manifest_content = "\n".join(lines)
    manifest_file = f"{DOC_MANIFEST_DIR}\\doc_manifest_{timestamp}.txt"

    with open(manifest_file, "w", encoding="utf-8") as f:
        f.write(manifest_content)

    print(manifest_content)
    print(f"Manifest saved: {manifest_file}")

def run():
    print("=" * 60)
    print("  STEP 3: GENERATE DOCS")
    print(f"  Score threshold: {SCORE_THRESHOLD}+")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Load scout job data
    jobs = load_latest_jobs()
    if not jobs:
        return

    # Load scores from Step 2 report (no re-scoring)
    scores = load_scores_from_report()
    if not scores:
        return

    # Merge and filter
    all_scored, high_scorers = merge_jobs_with_scores(jobs, scores)

    if not high_scorers:
        print("\n[Generate Docs] No jobs met the threshold today.")
        generate_doc_manifest(all_scored, [], {})
        return

    # Generate documents for high scorers
    print(f"\n[Generate Docs] Generating documents for {len(high_scorers)} jobs...")
    documents = {}

    for job in high_scorers:
        if is_blocked(job['company']):
            continue
        print(f"\n  Processing: {job['title']} @ {job['company']} ({job['score']}/10)")
        resume = tailor_resume_for_job(job)
        cover = write_cover_letter_for_job(job)
        resume_file, cover_file = save_documents(job, resume, cover, timestamp)
        documents[job['company']] = {"resume": resume_file, "cover": cover_file}
        print(f"  >> Documents saved")

    # Generate manifest
    print(f"\n[Generate Docs] Writing doc manifest...")
    generate_doc_manifest(all_scored, high_scorers, documents)

    print(f"\n[Generate Docs] Step 3 complete. Review docs in 03.0_resumes and 03.1_cover_letters.")

if __name__ == "__main__":
    run()

