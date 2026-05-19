from crewai import Agent, Task, Crew, LLM
import json
import os
from datetime import datetime
import sys
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from config import PROFILE_PATH, LLM_MODEL, LLM_BASE_URL, JOB_DATA_DIR, JOB_REPORTS_DIR
from utils import parse_summary, strip_think_tags, is_structured_response

EXTENDED_PROFILE = ""
if os.path.exists(PROFILE_PATH):
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        EXTENDED_PROFILE = f.read()

# ── LLM config ───────────────────────────────────────────────────
llm = LLM(model=LLM_MODEL, base_url=LLM_BASE_URL)

# ── Agent definition ─────────────────────────────────────────────
analyst = Agent(
    role="Senior Technical Recruiter and Career Strategist",
    goal="Analyze job postings and provide actionable intelligence for a job seeker",
    backstory="""You are an expert technical recruiter with 15 years of experience 
    placing network engineers and cybersecurity professionals. You have deep knowledge 
    of the Jacksonville FL job market and remote tech roles. You give honest, direct 
    assessments including red flags and realistic fit scores.""",
    llm=llm,
    verbose=False  # Set to True if you want to see thinking process
)

import re
import signal
import threading

# strip_think_tags, parse_summary, is_structured_response imported from utils

# Hard timeout per job — kill analysis if it takes longer than this
JOB_TIMEOUT_SECONDS = 90


def _run_with_timeout(fn, timeout, *args, **kwargs):
    """Run fn(*args) in a thread; return result or None if timeout exceeded."""
    result = [None]
    exc    = [None]

    def target():
        try:
            result[0] = fn(*args, **kwargs)
        except Exception as e:
            exc[0] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        return None, TimeoutError(f"Exceeded {timeout}s timeout")
    if exc[0]:
        return None, exc[0]
    return result[0], None

def pre_score_job(job):
    """
    Fast LLM call — returns a confidence integer 1-10 in ~3-5 seconds.
    Used to skip full analysis on obvious mismatches.
    Returns None if the call fails (safe — job will still be analyzed).
    """
    title = job.get("title", "")
    desc  = job.get("description", "")[:800]   # first 800 chars is enough to judge

    task = Task(
        description=f"""Rate this job's fit for the candidate in ONE number only.

Candidate summary: Senior network security analyst / IT consultant.
Core strengths: firewall COMPLIANCE & AUDITING (not deployment), SIEM log analysis (Splunk),
NIST/GRC frameworks, SQL/VBA automation, compliance reporting, security metrics.
AI engineering side projects (CrewAI, Ollama, Python).
Does NOT have: hands-on firewall deployment, red teaming, OT/ICS, cloud networking (AWS/Azure),
penetration testing, Go/Rust, Kubernetes, active clearance.
Target: $100k+, Jacksonville FL or remote US.

Job title: {title}
Job description excerpt: {desc}

Reply with ONLY a single integer from 1 to 10.
1 = completely wrong fit. 10 = perfect match.
No explanation. No words. Just the number.""",
        expected_output="A single integer from 1 to 10",
        agent=analyst
    )
    try:
        crew   = Crew(agents=[analyst], tasks=[task], verbose=False)
        result = strip_think_tags(str(crew.kickoff())).strip()
        # Extract first number found
        match  = re.search(r'\b(10|[0-9])\b', result)
        return int(match.group(1)) if match else None
    except Exception as e:
        print(f"  [pre-score error] {e}", flush=True)
        return None

# Minimum pre-score to proceed to full analysis.
# Jobs scoring below this get logged but skipped.
PRE_SCORE_THRESHOLD = 5

def analyze_job(job):
    """Run the analyst agent against a single job"""
    
    # Skip jobs with no meaningful description
    if len(job.get("description", "")) < 150:
        return f"""FIT SCORE: N/A
TOP 5 REQUIRED SKILLS: Unable to analyze - insufficient job description
CANDIDATE MATCH: N/A
SKILL GAPS: N/A
SALARY ESTIMATE: Unknown
RED FLAGS: Job description too short to analyze properly
APPLICATION STRATEGY: Visit the job URL directly for full details
WORTH APPLYING: MAYBE
(Insufficient description - check URL directly)"""

    task = Task(
        description=f"""Analyze this job posting for a candidate with the following background:

CANDIDATE PROFILE:
{EXTENDED_PROFILE}

IMPORTANT DISTINCTION FOR SCORING:
The candidate's firewall experience is ANALYSIS and COMPLIANCE focused, not engineering/deployment focused.
Specifically:
- They analyzed and audited existing firewall rules (25,000+ rules)
- They automated compliance reporting using SQL/VBA
- They performed rule cleanup and policy compliance checks
- They did NOT design or architect firewall deployments from scratch
- They did NOT configure new firewall deployments via CLI
- They do NOT have Panorama, Prisma Access, SASE, SD-WAN, or cloud firewall experience
- They do NOT have AWS/Azure/GCP cloud networking experience

When scoring, PENALIZE heavily for roles requiring:
- Hands-on firewall configuration/deployment/engineering
- Panorama, Prisma Access, SASE, GlobalProtect administration
- Cloud networking (AWS VPC, Transit Gateway, Cloud NGFW)
- On-call incident response and network troubleshooting
- Packet captures and CLI-based diagnostics

REWARD highly for roles requiring:
- Firewall rule analysis, auditing, and compliance
- Security metrics and reporting automation
- IS governance and risk assessment
- CISO-level reporting and dashboards
- SQL/VBA/PowerShell automation
- Compliance frameworks (NIST, SOX, PCI-DSS)
- Information security analysis and GRC
- Splunk SIEM log analysis and evidence gathering
- Vulnerability identification using Palo Alto and Check Point built-in tools
- Network traffic analysis and dormant connectivity management
- NIST framework compliance
- ServiceNow and Jira workflow management
- User access provisioning and identity management
- SOP and technical documentation authoring
- Advanced Regex for complex data reconciliation
- BGP routing configuration experience
- Wireshark network analysis
- Ansible exposure (Red Hat workshops)
- Azure/O365 administration exposure
- Production-quality AI engineering project experience
- Prompt engineering and AI agent design (multi-agent orchestration, CrewAI)
- Local LLM deployment and optimization (Ollama, NVIDIA GPU)
- Production-quality AI pipeline development (Python, Flask, automation)
- Multi-agent system architecture and orchestration
- Real-time data pipeline development and API integration
- AI solution QA and output validation
- Technical documentation and SOP authoring for AI workflows
- Cross-functional stakeholder coordination and SME experience
- Training and onboarding documentation development
- Agile methodology experience including Jira sprint tracking and cross-departmental epic coordination

SALARY FILTER:
Candidate's previous rate was $62/hr (~$124k annually).
Target compensation: $100k-$130k minimum.
MANDATORY: if your SALARY ESTIMATE is below $90k, you MUST subtract 1.0 from the FIT SCORE
before writing it. Do not just flag it as a red flag — actually reduce the numeric score.
Example: skills match = 8.5, but salary is $80-90k → final FIT SCORE must be 7.5 or lower.

JOB POSTING:
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Source: {job['source']}
URL: {job['url']}

Description:
{job['description']}

Provide a structured analysis with exactly these sections:

FIT SCORE: X/10
(Score based on how well candidate background matches requirements)

TOP 5 REQUIRED SKILLS:
(List them)

CANDIDATE MATCH:
(Which of the required skills does the candidate already have?)

SKILL GAPS:
(What is the candidate missing?)

SALARY ESTIMATE:
(Estimate based on role, company, seniority if not listed)

RED FLAGS:
(Any concerns about this role or company?)

APPLICATION STRATEGY:
(Top 3 specific things to emphasize in the application given this candidate's background)

WORTH APPLYING: YES / MAYBE / NO
(With one sentence reason)""",
        expected_output="Structured job analysis with all sections filled in",
        agent=analyst
    )

    crew = Crew(agents=[analyst], tasks=[task], verbose=False)
    result = strip_think_tags(str(crew.kickoff()))

    # If LLM returned bare reasoning with no structure, retry once with stricter prompt
    if not is_structured_response(result):
        print("  [analyze] Unstructured response detected — retrying with strict prompt", flush=True)
        strict_task = Task(
            description=f"""You MUST respond ONLY in this exact format with no other text:

FIT SCORE: X/10
TOP 5 REQUIRED SKILLS: skill1, skill2, skill3, skill4, skill5
CANDIDATE MATCH: brief match summary
SKILL GAPS: brief gap summary
SALARY ESTIMATE: $X-$Y
RED FLAGS: any concerns
APPLICATION STRATEGY: top 3 things to emphasize
WORTH APPLYING: YES or MAYBE or NO

Job: {job['title']} at {job['company']}
Description excerpt: {job['description'][:500]}

Do not explain. Do not think aloud. Just fill in the format above.""",
            expected_output="Structured analysis in exact format",
            agent=analyst
        )
        crew2  = Crew(agents=[analyst], tasks=[strict_task], verbose=False)
        result = strip_think_tags(str(crew2.kickoff()))

    return result

def load_latest_jobs():
    """Load the most recent scout results"""
    files = [f for f in os.listdir(JOB_DATA_DIR) if f.startswith("jobs_")]

    if not files:
        print("No job files found. Run job_scout.py first.")
        return []

    latest = sorted(files)[-1]
    filepath = os.path.join(JOB_DATA_DIR, latest)
    print(f"Loading jobs from: {filepath}\n")
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def save_report(results):
    """Save analysis report as readable text file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(JOB_REPORTS_DIR, f"report_{timestamp}.txt")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("JOB SEARCH ANALYSIS REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, (job, analysis) in enumerate(results):
            f.write(f"JOB {i+1}: {job['title']} @ {job['company']}\n")
            f.write(f"Source: {job['source']} | Location: {job['location']}\n")
            f.write(f"URL: {job['url']}\n")
            f.write("-" * 60 + "\n")
            f.write(analysis)
            f.write("\n" + "=" * 60 + "\n\n")
    
    print(f"\nReport saved to: {filename}")
    return filename


def run():
    jobs = load_latest_jobs()

    if not jobs:
        return

    print(f"Found {len(jobs)} jobs to analyze.", flush=True)
    print(f"Starting analysis at {datetime.now().strftime('%H:%M:%S')}...\n", flush=True)

    results          = []
    skipped_prescore = []

    for i, job in enumerate(jobs):
        print(f"[Job {i+1}/{len(jobs)}] {job['title']} @ {job['company']}", flush=True)
        try:
            # Step 1: fast pre-score
            pre = pre_score_job(job)
            if pre is not None and pre < PRE_SCORE_THRESHOLD:
                print(f"  >> Pre-score: {pre}/10 — SKIPPED (below threshold {PRE_SCORE_THRESHOLD})", flush=True)
                skipped_prescore.append((job, pre))
                continue
            if pre is not None:
                print(f"  >> Pre-score: {pre}/10 — proceeding to full analysis", flush=True)

            # Step 2: full analysis with hard timeout
            analysis, err = _run_with_timeout(analyze_job, JOB_TIMEOUT_SECONDS, job)
            if err:
                timed_out = isinstance(err, TimeoutError)
                label = f"TIMEOUT after {JOB_TIMEOUT_SECONDS}s" if timed_out else f"ERROR: {err}"
                msg   = f"FIT SCORE: N/A\nWORTH APPLYING: N/A\n({label})"
                print(f"  >> {label}", flush=True)
                results.append((job, msg))
                continue
            results.append((job, analysis))

            score, worth = parse_summary(analysis)
            print(f"  >> FIT SCORE: {score}/10 | WORTH APPLYING: {worth}", flush=True)

        except Exception as e:
            print(f"  >> Error: {e}", flush=True)
            results.append((job, f"FIT SCORE: ERROR\nWORTH APPLYING: ERROR\n(Analysis exception: {e})"))

    print(f"\n[Analyze] Skipped {len(skipped_prescore)} jobs (pre-score < {PRE_SCORE_THRESHOLD})")
    print(f"[Analyze] Fully analyzed {len(results)} jobs")

    report_file = save_report(results)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for i, (job, analysis) in enumerate(results):
        score, worth = parse_summary(analysis)
        print(f"{i+1:>3}. {job['title']} @ {job['company']}")
        print(f"      Score: {score}/10 | {worth}", flush=True)

    print(f"\nFull report: {report_file}")

if __name__ == "__main__":
    run()

