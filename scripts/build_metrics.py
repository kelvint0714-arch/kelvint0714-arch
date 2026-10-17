"""Render the BLOOM LOG cards from public GitHub data.

  assets/metrics/calendar-{light,dark}.svg  each day of the past year as a flower
  assets/metrics/bouquet-{light,dark}.svg   languages tied into a bouquet
  assets/metrics/notes-{light,dark}.svg     recent public activity

Fresh data is saved to data/snapshot.json. When GitHub cannot be reached the
last snapshot is used, so a failed fetch never blanks the cards. Pass
--offline to render from the snapshot without fetching.
"""

from __future__ import annotations

import json
import math
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))

from garden import data, flora  # noqa: E402
from garden.flora import place, wrap  # noqa: E402
from garden.palette import THEMES  # noqa: E402
from garden.svg import Doc, n  # noqa: E402
from garden.text import measure  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "snapshot.json"
OUT = ROOT / "assets" / "metrics"


# -- shared card frame -------------------------------------------------------
def card(doc: Doc, pal: dict, title: str, title_ja: str) -> None:
    w, h = doc.width, doc.height
    glow = doc.radial([(0, pal["glow"], .55), (1, pal["glow"], 0)], cx=.92, cy=.05, r=.6)
    doc.add(
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="18" fill="{pal["card"]}" stroke="{pal["border"]}"/>'
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="18" fill="url(#{glow})"/>'
    )
    head, head_w = doc.text([(title, "sans-bold", 13.5)], 50, 40, spacing=2.2, attrs=f' fill="{pal["ink"]}"')
    ja, _ = doc.text([(title_ja, "cjk-bold", 15)], 50 + head_w + 12, 40.5, spacing=2,
                     attrs=f' fill="{pal["kikyo"][1] if pal["scheme"] == "light" else pal["kikyo"][3]}"')
    doc.add(place(32, 35, flora.flower(doc, pal, "kikyo", 9, .2, hue="kikyo")))
    doc.add(wrap("fadeup", head + ja, .1))


def symbols(doc: Doc, pal: dict, scale: float = 1.0) -> list[str]:
    """Flower symbols for contribution levels 0-4, built once per card."""
    specs = [
        None,
        ("plum", 3.6, "kikyo"),
        ("sakura", 5.0, "sakura"),
        ("kikyo", 6.1, "kikyo"),
        ("peony", 6.9, "sakura"),
    ]
    ids = []
    for level, spec in enumerate(specs):
        sid = doc.uid("lv")
        if spec is None:
            body = f'<circle r="{n(1.7*scale)}" fill="{pal["ink3"]}" fill-opacity=".45"/>'
        else:
            kind, r, hue = spec
            body = flora.flower(doc, pal, kind, r * scale, 0, hue=hue, still=True)
        doc.defs.append(f'<g id="{sid}">{body}</g>')
        ids.append(sid)
    return ids


# -- bloom calendar ------------------------------------------------------------
def calendar_card(theme: str, snap: dict) -> Doc:
    pal = THEMES[theme]
    days = data.days_from(snap)
    columns = data.week_columns(days)
    total = snap["calendar"]["total"]
    longest, current = data.streaks(days)
    best = max(days, key=lambda d: d.count) if days else None

    doc = Doc(960, 272, title="Bloom calendar",
              desc=f"{total} contributions in the last year, one flower per day; longest streak {longest} days, "
                   f"current streak {current} days.")
    flora.install(doc)
    card(doc, pal, "BLOOM CALENDAR", "花暦")
    ids = symbols(doc, pal)

    # legend in the header
    x = 932
    more, more_w = doc.text([("More", "sans", 11)], x, 40, anchor="end", attrs=f' fill="{pal["ink3"]}"')
    x -= more_w + 14
    legend = [more]
    for level in range(4, -1, -1):
        legend.append(f'<use href="#{ids[level]}" transform="translate({n(x)} 36)"/>')
        x -= 17
    less, _ = doc.text([("Less", "sans", 11)], x - 2, 40, anchor="end", attrs=f' fill="{pal["ink3"]}"')
    legend.append(less)
    doc.add(wrap("fadeup", "".join(legend), .3))

    cell, x0, y0 = 16.0, 66.0, 84.0
    grid = []
    last_month_col = -9
    for col, week in enumerate(columns):
        for row, day in enumerate(week):
            if day is None:
                continue
            if day.date.day == 1 and col - last_month_col >= 3:
                label, _ = doc.text([(day.date.strftime("%b"), "sans", 10.5)], x0 + col * cell - 6, 72,
                                    attrs=f' fill="{pal["ink3"]}"')
                grid.append(label)
                last_month_col = col
            cx, cy = x0 + col * cell + cell / 2, y0 + row * cell + cell / 2
            delay = .4 + col * .035 + row * .012
            grid.append(f'<g transform="translate({n(cx)} {n(cy)})"><use href="#{ids[day.level]}" class="pop"'
                        f'{flora.delay_style(delay)}/></g>')
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        label, _ = doc.text([(name, "sans", 10)], x0 - 10, y0 + row * cell + cell / 2 + 3.5, anchor="end",
                            attrs=f' fill="{pal["ink3"]}"')
        grid.append(label)
    doc.add("".join(grid))

    stats = [
        (f"{total:,}", "CONTRIBUTIONS", "この一年"),
        (f"{longest} day{'s' if longest != 1 else ''}", "LONGEST STREAK", "最長連続"),
        (f"{current} day{'s' if current != 1 else ''}", "CURRENT STREAK", "現在の連続"),
        (best.date.strftime("%b %-d") if best and best.count else "—", "BEST DAY", "満開の日"),
    ]
    width = (960 - 64) / 4
    row = []
    for i, (value, label, ja) in enumerate(stats):
        sx = 32 + i * width
        if i:
            row.append(f'<path d="M{n(sx - 14)} 214V254" stroke="{pal["border"]}"/>')
        v, _ = doc.text([(value, "serif-bold", 25)], sx, 234, attrs=f' fill="{pal["ink"]}"')
        lab, lab_w = doc.text([(label, "sans", 10.5)], sx, 253, spacing=1.5, attrs=f' fill="{pal["ink2"]}"')
        j, _ = doc.text([(ja, "cjk", 11.5)], sx + lab_w + 8, 253.5, attrs=f' fill="{pal["ink3"]}"')
        row.append(v + lab + j)
    doc.add(wrap("fadeup", "".join(row), 1.6))
    return doc


# -- language bouquet ------------------------------------------------------------
RANKS = [("kikyo", "kikyo", 2), ("peony", "sakura", 1), ("rose", "rose", 1), ("plum", "peach", 1),
         ("sakura", "sakura", 2), ("aster", "lav", 2)]


def bouquet_card(theme: str, snap: dict) -> Doc:
    pal = THEMES[theme]
    rng = random.Random(7)
    langs = list(snap["languages"].items())
    total = sum(v for _, v in langs) or 1
    shown = langs[:5]
    rest = sum(v for _, v in langs[5:])
    if rest:
        shown.append(("Other", rest))
    shares = [(name, size / total) for name, size in shown]

    doc = Doc(480, 300, title="Language bouquet",
              desc="Languages across public, non-fork repositories by code size: "
                   + ", ".join(f"{name} {share:.1%}" for name, share in shares) + ".")
    flora.install(doc)
    card(doc, pal, "LANGUAGE BOUQUET", "言語の花束")

    knot = (128.0, 238.0)
    art = []
    # greenery and filler behind the heads
    for angle in (-56, -30, -6, 20, 46):
        a = math.radians(angle - 90)
        tip = (knot[0] + math.cos(a) * 108, knot[1] + math.sin(a) * 108)
        art.append(place(tip[0], tip[1], flora.leaf(doc, pal, 30, 9, .4), rotate=angle))
    for k in range(4):
        a = math.radians(rng.uniform(-70, 70) - 90)
        art.append(place(knot[0] + math.cos(a) * 92, knot[1] + math.sin(a) * 92,
                         flora.gypsophila(pal, rng, 1.2, 3, 26), rotate=math.degrees(a) + 90))
    count = len(shares) or 1
    # the largest share stands in the middle, the rest alternate outward
    step = min(24.0, 66.0 / max(1, math.ceil((count - 1) / 2)))
    heads = []
    for i, (name, share) in enumerate(shares):
        kind, hue, _ = RANKS[i % len(RANKS)]
        slot = (i + 1) // 2 * (-1 if i % 2 else 1)
        angle = slot * step + (0 if i == 0 else rng.uniform(-4, 4))
        length = 124 - 34 * abs(angle) / 66
        a = math.radians(angle - 90)
        tip = (knot[0] + math.cos(a) * length, knot[1] + math.sin(a) * length)
        mid = ((knot[0] + tip[0]) / 2 + rng.uniform(-6, 6), (knot[1] + tip[1]) / 2)
        art.append(f'<path class="grow" pathLength="1" d="M{n(knot[0])} {n(knot[1])}Q{n(mid[0])} {n(mid[1])} '
                   f'{n(tip[0])} {n(tip[1])}" fill="none" stroke="{pal["stem"]}" stroke-width="1.8"'
                   f'{flora.delay_style(.3 + i * .1)}/>')
        r = 12 + 21 * math.sqrt(share)
        head = flora.flower(doc, pal, kind, r, 1.0 + i * .2, hue=hue, squash=.9, tilt=rng.uniform(-10, 10))
        heads.append((r, place(tip[0], tip[1], wrap("breathe", head, -rng.uniform(0, 6)))))
    # smaller heads first so the largest sits in front
    art.extend(markup for _, markup in sorted(heads, key=lambda h: h[0]))
    # wrapping paper and ribbon
    paper = doc.linear([(0, pal["kikyo"][5], 1), (1, pal["sakura"][4], 1)], x2=1, y2=1)
    kx, ky = knot
    art.append(
        f'<path d="M{n(kx - 50)} {n(ky - 30)}L{n(kx + 50)} {n(ky - 30)}L{n(kx + 10)} {n(ky + 52)}L{n(kx - 10)} {n(ky + 52)}Z" '
        f'fill="url(#{paper})" stroke="{pal["kikyo"][3]}" stroke-opacity=".6"/>'
        f'<path d="M{n(kx - 50)} {n(ky - 30)}L{n(kx - 6)} {n(ky + 52)}M{n(kx + 50)} {n(ky - 30)}L{n(kx + 6)} {n(ky + 52)}" '
        f'stroke="{pal["kikyo"][4]}" stroke-width=".8"/>'
    )
    bow = (
        f'<path d="M0 0C-18 -14 -26 2 -10 6Z M0 0C18 -14 26 2 10 6Z" fill="{pal["sakura"][1]}"/>'
        f'<path d="M-2 2C-8 14 -14 22 -18 30M2 2C8 14 12 22 18 28" stroke="{pal["sakura"][1]}" stroke-width="3" '
        f'fill="none" stroke-linecap="round"/><circle r="4.2" fill="{pal["sakura"][0]}"/>'
    )
    art.append(place(kx, ky + 4, wrap("pop", bow, 1.6)))
    doc.add("".join(art))

    # legend
    rows = []
    y = 84.0
    step = min(36.0, 190.0 / max(1, len(shares)))
    for i, (name, share) in enumerate(shares):
        kind, hue, shade = RANKS[i % len(RANKS)]
        color = pal[hue][shade]
        rows.append(place(260, y - 4.5, flora.flower(doc, pal, kind, 7.2, 0, hue=hue, still=True)))
        label, _ = doc.text([(name, "sans-bold", 13)], 276, y, attrs=f' fill="{pal["ink"]}"')
        pct, _ = doc.text([(f"{share * 100:.1f}%", "serif-bold", 17)], 454, y + 1, anchor="end",
                          attrs=f' fill="{pal["ink"]}"')
        bar = max(4.0, 178 * share)
        rows.append(
            label + pct
            + f'<rect x="276" y="{n(y + 8)}" width="178" height="3" rx="1.5" fill="{pal["ink3"]}" fill-opacity=".22"/>'
            + f'<rect x="276" y="{n(y + 8)}" width="{n(bar)}" height="3" rx="1.5" fill="{color}"/>'
        )
        y += step
    if not shares:
        empty, _ = doc.text([("No public code yet", "serif-italic", 17)], 360, 150, anchor="middle",
                            attrs=f' fill="{pal["ink2"]}"')
        rows.append(empty)
    note, _ = doc.text([("PUBLIC, NON-FORK REPOSITORIES · BY CODE SIZE", "sans", 9)], 454, 280, anchor="end",
                       spacing=1, attrs=f' fill="{pal["ink3"]}"')
    rows.append(note)
    doc.add(wrap("fadeup", "".join(rows), .8))
    return doc


# -- garden notes ------------------------------------------------------------------
EVENT_FLOWER = {
    "PushEvent": ("kikyo", "kikyo"),
    "CreateEvent": ("sakura", "sakura"),
    "WatchEvent": ("plum", "peach"),
    "ForkEvent": ("plum", "kikyo"),
    "PullRequestEvent": ("peony", "sakura"),
    "IssuesEvent": ("rose", "rose"),
    "IssueCommentEvent": ("plum", "sakura"),
    "ReleaseEvent": ("peony", "kikyo"),
    "PublicEvent": ("sakura", "sakura"),
}


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


def fit(text: str, face: str, size: float, width: float) -> str:
    if measure([(text, face, size)]) <= width:
        return text
    while text and measure([(text + "…", face, size)]) > width:
        text = text[:-1]
    return text + "…"


def notes_card(theme: str, snap: dict, tz: ZoneInfo, now: datetime) -> Doc:
    pal = THEMES[theme]
    user = snap["user"]
    notes = recent_notes(snap, tz, now)
    doc = Doc(480, 300, title="Garden notes",
              desc="Recent public activity: " + ("; ".join(f"{n_['text']} in {n_['repo']}" for n_ in notes)
                                                 or "none in the last 30 days") + ".")
    flora.install(doc)
    card(doc, pal, "GARDEN NOTES", "花便り")
    rows = []
    y = 86.0
    for i, note in enumerate(notes):
        kind, hue = EVENT_FLOWER.get(note["type"], ("plum", "lav"))
        rows.append(place(40, y + 3, flora.flower(doc, pal, kind, 8.5, .3 + i * .2, hue=hue)))
        stamp = note["local"].strftime("%b %-d · %H:%M")
        stamp_svg, stamp_w = doc.text([(stamp, "serif-italic", 14)], 454, y, anchor="end",
                                      attrs=f' fill="{pal["ink2"]}"')
        line, _ = doc.text([(fit(note["text"], "sans-bold", 13, 380 - stamp_w - 70), "sans-bold", 13)], 60, y,
                           attrs=f' fill="{pal["ink"]}"')
        repo = note["repo"].split("/", 1)[1] if note["repo"].lower().startswith(user.lower() + "/") else note["repo"]
        repo_svg, _ = doc.text([(fit(repo, "sans", 11.5, 390), "sans", 11.5)], 60, y + 17,
                               attrs=f' fill="{pal["ink2"]}"')
        rows.append(wrap("fadeup", stamp_svg + line + repo_svg, .3 + i * .2))
        if i < len(notes) - 1:
            rows.append(f'<path d="M60 {n(y + 28)}H454" stroke="{pal["border"]}" stroke-dasharray="2 4"/>')
        y += 40
    if not notes:
        msg, _ = doc.text([("The garden is resting", "serif-italic", 20)], 240, 160, anchor="middle",
                          attrs=f' fill="{pal["ink2"]}"')
        ja, _ = doc.text([("庭はひと休み中", "cjk", 14)], 240, 186, anchor="middle", spacing=3,
                         attrs=f' fill="{pal["ink3"]}"')
        rows.append(wrap("fadeup", msg + ja, .4))
        rows.append(place(240, 120, flora.flower(doc, pal, "kikyo", 16, .2, hue="kikyo")))
    footer, _ = doc.text([(f"LAST 30 DAYS · {tz.key.upper()}", "sans", 9)], 454, 280, anchor="end", spacing=1,
                         attrs=f' fill="{pal["ink3"]}"')
    rows.append(footer)
    doc.add("".join(rows))
    return doc


def load_snapshot(user: str, offline: bool) -> dict:
    if not offline:
        try:
            snap = data.collect(user)
            SNAPSHOT.parent.mkdir(exist_ok=True)
            SNAPSHOT.write_text(json.dumps(snap, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            return snap
        except Exception as error:  # keep the last good cards rather than failing the run
            if not SNAPSHOT.exists():
                raise
            print(f"fetch failed ({error}); using {SNAPSHOT.relative_to(ROOT)}", file=sys.stderr)
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def main(argv: list[str]) -> int:
    config = json.loads((ROOT / "garden.json").read_text(encoding="utf-8"))
    snap = load_snapshot(config["user"], "--offline" in argv)
    tz = ZoneInfo(config.get("timezone", "UTC"))
    fetched = datetime.fromisoformat(snap["fetched_at"].replace("Z", "+00:00"))
    now = max(fetched, datetime.now(timezone.utc)) if "--offline" not in argv else fetched
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in ("light", "dark"):
        for name, doc in (("calendar", calendar_card(theme, snap)), ("bouquet", bouquet_card(theme, snap)),
                          ("notes", notes_card(theme, snap, tz, now))):
            (OUT / f"{name}-{theme}.svg").write_text(doc.render(animated=True), encoding="utf-8")
            print(f"{name}-{theme}.svg")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
