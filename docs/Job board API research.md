# Best Job Board APIs & Data Sources for an Automated Multi-Agent Job Search System in 2026

## Cybersecurity / Network Security / AI Engineering / IT Consulting · Jacksonville FL + Remote US · $100k+

---

## Executive Summary — What to Integrate Into `job_scout.py`

Based on the research, the **biggest single quality problem** with the current pipeline is that it relies on free general-purpose remote-work aggregators (Jooble, RemoteOK, Remotive, Jobicy) whose corpora are dominated by junior/non-cleared/non-defense roles. For a senior network-security/AI-engineering/IT-consulting candidate with a Bank of America/Citibank background targeting $100k+ defense and tech work, the highest-signal sources are:

1. **Direct ATS public job-board APIs** (Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Workday "CXS") — free, JSON, no auth, zero-ghost-job data sourced directly from employer ATS systems. **This is the single biggest unlock.**
2. **ClearanceJobs.com** — far and away the highest-conversion board for defense/cleared work (Booz Allen, SAIC, Leidos, Anduril all post there).
3. **USAJobs.gov API** — free, official, includes DHS/CISA cyber roles.
4. **InfoSec-Jobs.com (isecjobs.com) + ai-jobs.net** — both run by the same operator, have RSS feeds and lightweight APIs, niche-curated.
5. **Adzuna** (already integrated — keep it; tune the queries) and **LinkedIn via guest-API scraping** as the breadth layer.

Recommended drop-ins (replacing Jooble's dominance and RemoteOK/Remotive's empty returns) and full implementation guidance are below.

---

## Priority Tier 1 — Build These First (Free, Reliable, High-Signal)

### 1. ATS Public Job Board APIs — The Single Best ROI Move

Hundreds of the highest-paying tech, cyber, and AI-first companies (and a meaningful number of defense primes) publish to public, unauthenticated JSON endpoints exposed by their ATS. These are not scraping — they are documented public APIs. They have no rate limits worth mentioning at job-seeker scale, no anti-bot, no Cloudflare in the way, and the data is the literal employer-posted truth (zero ghost-job risk, zero reposts).

The approach is: maintain a YAML/JSON list of `{company_name, ats_type, board_token}` tuples, and iterate.

**Greenhouse** — most enterprise/scaleup tech and many security companies (Anduril is on Greenhouse, plus Cloudflare, CrowdStrike, Datadog, Stripe, Airbnb, Figma, Discord, Coinbase, OpenAI's hiring partners, etc.).
- Endpoint: `GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true`
- Auth: none. JSON response.
- Discover board tokens by visiting any company's careers page hosted on Greenhouse (`boards.greenhouse.io/{token}`) or via aggregator lists (see the GitHub projects below).
- Per-job detail: `GET /v1/boards/{token}/jobs/{job_id}` (or include `content=true` to inline descriptions).

**Lever** — many growth-stage and AI-first companies. Pattern:
- Endpoint: `GET https://api.lever.co/v0/postings/{company}?mode=json`
- Auth: none. Returns full JSON with categories, salary fields where the employer supplied them, hosted apply URL, plain-text + HTML description.
- Built-in filters at the source: `team`, `department`, `location`, `commitment`, `level`, `skip`, `limit`. Rate-limited at ~10 req/sec — irrelevant at this scale.

**Ashby** — newer, fast-growing AI-startup ATS (Linear, Ramp, many YC AI companies).
- Endpoint: `GET https://api.ashbyhq.com/posting-api/job-board/{company}?includeCompensation=true`
- Auth: none. Returns title, location, secondaryLocations, department, isRemote, workplaceType, descriptionHtml/Plain, publishedAt, employmentType, jobUrl, applyUrl, and compensation tier summary (often with explicit `$X–$Y` band — very useful for the $100k+ filter).

**Workday (CXS / Candidate Experience Service)** — this is the **single most important add for defense/enterprise**. Booz Allen, SAIC, Leidos, L3Harris, Lockheed Martin, Northrop Grumman, Raytheon, BAE, Capital One, Bank of America, Citi, Wells Fargo, JPMorgan, Pfizer, virtually all Fortune 500. Pattern:
- URL form: `https://{tenant}.wd{N}.myworkdayjobs.com/{locale}/{site}` (also `jobs.myworkdaysite.com/recruiting/{tenant}/{site}` for the newer hosting domain).
- API endpoint: `POST https://{tenant}.wd{N}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs`
- Headers: `Content-Type: application/json`, `Accept: application/json`
- Body: `{"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "cyber"}` — `searchText` supports keyword search, and you can include location facets in `appliedFacets` (the facet IDs are visible from a `GET` of the site root). Stop paging when `jobPostings` is empty.
- Per-job details: `GET /wday/cxs/{tenant}/{site}/job/{externalPath}` for full HTML description.
- No auth. 1–2 second delay between requests is courteous; in practice Workday tolerates much faster. The `wd{N}` (wd1/wd3/wd5/etc.) varies per tenant — always parse the actual careers URL.

**Specific Workday endpoints worth hard-coding for the user's target list:**
- Booz Allen Hamilton: `bah.wd1.myworkdayjobs.com/BAH_Jobs`
- SAIC: `saic.wd1.myworkdayjobs.com/SAIC_External`
- Leidos: `leidos.wd5.myworkdayjobs.com/External`
- L3Harris: `l3harris.wd1.myworkdayjobs.com/L3Harris`
- (Anduril uses Greenhouse, not Workday — see Greenhouse section.)

**SmartRecruiters** — used by some mid-market and a number of consulting firms. Free unauthenticated endpoint:
- `GET https://api.smartrecruiters.com/v1/companies/{company}/postings?q=cyber&country=us&limit=100&offset=0`
- Returns JSON with title, location, department, releasedDate, applyUrl.

**Workable** — small/mid SaaS and security startups:
- `GET https://apply.workable.com/api/v1/widget/accounts/{company}` — JSON list of public jobs.

**Recruitee** — `GET https://{company}.recruitee.com/api/offers/` (returns JSON).

#### Discovery: How to find which companies use which ATS

Three open-source resources solve this:

- **`plibither8/jobber`** on GitHub — a small wrapper that already standardizes Ashby/Greenhouse/Lever queries to a single JSON shape.
- **`daviderubio/wrkmatch`** — cross-references a LinkedIn connections CSV against Greenhouse/Lever/Ashby/Workable/Recruitee boards and ranks targets. The company-slug heuristics file is reusable.
- **`Feashliaa/job-board-aggregator`** — claims an indexed corpus of 4,000+ companies across these ATSs with daily updates.
- Search GitHub topic tags `greenhouse-api`, `lever-api`, `ashby`, and `ats` for community-maintained company→slug lists; several "weekly scanner" repos exist that already maintain a curated list.
- For Workday tenants specifically, the cleanest method is to (a) take a curated target-company list, (b) Google `"{company} workday careers"`, and (c) extract the tenant/site once and cache it.

**Concrete starter list (high relevance to this user) to hard-code into `job_scout.py`:**

| Company | ATS | Endpoint pattern |
|---|---|---|
| Anduril | Greenhouse | `boards-api.greenhouse.io/v1/boards/andurilindustries/jobs?content=true` |
| Booz Allen | Workday | `bah.wd1.myworkdayjobs.com/wday/cxs/bah/BAH_Jobs/jobs` |
| SAIC | Workday | `saic.wd1.myworkdayjobs.com/wday/cxs/saic/SAIC_External/jobs` |
| Leidos | Workday | `leidos.wd5.myworkdayjobs.com/wday/cxs/leidos/External/jobs` |
| L3Harris | Workday | `l3harris.wd1.myworkdayjobs.com/wday/cxs/l3harris/L3Harris/jobs` |
| CrowdStrike | Workday | `crowdstrike.wd5.myworkdayjobs.com/wday/cxs/crowdstrike/crowdstrikecareers/jobs` |
| Palo Alto Networks | SmartRecruiters | `api.smartrecruiters.com/v1/companies/PaloAltoNetworks2/postings` |
| Cloudflare | Greenhouse | `boards-api.greenhouse.io/v1/boards/cloudflare/jobs?content=true` |
| Datadog | Greenhouse | `boards-api.greenhouse.io/v1/boards/datadog/jobs?content=true` |
| OpenAI | Greenhouse | `boards-api.greenhouse.io/v1/boards/openai/jobs?content=true` |
| Anthropic | Greenhouse | `boards-api.greenhouse.io/v1/boards/anthropic/jobs?content=true` |
| Scale AI | Lever | `api.lever.co/v0/postings/scaleai?mode=json` |
| Ramp | Ashby | `api.ashbyhq.com/posting-api/job-board/Ramp?includeCompensation=true` |

This single tier — once wired up with a list of ~75–150 target companies — will dwarf the volume of high-quality, relevant, $100k+ jobs that the current four free aggregators are producing combined, with zero auth and no ghost-job pollution.

---

### 2. ClearanceJobs.com — Highest-Conversion Defense Board

Per ClearanceJobs' own published testimonials from defense recruiters, the platform reports interview-to-hire rates around 75–85% for the recruiters using it, and it is the single largest US security-cleared career network (~62,000 active jobs from ~1,776 pre-screened defense contractors). All of the user's named target companies — Booz Allen, SAIC, Leidos, L3Harris, Lockheed, Northrop, BAE, CACI, Amentum, Peraton, General Dynamics — post heavily here, and most cleared cyber roles in the Jacksonville/NAS-Jax area (NMCI, Navy cyber, DoD contractor work at NAS Jacksonville and Mayport) flow through ClearanceJobs first.

- **There is no official public API.** ClearanceJobs is owned by DHI Group (same parent as Dice). API access is recruiter-side and gated.
- **Practical options:**
  - **Apify "ClearanceJobs Scraper"** (parseforge/clearancejobs-scraper) — usage-based pricing on Apify (typically a few dollars per 1,000 jobs); supports filters for clearance level (Secret/TS/TS-SCI), polygraph, company, location, remote. Runs in stealth-browser mode with residential proxies. Fits well within the $50–100/month budget.
  - **Lightweight HTML scraping via `requests`+`BeautifulSoup`** of the public search URL (`https://www.clearancejobs.com/jobs?keywords=...&loc=...`) works for low-volume polling (e.g., every 6 hours), but the site uses bot detection — a `User-Agent` header alone is not enough; rotating residential proxies or a service like ScrapingBee/ScraperAPI is typically required for sustained use.
- **ToS risk:** moderate. Scraping is prohibited by ToS; the *hiQ v. LinkedIn* precedent provides some cover for personal-use scraping of public data, but for safety the Apify route is preferable because the legal exposure transfers to Apify and you get a stable, maintained scraper.
- **Best filter combination for this user:** `clearance=Secret,Top Secret,TS/SCI`, `keywords=("network security" OR "cyber" OR "SOC" OR "vulnerability" OR "incident response")`, location `Jacksonville, FL` plus `Remote`, and a second pass with `keywords=(consultant OR architect OR engineer)` against the named target companies.

---

### 3. USAJobs.gov REST API — Federal Cyber Jobs, Including DHS/CISA

Free, official, well-documented, and includes the *DHS Cybersecurity Service* — a higher-pay federal hiring authority specifically designed to compete with private-sector cyber pay (positions are NOT on the GS scale; they pay private-sector competitive bands, often $100k–$250k for the user's level).

- **Search endpoint:** `https://data.usajobs.gov/api/Search`
- **Auth:** Free API key obtained via the API Request form at developer.usajobs.gov. Headers required:
  - `Host: data.usajobs.gov`
  - `User-Agent: your-email@example.com`
  - `Authorization-Key: YOUR_API_KEY`
- **Paging:** `ResultsPerPage` up to 500, `Page` for pagination.
- **Useful query params:** `Keyword=cyber`, `LocationName=Jacksonville, Florida` (or omit for remote/national), `RemunerationMinimumAmount=100000`, `JobCategoryCode=2210` (IT Management series — covers most cyber/network roles), `PayGradeHigh=15` (GS-15 cap), `WhoMayApply=public`.
- **Specialty subsite:** `cybersecurity.usajobs.gov` is curated for cyber roles; same API can be filtered to those via `JobCategoryCode` 2210 and 1550, plus keywords.
- **Data quality:** highest possible — every record is a real federal vacancy. Geographic coverage includes specific Jacksonville-area hits (NAS Jax, Mayport, SOUTHCOM-adjacent agencies).

---

### 4. InfoSec-Jobs / iSecJobs and AI-Jobs.net — Curated Niche Boards (Same Operator)

These two sister sites (operated by the same team) are the highest-signal niche aggregators for the user's two primary specializations. Both are Python/Django-built and expose:

- **RSS feeds:** `https://infosec-jobs.com/feed/` and `https://ai-jobs.net/feed/` — easiest integration, parse with `feedparser`.
- **Public JSON list endpoints:** the sites expose helper JSON endpoints under `/api/` for taxonomies (job titles, skills, regions). The job-list HTML is also light and trivially scrapeable; `infosec-jobs.com/{role}-jobs/` and `ai-jobs.net/jobs/` return clean, tag-rich HTML with company, salary range (often stated explicitly), location, remote flag, and skill tags.
- **Quality:** very high. Salary indices are published. Filtering by region (`Remote/Americas`, `United States`) is well-supported. Many postings explicitly state salary bands, which is rare among aggregators.
- **The "isecjobs.com" mirror** is the same network and works as a fallback hostname.

These two will likely beat Jooble, RemoteOK, and Remotive combined for the user's target roles.

---

### 5. Keep Adzuna — But Retune

Adzuna is solid and already integrated. Free tier is generous (typically 250 calls/day on the developer tier), and the API has first-class salary filtering — perfect for the $100k+ requirement.

- Endpoint: `GET https://api.adzuna.com/v1/api/jobs/us/search/1?app_id={ID}&app_key={KEY}&what=cyber%20security&where=Jacksonville&salary_min=100000&results_per_page=50&content-type=application/json`
- Useful filters: `what`, `where`, `distance` (radius in miles), `salary_min`, `salary_max`, `sort_by=date`, `category=it-jobs`, `max_days_old=14`.
- Run **multiple parallel queries**: `("network security" + Jacksonville + 50mi)`, `("cybersecurity" + remote)`, `("AI engineer" + remote)`, `("IT consultant" + Jacksonville)`, `("security architect" salary>=130000)`. Deduplicate by `redirect_url`.
- Add the *salary-histogram* endpoint to feed the system with current market salary anchors for the user's titles — useful for filtering ghost/lowball roles.

---

### 6. LinkedIn (the user is paying for Premium — use it)

**The official LinkedIn Talent Solutions / Jobs API is not accessible to individuals.** It requires partner approval and enterprise contracts; LinkedIn Premium (job-seeker or career tiers) does *not* convey any API access. This has not changed in 2026.

There are, however, three workable ways to integrate LinkedIn job data:

#### (a) LinkedIn Guest-API endpoints (free, public, fragile)

When you visit a LinkedIn job page without being logged in, the page is served by a public "jobs-guest" API that is callable directly:

- `GET https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={q}&location={loc}&start={offset}`
- `GET https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}`

Filter query parameters:
- `f_E` — experience level: `4` (Mid-Senior) or `5` (Director)
- `f_JT=F` — full-time
- `f_TPR=r86400` (24h), `r604800` (week), `r2592000` (month)
- `f_WT=2` — remote
- `f_C` — company filter (LinkedIn company ID)

Returns HTML, not JSON — parse with BeautifulSoup. **No auth, no API key, no login.** LinkedIn returns HTTP 429 if you scrape too fast — keep to ~1 request every 2–3 seconds, single-thread, and use a realistic User-Agent. For sustained use, route through a residential-proxy service (ScraperAPI, ScrapingBee, or Bright Data Web Unlocker) to avoid IP-level rate limiting.

This is the same endpoint LinkedIn serves to Googlebot, so it is legally lower-risk than logged-in scraping — but it is still against the LinkedIn ToS and the endpoint occasionally changes shape (a working scraper in March may need a tweak in May). The *hiQ v. LinkedIn* ruling provides some cover for public data but is not a green light.

#### (b) Apify "LinkedIn Jobs Scraper" actors

Several public Apify actors (e.g., `cryptosignals/linkedin-jobs-scraper`, the bundled `fantastic-jobs/linkedin-jobs-api`) wrap the guest API and handle IP rotation. Pricing is typically $5/month flat or pay-per-result around $1.50/1,000 jobs (Bright Data's published LinkedIn Jobs scraper is similar). Fits easily in the budget and is the most reliable middle ground.

#### (c) What **NOT** to use in 2026

- **Proxycurl** — sued by LinkedIn in January 2025 and **shut down mid-2025**. Multiple sources confirm. Do not build on it. Any older guide recommending Proxycurl is stale.
- **PhantomBuster, ScrapingFish, RapidAPI ad-hoc LinkedIn endpoints** — these still exist but are highly volatile; success rates change week-to-week as LinkedIn rotates fingerprints. Not suitable for a long-lived pipeline.
- **Logged-in scraping with your real LinkedIn cookie (`li_at`)** — possible (the `linkedin-jobs-scraper` PyPI package supports it) but carries the meaningful risk of getting the user's actual Premium account banned. Not recommended given the user is paying for Premium.

#### What to do with the Premium subscription

LinkedIn Premium's actual job-search benefits (InMail, "Top Applicant" jobs, applicant insights, salary insights) are delivered through the logged-in web UI and are not API-exposed. The pragmatic play is: keep Premium for the UI-driven discovery and InMail outreach, and use the **guest-API / Apify route** for the automated pipeline. Treat them as separate channels.

**Bottom line:** For LinkedIn, use either (a) self-hosted guest-API scraping with light rate-limiting for the cheap path, or (b) an Apify LinkedIn-jobs actor (~$5–$30/month, pay-per-result) for the maintained path. Budget ~$20–40/month here.

---

## Priority Tier 2 — Add If Tier 1 Is Insufficient

### 7. Aggregator API — One Paid Subscription That Replaces Many Free Sources

If after Tier 1 the volume is still light, the cleanest single paid subscription within budget is **Fantastic.jobs / jobdataapi.com** (these are two competing aggregators that solve the same problem):

- They pre-index 175,000+ company career sites across 54 ATS platforms (Greenhouse, Lever, Ashby, Workday, Workable, iCIMS, SuccessFactors, Rippling, ADP, Eightfold AI, etc.), deduplicate, and enrich with LinkedIn company data.
- **Fantastic.jobs** is available self-serve on RapidAPI and Apify; pay-as-you-go is typically around **$1 per 1,000 jobs** — very cheap, well within budget.
- **jobdataapi.com** has tiered subscription plans (free trial, then ~$X–$XX/month for unlimited usage of the full feed) and offers vector embeddings + semantic search on Pro tiers — useful if the user wants embedding-based job-to-resume matching in their multi-agent system.
- **TheirStack** — competitor, also recommended. Strongest filtering on company attributes (industry, headcount, funding, tech stack). Free tier of 50 company / 200 API credits per month, then ~$X+/month. Updates every minute. Their value-add is that you can filter for "companies that use Splunk" or "companies funded in the last 12 months" — useful for IT-consulting-leaning prospecting.
- **Coresignal** — most expensive of the three (Starter $49/mo, Pro $800/mo, multi-source jobs costing 2 credits per record). Overkill unless the user also wants employee/recruiter contact data. **Skip for now.**

Recommendation: pick **one** of Fantastic.jobs or jobdataapi.com on the cheapest tier (~$20–50/month) **only if** the Tier 1 sources don't fill the pipeline. They will not produce better data than the ATS APIs — they just save the labor of maintaining the company → ATS mapping yourself.

### 8. Dice.com

Tech-focused, US, ~70,000 active listings, strong cyber and IT-contracting representation. **No official public API** in 2026 (the old API was for ATS partners only).
- Best access: **Apify "Dice Jobs Feed"** ($0 per request, fast HTTP-only) or `blackfalcondata/dice-jobs-feed`. Pay-per-event pricing; minimal cost.
- Worth integrating because Dice still indexes US contract/consulting tech roles that don't appear on Greenhouse/Lever (a lot of body-shop consulting work for banks and feds posts on Dice and ClearanceJobs but not LinkedIn or Greenhouse).
- Data quality: mixed — some quality dilution from staffing agencies reposting, but the salary and skills extraction is structured.

### 9. ClearedJobs.net

Second-tier cleared-jobs site, much smaller than ClearanceJobs but distinct posting set.
- No official API. Apify scraper available (`parseforge/clearedjobs-scraper`, `scrapestorm/clearedjobs-scraper-cheap`).
- Worth adding only if ClearanceJobs is already wired up — diminishing returns.

### 10. Built In (built in National + city sites)

Tech-focused with employer-profile depth (culture, tech stack, benefits) — useful if the multi-agent system does employer scoring. **No public API.** Scraping is straightforward; HTML is light and not heavily bot-protected. Built In Florida specifically covers Jacksonville-adjacent tech employers (smaller than Built In Austin/SF but non-zero).

### 11. Wellfound (formerly AngelList Talent)

Best for AI/early-stage. **No public API in 2026.** Apify actor `wellfound.com` scraper is the practical route. Has structured equity-grant data in salary ranges. Add only if the user is open to startup work; for someone with a 10-yr Fortune-50 background and a $100k+ floor, the relevance is moderate.

### 12. Y Combinator "Work at a Startup"

Free, requires a YC account to view full data programmatically. No formal public API, but the site exposes a JSON-backed search (`workatastartup.com/api/companies/dump.json` and `/api/jobs.json`-style endpoints discoverable from the Network tab). Useful specifically for AI-engineering roles since YC's W24, S24, W25, and S25 cohorts have been heavy on AI infrastructure companies. Light maintenance burden.

---

## Priority Tier 3 — Don't Bother (Stale, Defunct, or Negative ROI for This Use Case)

| Source | Status / Reason to Skip |
|---|---|
| **Indeed Publisher API** | Deprecated since 2020. Current Indeed API (Job Sync GraphQL) is for ATS partners only. Scraping Indeed at scale requires paid anti-bot services (Bright Data, ScraperAPI, Scrapingdog) — costs add up and the data overlaps heavily with ATS-direct sources. |
| **ZipRecruiter API** | Public API has been restricted; partner-only. Apify scrapers exist but data quality is mid; few $100k+ cyber/AI roles you won't already see elsewhere. |
| **Glassdoor API** | No public job-search API. Reviews and salary data are accessible via Bright Data's dataset, but for job hunting it is redundant with other sources. |
| **Monster, CareerBuilder, SimplyHired, Lensa, Hired.com** | All declining traffic and overlap heavily with Indeed/ZipRecruiter. Hired.com is now invite-curated only. Not worth integration effort. |
| **The Muse API** | Limited and skews early-career/lifestyle content. Wrong audience for a senior cyber/AI candidate. |
| **Welcome to the Jungle (Otta)** | API not generally available; UK/EU-skewed. |
| **CyberSecJobs.com, SANS, ISC2, ISACA career centers** | Small posting volume relative to engineering effort. The same employers post these roles on ClearanceJobs and the ATSs anyway. SANS Cyber Jobs has no API; ISC2/ISACA career centers run on white-labeled YourMembership/Naylor — scrapeable HTML, but volume is in the low hundreds. Skip unless the user has time for diminishing-returns long-tail. |
| **Cyberseek.org** | Cyberseek is a workforce-analytics project (NIST-funded), **not a job board** — its "heat map" links out to other boards. Useful as labor-market context, not as a source. |
| **JobsPikr** | Aggregator API — viable but more expensive than Fantastic.jobs for the same data; reviews mention sales/pricing friction. |
| **Apollo.io, Clay.com** | These are sales/people-intelligence platforms with some job-posting fields. Wrong primitive for this use case. |
| **Proxycurl** | **Defunct.** LinkedIn sued them in January 2025; service shut down mid-2025. Ignore any guide that still recommends it. |

---

## Specific Implementation Guidance for `job_scout.py`

### Suggested module structure

```
job_scout/
├── sources/
│   ├── ats_greenhouse.py     # iterates companies list
│   ├── ats_lever.py
│   ├── ats_ashby.py
│   ├── ats_workday.py        # POST-based CXS handler
│   ├── ats_smartrecruiters.py
│   ├── usajobs.py
│   ├── clearancejobs.py      # Apify or HTML scraping
│   ├── infosec_jobs.py       # RSS feedparser
│   ├── ai_jobs.py            # RSS feedparser
│   ├── adzuna.py             # already exists, retune
│   └── linkedin_guest.py     # guest-API or Apify
├── companies.yaml            # {name, ats, slug} target list
├── normalize.py              # unified Job schema
├── dedupe.py                 # by (company, title, location) + URL hash
├── filter.py                 # salary>=100k, location match, role match
└── agents/...                # your existing multi-agent layer
```

### Unified `Job` schema (target shape for all sources)

```python
@dataclass
class Job:
    source: str                  # "greenhouse", "workday-bah", "clearancejobs", ...
    source_id: str               # provider's unique ID
    title: str
    company: str
    location: str                # raw string
    locations_structured: list   # [{city, state, country, remote_flag}]
    remote: bool
    employment_type: str         # FullTime, Contract, ...
    description_html: str
    description_text: str
    salary_min: int | None
    salary_max: int | None
    salary_currency: str
    posted_at: datetime
    apply_url: str
    raw: dict                    # provider-native payload
```

### Worked example — Greenhouse fetcher (Python)

```python
import httpx, asyncio

async def fetch_greenhouse(client, slug: str) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    r = await client.get(url, timeout=20)
    r.raise_for_status()
    return r.json().get("jobs", [])

async def fetch_all(slugs):
    async with httpx.AsyncClient(headers={"User-Agent": "job-scout/1.0"}) as c:
        return await asyncio.gather(*[fetch_greenhouse(c, s) for s in slugs])
```

### Worked example — Workday CXS fetcher (the trickier one)

```python
def fetch_workday(tenant: str, site: str, search_text: str = "", wd_num: int = 1):
    base = f"https://{tenant}.wd{wd_num}.myworkdayjobs.com/wday/cxs/{tenant}/{site}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    jobs, offset, limit = [], 0, 20
    while True:
        body = {"appliedFacets": {}, "limit": limit,
                "offset": offset, "searchText": search_text}
        r = requests.post(f"{base}/jobs", json=body, headers=headers, timeout=30)
        r.raise_for_status()
        batch = r.json().get("jobPostings", [])
        if not batch:
            break
        jobs.extend(batch)
        offset += limit
        if offset >= r.json().get("total", 0):
            break
        time.sleep(1.2)  # polite delay
    # for full description, fetch each detail:
    # GET {base}/job/{posting['externalPath']}
    return jobs
```

### Worked example — USAJobs

```python
HEADERS = {
    "Host": "data.usajobs.gov",
    "User-Agent": "your-email@example.com",
    "Authorization-Key": os.environ["USAJOBS_API_KEY"],
}
params = {
    "Keyword": "cyber OR network security OR information security",
    "LocationName": "Jacksonville, Florida",
    "RemunerationMinimumAmount": 100000,
    "ResultsPerPage": 500,
    "Page": 1,
}
r = requests.get("https://data.usajobs.gov/api/Search",
                 headers=HEADERS, params=params)
```

### Dedup and filter recommendations

- **Dedup key:** `sha1((normalized_company + "::" + normalized_title + "::" + normalized_location).lower())`. Fall back to URL-hash for cross-source dedup (the same job often appears on the ATS *and* the company's LinkedIn page).
- **Salary floor:** apply only when the salary is *known*. Many ATS postings lack salary fields — gating on `salary_min >= 100000` would discard most relevant Workday/Greenhouse results. Better: a **soft scoring layer** where `known_salary >= 100k` boosts, `unknown_salary` is neutral, `known_salary < 100k` drops.
- **Role match:** boolean keyword filter is too brittle. Use an embedding-similarity score (OpenAI `text-embedding-3-small` or local `all-MiniLM-L6-v2`) between the job description and a "target role" prompt that captures the user's profile — this is the kind of step a multi-agent system should run as a second pass anyway.
- **Geo match:** match on (a) `Jacksonville` or `JAX` or `Mayport` or `NAS Jax` in the location string, (b) `Florida` + `remote`-friendly flag, or (c) any `remote-US` flag. Many Workday postings have a structured `locationsText` *and* `remoteType` field — use both.

---

## "Where Do People Actually Get Hired?" — Hiring-Outcome Signal

Synthesizing public discussion from r/cybersecurity, r/cscareerquestions, r/SecurityClearance, the Hacker News "Who's Hiring" threads, and the testimonials published by ClearanceJobs and InfoSec-Jobs:

- **For TS/SCI-eligible defense/cyber work at the user's targets (Booz, SAIC, Leidos, L3Harris, Anduril):** ClearanceJobs is the consensus #1 by a wide margin. Multiple cleared-recruiting firms cite 75–85% interview-to-hire conversion. Direct application to the company's Workday/Greenhouse instance is #2 (often *better* because you bypass agency markups). LinkedIn is #3 — useful for the warm-intro layer but rarely the source of the initial discovery.
- **For private-sector senior cyber (security architect, principal security engineer at FAANG / fintech / cloud-native security vendors):** the LinkedIn warm-intro path and direct-ATS applications dominate. Recruiter-initiated outreach via LinkedIn Premium accounts for a large share of *senior* placements (LinkedIn's own annual Hiring Trends report has reported this repeatedly), which is exactly why the user paying for Premium is justified — the *signal* is on LinkedIn even when the *postings* are best fetched elsewhere.
- **For AI engineering / ML platform roles:** Hacker News "Who's Hiring" monthly threads, Wellfound, YC Work-at-a-Startup, and direct Greenhouse/Lever/Ashby polling of AI-first companies are consistently cited as higher-conversion than any aggregator. ai-jobs.net is well-regarded for ML/Data role discovery; the actual interviews almost always come from direct-ATS application.
- **For IT consulting at $100k+:** Dice + ClearanceJobs + LinkedIn dominate. The Big 4 / Accenture / Deloitte all use Workday or Taleo; their ATS pages are scrapeable directly.

**Sources that the community consistently flags as low-conversion / time-wasters for senior roles:** Indeed (ghost-job pollution, recruiter spam), ZipRecruiter, Monster, CareerBuilder, SimplyHired, Lensa. The current pipeline's reliance on Jooble (which is an aggregator-of-aggregators that re-indexes Indeed and similar) is precisely why it's dominated by low-quality posts — Jooble inherits Indeed's noise floor.

---

## Final Prioritized Recommendation — Integrate These 6–8 Sources

| # | Source | Why | Effort | Cost | Replace? |
|---|---|---|---|---|---|
| 1 | **Direct ATS APIs** (Greenhouse + Lever + Ashby + Workday + SmartRecruiters) wired to a curated ~100-company target list | Highest signal, zero ghost jobs, free, no auth, salary often included | ~1–2 dev days for the framework + ongoing list curation | $0 | **Replace Jooble** |
| 2 | **ClearanceJobs** (via Apify scraper) | Single highest hire-rate source for the user's defense targets | 2–4 hours | ~$10–30/month | New |
| 3 | **USAJobs API** | Free, official, includes DHS Cybersecurity Service ($100k+ federal cyber) | 2 hours | $0 | New |
| 4 | **InfoSec-Jobs + ai-jobs.net** (RSS) | Curated, salary-tagged, niche-perfect | 1 hour (feedparser) | $0 | **Replace RemoteOK + Remotive** |
| 5 | **Adzuna** (retune with `salary_min=100000` + multiple parallel queries + Jacksonville radius) | Already integrated; just needs better query strategy | 1 hour | $0 (free tier) | Keep |
| 6 | **LinkedIn guest API** (or Apify LinkedIn Jobs actor for stability) | Largest single source of senior-role visibility, complements Premium | 3–4 hours + ongoing maintenance | $0 self-hosted or ~$20–30/month managed | **Replace Jobicy** |
| 7 *(optional)* | **Dice via Apify** | Adds US tech-contract and consulting roles not visible on ATS direct | 1 hour | ~$5–10/month | New |
| 8 *(optional)* | **Fantastic.jobs aggregator** (RapidAPI/Apify, pay-per-job) | Catch-all if the ATS list is missing companies | 2 hours | ~$20–40/month at expected volume | Conditional |

**Net effect on the user's $50–100/month budget:** Tiers 1–5 are free. Tier 6 (LinkedIn) consumes ~$20–30. Tiers 7–8 together consume ~$25–50. Total expected: **~$50–80/month** for a pipeline that should produce an order of magnitude more relevant $100k+ cyber/AI/IT-consulting jobs in Jacksonville + remote-US than the current free-aggregator-only setup, with dramatically lower ghost-job and repost noise.

---

## Closing Notes on Reliability, Risk, and Maintenance

- **Reliability ranking (highest to lowest):** USAJobs API → ATS public APIs (Greenhouse/Lever/Ashby) → Adzuna → Workday CXS → ai-jobs.net/InfoSec-Jobs RSS → Aggregator paid APIs → Apify managed scrapers → LinkedIn guest API → DIY LinkedIn/Indeed scraping. Build the bottom of that stack on top of the top — i.e., treat Tier-1 ATS sources as your bedrock and let the more fragile sources be supplementary.
- **What will break:** the LinkedIn guest endpoints have changed shape multiple times in 2024–2025 (the `seeMoreJobPostings` path has been renamed at least twice); Workday occasionally rotates which `wd{N}` subdomain hosts a tenant. Build a small health-check job (run nightly) that hits each source and alerts on schema drift or zero results.
- **ToS posture:** the ATS APIs (Greenhouse, Lever, Ashby, SmartRecruiters, Workable) are explicitly *public* APIs and there is no ToS issue. Workday CXS is technically a public API serving the careers UI; it has no ToS prohibition for read access. USAJobs is explicitly free for non-commercial use. LinkedIn, Indeed, Glassdoor, and Dice all prohibit scraping in ToS; the *hiQ v. LinkedIn* line of cases gives some legal cover for personal-use scraping of public data but is not a blanket green light. For ClearanceJobs and LinkedIn specifically, using a managed third-party (Apify, Bright Data) transfers most of the risk and gives a more stable result for the same money.
- **A note on "ghost jobs":** the single biggest predictor of ghost-job density is *how many hops the data has taken from the employer's ATS*. ATS-direct (Greenhouse/Lever/Ashby/Workday) ≈ zero ghost jobs. Indeed/Jooble/RemoteOK ≈ high ghost-job rate because they syndicate/re-index aggressively. This is the structural reason the recommended pipeline will see a step-change in quality.

The single most leveraged change the user can make is the first one: replace the current "aggregators of aggregators" with a curated set of ~75–150 direct ATS endpoints. Everything else in this report is icing on that cake.