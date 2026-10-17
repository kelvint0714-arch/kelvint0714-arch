"""Draw the monochrome manga bloom log; preserve public data and offline fallback."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parent))
from garden import data, manga, calendar3d
ROOT=Path(__file__).resolve().parent.parent
SNAPSHOT=ROOT/'data'/'snapshot.json'
OUT=ROOT/'assets'/'ink-v2'/'metrics'

def describe(event: dict) -> str:
    kind, p = event["type"], event.get("payload") or {}
    ref = (p.get("ref") or "").replace("refs/heads/", "")
    number = (p.get("pull_request") or p.get("issue") or {}).get("number")
    if kind == "PushEvent":
        size = p.get("size") or p.get("distinct_size")
        if size:
            return f"Pushed {size} commit{'s' if size != 1 else ''} to {ref or 'a branch'}"
        return f"Pushed to {ref or 'a branch'}"
    if kind == "CreateEvent":
        if p.get("ref_type") == "repository":
            return "Planted a new repository"
        return f"Created {p.get('ref_type', 'ref')} {p.get('ref') or ''}".strip()
    if kind == "DeleteEvent":
        return f"Deleted {p.get('ref_type', 'ref')} {p.get('ref') or ''}".strip()
    if kind == "WatchEvent":
        return "Starred"
    if kind == "ForkEvent":
        return "Forked"
    if kind == "PullRequestEvent":
        return f"{(p.get('action') or 'updated').capitalize()} pull request #{number}"
    if kind == "IssuesEvent":
        return f"{(p.get('action') or 'updated').capitalize()} issue #{number}"
    if kind == "IssueCommentEvent":
        return f"Commented on #{number}"
    if kind == "ReleaseEvent":
        return f"Released {(p.get('release') or {}).get('tag_name', '')}".strip()
    if kind == "PublicEvent":
        return "Made public"
    return kind.removesuffix("Event")

def recent_notes(snap: dict, tz: ZoneInfo, now: datetime, limit: int = 5) -> list[dict]:
    """Up to `limit` notes from the last 30 days; same-day pushes to one branch are merged."""
    cutoff = now - timedelta(days=30)
    notes: list[dict] = []
    events = sorted(snap["events"], key=lambda e: e["created_at"], reverse=True)
    for event in events:
        when = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
        if when < cutoff:
            continue
        local = when.astimezone(tz)
        text = describe(event)
        last = notes[-1] if notes else None
        if (last and event["type"] == "PushEvent" and last["type"] == "PushEvent" and last["repo"] == event["repo"]
                and last["base"] == text and last["day"] == local.date()):
            last["times"] += 1
            continue
        if len(notes) == limit:
            break
        notes.append({"type": event["type"], "repo": event["repo"], "base": text, "times": 1,
                      "day": local.date(), "local": local})
    for note in notes:
        note["text"] = note["base"]
        if note["times"] > 1 and note["base"].startswith("Pushed to "):
            note["text"] = f"Pushed {note['times']} times to {note['base'][len('Pushed to '):]}"
    return notes

def same_data(a: dict, b: dict) -> bool:
    """Equal apart from when they were fetched."""
    return {k: v for k, v in a.items() if k != "fetched_at"} == {k: v for k, v in b.items() if k != "fetched_at"}


def load_snapshot(user: str, offline: bool) -> dict:
    if not offline:
        try:
            snap = data.collect(user)
            SNAPSHOT.parent.mkdir(exist_ok=True)
            # Only rewrite when the public data moved, so frequent runs don't commit a new timestamp each time.
            if not SNAPSHOT.exists() or not same_data(json.loads(SNAPSHOT.read_text(encoding="utf-8")), snap):
                SNAPSHOT.write_text(json.dumps(snap, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            return snap
        except Exception as error:  # keep the last good cards rather than failing the run
            if not SNAPSHOT.exists():
                raise
            print(f"fetch failed ({error}); using {SNAPSHOT.relative_to(ROOT)}", file=sys.stderr)
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))

def calendar_card(theme: str, snap: dict):
    return calendar3d.calendar_card(theme,snap)

def bouquet_card(theme: str, snap: dict):
    return manga.bouquet_card(theme,snap)

def notes_card(theme: str, snap: dict, tz: ZoneInfo, now: datetime):
    return manga.notes_card(theme,snap,recent_notes(snap,tz,now),tz.key)

def main(argv: list[str]) -> int:
    config=json.loads((ROOT/'garden.json').read_text(encoding='utf-8'))
    snap=load_snapshot(config['user'],'--offline' in argv)
    tz=ZoneInfo(config.get('timezone','UTC'))
    fetched=datetime.fromisoformat(snap['fetched_at'].replace('Z','+00:00'))
    now=fetched if '--offline' in argv else max(fetched,datetime.now(timezone.utc))
    notes=recent_notes(snap,tz,now)
    OUT.mkdir(parents=True,exist_ok=True)
    for mobile in (False,True):
        for theme in ('light','dark'):
            for name,doc in [('calendar',calendar3d.calendar_card(theme,snap,mobile)),
                             ('bouquet',manga.bouquet_card(theme,snap,mobile)),
                             ('notes',manga.notes_card(theme,snap,notes,tz.key,mobile))]:
                suffix='-mobile' if mobile else ''
                path=OUT/f'{name}-{theme}{suffix}.svg'
                path.write_text(doc.render(),encoding='utf-8')
                print(path.name)
                if name == 'calendar':
                    alias = ROOT/'assets'/'metrics'/path.name
                    alias.parent.mkdir(parents=True, exist_ok=True)
                    alias.write_text(doc.render(), encoding='utf-8')
    return 0
if __name__=='__main__':
    sys.exit(main(sys.argv[1:]))
