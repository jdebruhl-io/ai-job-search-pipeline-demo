import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from config import JOB_DATA_DIR

import html as _html
import re as _re
import requests
import json
import time
from datetime import datetime

# ════════════════════════════════════════════════════════════════
#  SOURCE TOGGLE — flip enabled: True/False to turn sources on/off
#  FREE sources are on by default.
#  PAID / FRAGILE sources are off — enable when you're ready.
# ════════════════════════════════════════════════════════════════
SOURCE_CONFIG = {
    # ── FREE & RELIABLE ─────────────────────────────────────────
    "usajobs":       {"enabled": True,  "tier": "free",  "note": "Federal jobs API, free key"},
    "adzuna":        {"enabled": True,  "tier": "free",  "note": "Free tier 250 calls/day"},
    "infosec_jobs":  {"enabled": True,  "tier": "free",  "note": "RSS feed, no auth"},
    "ai_jobs":       {"enabled": True,  "tier": "free",  "note": "RSS feed, no auth"},
    "greenhouse":    {"enabled": True,  "tier": "free",  "note": "Public ATS API, no auth"},
    "lever":         {"enabled": True,  "tier": "free",  "note": "Public ATS API, no auth"},
    "ashby":         {"enabled": True,  "tier": "free",  "note": "Public ATS API, no auth"},
    "workday":       {"enabled": True,  "tier": "free",  "note": "Public CXS endpoint, no auth"},
    "smartrecruiters": {"enabled": True, "tier": "free", "note": "Public ATS API, no auth"},

    # ── FREE BUT FRAGILE (low-quality aggregators) ───────────────
    "remoteok":      {"enabled": True,  "tier": "free",  "note": "Often 0 results for cyber"},
    "remotive":      {"enabled": True,  "tier": "free",  "note": "Often 0 results for cyber"},
    "jobicy":        {"enabled": True,  "tier": "free",  "note": "Low signal but free"},
    "jooble":        {"enabled": False, "tier": "free",  "note": "High volume, low quality — disabled"},

    # ── PAID / REQUIRES ACCOUNT — disabled until ready ───────────
    # To enable: set enabled: True and ensure credentials are set
    "linkedin_guest": {"enabled": False, "tier": "fragile",
                       "note": "Guest API, breaks often, ToS gray area — enable when ready"},
    "clearancejobs":  {"enabled": False, "tier": "paid",
                       "note": "Apify scraper ~$10-30/mo — highest signal for defense roles"},
    "dice":           {"enabled": False, "tier": "paid",
                       "note": "Apify scraper ~$5-10/mo — good for IT contracting"},
}

YOUR_ZIP = "32259"
YOUR_CITY = "Jacksonville"
YOUR_STATE = "FL"

# ── Role filter terms ────────────────────────────────────────────
RELEVANT_TITLE_TERMS = [
    "firewall", "network security", "security analyst", "information security",
    "security engineer", "security compliance", "network engineer",
    "infrastructure security", "cybersecurity", "vulnerability",
    "ai security", "devsecops", "soc analyst", "incident response",
    "security architect", "it consultant", "security consultant",
    "ai engineer", "machine learning engineer", "mlops",
    "grc", "compliance analyst", "prompt engineer",
]

EXCLUDE_TERMS = [
    "sales", "marketing", "account executive", "copywriter",
    "designer", "creative", "counselor", "interior", "healthcare account",
    "revenue specialist", "advertising", "videograf", "social media",
    "influencer", "affiliate", "product manager", "project manager",
    "legal", "finance", "controller", "android", "ios", "mobile",
]

# ── Pre-filter: disqualify before LLM analysis ───────────────────
# Jobs matching ANY of these in title+description get dropped immediately.
# Keep this list focused on things that are genuinely never a fit.
PRE_FILTER_DISQUALIFY = [
    # Wrong discipline entirely
    "penetration test", "pen test", "red team", "offensive security",
    "exploit development", "malware analysis", "reverse engineer",
    "ot/ics", "industrial control", "scada", "operational technology",
    # Requires certs/skills you explicitly don't have
    "panorama", "prisma access", "sase", "sd-wan",
    "aws vpc", "transit gateway", "cloud ngfw", "azure firewall",
    "terraform", "kubernetes", "docker security",
    # Wrong seniority / clearly junior
    "entry level", "entry-level", "junior ", " intern", "internship",
    "0-2 years", "1-2 years", "1+ year",
    # Wrong geography (non-US postings)
    "australia", "canberra", "germany", "stuttgart", "uk only",
    "farnborough", "london only", "canada only", "ontario only",
    # Wrong role type
    "go engineer", "rust engineer", "mobile security",
    "game security", "blockchain security",
]

# Jobs matching ANY of these get a confidence BOOST in pre-scoring
PRE_FILTER_STRONG_MATCH = [
    "firewall compliance", "firewall rule", "firewall audit",
    "network security analyst", "information security analyst",
    "security reporting", "security metrics", "compliance automation",
    "nist", "grc", "pci", "splunk", "siem analyst",
    "identity management", "access management",
    "risk assessment", "security governance",
    "it consultant", "security consultant",
    "ai engineer", "ai security", "llm", "machine learning",
]

# ── Target companies → ATS mappings ─────────────────────────────
GREENHOUSE_COMPANIES = [
    ("andurilindustries", "Anduril Industries"),
    ("cloudflare",        "Cloudflare"),
    ("crowdstrike",       "CrowdStrike"),
    ("datadog",           "Datadog"),
    ("openai",            "OpenAI"),
    ("anthropic",         "Anthropic"),
    ("paloaltonetworks",  "Palo Alto Networks"),
    ("sentinelone",       "SentinelOne"),
    ("lacework",          "Lacework"),
    ("snyk",              "Snyk"),
    ("hashicorp",         "HashiCorp"),
    ("github",            "GitHub"),
    ("elastic",           "Elastic"),
]

LEVER_COMPANIES = [
    ("scaleai",           "Scale AI"),
    ("cohere",            "Cohere"),
    ("mistral",           "Mistral AI"),
    ("applovin",          "AppLovin"),
]

ASHBY_COMPANIES = [
    ("Ramp",              "Ramp"),
    ("Linear",            "Linear"),
    ("Retool",            "Retool"),
    ("Vercel",            "Vercel"),
    ("Hex",               "Hex"),
]

WORKDAY_COMPANIES = [
    # (tenant, site, wd_num, company_display_name, search_term)
    ("bah",         "BAH_Jobs",           1, "Booz Allen Hamilton", "cyber security"),
    ("saic",        "SAIC_External",      1, "SAIC",               "network security"),
    ("leidos",      "External",           5, "Leidos",             "cyber"),
    ("l3harris",    "L3Harris",           1, "L3Harris",           "network security"),
    ("crowdstrike", "crowdstrikecareers", 5, "CrowdStrike",        "security analyst"),
    ("deloitte",    "DeloitteCareers",    1, "Deloitte",           "it consultant"),
    ("accenture",   "AccentureCareers",   1, "Accenture",          "security consultant"),
    ("caci",        "ExternalSite",       5, "CACI",               "cyber"),
    ("peraton",     "External",           1, "Peraton",            "cyber"),
]

SMARTRECRUITERS_COMPANIES = [
    ("PaloAltoNetworks2",  "Palo Alto Networks"),
    ("Mandiant",           "Mandiant"),
    ("Fortinet",           "Fortinet"),
]

def is_relevant(job):
    title = job.get("title", "").lower()
    tags  = " ".join(job.get("tags", [])).lower() if isinstance(job.get("tags"), list) else str(job.get("tags","")).lower()
    desc  = job.get("description", "").lower()[:500]
    combined = f"{title} {tags} {desc}"
    if any(term in combined for term in EXCLUDE_TERMS):
        return False
    return any(term in combined for term in RELEVANT_TITLE_TERMS)


def pre_filter_jobs(jobs):
    """
    Fast keyword pre-filter before LLM analysis.
    Returns (keep_list, dropped_count, drop_reasons).
    Runs in milliseconds — no LLM involved.
    """
    keep, dropped = [], 0
    for job in jobs:
        title = job.get("title", "").lower()
        desc  = job.get("description", "").lower()
        loc   = job.get("location", "").lower()
        combined = f"{title} {desc} {loc}"

        # Hard disqualify on description content
        disqualifier = next((t for t in PRE_FILTER_DISQUALIFY if t in combined), None)
        if disqualifier:
            dropped += 1
            continue

        # Drop jobs with no description that aren't from high-trust ATS sources
        desc_len = len(job.get("description", "").strip())
        source   = job.get("source", "")
        high_trust = any(s in source for s in ["Workday", "Greenhouse", "Lever", "Ashby",
                                                "SmartRecruiters", "USAJobs"])
        if desc_len < 150 and not high_trust:
            dropped += 1
            continue

        # Attach a quick confidence hint for the analyzer
        strong_hits = sum(1 for t in PRE_FILTER_STRONG_MATCH if t in combined)
        job["_pre_score"] = min(strong_hits, 5)   # 0-5, used to sort analyze queue
        keep.append(job)

    return keep, dropped

def _clean_desc(raw):
    """Strip HTML tags and decode entities so LLM gets plain text."""
    text = _html.unescape(raw or "")
    text = _re.sub(r'<[^>]+>', ' ', text)
    text = _re.sub(r'\s+', ' ', text).strip()
    return text[:2000]


def _norm_job(title, company, url, description, location, source,
              salary_min=0, tags=None, date="", clearance=None):
    """Normalize any source's job dict to a common shape."""
    j = {
        "title":       title,
        "company":     company,
        "url":         url,
        "description": _clean_desc(description),
        "location":    location,
        "salary_min":  salary_min or 0,
        "tags":        tags or [],
        "date":        date or "",
        "source":      source,
    }
    if clearance is not None:
        j["clearance"] = clearance
    return j

# ════════════════════════════════════════════════════════════════
#  FREE TIER 1 — ATS DIRECT (highest quality, zero ghost jobs)
# ════════════════════════════════════════════════════════════════

def scrape_greenhouse():
    """Greenhouse public job board API — no auth, pure JSON."""
    if not SOURCE_CONFIG["greenhouse"]["enabled"]:
        return []
    print("[Scout] Searching Greenhouse ATS...")
    jobs = []
    headers = {"User-Agent": "job-scout/2.0"}
    for slug, company in GREENHOUSE_COMPANIES:
        try:
            url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                for j in r.json().get("jobs", []):
                    loc = j.get("location", {}).get("name", "Unknown")
                    remote = "remote" in loc.lower()
                    jax    = "jacksonville" in loc.lower() or "florida" in loc.lower()
                    if not (remote or jax):
                        continue
                    jobs.append(_norm_job(
                        title=j.get("title",""),
                        company=company,
                        url=j.get("absolute_url",""),
                        description=j.get("content",""),
                        location=loc,
                        source=f"Greenhouse ({company})",
                        date=j.get("updated_at",""),
                    ))
            time.sleep(0.3)
        except Exception as e:
            print(f"[Scout] Greenhouse {company}: {e}")
    print(f"[Scout] Greenhouse: {len(jobs)} jobs")
    return jobs


def scrape_lever():
    """Lever public posting API — no auth, pure JSON."""
    if not SOURCE_CONFIG["lever"]["enabled"]:
        return []
    print("[Scout] Searching Lever ATS...")
    jobs = []
    headers = {"User-Agent": "job-scout/2.0"}
    for slug, company in LEVER_COMPANIES:
        try:
            url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                for j in r.json():
                    cats = j.get("categories", {})
                    loc  = cats.get("location", "Unknown")
                    remote = "remote" in loc.lower()
                    if not remote:
                        continue
                    jobs.append(_norm_job(
                        title=j.get("text",""),
                        company=company,
                        url=j.get("hostedUrl",""),
                        description=j.get("descriptionPlain",""),
                        location=loc,
                        source=f"Lever ({company})",
                        date=str(j.get("createdAt","")),
                    ))
            time.sleep(0.3)
        except Exception as e:
            print(f"[Scout] Lever {company}: {e}")
    print(f"[Scout] Lever: {len(jobs)} jobs")
    return jobs


def scrape_ashby():
    """Ashby public posting API — no auth, includes compensation data."""
    if not SOURCE_CONFIG["ashby"]["enabled"]:
        return []
    print("[Scout] Searching Ashby ATS...")
    jobs = []
    headers = {"User-Agent": "job-scout/2.0"}
    for slug, company in ASHBY_COMPANIES:
        try:
            url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                for j in r.json().get("jobs", []):
                    remote = j.get("isRemote", False)
                    loc    = j.get("location", "Unknown")
                    if not remote and "jacksonville" not in loc.lower():
                        continue
                    comp = j.get("compensation", {})
                    sal_min = comp.get("minValue", 0) or 0
                    jobs.append(_norm_job(
                        title=j.get("title",""),
                        company=company,
                        url=j.get("jobUrl",""),
                        description=j.get("descriptionPlain",""),
                        location="Remote" if remote else loc,
                        source=f"Ashby ({company})",
                        salary_min=sal_min,
                        date=j.get("publishedAt",""),
                    ))
            time.sleep(0.3)
        except Exception as e:
            print(f"[Scout] Ashby {company}: {e}")
    print(f"[Scout] Ashby: {len(jobs)} jobs")
    return jobs

def _fetch_workday_description(base, external_path, headers):
    """Fetch full job description from Workday detail endpoint."""
    try:
        # externalPath already contains /job/... so just append to base root, not base/job
        # base = https://tenant.wd1.../wday/cxs/tenant/site
        # externalPath = /job/Location/Title_ID
        # detail URL = https://tenant.wd1.../wday/cxs/tenant/site/job/Location/Title_ID
        clean_path = external_path.lstrip('/')
        url = f"{base}/{clean_path}"
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            # Try multiple possible description field locations
            desc = (data.get("jobPostingInfo", {}).get("jobDescription", "")
                    or data.get("jobPostingInfo", {}).get("description", "")
                    or data.get("description", "")
                    or "")
            desc = _re.sub(r'<[^>]+>', ' ', _html.unescape(desc))
            desc = _re.sub(r'\s+', ' ', desc).strip()
            return desc[:3000]
        else:
            return ""
    except Exception:
        return ""


def scrape_workday():
    """Workday CXS endpoint — POST-based, no auth. Fetches full descriptions."""
    if not SOURCE_CONFIG["workday"]["enabled"]:
        return []
    print("[Scout] Searching Workday ATS (defense + enterprise)...")
    jobs = []
    list_headers = {"Content-Type": "application/json", "Accept": "application/json",
                    "User-Agent": "job-scout/2.0"}
    detail_headers = {"Accept": "application/json", "User-Agent": "job-scout/2.0"}

    for tenant, site, wd_num, company, search_text in WORKDAY_COMPANIES:
        base = f"https://{tenant}.wd{wd_num}.myworkdayjobs.com/wday/cxs/{tenant}/{site}"
        offset, limit = 0, 20
        company_jobs = 0
        try:
            while True:
                body = {"appliedFacets": {}, "limit": limit,
                        "offset": offset, "searchText": search_text}
                r = requests.post(f"{base}/jobs", json=body,
                                  headers=list_headers, timeout=20)
                if r.status_code != 200:
                    break
                data  = r.json()
                batch = data.get("jobPostings", [])
                if not batch:
                    break
                for j in batch:
                    loc         = j.get("locationsText", "")
                    ext_path    = j.get("externalPath", "")
                    job_url     = f"https://{tenant}.wd{wd_num}.myworkdayjobs.com{ext_path}"

                    # Fetch the full description from the detail endpoint
                    description = ""
                    if ext_path:
                        description = _fetch_workday_description(base, ext_path, detail_headers)
                        time.sleep(0.4)   # polite delay per detail request

                    jobs.append(_norm_job(
                        title=j.get("title", ""),
                        company=company,
                        url=job_url,
                        description=description,
                        location=loc or "See posting",
                        source=f"Workday ({company})",
                        date=j.get("postedOn", ""),
                    ))
                    company_jobs += 1

                offset += limit
                if offset >= data.get("total", 0):
                    break
                time.sleep(1.0)
            print(f"[Scout]   {company}: {company_jobs} jobs")
        except Exception as e:
            print(f"[Scout] Workday {company}: {e}")
    print(f"[Scout] Workday total: {len(jobs)} jobs")
    return jobs


def scrape_smartrecruiters():
    """SmartRecruiters public API — no auth."""
    if not SOURCE_CONFIG["smartrecruiters"]["enabled"]:
        return []
    print("[Scout] Searching SmartRecruiters ATS...")
    jobs = []
    headers = {"User-Agent": "job-scout/2.0"}
    for company_slug, company in SMARTRECRUITERS_COMPANIES:
        try:
            url = f"https://api.smartrecruiters.com/v1/companies/{company_slug}/postings"
            params = {"country": "us", "limit": 100, "offset": 0}
            r = requests.get(url, headers=headers, params=params, timeout=15)
            if r.status_code == 200:
                for j in r.json().get("content", []):
                    loc    = j.get("location", {}).get("city","") + ", " + j.get("location",{}).get("country","")
                    remote = j.get("location",{}).get("remote", False)
                    jobs.append(_norm_job(
                        title=j.get("name",""),
                        company=company,
                        url=j.get("applyUrl", j.get("ref","")),
                        description="",
                        location="Remote" if remote else loc,
                        source=f"SmartRecruiters ({company})",
                        date=j.get("releasedDate",""),
                    ))
            time.sleep(0.3)
        except Exception as e:
            print(f"[Scout] SmartRecruiters {company}: {e}")
    print(f"[Scout] SmartRecruiters: {len(jobs)} jobs")
    return jobs

# ════════════════════════════════════════════════════════════════
#  FREE TIER 1 — NICHE RSS FEEDS (InfoSec-Jobs, ai-jobs.net)
# ════════════════════════════════════════════════════════════════

def _ensure_feedparser():
    try:
        import feedparser
        return feedparser
    except ImportError:
        print("[Scout] Installing feedparser...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "feedparser", "-q"], check=True)
        import feedparser
        return feedparser


def scrape_infosec_jobs():
    """InfoSec-Jobs.com RSS feed — curated cyber roles, often with salary."""
    if not SOURCE_CONFIG["infosec_jobs"]["enabled"]:
        return []
    print("[Scout] Searching InfoSec-Jobs RSS...")
    fp = _ensure_feedparser()
    jobs = []
    try:
        feed = fp.parse("https://infosec-jobs.com/feed/")
        for entry in feed.entries:
            title = entry.get("title","")
            desc  = entry.get("summary","")
            loc   = entry.get("location", "Remote/US")
            jobs.append(_norm_job(
                title=title,
                company=entry.get("author","Unknown"),
                url=entry.get("link",""),
                description=desc,
                location=loc,
                source="InfoSec-Jobs",
                date=entry.get("published",""),
            ))
        print(f"[Scout] InfoSec-Jobs: {len(jobs)} jobs")
    except Exception as e:
        print(f"[Scout] InfoSec-Jobs error: {e}")
    return jobs


def scrape_ai_jobs():
    """ai-jobs.net RSS feed — curated AI/ML engineering roles."""
    if not SOURCE_CONFIG["ai_jobs"]["enabled"]:
        return []
    print("[Scout] Searching ai-jobs.net RSS...")
    fp = _ensure_feedparser()
    jobs = []
    try:
        feed = fp.parse("https://ai-jobs.net/feed/")
        for entry in feed.entries:
            jobs.append(_norm_job(
                title=entry.get("title",""),
                company=entry.get("author","Unknown"),
                url=entry.get("link",""),
                description=entry.get("summary",""),
                location=entry.get("location","Remote/US"),
                source="ai-jobs.net",
                date=entry.get("published",""),
            ))
        print(f"[Scout] ai-jobs.net: {len(jobs)} jobs")
    except Exception as e:
        print(f"[Scout] ai-jobs.net error: {e}")
    return jobs


# ════════════════════════════════════════════════════════════════
#  FREE TIER 1 — USAJOBS (official federal API)
# ════════════════════════════════════════════════════════════════

def scrape_usajobs():
    """USAJobs API — includes DHS Cybersecurity Service competitive-pay roles."""
    if not SOURCE_CONFIG["usajobs"]["enabled"]:
        return []
    print("[Scout] Searching USAJobs...")
    jobs = []
    headers = {
        "Host": "data.usajobs.gov",
        "User-Agent": "james.t.debruhl@gmail.com",
        "Authorization-Key": os.environ.get("USAJOBS_API_KEY", ""),
    }
    searches = [
        {"Keyword": "cybersecurity",        "LocationName": "Jacksonville, Florida"},
        {"Keyword": "network security",     "LocationName": "Jacksonville, Florida"},
        {"Keyword": "information security", "LocationName": "Jacksonville, Florida"},
        {"Keyword": "cybersecurity",        "WhoMayApply": "all"},   # national remote
    ]
    for params in searches:
        try:
            params.update({"ResultsPerPage": "25", "JobCategoryCode": "2210"})
            r = requests.get("https://data.usajobs.gov/api/search",
                             headers=headers, params=params, timeout=15)
            if r.status_code == 200:
                for item in r.json().get("SearchResult",{}).get("SearchResultItems",[]):
                    pos     = item.get("MatchedObjectDescriptor",{})
                    details = pos.get("UserArea",{}).get("Details",{})
                    sal     = pos.get("PositionRemuneration",[{}])
                    try:    sal_min = float(sal[0].get("MinimumRange",0))
                    except: sal_min = 0
                    jobs.append(_norm_job(
                        title=pos.get("PositionTitle",""),
                        company=pos.get("OrganizationName","US Government"),
                        url=pos.get("PositionURI",""),
                        description=details.get("JobSummary",""),
                        location=pos.get("PositionLocationDisplay",""),
                        source="USAJobs",
                        salary_min=sal_min,
                        date=pos.get("PublicationStartDate",""),
                        clearance=details.get("SecurityClearance",""),
                    ))
        except Exception as e:
            print(f"[Scout] USAJobs error: {e}")
    print(f"[Scout] USAJobs: {len(jobs)} jobs")
    return jobs

# ════════════════════════════════════════════════════════════════
#  FREE TIER 1 — ADZUNA (already working, retuned)
# ════════════════════════════════════════════════════════════════

def scrape_adzuna():
    """Adzuna API — free tier 250 calls/day, strong salary filtering."""
    if not SOURCE_CONFIG["adzuna"]["enabled"]:
        return []
    print("[Scout] Searching Adzuna...")
    APP_ID  = os.environ.get("ADZUNA_APP_ID",  "aef494c1")
    APP_KEY = os.environ.get("ADZUNA_APP_KEY", "a74c0846f74eb992329b1964a2fdecd7")
    if not APP_ID or not APP_KEY:
        print("[Scout] Adzuna: Set ADZUNA_APP_ID and ADZUNA_APP_KEY env vars")
        return []
    jobs    = []
    headers = {"User-Agent": "job-scout/2.0"}
    queries = [
        ("network security engineer",    "Jacksonville FL", 50),
        ("cybersecurity analyst",         "Jacksonville FL", 50),
        ("security architect",            "Jacksonville FL", 50),
        ("information security analyst",  "Jacksonville FL", 50),
        ("network security engineer",     "remote",          0),
        ("cybersecurity",                 "remote",          0),
        ("AI engineer security",          "remote",          0),
        ("IT security consultant",        "remote",          0),
    ]
    for what, where, distance in queries:
        try:
            params = {
                "app_id": APP_ID, "app_key": APP_KEY,
                "results_per_page": 20, "what": what,
                "where": where, "sort_by": "date",
                "salary_min": 80000, "max_days_old": 30,
                "content-type": "application/json",
            }
            if distance:
                params["distance"] = distance
            r = requests.get("https://api.adzuna.com/v1/api/jobs/us/search/1",
                             params=params, headers=headers, timeout=15)
            if r.status_code == 200:
                for j in r.json().get("results", []):
                    jobs.append(_norm_job(
                        title=j.get("title",""),
                        company=j.get("company",{}).get("display_name","Unknown"),
                        url=j.get("redirect_url",""),
                        description=j.get("description",""),
                        location=j.get("location",{}).get("display_name", where),
                        source="Adzuna",
                        salary_min=j.get("salary_min",0) or 0,
                        date=j.get("created",""),
                    ))
            time.sleep(0.5)
        except Exception as e:
            print(f"[Scout] Adzuna error '{what}': {e}")
    print(f"[Scout] Adzuna: {len(jobs)} jobs")
    return jobs


# ════════════════════════════════════════════════════════════════
#  FREE TIER 2 — LEGACY AGGREGATORS (kept, low-signal warning)
# ════════════════════════════════════════════════════════════════

def scrape_remoteok():
    if not SOURCE_CONFIG["remoteok"]["enabled"]:
        return []
    print("[Scout] Searching RemoteOK...")
    jobs = []
    try:
        r = requests.get("https://remoteok.com/api",
                         headers={"User-Agent": "job-scout/2.0"}, timeout=10)
        for job in r.json()[1:]:
            title = job.get("position","").lower()
            if any(t in title for t in RELEVANT_TITLE_TERMS):
                if not any(ex in title for ex in EXCLUDE_TERMS):
                    jobs.append(_norm_job(
                        title=job.get("position",""), company=job.get("company",""),
                        url=job.get("url",""), description=job.get("description",""),
                        location="Remote", source="RemoteOK",
                        tags=job.get("tags",[]), date=job.get("date",""),
                    ))
    except Exception as e:
        print(f"[Scout] RemoteOK error: {e}")
    print(f"[Scout] RemoteOK: {len(jobs)} jobs")
    return jobs


def scrape_remotive():
    if not SOURCE_CONFIG["remotive"]["enabled"]:
        return []
    print("[Scout] Searching Remotive...")
    jobs = []
    for cat in ["software-dev","devops-sysadmin","security"]:
        try:
            r = requests.get(f"https://remotive.com/api/remote-jobs?category={cat}&limit=50",
                             headers={"User-Agent": "job-scout/2.0"}, timeout=15)
            if r.status_code == 200:
                for j in r.json().get("jobs",[]):
                    title = j.get("title","").lower()
                    if any(t in title for t in RELEVANT_TITLE_TERMS):
                        if not any(ex in title for ex in EXCLUDE_TERMS):
                            jobs.append(_norm_job(
                                title=j.get("title",""), company=j.get("company_name",""),
                                url=j.get("url",""), description=j.get("description",""),
                                location=j.get("candidate_required_location","Remote"),
                                source="Remotive", tags=j.get("tags",[]),
                                date=j.get("publication_date",""),
                            ))
        except Exception as e:
            print(f"[Scout] Remotive {cat}: {e}")
    print(f"[Scout] Remotive: {len(jobs)} jobs")
    return jobs


def scrape_jobicy():
    if not SOURCE_CONFIG["jobicy"]["enabled"]:
        return []
    print("[Scout] Searching Jobicy...")
    jobs = []
    for term in ["network-security","cybersecurity","information-security","security-engineer"]:
        try:
            r = requests.get(f"https://jobicy.com/api/v2/remote-jobs?tag={term}&count=20",timeout=10)
            if r.status_code == 200:
                for j in r.json().get("jobs",[]):
                    title = j.get("jobTitle","").lower()
                    if not any(ex in title for ex in EXCLUDE_TERMS):
                        jobs.append(_norm_job(
                            title=j.get("jobTitle",""), company=j.get("companyName",""),
                            url=j.get("url",""), description=j.get("jobDescription",""),
                            location="Remote", source="Jobicy",
                            tags=j.get("jobIndustry",[]), date=j.get("pubDate",""),
                        ))
        except Exception as e:
            print(f"[Scout] Jobicy {term}: {e}")
    print(f"[Scout] Jobicy: {len(jobs)} jobs")
    return jobs


def scrape_jooble():
    if not SOURCE_CONFIG["jooble"]["enabled"]:
        return []
    print("[Scout] Searching Jooble...")
    jobs = []
    API_KEY = os.environ.get("JOOBLE_API_KEY","")
    if not API_KEY:
        print("[Scout] Jooble: Set JOOBLE_API_KEY env var")
        return []
    for kw, loc in [
        ("network security engineer","Jacksonville, FL"),
        ("cybersecurity analyst","Jacksonville, FL"),
        ("network security engineer","remote"),
        ("security engineer","remote"),
    ]:
        try:
            r = requests.post(
                f"https://jooble.org/api/{API_KEY}",
                headers={"Content-Type":"application/json"},
                json={"keywords":kw,"location":loc,"resultonpage":"10"},
                timeout=15,
            )
            if r.status_code == 200:
                for j in r.json().get("jobs",[]):
                    title = j.get("title","").lower()
                    if any(t in title for t in RELEVANT_TITLE_TERMS):
                        if not any(ex in title for ex in EXCLUDE_TERMS):
                            if len(j.get("snippet","")) >= 100:
                                jobs.append(_norm_job(
                                    title=j.get("title",""), company=j.get("company",""),
                                    url=j.get("link",""), description=j.get("snippet",""),
                                    location=j.get("location",loc), source="Jooble",
                                    date=j.get("updated",""),
                                ))
        except Exception as e:
            print(f"[Scout] Jooble '{kw}': {e}")
    print(f"[Scout] Jooble: {len(jobs)} jobs")
    return jobs

# ════════════════════════════════════════════════════════════════
#  PAID / FRAGILE — disabled by default, enable when ready
# ════════════════════════════════════════════════════════════════

def scrape_linkedin_guest():
    """
    LinkedIn guest API — free but fragile, ToS gray area.
    Enable in SOURCE_CONFIG when ready. No login required.
    Endpoint changes shape periodically — check if 0 results.
    """
    if not SOURCE_CONFIG["linkedin_guest"]["enabled"]:
        return []
    print("[Scout] Searching LinkedIn (guest API)...")
    jobs  = []
    hdrs  = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    queries = [
        ("network security engineer", "Jacksonville, Florida"),
        ("cybersecurity analyst",     "Jacksonville, Florida"),
        ("security engineer",         "United States"),
        ("AI engineer",               "United States"),
    ]
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "beautifulsoup4", "-q"])
        from bs4 import BeautifulSoup

    for keywords, location in queries:
        for start in [0, 25]:
            try:
                url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
                params = {
                    "keywords": keywords, "location": location,
                    "f_E": "4", "f_JT": "F", "f_TPR": "r2592000",
                    "start": start,
                }
                r = requests.get(url, headers=hdrs, params=params, timeout=15)
                if r.status_code == 429:
                    print("[Scout] LinkedIn: rate limited, slowing down")
                    time.sleep(10)
                    continue
                if r.status_code != 200:
                    break
                soup = BeautifulSoup(r.text, "html.parser")
                for card in soup.find_all("div", class_="base-card"):
                    title   = card.find("h3")
                    company = card.find("h4")
                    loc_el  = card.find("span", class_="job-search-card__location")
                    link    = card.find("a", class_="base-card__full-link")
                    if title and company and link:
                        jobs.append(_norm_job(
                            title=title.get_text(strip=True),
                            company=company.get_text(strip=True),
                            url=link.get("href",""),
                            description="",
                            location=loc_el.get_text(strip=True) if loc_el else location,
                            source="LinkedIn",
                        ))
                time.sleep(2.5)
            except Exception as e:
                print(f"[Scout] LinkedIn '{keywords}': {e}")
    print(f"[Scout] LinkedIn: {len(jobs)} jobs")
    return jobs


def scrape_clearancejobs():
    """
    ClearanceJobs — highest-conversion source for cleared defense work.
    Requires Apify API key (~$10-30/mo). Enable in SOURCE_CONFIG when ready.
    """
    if not SOURCE_CONFIG["clearancejobs"]["enabled"]:
        return []
    print("[Scout] Searching ClearanceJobs (Apify)...")
    APIFY_TOKEN = os.environ.get("APIFY_TOKEN","")
    if not APIFY_TOKEN:
        print("[Scout] ClearanceJobs: Set APIFY_TOKEN env var")
        return []
    # Placeholder — wire in the Apify actor run when token is set
    # Actor: parseforge/clearancejobs-scraper
    print("[Scout] ClearanceJobs: Apify integration ready — add actor call here")
    return []


def scrape_dice():
    """
    Dice.com — good for US IT contracting/consulting roles.
    Requires Apify API key (~$5-10/mo). Enable in SOURCE_CONFIG when ready.
    """
    if not SOURCE_CONFIG["dice"]["enabled"]:
        return []
    print("[Scout] Searching Dice (Apify)...")
    APIFY_TOKEN = os.environ.get("APIFY_TOKEN","")
    if not APIFY_TOKEN:
        print("[Scout] Dice: Set APIFY_TOKEN env var")
        return []
    print("[Scout] Dice: Apify integration ready — add actor call here")
    return []

# ════════════════════════════════════════════════════════════════
#  DEDUP, SAVE, RUN
# ════════════════════════════════════════════════════════════════

def deduplicate(jobs):
    seen, unique = set(), []
    for job in jobs:
        key = f"{job['title'].lower().strip()}::{job['company'].lower().strip()}"
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique


def save_jobs(jobs):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(JOB_DATA_DIR, exist_ok=True)
    filename  = os.path.join(JOB_DATA_DIR, f"jobs_{timestamp}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    print(f"[Scout] Saved {len(jobs)} jobs → {filename}")
    return filename


def run():
    print("\n[Scout] ═══ Job Scout v2.0 ═══")
    enabled = [k for k,v in SOURCE_CONFIG.items() if v["enabled"]]
    disabled = [k for k,v in SOURCE_CONFIG.items() if not v["enabled"]]
    print(f"[Scout] Active sources  : {', '.join(enabled)}")
    if disabled:
        print(f"[Scout] Disabled sources: {', '.join(disabled)}")
    print()

    all_jobs = []

    # Tier 1 — ATS direct (highest quality)
    all_jobs.extend(scrape_greenhouse())
    all_jobs.extend(scrape_lever())
    all_jobs.extend(scrape_ashby())
    all_jobs.extend(scrape_workday())
    all_jobs.extend(scrape_smartrecruiters())

    # Tier 1 — Niche RSS + official APIs
    all_jobs.extend(scrape_infosec_jobs())
    all_jobs.extend(scrape_ai_jobs())
    all_jobs.extend(scrape_usajobs())
    all_jobs.extend(scrape_adzuna())

    # Tier 2 — Legacy aggregators (kept, lower signal)
    all_jobs.extend(scrape_remoteok())
    all_jobs.extend(scrape_remotive())
    all_jobs.extend(scrape_jobicy())
    all_jobs.extend(scrape_jooble())

    # Paid / fragile — disabled by default
    all_jobs.extend(scrape_linkedin_guest())
    all_jobs.extend(scrape_clearancejobs())
    all_jobs.extend(scrape_dice())

    # Filter + dedup
    filtered = [j for j in all_jobs if is_relevant(j)]
    unique   = deduplicate(filtered)

    # Pre-filter: keyword disqualify + confidence hint
    unique, dropped = pre_filter_jobs(unique)
    print(f"\n[Scout] Pre-filter dropped {dropped} jobs (keyword disqualify / no description)")

    # Sort highest pre-score first so analyzer sees best jobs first
    unique.sort(key=lambda j: j.get("_pre_score", 0), reverse=True)

    # Source breakdown
    from collections import Counter
    counts = Counter(j["source"].split("(")[0].strip() for j in unique)
    print("\n[Scout] Results by source:")
    for src, n in counts.most_common():
        print(f"         {src:<30} {n}")

    print(f"\n[Scout] Total relevant unique jobs: {len(unique)}")
    print("\n--- JOB LIST ---")
    for i, job in enumerate(unique):
        sal = f"${job['salary_min']:,.0f}+" if job.get("salary_min",0) > 0 else "Salary TBD"
        clr = f" | Clearance: {job['clearance']}" if job.get("clearance") else ""
        print(f"{i+1:>3}. {job['title']} @ {job['company']} ({job['source']}) | {job['location']} | {sal}{clr}")

    if unique:
        filename = save_jobs(unique)
        return filename, unique

    return None, []


if __name__ == "__main__":
    run()
