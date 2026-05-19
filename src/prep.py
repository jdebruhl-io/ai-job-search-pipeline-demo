from crewai import Agent, Task, Crew, LLM
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from config import PROFILE_PATH, INTERVIEW_DIR, LLM_MODEL, LLM_BASE_URL

llm = LLM(model=LLM_MODEL, base_url=LLM_BASE_URL)

EXTENDED_PROFILE = ""
if os.path.exists(PROFILE_PATH):
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        EXTENDED_PROFILE = f.read()

# Fill this in when you get a callback
ACTIVE_JOB = {
    "title": "Technical Solutions Architect II - Network Security",
    "company": "World Wide Technology",
    "interview_stage": "Phone Screen",  # Phone Screen / Technical / Final / Panel
    "job_description": """
    Paste the full job description here when you get a callback.
    The more detail the better — requirements, responsibilities, 
    company culture info, anything from the posting.
    """,
    "interviewer_info": """
    Add anything you know about who's interviewing you.
    Name, title, LinkedIn info, how long they've been at the company.
    Leave blank if unknown.
    """,
    "company_research": """
    Add any notes about the company you've gathered.
    Recent news, their clients, tech stack, culture, glassdoor reviews.
    Leave blank and the agent will work from general knowledge.
    """
}

def generate_prep_package(job, background):
    """Generate complete interview prep package"""

    researcher = Agent(
        role="Interview Research Specialist",
        goal="Research the company and role to identify likely interview topics and questions",
        backstory="""You are an expert interview coach with 20 years experience preparing
        candidates for technical roles in cybersecurity and network engineering. You have
        deep knowledge of how major tech companies, defense contractors, and financial firms
        conduct technical interviews. You know exactly what interviewers look for at each
        stage — phone screen vs technical vs final round.""",
        llm=llm,
        verbose=False
    )

    prep_task = Task(
        description=f"""Generate a comprehensive interview prep package for this candidate
and role. Be specific, practical, and honest about gaps.

CANDIDATE PROFILE:
{background}

TARGET ROLE:
Title: {job['title']}
Company: {job['company']}
Interview Stage: {job['interview_stage']}

JOB DESCRIPTION:
{job['job_description']}

INTERVIEWER INFO:
{job['interviewer_info']}

COMPANY RESEARCH:
{job['company_research']}

Generate a complete prep package with these exact sections:

## COMPANY BRIEF
3-4 sentences on what this company does, their market position,
and what they care about in candidates. Include anything specific
to this role.

## WHAT THIS STAGE IS TESTING
What the {job['interview_stage']} stage is specifically evaluating.
What they're trying to learn about you. What gets candidates cut here.

## LIKELY QUESTIONS WITH YOUR ANSWERS
Generate 10 likely interview questions for this role and stage.
For each question provide:
- The question
- Why they ask it
- Your specific answer drawing from YOUR background (not generic)
- What to avoid saying

Format each as:
Q: [question]
WHY: [why they ask]
YOUR ANSWER: [specific answer using James's actual experience]
AVOID: [what not to say]

## TECHNICAL TOPICS TO REVIEW
List 5 specific technical areas to brush up on before this interview
based on the job requirements and your gaps. For each give a
1-2 sentence study guide on what to focus on.

## YOUR STRONGEST TALKING POINTS
Top 5 things from your background that are most relevant to this
specific role. These are your anchors — bring conversations back
to these.

## QUESTIONS TO ASK THEM
5 smart questions to ask the interviewer that show genuine interest
and research. Avoid generic questions.

## SALARY NEGOTIATION NOTES
Given the role, company, and candidate's previous rate of $62/hr
($124k), provide specific negotiation guidance for this role.
What to say when they ask about salary expectations.

## RED FLAGS TO WATCH FOR
2-3 things in the interview that should raise concerns about
this role or company.""",
        expected_output="Complete interview prep package with all sections",
        agent=researcher
    )

    crew = Crew(agents=[researcher], tasks=[prep_task], verbose=False)
    result = crew.kickoff()
    return str(result)

def run():
    print(f"Interview Prep Agent")
    print(f"Preparing for: {ACTIVE_JOB['title']} @ {ACTIVE_JOB['company']}")
    print(f"Stage: {ACTIVE_JOB['interview_stage']}")
    print(f"\nGenerating prep package... (2-3 minutes)\n")

    try:
        prep = generate_prep_package(ACTIVE_JOB, EXTENDED_PROFILE)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_company = ACTIVE_JOB['company'].replace(" ", "_")[:30]
        filename = os.path.join(INTERVIEW_DIR, f"interview_prep_{safe_company}_{timestamp}.txt")

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"INTERVIEW PREP: {ACTIVE_JOB['title']} @ {ACTIVE_JOB['company']}\n")
            f.write(f"Stage: {ACTIVE_JOB['interview_stage']}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write("=" * 60 + "\n\n")
            f.write(prep)

        print(f"Prep package saved to: {filename}")
        print(f"\nOpen it, read it tonight, sleep on it.")
        print(f"You know this material — the agent is just organizing it.\n")

    except Exception as e:
        print(f"Error generating prep: {e}")

if __name__ == "__main__":
    run()

