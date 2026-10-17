"""Public GitHub data for the profile cards.

Everything here is what any visitor can see: the contribution calendar is read
from the public profile page without credentials, and repositories, languages
and events come from public REST endpoints. GITHUB_TOKEN, when set, only raises
the API rate limit.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

API = "https://api.github.com"
USER_AGENT = "kikyo-garden-profile/1.0"


def _get(url: str, token: str | None = None, accept: str = "application/vnd.github+json") -> bytes:
    headers = {"User-Agent": USER_AGENT, "Accept": accept}
    if token and url.startswith(API):
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def api(path: str) -> object:
    return json.loads(_get(f"{API}{path}", os.environ.get("GITHUB_TOKEN")))


# -- contribution calendar ---------------------------------------------------
@dataclass
class Day:
    date: date
    level: int
    count: int


TD_RE = re.compile(r"<td\b[^>]*\bContributionCalendar-day\b[^>]*>")
ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')
TIP_RE = re.compile(r'<tool-tip\b[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>')
COUNT_RE = re.compile(r"(\d[\d,]*)\s+contributions?")
TOTAL_RE = re.compile(r"(\d[\d,]*)\s+contributions?\s+in the last year")


def parse_calendar(page: str) -> tuple[list[Day], int]:
    counts: dict[str, int] = {}
    for target, text in TIP_RE.findall(page):
        match = COUNT_RE.search(text)
        counts[target] = int(match.group(1).replace(",", "")) if match else 0
    days = []
    for tag in TD_RE.findall(page):
        attrs = dict(ATTR_RE.findall(tag))
        if "data-date" not in attrs:
            continue
        days.append(Day(date.fromisoformat(attrs["data-date"]), int(attrs.get("data-level", 0)),
                        counts.get(attrs.get("id", ""), 0)))
    days.sort(key=lambda d: d.date)
    total = TOTAL_RE.search(re.sub(r"\s+", " ", page))
    return days, int(total.group(1).replace(",", "")) if total else sum(d.count for d in days)


def fetch_calendar(user: str) -> tuple[list[Day], int]:
    page = _get(f"https://github.com/users/{user}/contributions", accept="text/html").decode("utf-8")
    days, total = parse_calendar(page)
    if not days:
        raise RuntimeError("the contribution calendar markup was not recognised")
    return days, total


def streaks(days: list[Day]) -> tuple[int, int]:
    """(longest, current) runs of days with contributions.

    The current run may end yesterday: today is still being written.
    """
    longest = run = 0
    for day in days:
        run = run + 1 if day.count > 0 else 0
        longest = max(longest, run)
    current = 0
    tail = list(days)
    if tail and tail[-1].count == 0:
        tail.pop()
    for day in reversed(tail):
        if day.count == 0:
            break
        current += 1
    return longest, current


# -- repositories, languages, events ----------------------------------------
def fetch_repos(user: str) -> list[dict]:
    repos = api(f"/users/{user}/repos?type=owner&sort=pushed&per_page=100")
    return [r for r in repos if r["name"].lower() != user.lower() and not r.get("private")]


def fetch_languages(repos: list[dict]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        for name, size in api(f"/repos/{repo['full_name']}/languages").items():
            totals[name] = totals.get(name, 0) + size
    return dict(sorted(totals.items(), key=lambda kv: -kv[1]))


def fetch_events(user: str) -> list[dict]:
    return api(f"/users/{user}/events/public?per_page=100")


def collect(user: str) -> dict:
    """Everything the cards need, as a JSON-serialisable snapshot."""
    days, total = fetch_calendar(user)
    profile = api(f"/users/{user}")
    repos = fetch_repos(user)
    return {
        "user": user,
        "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "calendar": {"total": total, "days": [[d.date.isoformat(), d.level, d.count] for d in days]},
        "profile": {"followers": profile.get("followers", 0), "public_repos": profile.get("public_repos", 0)},
        "repos": [
            {k: r.get(k) for k in ("name", "full_name", "html_url", "description", "language", "fork",
                                    "stargazers_count", "pushed_at", "archived")}
            for r in repos
        ],
        "languages": fetch_languages(repos),
        "events": [
            {"type": e["type"], "repo": e["repo"]["name"], "created_at": e["created_at"], "payload": e.get("payload", {})}
            for e in fetch_events(user)
        ],
    }


def days_from(snapshot: dict) -> list[Day]:
    return [Day(date.fromisoformat(d), level, count) for d, level, count in snapshot["calendar"]["days"]]


def week_columns(days: list[Day]) -> list[list[Day | None]]:
    """Columns of seven (Sunday first), as on GitHub."""
    if not days:
        return []
    start = days[0].date - timedelta(days=(days[0].date.weekday() + 1) % 7)
    by_date = {d.date: d for d in days}
    columns: list[list[Day | None]] = []
    cursor = start
    while cursor <= days[-1].date:
        columns.append([by_date.get(cursor + timedelta(days=i)) for i in range(7)])
        cursor += timedelta(days=7)
    return columns
