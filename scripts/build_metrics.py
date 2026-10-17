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


# -- shared card frame -------------------------------------------------------
def card(doc: Doc, pal: dict, title: str, title_ja: str) -> None:
    """A raised panel inset from the canvas so its shadow has room, with the card's heading."""
    doc.add(depth.raised(doc, pal, 8, 6, doc.width - 16, doc.height - 22, rx=18))
    head, head_w = doc.text([(title, "sans-bold", 13.5)], 54, 44, spacing=2.2, attrs=f' fill="{pal["ink"]}"')
    ja, _ = doc.text([(title_ja, "cjk-bold", 15)], 54 + head_w + 12, 44.5, spacing=2,
                     attrs=f' fill="{pal["kikyo"][1] if pal["scheme"] == "light" else pal["kikyo"][3]}"')
    doc.add(place(36, 39, flora.flower(doc, pal, "kikyo", 9, .2, hue="kikyo")))
    doc.add(wrap("fadeup", head + ja, .1))


def mix(color: str, other: str, t: float) -> str:
    a = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


# -- bloom calendar: an isometric flower bed -----------------------------------
U = (15.0, 3.3)    # one week to the right and slightly toward the viewer
V = (-7.4, 7.0)    # one weekday toward the viewer (Sunday at the back)
TILE = .86         # share of a cell covered by its tile
RAISE = [0, 3, 6, 9, 13]          # tile height per level
STEM = [0, 7, 11, 15, 20]         # stem height above the tile
HEADS = [None, ("plum", 4.2, "kikyo"), ("sakura", 5.8, "sakura"), ("kikyo", 7.0, "kikyo"), ("peony", 8.0, "sakura")]


def iso(origin, col: float, row: float) -> tuple[float, float]:
    return origin[0] + col * U[0] + row * V[0], origin[1] + col * U[1] + row * V[1]


def poly(points, fill: str, extra: str = "") -> str:
    d = "M" + "L".join(f"{n(x)} {n(y)}" for x, y in points) + "Z"
    return f'<path d="{d}" fill="{fill}"{extra}/>'


def tile_colors(pal: dict) -> list[tuple[str, str, str]]:
    """(top, front, right) faces per level, soil to lush grass."""
    if pal["scheme"] == "light":
        tops = [pal["soil"][0], "#DCEBD3", "#C3DFB7", "#A6CF98", "#86BC7B"]
        shade = "#4A3F66"
    else:
        tops = [pal["soil"][0], "#2F4A3C", "#3A5E45", "#467451", "#548A5F"]
        shade = "#05060F"
    return [(top, mix(top, shade, .16), mix(top, shade, .3)) for top in tops]


def calendar_card(theme: str, snap: dict) -> Doc:
    pal = THEMES[theme]
    light = pal["scheme"] == "light"
    days = data.days_from(snap)
    columns = data.week_columns(days)
    total = snap["calendar"]["total"]
    longest, current = data.streaks(days)
    best = max(days, key=lambda d: d.count) if days else None

    doc = Doc(960, 408, title="Bloom calendar",
              desc=f"An isometric flower bed with one tile per day of the past year: {total} contributions, "
                   f"longest streak {longest} days, current streak {current} days. Busier days rise higher "
                   "and carry fuller flowers.")
    flora.install(doc)
    card(doc, pal, "BLOOM CALENDAR", "花暦")
    note, _ = doc.text([("ONE FLOWER A DAY · 一日一輪", "sans", 10.5)], 930, 44, anchor="end", spacing=1.4,
                       attrs=f' fill="{pal["ink3"]}"')
    doc.add(wrap("fadeup", note, .2))

    origin = (120.0, 118.0)
    cols = len(columns)
    colors = tile_colors(pal)
    heads = [None] + [flora.flower_symbol(doc, pal, kind, hue) for kind, _, hue in HEADS[1:]]

    # the planter: soil bed with a lit rim, a front face and a darker right face
    thick = 18
    a, b = iso(origin, -.45, -.45), iso(origin, cols + .3, -.45)
    c, d = iso(origin, cols + .3, 7.3), iso(origin, -.45, 7.3)
    front = doc.linear([(0, pal["planter"][1], 1), (1, pal["planter"][2], 1)])
    bed = [
        poly([(x + 10, y + 12) for x, y in (d, c, (c[0], c[1] + thick), (d[0], d[1] + thick))], pal["shadow"],
             f' fill-opacity="{".1" if light else ".35"}"'),
        poly([b, c, (c[0], c[1] + thick), (b[0], b[1] + thick)], pal["planter"][3]),
        poly([d, c, (c[0], c[1] + thick), (d[0], d[1] + thick)], f"url(#{front})"),
        poly([a, b, c, d], pal["soil"][1]),
        poly([a, b, c, d], "none", f' stroke="{pal["planter"][0]}" stroke-width="3" stroke-linejoin="round"'),
        f'<path d="M{n(d[0])} {n(d[1] + 1.6)}L{n(c[0])} {n(c[1] + 1.6)}" stroke="#FFFFFF" '
        f'stroke-opacity="{".7" if light else ".18"}" stroke-width="1.2"/>',
    ]
    doc.add(wrap("fadeup", "".join(bed), .3))

    # flat tiles first (they never hide one another), grouped into one path per colour
    flat: dict[str, list[str]] = {}
    raised_tiles = []
    for col, week in enumerate(columns):
        for row, day in enumerate(week):
            if day is None:
                continue
            if day.level == 0:
                pts = [iso(origin, col, row), iso(origin, col + TILE, row), iso(origin, col + TILE, row + TILE),
                       iso(origin, col, row + TILE)]
                flat.setdefault(colors[0][0], []).append("M" + "L".join(f"{n(x)} {n(y)}" for x, y in pts) + "Z")
            else:
                raised_tiles.append((iso(origin, col + .5, row + .5)[1], col, row, day))
    doc.add(wrap("fadeup", "".join(f'<path d="{"".join(ds)}" fill="{fill}"/>' for fill, ds in flat.items()), .5))

    # raised tiles and their flowers, painted back to front
    cells = []
    for _, col, row, day in sorted(raised_tiles):
        h = RAISE[day.level]
        top, side_front, side_right = colors[day.level]
        base = iso(origin, col, row)
        local = lambda c_, r_: (iso(origin, col + c_, row + r_)[0] - base[0], iso(origin, col + c_, row + r_)[1] - base[1])
        p0, p1, p2, p3 = local(0, 0), local(TILE, 0), local(TILE, TILE), local(0, TILE)
        up = lambda p: (p[0], p[1] - h)
        body = (
            poly([p3, p2, up(p2), up(p3)], side_front)
            + poly([p1, p2, up(p2), up(p1)], side_right)
            + poly([up(p0), up(p1), up(p2), up(p3)], top)
        )
        kind, r, _ = HEADS[day.level]
        cx, cy = local(TILE / 2, TILE / 2)
        cy -= h
        stem = STEM[day.level]
        body += (
            f'<ellipse cx="{n(cx + 1)}" cy="{n(cy + .6)}" rx="{n(r * .7)}" ry="{n(r * .3)}" fill="{pal["shadow"]}" fill-opacity=".18"/>'
            f'<path d="M{n(cx)} {n(cy)}q1 {n(-stem * .5)} 0 {n(-stem)}" stroke="{pal["stem"]}" stroke-width="1.1" fill="none"/>'
            f'<use href="#{heads[day.level]}" transform="translate({n(cx)} {n(cy - stem)}) scale({n(r / flora.UNIT, 3)} {n(r * .82 / flora.UNIT, 3)})"/>'
        )
        cells.append(place(base[0], base[1], wrap("fadeup", body, .7 + col * .03 + row * .01)))
    doc.add("".join(cells))

    # months along the back edge, weekdays down the left edge
    labels = []
    last = -9
    for col, week in enumerate(columns):
        first = next((d for d in week if d and d.date.day == 1), None)
        if first and col - last >= 3:
            x, y = iso(origin, col, -2.1)
            text, _ = doc.text([(first.date.strftime("%b"), "sans", 10.5)], x, y - 2, attrs=f' fill="{pal["ink3"]}"')
            labels.append(text)
            last = col
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        x, y = iso(origin, -1.0, row + .5)
        text, _ = doc.text([(name, "sans", 10)], x, y + 3.5, anchor="end", attrs=f' fill="{pal["ink3"]}"')
        labels.append(text)
    doc.add(wrap("fadeup", "".join(labels), .4))  # after the cells: labels stay readable over tall flowers

    # stats in the open corner above the bed
    stats = [
        (f"{total:,}", "CONTRIBUTIONS", "この一年"),
        (f"{longest} day{'s' if longest != 1 else ''}", "LONGEST STREAK", "最長連続"),
        (f"{current} day{'s' if current != 1 else ''}", "CURRENT STREAK", "現在の連続"),
        (best.date.strftime("%b %-d") if best and best.count else "—", "BEST DAY", "満開の日"),
    ]
    block = []
    for i, (value, label, ja) in enumerate(stats):
        sx, sy = 584 + (i % 2) * 190, 96 + (i // 2) * 60
        v, _ = depth.text3d(doc, pal, [(value, "serif-bold", 28)], sx, sy, face=pal["ink"],
                            side=[pal["kikyo"][3], pal["kikyo"][2]] if light else [pal["kikyo"][1], pal["kikyo"][0]],
                            depth=3, step=(.6, .8))
        lab, lab_w = doc.text([(label, "sans", 10)], sx, sy + 19, spacing=1.4, attrs=f' fill="{pal["ink2"]}"')
        j, _ = doc.text([(ja, "cjk", 11)], sx + lab_w + 7, sy + 19.5, attrs=f' fill="{pal["ink3"]}"')
        block.append(v + lab + j)
    doc.add(wrap("fadeup", "".join(block), 1.6))

    # legend in the open corner below the bed
    legend = []
    lx, ly = 52.0, 352.0
    less, less_w = doc.text([("Less", "sans", 11)], lx, ly, attrs=f' fill="{pal["ink3"]}"')
    legend.append(less)
    x = lx + less_w + 14
    for level in range(5):
        top, side_front, side_right = colors[level]
        h = RAISE[level] * .7
        sq = [(0, 0), (11, 2.4), (5.6, 7.4), (-5.4, 5)]
        up = lambda p: (p[0], p[1] - h)
        item = (poly([sq[3], sq[2], up(sq[2]), up(sq[3])], side_front) + poly([sq[1], sq[2], up(sq[2]), up(sq[1])], side_right)
                + poly([up(p) for p in sq], top))
        if level:
            kind, r, _ = HEADS[level]
            item += f'<use href="#{heads[level]}" transform="translate(2.8 {n(3.7 - h - 6)}) scale({n(r / flora.UNIT, 3)})"/>'
        legend.append(place(x, ly - 6, item))
        x += 26
    more, _ = doc.text([("More", "sans", 11)], x - 2, ly, attrs=f' fill="{pal["ink3"]}"')
    legend.append(more)
    doc.add(wrap("fadeup", "".join(legend), 1.8))
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

    doc = Doc(480, 316, title="Language bouquet",
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
    # wrapping paper: a lit cone with a shaded flank, standing on the table
    kx, ky = knot
    light = pal["scheme"] == "light"
    paper = doc.linear([(0, pal["kikyo"][4], 1), (.35, pal["kikyo"][5], 1), (.7, pal["sakura"][4], 1),
                        (1, pal["sakura"][3], 1)], x2=1, y2=0)
    flap = doc.linear([(0, pal["kikyo"][3], 1), (1, pal["sakura"][3], 1)], x2=1, y2=0)
    table = doc.radial([(0, pal["shadow"], .22 if light else .5), (1, pal["shadow"], 0)])
    cone = f"M{n(kx - 50)} {n(ky - 30)}L{n(kx + 50)} {n(ky - 30)}L{n(kx + 10)} {n(ky + 52)}L{n(kx - 10)} {n(ky + 52)}Z"
    art.insert(0, f'<ellipse cx="{n(kx + 8)}" cy="{n(ky + 56)}" rx="48" ry="8" fill="url(#{table})"/>'
                  f'<path d="M{n(kx - 58)} {n(ky - 46)}L{n(kx + 58)} {n(ky - 46)}L{n(kx + 10)} {n(ky + 40)}L{n(kx - 10)} {n(ky + 40)}Z" '
                  f'fill="url(#{flap})"/>')
    art.append(
        f'<path d="{cone}" fill="url(#{paper})"/>'
        f'<path d="M{n(kx + 14)} {n(ky - 30)}L{n(kx + 50)} {n(ky - 30)}L{n(kx + 10)} {n(ky + 52)}L{n(kx + 3)} {n(ky + 52)}Z" '
        f'fill="{pal["shadow"]}" fill-opacity="{".08" if light else ".25"}"/>'
        f'<path d="M{n(kx - 50)} {n(ky - 30)}L{n(kx + 50)} {n(ky - 30)}" stroke="#FFFFFF" stroke-opacity="{".9" if light else ".35"}" stroke-width="2"/>'
        f'<path d="{cone}" fill="none" stroke="{pal["kikyo"][3]}" stroke-opacity=".6"/>'
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
        bar = max(6.0, 178 * share)
        gloss = doc.memo("bar-gloss", lambda: doc.linear(
            [(0, "#FFFFFF", .55), (.45, "#FFFFFF", 0), (.6, pal["shadow"], 0), (1, pal["shadow"], .25)]))
        groove = doc.memo("bar-groove", lambda: doc.linear(
            [(0, pal["shadow"], .22 if pal["scheme"] == "light" else .55), (1, pal["ink3"], .12)]))
        rows.append(
            label + pct
            + f'<rect x="276" y="{n(y + 6.5)}" width="178" height="6" rx="3" fill="url(#{groove})"/>'
            + f'<rect x="276" y="{n(y + 6.5)}" width="{n(bar)}" height="6" rx="3" fill="{color}"/>'
            + f'<rect x="276" y="{n(y + 6.5)}" width="{n(bar)}" height="6" rx="3" fill="url(#{gloss})"/>'
        )
        y += step
    if not shares:
        empty, _ = doc.text([("No public code yet", "serif-italic", 17)], 360, 150, anchor="middle",
                            attrs=f' fill="{pal["ink2"]}"')
        rows.append(empty)
    note, _ = doc.text([("PUBLIC, NON-FORK REPOSITORIES · BY CODE SIZE", "sans", 9)], 454, 288, anchor="end",
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
    doc = Doc(480, 316, title="Garden notes",
              desc="Recent public activity: " + ("; ".join(f"{n_['text']} in {n_['repo']}" for n_ in notes)
                                                 or "none in the last 30 days") + ".")
    flora.install(doc)
    card(doc, pal, "GARDEN NOTES", "花便り")
    rows = []
    y = 84.0
    for i, note in enumerate(notes):
        kind, hue = EVENT_FLOWER.get(note["type"], ("plum", "lav"))
        chip = depth.raised(doc, pal, 24, y - 16, 432, 36, rx=12, lift=.35)
        rows.append(wrap("fadeup", chip, .2 + i * .2))
        rows.append(place(44, y + 2, flora.flower(doc, pal, kind, 8.5, .3 + i * .2, hue=hue)))
        stamp = note["local"].strftime("%b %-d · %H:%M")
        stamp_svg, stamp_w = doc.text([(stamp, "serif-italic", 14)], 444, y - .5, anchor="end",
                                      attrs=f' fill="{pal["ink2"]}"')
        line, _ = doc.text([(fit(note["text"], "sans-bold", 13, 370 - stamp_w - 70), "sans-bold", 13)], 64, y - .5,
                           attrs=f' fill="{pal["ink"]}"')
        repo = note["repo"].split("/", 1)[1] if note["repo"].lower().startswith(user.lower() + "/") else note["repo"]
        repo_svg, _ = doc.text([(fit(repo, "sans", 11.5, 370), "sans", 11.5)], 64, y + 14.5,
                               attrs=f' fill="{pal["ink2"]}"')
        rows.append(wrap("fadeup", stamp_svg + line + repo_svg, .3 + i * .2))
        y += 42
    if not notes:
        msg, _ = doc.text([("The garden is resting", "serif-italic", 20)], 240, 160, anchor="middle",
                          attrs=f' fill="{pal["ink2"]}"')
        ja, _ = doc.text([("庭はひと休み中", "cjk", 14)], 240, 186, anchor="middle", spacing=3,
                         attrs=f' fill="{pal["ink3"]}"')
        rows.append(wrap("fadeup", msg + ja, .4))
        rows.append(place(240, 120, flora.flower(doc, pal, "kikyo", 16, .2, hue="kikyo")))
    footer, _ = doc.text([(f"LAST 30 DAYS · {tz.key.upper()}", "sans", 9)], 454, 290, anchor="end", spacing=1,
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
