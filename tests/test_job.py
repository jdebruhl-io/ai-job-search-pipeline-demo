from crewai import Agent, Task, Crew, LLM
import sys
sys.stdout.reconfigure(line_buffering=True)

llm = LLM(
    model="ollama/qwen3:14b",
    base_url="http://localhost:11434"
)

MY_BACKGROUND = """
James T Debruhl | Jacksonville FL | CCNA, Network+, A+
Clearance: Eligible | Previous rate: $62/hr (~$124k)

Citibank (Contract - Matrix/Motion Recruitment) Oct 2022 - Oct 2025
Senior Network Security Analyst
- SQL/VBA-driven reporting pipelines for CISO metrics and IS governance
- Monthly Information Security reports using Cognos, Excel, SQL
- Interactive dashboards for IS risk, firewall compliance, connectivity metrics
- Firewall rule cleanup and compliance checks on Palo Alto and Check Point
- Audit support ensuring firewall policy compliance with regulatory standards
- Scripts and macros automating data refreshes and compliance checks
- Utilized Splunk (SIEM) to run complex searches and queries against firewall log data for evidence gathering, connectivity analysis, and compliance investigation support
- Utilized built-in vulnerability identification and threat prevention features in Palo Alto and Check Point firewalls to identify and report security risks
- Managed user access provisioning and onboarding through enterprise identity management portal ensuring role-based access compliance
- Performed network traffic analysis to identify dormant connectivity, supporting firewall rule lifecycle management and decommissioning
- Ensured firewall compliance and reporting alignment with NIST cybersecurity framework standards
- Leveraged ServiceNow for change management ticketing, incident tracking, and compliance reporting workflows
- Authored and maintained SOPs and technical documentation for security processes, compliance workflows, and tool usage procedures
- Used Jira for project tracking and issue management
- Managed cross-departmental project epics in Jira, coordinating requests and priorities between management and delivery teams

Bank of America (Contract - The Select Group/Cisco) Jun 2016 - Oct 2022
Network Engineer
- Banking center network upgrades using Cisco CLI/IOS
- Analyzed 25,000+ firewall security rules using SQL and VBA automation
- Change orders on Cisco routers and switches for ATM network upgrades
- Maintained firewall security rules per enterprise standards
- Coordinated SSL/TLS certificate installation on network devices during hardware migrations and network upgrades

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

AI Projects 2026: Built local multi-agent job search system
"""

# Load extended profile if available
import os
PROFILE_PATH = "C:\\ai-agents\\ai-job-search-pipeline\\data\\james_profile.md"
EXTENDED_PROFILE = ""
if os.path.exists(PROFILE_PATH):
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        EXTENDED_PROFILE = f.read()

IMPORTANT_DISTINCTION = """
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
"""

# Paste any job description here to test scoring
TEST_JOB = {
    "title": "Sr Prompt Engineer - AI Innovation",
    "company": "SitusAMC",
    "location": "Remote",
    "description": """
    This role is responsible for the development and execution of AI-driven 
    solutions within the residential real estate division. Responsible for 
    crafting sophisticated prompts and overseeing the design of advanced agents 
    to enhance operational efficiency, optimize customer engagement, and drive 
    digital transformation. Serves as Subject Matter Expert for others on the 
    delivery team.
    
    Essential Functions:
    - Develop AI solutions by creating sophisticated agents and prompts
    - Ensure AI models are built with scalability, reliability, and compliance
    - Serve as primary contact for delivery team questions on best practices
    - Perform quality assurance reviews of delivery team work
    - Manage cross-team coordination with VP and stakeholders
    - Maintain and improve delivery team training documentation
    - Plan and execute onboarding and ongoing training for delivery team
    - Partner with Training department on formal curricula design
    
    Requirements:
    - 6+ years experience
    - Knowledge of Agile methodologies
    - Strong analytical skills
    - Previous SME or trainer experience embedded in delivery team
    - Excellent communication and cross-functional collaboration skills
    """
}

analyst = Agent(
    role="Senior Technical Recruiter and Career Strategist",
    goal="Quickly score jobs for fit and return only the best matches",
    backstory="""Expert technical recruiter specializing in cybersecurity
    and network engineering. You give fast, accurate fit scores and
    identify the top opportunities worth pursuing.""",
    llm=llm,
    verbose=False
)

task = Task(
    description=f"""Score this job for the candidate. Be concise.

CANDIDATE: {MY_BACKGROUND}

EXTENDED CANDIDATE PROFILE:
{EXTENDED_PROFILE}

{IMPORTANT_DISTINCTION}

JOB:
Title: {TEST_JOB['title']}
Company: {TEST_JOB['company']}
Location: {TEST_JOB['location']}
Description: {TEST_JOB['description']}

Respond with ONLY this format, nothing else:
SCORE: X.X
VERDICT: YES/MAYBE/NO
TOP_REQUIREMENT: [single most important requirement]
BIGGEST_GAP: [single biggest gap or NONE]
SALARY_EST: [estimated salary range]
APPLY_ANGLE: [one sentence on how to position application]""",
    expected_output="Concise structured scoring in exact format specified",
    agent=analyst
)

crew = Crew(agents=[analyst], tasks=[task], verbose=False)
result = str(crew.kickoff())
print("\n=== SCORE RESULT ===")
print(result)
