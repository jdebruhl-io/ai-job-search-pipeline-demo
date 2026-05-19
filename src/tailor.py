from crewai import Agent, Task, Crew, LLM
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from config import PROFILE_PATH, RESUMES_DIR, LLM_MODEL, LLM_BASE_URL

llm = LLM(model=LLM_MODEL, base_url=LLM_BASE_URL)

# Your master resume content
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
Senior Network Security Analyst with 10+ years of experience in firewall compliance,
information security metrics, and infrastructure operations across major financial
institutions. Expertise in Palo Alto and Check Point firewall rule analysis, compliance
automation, and CISO-level reporting. Proven ability to design SQL/VBA-driven pipelines
that process 25,000+ firewall rules at enterprise scale. Currently expanding into AI
engineering — building local multi-agent systems with CrewAI and Ollama for security
workflow automation. Strong background in Cisco networking, governance, risk assessment,
and cross-functional stakeholder coordination.

PROFESSIONAL SKILLS:
Firewalls & Security: Palo Alto, Check Point, Fortinet, Cisco CLI/IOS,
firewall rule analysis, compliance, vulnerability identification
SIEM & Monitoring: Splunk (SIEM), network traffic analysis, Wireshark
Automation & Scripting: SQL (Impala), VBA, PowerShell, Python, Batch
scripting, Advanced Regex (nested VBA/SQL implementations)
Reporting & Analytics: Cognos Analytics, Advanced Excel, Power Query,
PivotTables, ServiceNow reporting, dashboard development
Compliance & Governance: NIST framework, IS governance, GRC, audit
support, risk assessment, SOP documentation
Project & Workflow: ServiceNow, Jira, change management, Agile methodologies (Scrum, iterative development)
Agile Methodologies: Jira sprint tracking, backlog management, cross-departmental epic coordination and project request management
Networking: BGP routing configuration (BofA network implementation),
Cisco CLI/IOS, network architecture
Identity & Access: User access provisioning, role-based access management,
identity management portal administration
Documentation: SOP authoring, technical documentation, process documentation
Certifications: CCNA (2016), Network+ (2015), A+ (2014)

WORKING KNOWLEDGE & EXPOSURE:
AI/ML Engineering (Independent Projects, Production-Quality, 2025-2026):
CrewAI, Ollama, LangChain, Flask, multi-agent systems, local LLM
deployment and optimization, NVIDIA GPU inference, automated pipeline
development, real-time web dashboards

Infrastructure & DevOps:
Ansible (Red Hat Summit workshops, OpenShift and AI model deployment),
Docker (containerized development), Git/GitHub (VS Code integration),
Linux (Raspberry Pi projects, CLI proficient with AI-assisted tooling)

Cloud & SaaS:
Azure (O365/Exchange administration, Gutter Helmet IT management),
Microsoft 365 administration, Cloud SaaS portal administration

Security Tools:
Wireshark (Cisco Academy + personal network analysis),
Privacy OS deployment (secure boot environments),
Pi-hole DNS filtering

EXPERIENCE:

Citibank (Contract - Matrix/Motion Recruitment) | Oct 2022 - Oct 2025 | Jacksonville, FL
Senior Network Security Analyst
- Designed and automated SQL and VBA-driven reporting pipelines to support CISO metrics,
  IS governance, and compliance tracking across global firewall infrastructure
- Produced monthly and ad-hoc Information Security reports using Cognos, Excel, and SQL
  datasets for executive management decision-making
- Built interactive Excel dashboards and visualizations for IS risk, firewall compliance,
  and connectivity metrics supporting executive visibility
- Developed data workflows to extract, transform, and standardize registration and firewall
  rule data across multiple systems (Cognos, Impala, Excel)
- Analyzed structured and unstructured datasets to identify discrepancies, assess security
  risk posture, and ensure alignment with IS policies and standards
- Partnered with IS program owners, technology teams, and risk management to gather data
  inputs, resolve data quality issues, and refine reporting accuracy
- Authored and maintained scripts and macros to automate periodic data refreshes,
  compliance checks, and report generation cycles
- Collaborated with stakeholders to improve metric and reporting dashboard processes,
  contributing to near real-time data visibility
- Reviewed connectivity requests during Annual Verification phase, validating ownership
  and registration details
- Performed firewall rule cleanup and compliance checks on Palo Alto and Check Point
  firewalls using scripts and structured analysis
- Responded to audit-related efforts to ensure firewall policy compliance with regulatory
  standards
- Utilized Splunk (SIEM) to run complex searches and queries against firewall log data
  for evidence gathering, connectivity analysis, and compliance investigation support
- Utilized built-in vulnerability identification and threat prevention features in Palo
  Alto and Check Point firewalls to identify and report security risks
- Managed user access provisioning and onboarding through enterprise identity management
  portal ensuring role-based access compliance
- Performed network traffic analysis to identify dormant connectivity, supporting firewall
  rule lifecycle management and decommissioning
- Ensured firewall compliance and reporting alignment with NIST cybersecurity framework
  standards
- Leveraged ServiceNow for change management ticketing, incident tracking, and compliance
  reporting workflows
- Authored and maintained SOPs and technical documentation for security processes,
  compliance workflows, and tool usage procedures
- Used Jira for project tracking and issue management
- Managed cross-departmental project epics in Jira, coordinating requests
  and priorities between management and delivery teams


Bank of America (Contract - The Select Group/Cisco) | Jun 2016 - Oct 2022 | Jacksonville, FL
Network Engineer
- Remotely coordinated banking center network upgrades and decommissioning using Cisco CLI/IOS
- Executed change orders on Cisco routers and switches supporting ATM network upgrades
- Collaborated with teams and lines of business to maintain firewall security rules per
  enterprise standards and lifecycle requirements
- Analyzed 25,000+ firewall security rules using bank database systems, SQL, and VBA
  automation to streamline large-scale compliance reporting
- Supported security metrics, compliance reporting, governance, and risk assessment programs
- Coordinated SSL/TLS certificate installation on network devices during hardware migrations
  and network upgrades

Gutter Helmet of North Florida | 2014 - 2019 | Jacksonville, FL
IT Consultant
- Managed all IT responsibilities at branch SOHO office including infrastructure and vendors
- Established and maintained Office 365 Exchange environment
- Managed location migration project for IT equipment and systems
- Implemented security monitoring system including cameras and viewing media

St. Johns River State College | 2013 - 2015 | Orange Park, FL
Cisco Academy Scholar | Network Engineer & Math Tutor | Office Assistant

EDUCATION:
St. Johns River State College | Orange Park, FL
Associate in Science, Computer Network Engineering Technology (2013-2015)
- Finalist & Top Achiever: NetRiders CCNA Competition (2015)
- Finalist: NetRiders CCENT Competition (2014)
- Graduated Cisco Networking Academy (2015)
- Dean's List (2013-2015)

College Credit Certificates:
Computer Specialist | Microcomputer Repair | Network Security |
Network Enterprise Administration | Network Infrastructure (Cisco) |
Cisco Certified Network Associate

CERTIFICATIONS:
CCNA Certified (Aug 2016)
CompTIA Network+ (April 2015)
CompTIA A+ (March 2014)

AI/AUTOMATION PROJECTS (2026):
- Built local multi-agent AI system using CrewAI + Ollama on NVIDIA RTX 4070 Super
  for automated job market intelligence and security workflow automation
- Developed Python-based web scraping pipeline that scouts job boards, scores postings
  against candidate profile, and generates tailored resume versions automatically
- Running and optimizing large language models locally for security-focused automation tasks

AI/ML ENGINEERING PROJECTS (Independent/Freelance, 2025-2026):
- Designed and built production-quality multi-agent job search automation
  system using CrewAI, Ollama, Flask, and Python
- Deployed local LLM infrastructure on NVIDIA RTX 4070 Super with full
  GPU utilization and network-accessible API serving
- Built automated web scraping pipelines integrating 6+ job board APIs
- Developed full-stack web dashboard with real-time streaming agent output
- Implemented Windows Task Scheduler for autonomous 7am daily pipeline execution
- All projects built to production standards: modular architecture, error
  handling, logging, API integration, and scalable design
"""

EXTENDED_PROFILE = ""
if os.path.exists(PROFILE_PATH):
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        EXTENDED_PROFILE = f.read()

# Jobs to tailor for - paste from your report
TARGET_JOBS = [
    {
        "title": "IT Specialist (INFOSEC)",
        "company": "Naval Facilities Engineering Systems Command",
        "url": "https://www.usajobs.gov:443/job/865830100",
        "key_requirements": """
        - Information security compliance (NIST, DoD regulations)
        - Firewall and perimeter security (Palo Alto, Check Point, Fortinet)
        - Security metrics, automation, and compliance reporting
        - Network engineering and infrastructure operations
        - Federal/government IT systems
        """,
        "application_strategy": """
        - Highlight private-sector INFOSEC experience as directly applicable
        - Emphasize firewall compliance, security metrics, and automation
        - Frame Bank of America scale (25,000+ rules) as enterprise-grade experience
        - Mention clearance eligibility prominently
        """
    },
    {
        "title": "IT Network Engineer",
        "company": "ECS",
        "url": "https://jobicy.com/jobs/141308-it-network-engineer",
        "key_requirements": """
        - Network monitoring tools and health reporting
        - DISA STIGs remediation and mitigation
        - Network architecture and process development
        - Program status reporting to leadership
        - Comply to Connect (C2C) implementation
        """,
        "application_strategy": """
        - Frame firewall compliance work as equivalent to DISA STIGs experience
        - Showcase SQL/VBA automation for monitoring and reporting
        - Mention AI/LLM skills as differentiator for process automation
        - Emphasize executive-level reporting experience
        """
    },
    {
        "title": "Technical Solutions Architect II - Network Security",
        "company": "World Wide Technology",
        "url": "",
        "key_requirements": """
        - Network security architecture and design
        - Cisco networking expertise
        - Security solutions and perimeter defense
        - Client-facing technical leadership
        - Firewall and infrastructure security
        """,
        "application_strategy": """
        - Lead with Cisco CLI/IOS and BofA network engineering experience
        - Emphasize Palo Alto/Check Point architecture knowledge
        - Frame 25,000+ rule analysis as large-scale architecture experience
        - Position AI automation as forward-thinking differentiator
        """
    }
]


def tailor_resume(job, master_resume):
    """Generate a tailored resume for a specific job"""
    
    tailor = Agent(
        role="Expert Resume Writer and Career Coach",
        goal="Rewrite resume bullets to maximize interview chances for a specific role",
        backstory="""You are a professional resume writer with 20 years of experience 
        specializing in cybersecurity, network engineering, and federal government positions. 
        You know exactly how to reframe experience to match job requirements while staying 
        100% truthful. You never invent experience — you reframe real experience using 
        the language and priorities of the target role.""",
        llm=llm,
        verbose=False
    )
    
    task = Task(
        description=f"""Rewrite this candidate's resume to be optimized for the following job.
        
TARGET JOB: {job['title']} at {job['company']}
URL: {job['url']}

KEY REQUIREMENTS:
{job['key_requirements']}

APPLICATION STRATEGY FROM ANALYSIS:
{job['application_strategy']}

MASTER RESUME:
{master_resume}

EXTENDED CANDIDATE PROFILE:
{EXTENDED_PROFILE}

Your task:
1. Rewrite the SUMMARY section to directly mirror the language of this job posting
2. Reorder and rewrite the SKILLS section to put the most relevant skills first
3. Rewrite each EXPERIENCE bullet to emphasize what this employer cares about
4. Keep all facts 100% accurate - only reframe, never invent
5. Add power verbs and quantify where possible
6. Output the complete rewritten resume ready to use

Format as a complete resume, not just bullet points.""",
        expected_output="Complete tailored resume optimized for the target role",
        agent=tailor
    )
    
    crew = Crew(agents=[tailor], tasks=[task], verbose=False)
    result = crew.kickoff()
    return str(result)


def run():
    print(f"Resume Tailor - Generating {len(TARGET_JOBS)} tailored resumes\n")
    print("Each resume takes 1-2 minutes. Please wait...\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for i, job in enumerate(TARGET_JOBS):
        print(f"[{i+1}/{len(TARGET_JOBS)}] Tailoring for: {job['title']} @ {job['company']}...")
        
        try:
            tailored = tailor_resume(job, MASTER_RESUME)
            
            # Save each tailored resume as its own file
            safe_company = job['company'].replace(" ", "_").replace("/", "-")[:30]
            filename = os.path.join(RESUMES_DIR, f"resume_{safe_company}_{timestamp}.txt")
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"TAILORED RESUME: {job['title']} @ {job['company']}\n")
                f.write(f"URL: {job['url']}\n")
                f.write("=" * 60 + "\n\n")
                f.write(tailored)
            
            print(f"  → Saved to: {filename}")
        
        except Exception as e:
            print(f"  → Error: {e}")
    
    print(f"\nAll tailored resumes saved to {RESUMES_DIR}")
    print("Open each file, review carefully, then paste into your resume template.")


if __name__ == "__main__":
    run()

