"""Smoke tests for utils.parse_summary and utils.parse_report_text."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from utils import parse_summary, parse_report_text

def test_parse_summary():
    score, worth = parse_summary("FIT SCORE: 8/10\nWORTH APPLYING: YES\n(Good match)")
    assert score == "8", f"score={score}"
    assert worth == "YES", f"worth={worth}"

    score2, worth2 = parse_summary("FIT SCORE: N/A\nWORTH APPLYING: MAYBE")
    assert score2 == "N/A"
    assert worth2 == "MAYBE"
    print("test_parse_summary PASSED")

def test_parse_report_text():
    sample = (
        "JOB 1: Senior Security Analyst @ Citigroup\n"
        "Source: LinkedIn | Location: Remote\n"
        "URL: https://example.com/job1\n"
        "FIT SCORE: 8/10\n"
        "TOP 5 REQUIRED SKILLS: SIEM, firewall auditing, GRC, NIST, SQL\n"
        "SALARY ESTIMATE: $120k-$140k\n"
        "SKILL GAPS: None significant\n"
        "APPLICATION STRATEGY: Emphasize Citibank experience\n"
        "WORTH APPLYING: YES\n"
        "============================================================\n"
        "\n"
        "JOB 2: Firewall Engineer @ Palo Alto Networks\n"
        "Source: Indeed | Location: Jacksonville FL\n"
        "URL: https://example.com/job2\n"
        "FIT SCORE: 4/10\n"
        "TOP 5 REQUIRED SKILLS: Panorama, SASE, BGP\n"
        "SALARY ESTIMATE: $130k\n"
        "SKILL GAPS: Panorama, SASE, deployment\n"
        "APPLICATION STRATEGY: N/A\n"
        "WORTH APPLYING: NO\n"
        "============================================================\n"
    )

    jobs = parse_report_text(sample)
    assert len(jobs) == 2, f"expected 2 jobs, got {len(jobs)}"

    j0 = jobs[0]
    assert j0["title"] == "Senior Security Analyst", f"title={j0['title']}"
    assert j0["company"] == "Citigroup", f"company={j0['company']}"
    assert j0["score"] == "8", f"score={j0['score']}"
    assert "YES" in j0["verdict"], f"verdict={j0['verdict']}"
    assert j0["url"] == "https://example.com/job1", f"url={j0['url']}"
    assert "$120k" in j0["salary"], f"salary={j0['salary']}"
    assert "SIEM" in j0["top_requirement"], f"top_req={j0['top_requirement']}"

    j1 = jobs[1]
    assert j1["score"] == "4", f"score={j1['score']}"
    assert "NO" in j1["verdict"], f"verdict={j1['verdict']}"

    print(f"test_parse_report_text PASSED ({len(jobs)} jobs parsed)")
    print(f"  Job 1: {j0['title']} @ {j0['company']} | score={j0['score']} verdict={j0['verdict']}")
    print(f"  Job 2: {j1['title']} @ {j1['company']} | score={j1['score']} verdict={j1['verdict']}")

if __name__ == "__main__":
    test_parse_summary()
    test_parse_report_text()
    print("\nALL TESTS PASSED")
