from crewai import Agent, Task, Crew, LLM

# Point CrewAI at your local Ollama model
llm = LLM(
    model="ollama/qwen3:14b",
    base_url="http://localhost:11434"
)

# Define your agent
analyst = Agent(
    role="Job Description Analyst",
    goal="Analyze job descriptions and identify key requirements",
    backstory="""You are an expert technical recruiter with 10 years 
    of experience in AI, cybersecurity, and network engineering roles. 
    You extract key insights from job postings.""",
    llm=llm,
    verbose=True
)

# The job description to analyze - paste a real one here
job_description = """
About the job
We are looking for a Cybersecurity Analyst to help protect the organization’s systems, data, and users through active monitoring, investigation, and response to security events. This Long-term Contract position is based in Jacksonville, Florida, and offers the opportunity to support daily security operations while strengthening vulnerability management, compliance readiness, and security awareness efforts. The ideal candidate brings hands-on experience in cybersecurity analysis and enjoys working across teams to reduce risk and improve response capabilities.

Responsibilities:
• Monitor security events across SIEM, endpoint, email, and cloud-based security platforms to identify suspicious activity and escalate issues as needed.
• Examine phishing attempts, malware activity, unauthorized access events, and unusual account behavior to determine severity and next steps.
• Perform incident triage, analyze contributing factors, and help define containment, remediation, and recovery actions.
• Partner with infrastructure and IT operations teams to resolve security issues and restore affected services efficiently.
• Maintain thorough records of investigations, response actions, and outcomes to support reporting and future review.
• Use threat intelligence and indicator analysis to refine detections and recognize developing attack trends across the environment.
• Support vulnerability scanning efforts, follow remediation progress with system owners, and confirm that identified weaknesses have been addressed.
• Assist with audit preparation and compliance activities by organizing evidence, documenting controls, and supporting regulatory security requirements.
• Contribute to security awareness initiatives such as phishing exercises and training efforts, and recommend improvements to detection logic, playbooks, and response workflows.
• At least 2 years of experience in cybersecurity, with broader IT background in systems administration, engineering, or security operations strongly preferred.
• Hands-on familiarity with SIEM tools, endpoint protection platforms, cloud security monitoring, and incident investigation practices.
• Working knowledge of threats such as phishing, malware, privilege misuse, and anomalous user activity patterns.
• Experience with vulnerability management, patch tracking, and remediation coordination across technical teams.
• Understanding of cybersecurity frameworks and compliance standards such as NIST, PCI DSS, and MITRE ATT& CK.
• Strong written and verbal communication skills with the ability to document incidents clearly and collaborate with technical and business stakeholders.
• Relevant certifications such as ISC2 CC, CompTIA Security+, CEH, AZ-500, SC-200, or similar credentials are preferred.
"""

my_background = """
10+ years network engineering experience
Network security analyst with expertise in firewall compliance (Palo Alto, Check Point), specializing in Information Security metrics, automation, and compliance reporting registration governance, and risk assessment. Skilled in SQL and VBA automation to streamline large - scale data analysis and reporting for compliance programs. Strong background in Cisco networking, network perimeter security, and infrastructure operations.
Advanced Excel, VBA, Power Query, PivotTables • SQL (Impala), Cognos Analytics • AI foundations, LLM, Agents, Ansible • Reporting pipelines, dashboards, metrics • Data extraction, normalization, reconciliation • Risk metrics, compliance reporting • Risk Analysis, Data Discrepancy Analysis • Incident Response Support, Security Investigations • Palo Alto, Check Point, Fortinet • Firewall rule analysis, cleanup, compliance • Network perimeter security • Connectivity validation • Governance / audit support • PowerShell • Workflow automation • Tool building • Macro - driven pipelines • Process optimization • Data quality controls • Stakeholder coordination • Program owners • Reporting governance • Cross - team integration • Technical Leadership, Mentoring
James T Debruhl Bank of America (Contract - The Select Group, LLC. – Cisco) Jun 2016 - Oct 2022 Jacksonville, FL Network Engineer ▪ Remotely coordinate banking center network upgrades/decommissioning using Cisco CLI/IOS. ▪ Execute change orders on Cisco routers and switches for support of ATM network upgrades. ▪ Collaboration with team members and lines of business to ensure firewall security rules are maintained according to current bank standards and lifecycle. ▪ Coordinated use of various bank database systems to analyze large sets (25,000+) of firewall security rules. Gutter Helmet of North Florida 2014 - 2019 Jacksonville, FL IT Consultant ▪ Manage all IT - related responsibilities at the branch SOHO office ▪ Establish and maintain Office 365 exchange environment ▪ Manage location migration project for IT - related equipment and systems ▪ Implement security - monitoring system including cameras and viewing media St. Johns River State College 2013 - 2015 Cisco Academy Scholar Network Engineer & Math Tutor & Office Assistant Education St. Johns River State College Orange Park, FL Associate in Science , Computer Network Engineering Technology 2013 - 2015 ▪ Finalist & Top Achiever: NetRiders CCNA Competition (2015) ▪ Finalist: NetRiders CCENT Competition (2014) ▪ Graduated from Cisco Networking Academy ( 2015) ▪ Dean’s List (2013 - 2015) College Credit Certificates (CCC) ▪ Computer Specialist ▪ Microcomputer Repair ▪ Network Security ▪ Network Enterprise Administration ▪ Network Infrastructure (CISCO) ▪ Cisco Certified Network Associate St. Johns River State College Orange Park, FL Associate in Arts degree 2013 - 2014 Certifications CCNA Certified (Aug 2016) CCENT Certified (March 2015) CompTIA A+ Certified (March 2014) CompTIA Network+ Certified (April 201 5) 
Currently adding: AI agents, local LLMs, Python, CrewAI
"""

# Define the task
task = Task(
    description=f"""Analyze this job description and provide:
    1. Top 8 required technical skills
    2. Top 3 nice-to-have skills  
    3. Seniority level and why
    4. Red flags or concerns if any
    5. Gap analysis: compare the requirements against this background:
    {my_background}
    6. Top 3 things I should emphasize in my application
    
    Job Description:
    {job_description}""",
    expected_output="A structured analysis with clear sections for each point",
    agent=analyst
)

# Run it
crew = Crew(agents=[analyst], tasks=[task], verbose=True)
result = crew.kickoff()

print("\n=== FINAL ANALYSIS ===")
print(result)

