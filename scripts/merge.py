"""Merge classified new jobs (scripts/_classified.json) into jobs.json.

_classified.json is a JSON list of job objects with the jobs.json fields.
Rows are validated; bad rows are reported and skipped. Sets "updated" to today.

Usage: python scripts/merge.py [--dry-run]
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOBS = ROOT / "jobs.json"
IN = ROOT / "scripts" / "_classified.json"

INDUSTRY = {"金融科技", "金融", "互联网"}
SIZE = {"small", "big"}
FIT = {"高", "中", "低"}
ROLE = {"产品", "数据", "运营", "用户/增长", "合规/风控", "战略", "财富/投资",
        "BD/商务", "市场", "财务", "设计", "综合"}
PT = {"可兼职", "远程", "弹性时间"}
REQUIRED = ["id", "company", "desc", "title", "date", "cat", "fit", "role", "size", "industry"]
ORDER = REQUIRED[:7] + ["url"] + REQUIRED[7:] + ["pt", "ptnote"]


def key(j):
    return (j["company"].strip().lower(), " ".join(j["title"].lower().split()))


def check(j):
    miss = [k for k in REQUIRED if not str(j.get(k, "")).strip()]
    if miss:
        return f"missing {miss}"
    if j["industry"] not in INDUSTRY:
        return f"industry {j['industry']!r}"
    if j["size"] not in SIZE:
        return f"size {j['size']!r}"
    if j["fit"] not in FIT:
        return f"fit {j['fit']!r}"
    if j["role"] not in ROLE:
        return f"role {j['role']!r}"
    if j.get("pt") and j["pt"] not in PT:
        return f"pt {j['pt']!r}"
    try:
        dt.date.fromisoformat(j["date"])
    except ValueError:
        return f"date {j['date']!r}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    data = json.loads(JOBS.read_text(encoding="utf-8"))
    have = {j["id"] for j in data["jobs"]}
    # LinkedIn reposts keep company + title but get a new id: update the old row instead.
    by_key = {key(j): j for j in data["jobs"]}
    new = json.loads(IN.read_text(encoding="utf-8")) if IN.exists() else []

    added, reposted, skipped = [], [], []
    for j in new:
        j = {k: v for k, v in j.items() if v not in (None, "")}
        j["id"] = str(j.get("id", ""))
        err = check(j)
        if not err and j["id"] in have:
            err = "already in jobs.json"
        if err:
            skipped.append((j.get("id"), j.get("title"), err))
            continue
        j["url"] = f"https://www.linkedin.com/jobs/view/{j['id']}"
        if not j.get("pt"):
            j.pop("ptnote", None)
        row = {k: j[k] for k in ORDER if k in j}
        have.add(j["id"])
        old = by_key.get(key(row))
        if old is not None:
            if row["date"] > old["date"]:
                reposted.append((old, row))
            else:
                skipped.append((j["id"], j["title"], "same company + title already listed, not newer"))
            continue
        by_key[key(row)] = row
        added.append(row)

    for s in skipped:
        print("skip", *s)
    print(f"adding {len(added)} jobs, refreshing {len(reposted)} reposts, skipped {len(skipped)}")
    for j in added:
        print(f"  + [{j['industry']}/{j['role']}/{j['fit']}] {j['company']} · {j['title']}")
    for old, row in reposted:
        print(f"  ~ repost {old['id']} -> {row['id']} ({old['date']} -> {row['date']}) "
              f"{row['company']} · {row['title']}")
    if a.dry_run:
        return

    for old, row in reposted:
        old.clear()
        old.update(row)
    data["jobs"].extend(added)
    data["updated"] = dt.date.today().isoformat()
    JOBS.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                    encoding="utf-8")
    print(f"jobs.json now has {len(data['jobs'])} jobs, updated {data['updated']}")


if __name__ == "__main__":
    main()
