"""A dimensional ink garden for the existing manga contribution calendar.

Only the contribution calendar is replaced. All marks are original vector
geometry, not a raster recolouring. Dates/counts/levels come from garden.data
unchanged; height is an ordinal encoding of the original GitHub level.

The fixed oblique view has one week per column and seven weekday rows. The
platform has physical side faces, each date has a shallow raised plot, and
flowers have upright stems and foreshortened, layered petals. All shading is
ink, hatching or screentone. No gradients, bitmap assets, fonts or filters are
embedded. Uses only the standard library and the existing manga title helper.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import data, manga

N = manga.n
INK = '#101010'
PAPER = '#ffffff'
FAINT = '#c9c9c9'


class CalendarDoc:
    """The same minimal render interface as the existing card builders."""
    def __init__(self, width: int, height: int, title: str, desc: str):
        self.width, self.height = width, height
        self.title, self.desc = title, desc
        self.pal = dict(paper=PAPER, ink=INK, secondary='#444444', faint=FAINT,
                        tone='#eeeeee', deep=INK)
        self.parts: list[str] = []
        self.defs: list[str] = [
            '<pattern id="cal-ground-tone" width="4" height="4" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".34" fill="#b3b3b3"/></pattern>',
            '<pattern id="cal-side-hatch" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(31)"><path d="M0 0V4" stroke="#101010" stroke-width=".55"/></pattern>',
            '<pattern id="cal-edge-hatch" width="2.8" height="2.8" patternUnits="userSpaceOnUse" patternTransform="rotate(-32)"><path d="M0 0V2.8" stroke="#101010" stroke-width=".6"/></pattern>',
            '<pattern id="cal-fine-tone" width="3" height="3" patternUnits="userSpaceOnUse"><circle cx=".8" cy=".8" r=".52" fill="#101010"/></pattern>',
            '<pattern id="cal-shadow-tone" width="3" height="3" patternUnits="userSpaceOnUse"><circle cx=".8" cy=".8" r=".76" fill="#101010"/></pattern>',
        ]

    def add(self, markup: str) -> None:
        self.parts.append(markup)

    def render(self, animated: bool = True) -> str:
        # Decorative movement is deliberately absent. The video remains the
        # only continuously moving part of the profile.
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}" role="img" aria-labelledby="title desc" '
            'data-calendar-style="ink-3d-v1">'
            f'<title id="title">{manga.esc(self.title)}</title><desc id="desc">{manga.esc(self.desc)}</desc>'
            '<style>text{font-kerning:normal}@media(prefers-reduced-motion:reduce){*{animation:none!important}}</style>'
            '<defs>' + ''.join(self.defs) + '</defs>'
            '<g data-edition="ink-v2" stroke-linecap="round" stroke-linejoin="round">'
            + ''.join(self.parts) + '</g></svg>'
        )


def poly(points: list[tuple[float, float]], fill: str = PAPER,
         stroke: str = INK, width: float = .75, attrs: str = '') -> str:
    pts = ' '.join(f'{N(x)},{N(y)}' for x, y in points)
    return (f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{N(width)}"{attrs}/>')


def path(d: str, stroke: str = INK, width: float = .7,
         fill: str = 'none', attrs: str = '') -> str:
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{N(width)}"{attrs}/>'


def ellipse(x: float, y: float, rx: float, ry: float,
            fill: str, stroke: str = 'none', width: float = .5) -> str:
    return (f'<ellipse cx="{N(x)}" cy="{N(y)}" rx="{N(rx)}" ry="{N(ry)}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{N(width)}"/>')


@dataclass(frozen=True)
class View:
    """A fixed parallel projection. x = weeks, y = weekdays, z = height."""
    x: float
    y: float
    sx: float
    sy: float = 20.0
    skew: float = 7.0
    rise: float = -.55

    def at(self, x: float, y: float, z: float = 0) -> tuple[float, float]:
        return self.x + x * self.sx - y * self.skew, self.y + x * self.rise + y * self.sy - z

    def quad(self, x0: float, y0: float, x1: float, y1: float,
             z: float = 0) -> list[tuple[float, float]]:
        return [self.at(x0, y0, z), self.at(x1, y0, z),
                self.at(x1, y1, z), self.at(x0, y1, z)]


def _plot(doc: CalendarDoc, view: View, col: int, row: int, level: int) -> tuple[str, tuple[float, float]]:
    """A solid seed plot with a visible front and right face, even at level 0."""
    raised = (1.25, 2.7, 4.4, 6.8, 9.5)[level]
    points = view.quad(col + .14, row + .16, col + .86, row + .84, raised)
    a, b, c, d = points
    drop = lambda q: (q[0], q[1] + raised)
    parts = []
    if level:
        parts.append(poly([d, c, drop(c), drop(d)], '#f4f4f4', '#777777', .55))
        parts.append(poly([d, c, drop(c), drop(d)], 'url(#cal-side-hatch)', 'none', 0))
        parts.append(poly([b, c, drop(c), drop(b)], INK, INK, .45))
    else:
        parts.append(poly([d, c, drop(c), drop(d)], '#e7e7e7', 'none', 0))
    parts.append(poly(points, PAPER, '#999999' if level else '#d5d5d5', .55 if level else .42))
    # The small edge is a face boundary, not a drop-shadow filter.
    if level:
        parts.append(path(f'M{N(a[0]+.5)} {N(a[1]+.55)}L{N(b[0]-.2)} {N(b[1]+.55)}', '#bbbbbb', .35))
    return ''.join(parts), view.at(col + .5, row + .5, raised)


def _leaf(sign: int, y: float, length: float, black: bool = False) -> str:
    """One cupped leaf: dark underside and a short white midrib."""
    x = sign * length
    shape = (f'M0 {N(y)}Q{N(x*.25)} {N(y-length*.9)} {N(x)} {N(y-length*.74)}'
             f'Q{N(x*.85)} {N(y+length*.03)} 0 {N(y)}Z')
    parts = path(shape, INK, .5, INK if black else PAPER)
    if black:
        parts += path(f'M.2 {N(y-.3)}Q{N(x*.42)} {N(y-length*.48)} {N(x*.88)} {N(y-length*.67)}', PAPER, .37)
    else:
        parts += path(f'M0 {N(y)}Q{N(x*.63)} {N(y-length*.12)} {N(x)} {N(y-length*.74)}Q{N(x*.53)} {N(y-length*.35)} 0 {N(y)}Z', 'none', 0, INK)
        parts += path(f'M0 {N(y)}L{N(x*.88)} {N(y-length*.64)}', INK, .36)
    return parts


def _bloom(radius: float, level: int, angle: float) -> str:
    """Small foreshortened cup, with separate rear and front petals.

    The head is not the old flat flower icon. Individual petals have a curved
    face, ink underfold and an upper rim. Deterministic date-based lean is used
    without making higher levels randomly smaller than lower ones.
    """
    parts = []
    # Ink undercup first; the rim casts a tiny hard-edged overlap shadow.
    parts.append(ellipse(0, 1.3, radius*.86, radius*.47, INK))
    count = 5 if level < 3 else 7
    for ring in range(1 if level < 3 else 2):
        r = radius * (1 if ring == 0 else .6)
        for k in range(count if ring == 0 else 5):
            a = k * 360 / (count if ring == 0 else 5) + angle + ring * 29
            w = r * .57
            shape = (f'M-.2 -.25C{N(-w*.66)} {N(-r*.21)} {N(-w*1.25)} {N(-r*.66)} {N(-w*.82)} {N(-r*.93)}'
                     f'C{N(-w*.43)} {N(-r*1.17)} {N(w*.79)} {N(-r*1.11)} {N(w*.97)} {N(-r*.72)}'
                     f'Q{N(w*.98)} {N(-r*.34)} .2 -.2Z')
            petal = path(shape, INK, .54 if ring == 0 else .44, PAPER)
            if level >= 2:
                petal += path(f'M-.2 -.3Q{N(-w*.88)} {N(-r*.36)} {N(-w*.76)} {N(-r*.82)}'
                              f'Q{N(-w*.21)} {N(-r*.42)} -.2 -.3Z', 'none', 0, INK)
            else:
                petal += path(f'M-.1 -.2Q{N(-w*.64)} {N(-r*.37)} {N(-w*.57)} {N(-r*.8)}', INK, .42)
            petal += path(f'M{N(-w*.52)} {N(-r*.84)}Q0 {N(-r*.96)} {N(w*.51)} {N(-r*.8)}', '#555555', .33)
            if level == 4 and ring == 0:
                petal += path(f'M.1 -.4L{N(w*.34)} {N(-r*.63)}', INK, .32)
            parts.append(f'<g transform="rotate({N(a)})">{petal}</g>')
    parts.append(ellipse(0, 0, radius*.23, radius*.23, INK))
    parts.append(ellipse(-radius*.06, -radius*.07, radius*.08, radius*.06, PAPER))
    # Oblique flower head: white petal faces above the black undersides.
    return '<g transform="scale(1 .72)">' + ''.join(parts) + '</g>'


def plant(doc: CalendarDoc, level: int, seed: int, mobile: bool = False) -> str:
    """A single botanical data mark drawn upright, anchored to its own plot."""
    if level == 0:
        return (ellipse(0, 0, 1.5, .9, '#f4f4f4', '#aaaaaa', .38)
                + path('M-.6 .15Q0 -.35 .6 -.15', '#aaaaaa', .28))
    scale = .87 if mobile else 1
    height = (0, 9, 15, 22, 29)[level] * scale
    radius = (0, 3.1, 4.05, 5.2, 6.6)[level] * scale
    # Stable between daily updates and theme changes; never rerolls the garden.
    lean = ((seed % 9) - 4) * .31 * scale
    angle = ((seed * 7) % 34) - 17
    parts = [ellipse(1.6, .4, 3.6+level*.24, 1.1+level*.13, 'url(#cal-fine-tone)')]
    # One offset white rim makes a real stalk instead of a line with a floating symbol.
    stem = f'M0 0C{N(-lean*.45)} {N(-height*.3)} {N(lean*.55)} {N(-height*.7)} {N(lean)} {N(-height)}'
    parts.append(path(stem, INK, .9 if level >= 3 else .65))
    parts.append(path(stem, PAPER, .27, attrs=' transform="translate(-.23 0)"'))
    parts.append(_leaf(-1 if seed % 2 else 1, -height*.39, (2.5+level*.8)*scale, True))
    if level >= 2:
        parts.append(_leaf(1 if seed % 2 else -1, -height*.59, (2.2+level*.8)*scale))
    # Sepals remain below the cup and therefore behind the blossom.
    parts.append(path(f'M{N(lean-2.1)} {N(-height+2.1)}L{N(lean)} {N(-height+4.0)}L{N(lean+2.1)} {N(-height+1.4)}Z', INK, .4, INK))
    parts.append(f'<g transform="translate({N(lean)} {N(-height)}) rotate({N(lean*2.5)})">{_bloom(radius, level, angle)}</g>')
    return ''.join(parts)


def _bed(doc: CalendarDoc, view: View, columns: list[list[data.Day | None]],
         mobile: bool = False, band: int = 0) -> None:
    """Draw back-to-front with screen-depth sorting, then label the two axes."""
    count = max(1, len(columns))
    back_left, back_right, front_right, front_left = view.quad(-.36, -.35, count+.20, 7.30)
    thickness = 17 if mobile else 21
    lower = lambda q: (q[0], q[1]+thickness)
    outline = [back_left, back_right, front_right, front_left]
    # A line-and-screentone ground shadow, not blurred UI drop-shadow.
    shadow = [(x+10, y+thickness+10) for x, y in outline]
    doc.add(poly(shadow, 'url(#cal-ground-tone)', 'none', 0, ' data-ink-art="bed-ground-shadow"'))
    doc.add(poly([front_left, front_right, lower(front_right), lower(front_left)], '#fafafa', INK, 1.0, ' data-face="front"'))
    doc.add(poly([front_left, front_right, lower(front_right), lower(front_left)], 'url(#cal-side-hatch)', 'none', 0))
    doc.add(poly([back_right, front_right, lower(front_right), lower(back_right)], INK, INK, 1.05, ' data-face="right"'))
    doc.add(poly(outline, PAPER, INK, 1.0, ' data-face="top"'))
    doc.add(poly(outline, 'url(#cal-ground-tone)', 'none', 0))
    # Fine inner lip preserves the crisp manga contour.
    doc.add(poly(view.quad(-.16, -.12, count+.04, 7.08), 'none', '#888888', .48))
    # A double ruled ledge with little nib hatching gives the base a clear thickness.
    doc.add(path(f'M{N(front_left[0])} {N(front_left[1]+3.4)}L{N(front_right[0])} {N(front_right[1]+3.4)}', INK, .5))
    # Draw plots and their plants in far-to-near order. No decorative fake dates.
    items = [(view.at(col+.5, row+.5)[1], col, row, day)
             for col, column in enumerate(columns) for row, day in enumerate(column) if day is not None]
    for _, col, row, day in sorted(items, key=lambda t: (t[0], -t[1])):
        level = max(0, min(4, int(day.level)))
        tile, (x, y) = _plot(doc, view, col, row, level)
        mark = plant(doc, level, day.date.toordinal(), mobile)
        doc.add(f'<g data-date="{day.date.isoformat()}" data-count="{day.count}" data-level="{day.level}" '
                f'data-week="{col}" data-weekday="{row}" data-band="{band}" data-ink-art="raised-day">'
                f'<title>{day.date.isoformat()}: {day.count} contributions; GitHub level {day.level}</title>'
                + tile + f'<g transform="translate({N(x)} {N(y)})">{mark}</g></g>')
    # Weekday markers follow the depth axis. All seven labels, rather than an
    # unlabelled perspective that makes Monday and Sunday indistinguishable.
    for row, label in enumerate(('S', 'M', 'T', 'W', 'T', 'F', 'S')):
        x, y = view.at(-.95, row+.5)
        doc.add(manga.text(doc, label, x-4, y+2.5, 8.5 if mobile else 9,
                           anchor='end', fill='#555555'))
    # Labels remain horizontal; the leaders, not the typography, follow the plane.
    month_marks: list[tuple[float, float, str, int]] = []
    last_x = -1e9
    for col, column in enumerate(columns):
        present = [d for d in column if d is not None]
        if not present:
            continue
        starts = [d for d in present if d.date.day == 1]
        first = col == 0
        if not starts and not first:
            continue
        d = starts[0] if starts else present[0]
        x, y = view.at(col+.5, -.35)
        lane = 1 if x-last_x < (22 if mobile else 29) else 0
        month_marks.append((x, y, d.date.strftime('%b').upper(), lane))
        last_x = x
    for x, y, label, lane in month_marks:
        offset = lane * 18
        doc.add(manga.text(doc, label, x, y-43-offset, 9 if mobile else 10,
                           anchor='middle', fill='#555555'))
        doc.add(path(f'M{N(x)} {N(y-34-offset)}V{N(y-27)}', '#777777', .45))


def calendar_card(theme: str, snap: dict[str, Any], mobile: bool = False) -> CalendarDoc:
    """Build the four existing light/dark x desktop/mobile variants.

    Both themes intentionally keep white paper and black ink, like the avatar.
    The host profile background is unaffected. Input data is never mutated.
    """
    if theme not in ('light', 'dark'):
        raise ValueError(f'Unsupported theme: {theme}')
    days = sorted(data.days_from(snap), key=lambda d: d.date)
    if len({d.date for d in days}) != len(days):
        raise ValueError('Contribution dates must be unique')
    cols = data.week_columns(days)
    # Two half-year flowerbeds keep stems readable on phones. Oversized data
    # sets receive further bands instead of being silently truncated.
    per_band = 27 if mobile else 54
    groups = [cols[i:i+per_band] for i in range(0, len(cols), per_band)] or [[]]
    w = 480 if mobile else 960
    band_gap = 284 if mobile else 282
    h = (654 if mobile else 589) + band_gap * (len(groups)-1)
    total = snap.get('calendar', {}).get('total', sum(d.count for d in days))
    doc = CalendarDoc(w, h, 'Bloom Calendar — an ink garden in relief',
        f'{total} contributions. One date per raised plot, seven weekday rows per band, Sunday first. '
        'Height and flowering represent the original GitHub activity levels, not a new count. '
        'White paper, black outlines, petal folds, hatching and screentones. '
        'The mobile layout continues the same dates in two half-year flowerbeds.')
    manga.panel(doc)
    tx = 28 if mobile else 38
    doc.add(manga.title(doc, 'Bloom Calendar', tx, 63, 45 if mobile else 54, max_width=w-112))
    doc.add(manga.text(doc, '花暦', w-38, 55, 17, 'cjk', anchor='end', spacing=3))
    doc.add(manga.line(doc, tx, 84, w-38, 84, 1))
    longest, current = data.streaks(days)
    best = max(days, key=lambda d: d.count) if days else None
    items = [(f'{total:,}', 'CONTRIBUTIONS'), (str(longest), 'LONGEST / DAYS'),
             (str(current), 'CURRENT / DAYS'),
             (best.date.strftime('%m.%d') if best and best.count else '—', 'BEST DAY')]
    for j, (value, caption) in enumerate(items):
        x = 31+(j % 2)*225 if mobile else 40+j*228
        y = 128+(j//2)*76 if mobile else 146
        stat_size = min(39 if mobile else 45, 200/max(1, len(value)*.61))
        doc.add(manga.text(doc, value, x, y, stat_size, 'serif', italic=True))
        doc.add(manga.text(doc, caption, x, y+22, 10 if mobile else 11.5,
                           spacing=.8, fill='#444444'))
        if not mobile and j:
            doc.add(manga.line(doc, x-23, 110, x-23, 170, .6, '#cccccc'))
    first_y = 326 if mobile else 287
    for band, group in enumerate(groups):
        # Keep individual dates equally spaced within a view, including the
        # last short band. Do not stretch a few days into enormous tiles.
        max_cols = max(1, min(per_band, len(cols)))
        step = min(12.3, 335/max_cols) if mobile else min(15.15, 799/max_cols)
        plane_width = max_cols*step
        x0 = (w-plane_width+45)/2 if mobile else (w-plane_width+56)/2
        view = View(x0, first_y+band*band_gap, step,
                    sy=19.0 if mobile else 21.0,
                    skew=5.8 if mobile else 7.6,
                    rise=-.47 if mobile else -.65)
        doc.add('<g data-ink-art="dimensional-flowerbed">')
        _bed(doc, view, group, mobile, band)
        doc.add('</g>')
        if not days:
            doc.add(manga.text(doc, 'The first seeds are still waiting.', w/2,
                               first_y+82, 17, 'serif', italic=True, anchor='middle'))
        if mobile and len(groups)>1:
            # Half-year date captions make the chronological continuation explicit.
            values = [d for column in group for d in column if d is not None]
            if values:
                label = f'{values[0].date:%Y.%m.%d} — {values[-1].date:%Y.%m.%d}'
                doc.add(manga.text(doc, label, 35, first_y+band*band_gap+190,
                                   9, 'mono', fill='#666666'))
    legend_y = h-70
    if mobile:
        doc.add(manga.text(doc, 'LESS', 31, legend_y+2, 9, spacing=1, fill='#555555'))
        base_x, gap = 97, 35
    else:
        doc.add(manga.text(doc, 'LESS', 38, legend_y+2, 10, spacing=1, fill='#555555'))
        base_x, gap = 105, 37
    for level in range(5):
        # Legend uses the actual same dimensional plant, not a flat substitute.
        view = View(base_x+gap*level-4.2, legend_y-8, 12, 14, 4.5, -.6)
        plot, (x, y) = _plot(doc, view, 0, 0, level)
        doc.add('<g data-legend-level="'+str(level)+'">'+plot
                + f'<g transform="translate({N(x)} {N(y)})">{plant(doc, level, 730000+level, True)}</g></g>')
    doc.add(manga.text(doc, 'MORE', base_x+gap*4+29, legend_y+2,
                       9 if mobile else 10, spacing=1, fill='#555555'))
    date_range = f'{days[0].date.isoformat()} — {days[-1].date.isoformat()}' if days else 'No contribution data'
    doc.add(manga.text(doc, date_range, tx, h-30, 10 if mobile else 11, fill='#555555'))
    if not mobile:
        doc.add(manga.text(doc, 'ONE DAY, ONE FLOWER.', w-39, h-69, 11.5,
                           anchor='end', spacing=1.8))
        doc.add(manga.text(doc, '一日一輪', w-39, h-32, 16, 'cjk', anchor='end', spacing=6))
    else:
        doc.add(manga.text(doc, '一日一輪', w-34, h-29, 13, 'cjk', anchor='end', spacing=3))
    return doc
