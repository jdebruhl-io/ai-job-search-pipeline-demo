from crewai import Agent, Task, Crew, LLM
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from config import PROFILE_PATH, COVER_DIR, LLM_MODEL, LLM_BASE_URL

llm = LLM(model=LLM_MODEL, base_url=LLM_BASE_URL)

# Your personal details for the letter header
YOUR_INFO = """
James T Debruhl
Jacksonville, FL 32259
LinkedIn: linkedin.com/in/james-debruhl-b017aa66
Security Clearance: Eligible
Previous Rate: $62/hr (~$124k annually)
"""

# Your master background for the writer to draw from

EXTENDED_PROFILE = ""
if os.path.exists(PROFILE_PATH):
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        EXTENDED_PROFILE = f.read()

# Jobs to write cover letters for
TARGET_JOBS = [
    {
        "title": "IT Specialist (INFOSEC)",
        "company": "Naval Facilities Engineering Systems Command",
        "hiring_manager": "Hiring Manager",
        "url": "https://www.usajobs.gov:443/job/865830100",
        "key_requirements": """
        - Information security compliance (NIST, DoD regulations)
        - Firewall and perimeter security (Palo Alto, Check Point, Fortinet)
        - Security metrics, automation, and compliance reporting
        - Network engineering and infrastructure operations
        """,
        "tone": "formal federal government",
        "key_angle": """
        Emphasize that private sector INFOSEC at Citibank scale directly translates
        to federal requirements. Highlight clearance eligibility. Frame the 25,000+
        firewall rule analysis at BofA as enterprise-grade experience equivalent to
        DoD environments. Express genuine interest in serving in a federal role at
        NAS Jacksonville specifically as a local candidate.
        """
    },
    {
        "title": "IT Network Engineer",
        "company": "ECS",
        "hiring_manager": "Hiring Manager",
        "url": "https://jobicy.com/jobs/141308-it-network-engineer",
        "key_requirements": """
        - DISA STIGs remediation and mitigation
        - Network monitoring tools and health reporting
        - Program status reporting to leadership
        - Comply to Connect (C2C) implementation
        """,
        "tone": "professional defense contractor",
        "key_angle": """
        Frame firewall compliance work as directly equivalent to DISA STIGs experience.
        Lead with automation and reporting credentials. Position AI/LLM skills as a
        unique differentiator that modernizes traditional network engineering work.
        Mention clearance eligibility as a practical asset for defense contractor work.
        """
    },
    {
        "title": "Technical Solutions Architect II - Network Security",
        "company": "World Wide Technology",
        "hiring_manager": "Hiring Manager",
        "url": "",
        "key_requirements": """
        - Network security architecture and design
        - Cisco networking expertise
        - Security solutions and perimeter defense
        - Client-facing technical leadership
        """,
        "tone": "professional technology company",
        "key_angle": """
        Lead with Cisco expertise from BofA — WWT is a massive Cisco partner so this
        is the primary hook. Emphasize the architecture and design aspect of managing
        25,000+ firewall rules at enterprise scale. Position AI automation work as
        forward-thinking differentiation that adds value to client engagements.
        """
    }
]

def write_cover_letter(job, background, your_info):
    """Generate a tailored cover letter for a specific job"""

    writer = Agent(
        role="Professional Cover Letter Writer",
        goal="Write compelling cover letters that get candidates interviews",
        backstory="""You are an expert cover letter writer with 20 years of experience
        helping cybersecurity and network engineering professionals land roles at top
        companies and federal agencies. You write letters that are confident, specific,
        and human — never generic or robotic. You know that the best cover letters tell
        a story that connects the candidate's specific experience to the employer's
        specific needs. You never use hollow phrases like 'I am writing to express my
        interest' or 'I would be a great fit'. You open with impact.""",
        llm=llm,
        verbose=False
    )

    task = Task(
        description=f"""Write a compelling cover letter for this job application.

CANDIDATE INFO:
{your_info}

CANDIDATE PROFILE:
{background}

TARGET JOB:
Title: {job['title']}
Company: {job['company']}
URL: {job['url']}
Tone: {job['tone']}

KEY REQUIREMENTS:
{job['key_requirements']}

STRATEGIC ANGLE — what to emphasize:
{job['key_angle']}

COVER LETTER REQUIREMENTS:
1. Open with a strong hook — not "I am writing to apply for"
2. Paragraph 1: Connect most relevant experience directly to their biggest need
3. Paragraph 2: Specific achievement or project that proves capability
4. Paragraph 3: Why this company/role specifically — show you did research
5. Closing: Confident call to action
6. Keep it to 4 paragraphs max, under 400 words
7. Match the tone specified ({job['tone']})
8. Address to: {job['hiring_manager']}
9. Never use these phrases: "I am writing to", "I would be a great fit",
   "passionate about", "leverage my skills", "team player"
10. Be specific — use real numbers and technologies from the background

Format as a complete ready-to-send letter including date, address block, salutation,
body, and professional closing.""",
        expected_output="Complete professional cover letter ready to send",
        agent=writer
    )

    crew = Crew(agents=[writer], tasks=[task], verbose=False)
    result = crew.kickoff()
    return str(result)

def run():
    print(f"Cover Letter Generator - Writing {len(TARGET_JOBS)} letters\n")
    print("Each letter takes 1-2 minutes. Please wait...\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, job in enumerate(TARGET_JOBS):
        print(f"[{i+1}/{len(TARGET_JOBS)}] Writing for: {job['title']} @ {job['company']}...")

        try:
            letter = write_cover_letter(job, EXTENDED_PROFILE, YOUR_INFO)

            safe_company = job['company'].replace(" ", "_").replace("/", "-")[:30]
            filename = os.path.join(COVER_DIR, f"cover_letter_{safe_company}_{timestamp}.txt")

            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"COVER LETTER: {job['title']} @ {job['company']}\n")
                f.write(f"URL: {job['url']}\n")
                f.write("=" * 60 + "\n\n")
                f.write(letter)

            print(f"  >> Saved to: {filename}")

        except Exception as e:
            print(f"  >> Error: {e}")

    print(f"\nAll cover letters saved to {COVER_DIR}")
    print("Review each one carefully before sending.")
    print("Personalize the hiring manager name if you can find it on LinkedIn.")

if __name__ == "__main__":
    run()

