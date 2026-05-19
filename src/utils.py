import re


def parse_summary(text):
    """Extract score and verdict strings from a single job analysis result."""
    score = "N/A"
    worth = "N/A"
    clean = text.replace("*", "").replace("#", "")
    for line in clean.split("\n"):
        line = line.strip()
        m = re.search(r'FIT SCORE\s*:\s*([0-9.]+|N/A|ERROR)', line, re.IGNORECASE)
        if m:
            score = m.group(1)
        m2 = re.search(r'WORTH APPLYING\s*:\s*(YES|MAYBE|NO|ERROR|N/A)', line, re.IGNORECASE)
        if m2:
            worth = m2.group(1).upper()
    return score, worth


def parse_report_text(text):
    """Parse a full multi-job report into a list of job result dicts.

    Each dict has: title, company, score (str), verdict, url, salary,
    top_requirement, apply_angle, biggest_gap.
    """
    results = []
    current = None

    for line in text.split("\n"):
        clean = line.strip().replace("**", "").replace("*", "")
        if line.startswith("JOB "):
            if current is not None:
                results.append(current)
            parts = line.split(": ", 1)
            if len(parts) > 1:
                job_parts = parts[1].split(" @ ", 1)
                current = {
                    "title":           job_parts[0].strip(),
                    "company":         job_parts[1].strip() if len(job_parts) > 1 else "",
                    "score":           "?",
                    "verdict":         "?",
                    "url":             "",
                    "salary":          "",
                    "top_requirement": "",
                    "apply_angle":     "",
                    "biggest_gap":     "",
                }
        elif current is not None:
            cl = clean.lower()
            if cl.startswith("fit score:"):
                raw = clean.split(":", 1)[1].strip()
                current["score"] = raw.split("/")[0].split()[0] if raw else "?"
            elif cl.startswith("worth applying:"):
                current["verdict"] = clean.split(":", 1)[1].strip().split()[0].upper()
            elif cl.startswith("url:") and "http" in clean:
                current["url"] = clean.split(":", 1)[1].strip()
            elif cl.startswith("salary estimate:"):
                current["salary"] = clean.split(":", 1)[1].strip()
            elif cl.startswith("top 5 required skills:") or cl.startswith("top requirement:"):
                current["top_requirement"] = clean.split(":", 1)[1].strip()
            elif cl.startswith("application strategy:"):
                current["apply_angle"] = clean.split(":", 1)[1].strip()
            elif cl.startswith("skill gaps:"):
                current["biggest_gap"] = clean.split(":", 1)[1].strip()

    if current is not None:
        results.append(current)

    return results
