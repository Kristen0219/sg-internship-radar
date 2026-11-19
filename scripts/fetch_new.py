"""Fetch new Singapore internship postings from LinkedIn's public job search.

Writes scripts/_candidates.json: postings not yet in jobs.json, each with the
job description text, plus the companies already known in jobs.json so new
rows can reuse their desc / industry / size.

Usage: python scripts/fetch_new.py [--days 2] [--max-pages 25]
"""
import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOBS = ROOT / "jobs.json"
OUT = ROOT / "scripts" / "_candidates.json"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
SEARCH = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
DETAIL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{}"

# Each query is a set of search params; results are merged and de-duplicated.
QUERIES = [
    {"keywords": "intern"},
    {"keywords": "internship"},
    {"f_E": "1"},  # LinkedIn "Internship" experience level
]

INTERN_RE = re.compile(
    r"\b(intern|interns|internship|trainee|attachment|placement|summer analyst|"
    r"off[- ]cycle|industrial attachment|co-?op)\b", re.I)
# Developer roles are out of scope for the radar; skip them before fetching details.
DEV_RE = re.compile(
    r"\b(software|developer|engineer(ing)?|front[- ]?end|back[- ]?end|full[- ]?stack|"
    r"devops|sre|swe|mobile|ios|android|qa|test automation|firmware|embedded|"
    r"machine learning engineer|ml engineer|cyber|security engineer|infrastructure|"
    r"cloud engineer|it support|network)\b", re.I)


def get(url, tries=5):
    delay = 4
    for i in range(tries):
        req = urllib.request.Request(url, headers={
            "User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and i < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            if e.code == 400:  # past the last page
                return ""
            raise
        except (urllib.error.URLError, TimeoutError):
            if i < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    return ""


def text(s):
    s = re.sub(r"<br\s*/?>|</p>|</li>|</h\d>", "\n", s, flags=re.I)
    s = re.sub(r"<li[^>]*>", "- ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t\xa0]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()


def first(pattern, s):
    m = re.search(pattern, s, re.S)
    return text(m.group(1)) if m else ""


def parse_cards(page):
    cards = []
    for chunk in page.split("<li")[1:]:
        m = re.search(r"jobPosting:(\d+)", chunk)
        if not m:
            continue
        cards.append({
            "id": m.group(1),
            "title": first(r'base-search-card__title[^>]*>(.*?)</h3>', chunk),
            "company": first(r'base-search-card__subtitle[^>]*>(.*?)</h4>', chunk),
            "location": first(r'job-search-card__location[^>]*>(.*?)</span>', chunk),
            "date": (re.search(r'datetime="([\d-]+)"', chunk) or [None, ""])[1],
        })
    return cards


def search(params, days, max_pages):
    found = {}
    for p in range(max_pages):
        q = {"location": "Singapore", "geoId": "102454443",
             "f_TPR": f"r{days * 86400}", "start": p * 10, **params}
        page = get(SEARCH + "?" + urllib.parse.urlencode(q))
        cards = parse_cards(page)
        if not cards:
            break
        for c in cards:
            found.setdefault(c["id"], c)
        time.sleep(1.5)
    return found


def detail(job_id):
    page = get(DETAIL.format(job_id))
    desc = first(r'show-more-less-html__markup[^>]*>(.*?)</div>', page)
    criteria = [text(c) for c in re.findall(
        r'description__job-criteria-text[^>]*>(.*?)</span>', page, re.S)]
    return desc, criteria


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=2,
                    help="look back this many days (default 2, overlaps yesterday's run)")
    ap.add_argument("--max-pages", type=int, default=25)
    ap.add_argument("--max-details", type=int, default=150)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    data = json.loads(JOBS.read_text(encoding="utf-8"))
    have = {j["id"] for j in data["jobs"]}
    known = {}
    for j in data["jobs"]:
        known.setdefault(j["company"], {
            "desc": j["desc"], "industry": j["industry"], "size": j["size"]})

    found = {}
    for params in QUERIES:
        got = search(params, a.days, a.max_pages)
        print(f"query {params}: {len(got)} postings")
        for k, v in got.items():
            found.setdefault(k, v)

    fresh = [c for c in found.values() if c["id"] not in have]
    intern = [c for c in fresh if INTERN_RE.search(c["title"])]
    keep = [c for c in intern if not DEV_RE.search(c["title"])]
    print(f"total {len(found)} · not in jobs.json {len(fresh)} · "
          f"internship titles {len(intern)} · after dropping dev roles {len(keep)}")

    keep.sort(key=lambda c: c["date"], reverse=True)
    keep = keep[:a.max_details]
    for i, c in enumerate(keep, 1):
        try:
            desc, crit = detail(c["id"])
        except Exception as e:  # keep going; the card still has title/company
            desc, crit = "", []
            print(f"  detail failed for {c['id']}: {e}")
        c["criteria"] = crit
        c["description"] = desc[:4000]
        c["known_company"] = c["company"] in known
        if i % 10 == 0:
            print(f"  details {i}/{len(keep)}")
        time.sleep(2)

    OUT.write_text(json.dumps({
        "fetched_at": time.strftime("%Y-%m-%d %H:%M"),
        "candidates": keep,
        "known_companies": known,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(keep)} candidates to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
