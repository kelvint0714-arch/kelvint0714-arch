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

from garden import data, depth, flora  # noqa: E402
from garden.flora import place, wrap  # noqa: E402
from garden.palette import THEMES  # noqa: E402
from garden.svg import Doc, n  # noqa: E402
from garden.text import measure  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "snapshot.json"
OUT = ROOT / "assets" / "metrics"


# -- shared soft card -------------------------------------------------------
def card(doc: Doc, pal: dict, title: str, title_ja: str) -> None:
    """A rounded surface with a gently curved line below the heading."""
    doc.add(depth.raised(doc, pal, 8, 6, doc.width - 16, doc.height - 22, rx=23))
    head, head_w = doc.text([(title, "sans-bold", 12)], 52, 43, spacing=1.6,
                            attrs=f' fill="{pal["ink"]}"')
    ja, _ = doc.text([(title_ja, "cjk", 13)], 52 + head_w + 12, 43.5, spacing=1.2,
                     attrs=f' fill="{pal["ink2"]}"')
    doc.add(place(35, 38, flora.flower(doc, pal, "sakura", 7.3, .1, hue="sakura", shadow=True)))
    doc.add(wrap("fadeup", head + ja, .1))
    doc.add(f'<path d="M32 62Q{n(doc.width / 2)} 58 {n(doc.width - 32)} 62" '
            f'fill="none" stroke="{pal["border"]}" stroke-width=".8" stroke-opacity=".7"/>')


def mix(color: str, other: str, t: float) -> str:
    a = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


# -- bloom calendar: a low, softly rounded garden ----------------------------
CALENDAR_FLOWERS = [None, ("plum", "calendar-1", 3.6, 4.5), ("sakura", "calendar-2", 4.5, 6.8),
                    ("sakura", "calendar-3", 5.5, 9.0), ("peony", "calendar-4", 6.5, 12.0)]
CALENDAR_RAMPS = {
    "light": [
        ["#B47D92", "#C58FA4", "#D6A7B7", "#E1BBC7", "#EBCFDA", "#F6E4E8"],
        ["#A85D7F", "#B97093", "#CB90AB", "#DCA9BB", "#E7C1CC", "#F2DAE0"],
        ["#92445F", "#AB5D7B", "#BF7A94", "#D094A9", "#E1AFBC", "#EECBD5"],
        ["#7F3A59", "#984B6B", "#B16484", "#C37F9A", "#D89AAF", "#E9B9CB"],
    ],
    "dark": [
        ["#7D4D6A", "#95667F", "#A7758F", "#B88CA2", "#CAA2B6", "#DDBBCC"],
        ["#91617D", "#AA7A96", "#BD8FA9", "#CEA5BC", "#DDBAD0", "#EAD2DF"],
        ["#A37890", "#BB94A9", "#CAA8B9", "#DBBDC9", "#E6D0D9", "#F1E1E7"],
        ["#B38B9D", "#C7A5B4", "#D8BBC7", "#E6CED6", "#F0DEE5", "#F8EBEF"],
    ],
}


def calendar_symbols(doc: Doc, pal: dict) -> list[str]:
    """One sleeping seed and four increasingly full flower heads.

    The heads share the dimensional petal drawing used elsewhere in the
    garden. The calendar supplies their stems and paints them back to front.
    """
    light = pal["scheme"] == "light"
    # Separate hue names also separate flora's memoized gradients and symbols
    # from the decorative title flowers already drawn in this document.
    flower_pal = dict(pal)
    flower_pal.update({f"calendar-{i}": ramp for i, ramp in enumerate(CALENDAR_RAMPS[pal["scheme"]], 1)})
    seed = doc.radial([(0, mix(pal["card"], pal["kikyo"][3], .22 if light else .18), 1),
                       (.7, mix(pal["soil"][0], pal["kikyo"][2], .2 if light else .12), 1),
                       (1, mix(pal["soil"][1], pal["ink3"], .12), 1)], cx=.3, cy=.2, r=.95)
    ref = doc.uid("dayseed")
    doc.defs.append(f'<g id="{ref}"><ellipse cx=".5" cy="1" rx="2.8" ry="1.5" '
                    f'fill="{pal["shadow"]}" fill-opacity="{.07 if light else .18}"/>'
                    f'<ellipse rx="2.45" ry="1.45" fill="url(#{seed})"/></g>')
    ids = [ref]
    for spec in CALENDAR_FLOWERS[1:]:
        kind, hue, radius, _ = spec
        ref = doc.uid("dayflower")
        head = flora.flower(doc, flower_pal, kind, radius, 0, hue=hue, squash=.88,
                            still=True, shadow=True)
        doc.defs.append(f'<g id="{ref}">{head}</g>')
        ids.append(ref)
    return ids


def soft_bed(doc: Doc, pal: dict, corners: list[tuple[float, float]]) -> str:
    """A shallow, rounded flower bed with a broad light and a soft lower lip."""
    light = pal["scheme"] == "light"
    entry, leave = [], []
    for i, point in enumerate(corners):
        before, after = corners[i - 1], corners[(i + 1) % len(corners)]
        distances = [math.dist(point, before), math.dist(point, after)]
        radius = min(20.0, *[distance * .24 for distance in distances])
        entry.append(tuple(a + (b - a) * radius / distances[0] for a, b in zip(point, before)))
        leave.append(tuple(a + (b - a) * radius / distances[1] for a, b in zip(point, after)))
    outline = f'M{n(leave[0][0])} {n(leave[0][1])}'
    for i in (1, 2, 3, 0):
        outline += (f'L{n(entry[i][0])} {n(entry[i][1])}Q{n(corners[i][0])} {n(corners[i][1])} '
                    f'{n(leave[i][0])} {n(leave[i][1])}')
    outline += 'Z'
    surface = doc.linear([(0, pal["planter"][0], 1),
                          (.45, mix(pal["planter"][1], pal["kikyo"][4], .24 if light else .045), 1),
                          (1, pal["soil"][0], 1)], x1=0, y1=0, x2=.15, y2=1)
    edge = doc.linear([(0, pal["planter"][1], 1), (.65, pal["planter"][2], 1),
                       (1, mix(pal["planter"][3], pal["kikyo"][1], .12), 1)])
    cast = doc.radial([(0, pal["shadow"], .19 if light else .38), (.65, pal["shadow"], .08 if light else .2),
                       (1, pal["shadow"], 0)])
    glow = doc.radial([(0, pal["cream"][0], .36 if light else .045), (1, pal["cream"][0], 0)], cx=.23, cy=.15, r=.85)
    center = tuple(sum(p[i] for p in corners) / 4 for i in (0, 1))
    width = max(p[0] for p in corners) - min(p[0] for p in corners)
    angle = math.degrees(math.atan2(corners[1][1] - corners[0][1], corners[1][0] - corners[0][0]))
    return (
        f'<ellipse cx="{n(center[0] + 3)}" cy="{n(center[1] + 35)}" rx="{n(width * .53)}" ry="48" '
        f'transform="rotate({n(angle)} {n(center[0] + 3)} {n(center[1] + 35)})" fill="url(#{cast})"/>'
        f'<path d="{outline}" transform="translate(0 9)" fill="url(#{edge})"/>'
        f'<path d="{outline}" transform="translate(0 3.5)" fill="{pal["planter"][1]}"/>'
        f'<path d="{outline}" fill="url(#{surface})"/>'
        f'<path d="{outline}" fill="url(#{glow})" stroke="{pal["cream"][0] if light else pal["border"]}" '
        f'stroke-opacity="{.36 if light else .45}" stroke-width="1"/>'
    )


def calendar_card(theme: str, snap: dict) -> Doc:
    pal = THEMES[theme]
    days = data.days_from(snap)
    columns = data.week_columns(days)
    total = snap["calendar"]["total"]
    longest, current = data.streaks(days)
    best = max(days, key=lambda d: d.count) if days else None
    interval = (f"{days[0].date.isoformat()} to {days[-1].date.isoformat()}" if days else "the past year")

    doc = Doc(960, 440, title="Bloom calendar",
              desc=f"A softly dimensional flower garden for {interval}: one mark per supplied day in seven weekday rows, "
                   f"{total} contributions, longest streak {longest} days, current streak {current} days. "
                   "Sleeping seeds mean no contributions. Taller stems and fuller flowers mean busier days; "
                   "the four activity levels are the ones reported by GitHub. Weeks run diagonally across the garden.")
    flora.install(doc)
    card(doc, pal, "BLOOM CALENDAR", "花暦")
    note, _ = doc.text([("ONE FLOWER A DAY · 一日一輪", "sans", 9.5)], 924, 43, anchor="end", spacing=.8,
                       attrs=f' fill="{pal["ink3"]}"')
    doc.add(wrap("fadeup", note, .2))

    stats = [
        (f"{total:,}", "CONTRIBUTIONS", "この一年"),
        (f"{longest} day{'s' if longest != 1 else ''}", "LONGEST STREAK", "最長連続"),
        (f"{current} day{'s' if current != 1 else ''}", "CURRENT STREAK", "現在の連続"),
        (best.date.strftime("%b %-d") if best and best.count else "—", "BEST DAY", "満開の日"),
    ]
    block = []
    for i, (value, label, ja) in enumerate(stats):
        sx = (40, 274, 504, 736)[i]
        v, _ = doc.text([(value, "serif-bold", 37 if i == 0 else 32)], sx, 105,
                        attrs=f' fill="{pal["ink"]}"')
        lab, lab_w = doc.text([(label, "sans", 9)], sx, 125, spacing=.8,
                              attrs=f' fill="{pal["ink2"]}"')
        j, _ = doc.text([(ja, "cjk", 10.2)], sx + lab_w + 9, 125.5,
                        attrs=f' fill="{pal["ink3"]}"')
        block.append(v + lab + j)
        if i:
            block.append(f'<path d="M{sx - 24} 86Q{sx - 26} 104 {sx - 24} 122" '
                         f'stroke="{pal["border"]}" stroke-width=".8" fill="none"/>')
    doc.add(wrap("fadeup", "".join(block), .2))

    # A shallow projection leaves the entire statistics band clear. Every
    # week still has Sunday through Saturday in the same seven row positions.
    cols = max(1, len(columns))
    u = (min(15.2, 790 / max(1, cols - 1)), 1.2)
    v = (-3.8, 11.5)
    origin = (124.0, 207.0)
    def project(col: float, row: float) -> tuple[float, float]:
        return origin[0] + col * u[0] + row * v[0], origin[1] + col * u[1] + row * v[1]

    corners = [project(-1, -1.05), project(cols - .15, -1.05),
               project(cols - .15, 7.0), project(-1, 7.0)]
    doc.add(wrap("fadeup", soft_bed(doc, pal, corners), .25))
    marks = calendar_symbols(doc, pal)

    cells = []
    for col, week in enumerate(columns):
        for row, day in enumerate(week):
            if day is None:
                continue
            x, y = project(col, row)
            if day.level == 0:
                body = f'<use href="#{marks[0]}"/>'
            else:
                _, _, radius, height = CALENDAR_FLOWERS[day.level]
                bend = math.sin(col * .7 + row * 1.15) * 1.5
                ground = doc.memo("day-ground", lambda: doc.radial(
                    [(0, pal["shadow"], .2 if pal["scheme"] == "light" else .38), (1, pal["shadow"], 0)]))
                body = (
                    f'<ellipse cx="1.6" cy="1.4" rx="{n(radius + 2)}" ry="3" fill="url(#{ground})"/>'
                    f'<path d="M0 .8C{n(-bend)} {n(-height * .22)} {n(bend * 1.7)} {n(-height * .72)} '
                    f'{n(bend)} {n(-height)}" fill="none" stroke="{pal["stem"]}" '
                    f'stroke-width="1" stroke-linecap="round"/>'
                )
                if day.level > 2:
                    body += place(bend * .2, -height * .38,
                                  flora.leaf(doc, pal, 4.2, 1.35, 0, shade=2), rotate=58 if (col + row) % 2 else -54)
                body += place(bend, -height, f'<use href="#{marks[day.level]}"/>')
            label = f"{day.date.isoformat()}: {day.count} contribution{'s' if day.count != 1 else ''}"
            cell = (f'<g class="calendar-day" data-date="{day.date.isoformat()}" data-level="{day.level}" '
                    f'data-count="{day.count}" transform="translate({n(x)} {n(y)})">'
                    f'<title>{label}</title>{wrap("fadeup", body, .35 + col * .012 + row * .018)}</g>')
            cells.append((y, x, cell))
    doc.add("".join(cell for _, _, cell in sorted(cells)))

    # Labels share the projection but remain horizontal for easy reading.
    labels = []
    last_right = -1.0
    for col, week in enumerate(columns):
        day = next((d for d in week if d and (d.date.day == 1 or d.date == days[0].date)), None)
        if day:
            x, y = project(col, -2.65)
            label, width = doc.text([(day.date.strftime("%b"), "sans", 10.5)], x - 7, y,
                                    attrs=f' fill="{pal["ink2"]}"')
            if x - 7 >= last_right + 7:
                labels.append(label)
                last_right = x - 7 + width
    for row, name in enumerate(("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")):
        x, y = project(-2.2, row)
        text, _ = doc.text([(name, "sans", 9)], x - 7, y + 3, anchor="end",
                           attrs=f' fill="{pal["ink3"]}"')
        labels.append(text)
    doc.add(wrap("fadeup", "".join(labels), .3))

    footer = []
    if days:
        period = f"{days[0].date.strftime('%b %-d, %Y')} — {days[-1].date.strftime('%b %-d, %Y')}"
        text, _ = doc.text([(period, "sans", 9.5)], 39, 405,
                           attrs=f' fill="{pal["ink3"]}"')
        footer.append(text)
    less, _ = doc.text([("Less", "sans", 9.5)], 737, 405, anchor="end",
                       attrs=f' fill="{pal["ink3"]}"')
    footer.append(less)
    for level, x in enumerate((756, 782, 808, 834, 860)):
        footer.append(place(x, 401.5, f'<use href="#{marks[level]}"/>'))
    more, _ = doc.text([("More", "sans", 9.5)], 883, 405,
                       attrs=f' fill="{pal["ink3"]}"')
    footer.append(more)
    doc.add(wrap("fadeup", "".join(footer), .8))
    return doc


# -- language bouquet -------------------------------------------------------
RANKS = [("peony", "sakura", 1), ("rose", "rose", 1), ("sakura", "kikyo", 1), ("plum", "peach", 1),
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

    doc = Doc(480, 336, title="Language bouquet",
              desc="Languages across public, non-fork repositories by code size: "
                   + ", ".join(f"{name} {share:.1%}" for name, share in shares) + ".")
    flora.install(doc)
    card(doc, pal, "LANGUAGE BOUQUET", "言語の花束")

    # Bowed stems cross loosely at the ribbon; the flower heads overlap in depth.
    knot = (111.0, 252.0)
    tips = [(110, 124), (54, 157), (160, 164), (83, 193), (161, 207), (47, 217)]
    art, heads = [], []
    cast = doc.radial([(0, pal["shadow"], .15 if pal["scheme"] == "light" else .28),
                       (.5, pal["shadow"], .055 if pal["scheme"] == "light" else .1), (1, pal["shadow"], 0)])
    if shares:
        art.append(f'<ellipse cx="120" cy="274" rx="67" ry="16" fill="url(#{cast})"/>')
    for i, (_, share) in enumerate(shares):
        kind, hue, _ = RANKS[i % len(RANKS)]
        tx, ty = tips[i]
        side = -1 if i % 2 else 1
        start = (knot[0] + (i - 2) * 1.6, knot[1] + 17 + (i % 3) * 2)
        c1 = (knot[0] + side * 16, 229.0)
        c2 = (tx - side * 19, ty + 43.0)
        art.append(
            f'<path class="grow" pathLength="1" d="M{n(start[0])} {n(start[1])}'
            f'C{n(c1[0])} {n(c1[1])} {n(c2[0])} {n(c2[1])} {tx} {ty}" '
            f'fill="none" stroke="{pal["stem"]}" stroke-width="1.65" stroke-linecap="round"'
            f'{flora.delay_style(.2 + i * .08)}/>'
        )
        t = .54
        lx, ly = [((1 - t) ** 3 * start[j] + 3 * (1 - t) ** 2 * t * c1[j]
                   + 3 * (1 - t) * t * t * c2[j] + t ** 3 * (tx, ty)[j]) for j in (0, 1)]
        art.append(place(lx, ly, flora.leaf(doc, pal, 20 + i % 2 * 5, 6, .3 + i * .08),
                         rotate=-55 if i % 2 else 54))
        r = 11 + 24 * math.sqrt(share)
        head = flora.flower(doc, pal, kind, r, .45 + i * .12, hue=hue,
                            squash=.86 + .02 * (i % 3), tilt=rng.uniform(-20, 20), shadow=True)
        heads.append((ty, place(tx, ty, head)))
    art.extend(markup for _, markup in sorted(heads, key=lambda h: h[0]))
    if shares:
        ribbon = doc.linear([(0, pal["sakura"][4], 1), (.38, pal["sakura"][2], 1),
                             (.72, pal["sakura"][1], 1), (1, pal["sakura"][3], 1)],
                            x1=-29, y1=-17, x2=27, y2=21, user=True)
        bow = (
            f'<path d="M-3 3C-4 15 -20 22 -17 34L-8 28C-11 19 3 12 4 4Z'
            f'M2 3C10 11 17 14 25 25L27 16C21 9 12 7 5 1Z" fill="url(#{ribbon})"/>'
            f'<path d="M0 0C-12 -21 -33 -19 -28 -4C-25 6 -9 7 0 0'
            f'C14 -18 31 -11 27 2C24 11 8 5 0 0Z" fill="url(#{ribbon})" '
            f'stroke="{pal["sakura"][1]}" stroke-opacity=".35" stroke-width=".65"/>'
            f'<path d="M-22 -9Q-13 -11 -4 -1M5 -2Q15 -8 23 -4" fill="none" '
            f'stroke="{pal["sakura"][5]}" stroke-width=".8" stroke-opacity=".5"/>'
            f'<ellipse rx="4" ry="3.4" fill="{pal["sakura"][2]}"/>'
        )
        art.append(place(*knot, wrap("fadeup", bow, .65)))
    caption, _ = doc.text([("growing, quietly", "serif-italic", 13.5)], 110, 296, anchor="middle",
                          attrs=f' fill="{pal["ink3"]}"')
    art.append(caption)
    doc.add("".join(art))

    rows = []
    y = 90.0
    for i, (name, share) in enumerate(shares):
        kind, hue, shade = RANKS[i % len(RANKS)]
        color = pal[hue][shade if pal["scheme"] == "light" else max(shade, 3)]
        rows.append(place(212, y - 4, flora.flower(doc, pal, kind, 5.4, 0, hue=hue,
                                                 still=True, shadow=True)))
        label, _ = doc.text([(fit(name, "sans-bold", 12, 160), "sans-bold", 12)], 227, y,
                            attrs=f' fill="{pal["ink"]}"')
        pct, _ = doc.text([(f"{share * 100:.1f}%", "serif-bold", 17)], 448, y + 1, anchor="end",
                          attrs=f' fill="{pal["ink"]}"')
        rows.append(label + pct)
        rows.append(f'<path d="M227 {n(y + 13.8)}H448" stroke="{pal["shadow"]}" stroke-width="3.8" '
                    f'stroke-opacity=".055" stroke-linecap="round"/>')
        rows.append(f'<path d="M227 {n(y + 13)}H448" stroke="{pal["border"]}" stroke-width="3.2" stroke-linecap="round"/>')
        if share > 0:
            tint = doc.linear([(0, pal[hue][3], 1), (.55, color, 1), (1, pal[hue][2], 1)],
                              x1=227, y1=y + 13, x2=227 + 221 * share, y2=y + 13, user=True)
            rows.append(f'<path d="M227 {n(y + 13)}h{n(221 * share)}" stroke="url(#{tint})" '
                        f'stroke-width="3.2" stroke-linecap="round"/>')
        y += 35.5
    if not shares:
        empty, _ = doc.text([("No public code yet", "serif-italic", 17)], 327, 162, anchor="middle",
                            attrs=f' fill="{pal["ink2"]}"')
        rows.append(empty)
    note, _ = doc.text([("PUBLIC, NON-FORK REPOSITORIES · BY CODE SIZE", "sans", 8)], 448, 312, anchor="end",
                       spacing=.65, attrs=f' fill="{pal["ink3"]}"')
    rows.append(note)
    doc.add(wrap("fadeup", "".join(rows), .4))
    return doc


# -- garden notes ------------------------------------------------------------------
EVENT_FLOWER = {
    "PushEvent": ("sakura", "sakura"),
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
    doc = Doc(480, 336, title="Garden notes",
              desc="Recent public activity: " + ("; ".join(
                  f"{n_['local'].strftime('%Y-%m-%d %H:%M')} {tz.key}, {n_['text']} in {n_['repo']}" for n_ in notes)
                                                 or "none in the last 30 days") + ".")
    flora.install(doc)
    card(doc, pal, "GARDEN NOTES", "花便り")
    rows = []
    y = 91.0
    nodes = [(105 + 3.2 * math.sin(i * 1.45), y - 4 + i * 43) for i in range(len(notes))]
    light = pal["scheme"] == "light"
    note_face = doc.linear([(0, mix(pal["card"], pal["sakura"][5], .48 if light else .025), 1),
                            (1, pal["card"], 1)])
    note_shadow = doc.radial([(0, pal["shadow"], .08 if light else .15), (1, pal["shadow"], 0)])
    if len(notes) > 1:
        vine = f'M{n(nodes[0][0])} {n(nodes[0][1])}'
        for before, after in zip(nodes, nodes[1:]):
            vine += (f'C{n(before[0] - 7)} {n(before[1] + 16)} '
                     f'{n(after[0] + 6)} {n(after[1] - 15)} {n(after[0])} {n(after[1])}')
        rows.append(f'<path class="grow" pathLength="1" d="{vine}" stroke="{pal["vine"]}" '
                    f'stroke-opacity=".7" stroke-width="1.2" fill="none"{flora.delay_style(.15)}/>')
    for i, note in enumerate(notes):
        kind, hue = EVENT_FLOWER.get(note["type"], ("plum", "lav"))
        row_surface = (f'<ellipse cx="285" cy="{n(y + 9)}" rx="172" ry="20" fill="url(#{note_shadow})"/>'
                       f'<rect x="116" y="{n(y - 15)}" width="338" height="37" rx="14" '
                       f'fill="url(#{note_face})"/>')
        rows.append(wrap("fadeup", row_surface, .15 + i * .08))
        node_x, node_y = nodes[i]
        rows.append(place(node_x - 1, node_y + 15,
                          flora.leaf(doc, pal, 7.5, 2.4, .2 + i * .08, shade=2), rotate=-50 if i % 2 else 52))
        rows.append(place(node_x, node_y, flora.flower(doc, pal, kind, 6.8, .2 + i * .08, hue=hue, shadow=True)))
        stamp = note["local"].strftime("%b %-d")
        stamp_svg, _ = doc.text([(stamp, "sans", 10)], 83, y - 1, anchor="end",
                                attrs=f' fill="{pal["ink2"]}"')
        clock, _ = doc.text([(note["local"].strftime("%H:%M"), "sans", 9)], 83, y + 14, anchor="end",
                            attrs=f' fill="{pal["ink3"]}"')
        line, _ = doc.text([(fit(note["text"], "sans-bold", 11.6, 325), "sans-bold", 11.6)], 123, y,
                           attrs=f' fill="{pal["ink"]}"')
        repo = note["repo"].split("/", 1)[1] if note["repo"].lower().startswith(user.lower() + "/") else note["repo"]
        repo_svg, _ = doc.text([(fit(repo, "sans", 10.5, 325), "sans", 10.5)], 123, y + 16,
                               attrs=f' fill="{pal["ink2"]}"')
        rows.append(wrap("fadeup", stamp_svg + clock + line + repo_svg, .2 + i * .08))
        y += 43
    if not notes:
        msg, _ = doc.text([("The garden is resting", "serif-italic", 20)], 240, 160, anchor="middle",
                          attrs=f' fill="{pal["ink2"]}"')
        ja, _ = doc.text([("庭はひと休み中", "cjk", 14)], 240, 186, anchor="middle", spacing=3,
                         attrs=f' fill="{pal["ink3"]}"')
        rows.append(wrap("fadeup", msg + ja, .4))
        rows.append(place(240, 120, flora.flower(doc, pal, "sakura", 16, .2, hue="sakura", shadow=True)))
    footer, _ = doc.text([(f"LAST 30 DAYS · {tz.key.upper()}", "sans", 8)], 448, 312, anchor="end", spacing=.65,
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
