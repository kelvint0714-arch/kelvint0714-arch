"""A small SVG document builder with animated and still renderings.

Every animated element is styled so that its base CSS is the finished frame.
`render(animated=False)` drops the animation rules, which gives the still used
for visitors who ask for reduced motion.
"""

from __future__ import annotations

import html
import itertools

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

from .text import Glyph, layout

REDUCED_MOTION = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


def n(value: float, places: int = 2) -> str:
    """Compact number formatting for attributes."""
    text = f"{value:.{places}f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def k(value: float) -> str:
    """Glyph scale factors (size / units per em) need more precision than coordinates."""
    return n(value, 6)


class Doc:
    def __init__(self, width: int, height: int, title: str, desc: str = "") -> None:
        self.width = width
        self.height = height
        self.title = title
        self.desc = desc
        self.base_css: list[str] = []
        self.anim_css: list[str] = []
        self.defs: list[str] = []
        self.body: list[str] = []
        self._glyph_ids: dict[tuple[str, str], str] = {}
        self._glyph_defs: list[str] = []
        self._counter = itertools.count()
        self._installed: set[str] = set()

    # -- bookkeeping -----------------------------------------------------
    def uid(self, prefix: str) -> str:
        return f"{prefix}{next(self._counter)}"

    def once(self, key: str) -> bool:
        """True the first time `key` is seen, for shared CSS and defs."""
        if key in self._installed:
            return False
        self._installed.add(key)
        return True

    def memo(self, key: str, factory):
        """Build a shared def once and return its id on every later call."""
        if not hasattr(self, "_memo"):
            self._memo: dict[str, str] = {}
        if key not in self._memo:
            self._memo[key] = factory()
        return self._memo[key]

    def css(self, rules: str, anim: bool = False) -> None:
        (self.anim_css if anim else self.base_css).append(rules)

    def add(self, markup: str) -> None:
        self.body.append(markup)

    def linear(self, stops: list[tuple[float, str, float]], x1=0, y1=0, x2=0, y2=1, user=False) -> str:
        gid = self.uid("lg")
        units = ' gradientUnits="userSpaceOnUse"' if user else ""
        body = "".join(f'<stop offset="{n(o)}" stop-color="{c}" stop-opacity="{n(a)}"/>' for o, c, a in stops)
        self.defs.append(
            f'<linearGradient id="{gid}" x1="{n(x1)}" y1="{n(y1)}" x2="{n(x2)}" y2="{n(y2)}"{units}>{body}</linearGradient>'
        )
        return gid

    def radial(self, stops: list[tuple[float, str, float]], cx=0.5, cy=0.5, r=0.5, user=False) -> str:
        gid = self.uid("rg")
        units = ' gradientUnits="userSpaceOnUse"' if user else ""
        body = "".join(f'<stop offset="{n(o)}" stop-color="{c}" stop-opacity="{n(a)}"/>' for o, c, a in stops)
        self.defs.append(f'<radialGradient id="{gid}" cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}"{units}>{body}</radialGradient>')
        return gid

    # -- text ------------------------------------------------------------
    def _glyph_ref(self, glyph: Glyph) -> str | None:
        key = (glyph.face.key, glyph.name)
        if key not in self._glyph_ids:
            outline = glyph.face.outline(glyph.name)
            if not outline:
                self._glyph_ids[key] = ""
            else:
                gid = f"g{len(self._glyph_ids)}"
                self._glyph_ids[key] = gid
                self._glyph_defs.append(f'<path id="{gid}" d="{outline}"/>')
        return self._glyph_ids[key] or None

    def text(
        self,
        segments: list[tuple[str, str, float]],
        x: float,
        y: float,
        *,
        anchor: str = "start",
        spacing: float = 0.0,
        attrs: str = "",
        glyph_class: str | None = None,
        glyph_delay: tuple[float, float] | None = None,
        inline: bool = False,
        glyph_attrs: str = "",
    ) -> tuple[str, float]:
        """Markup for one baseline of text and its width in px.

        `glyph_class` wraps each glyph in its own animated group;
        `glyph_delay` = (start, step) staggers them. `inline` writes the
        outlines in the run's own coordinates so a userSpaceOnUse gradient
        or a stroke spans the whole word.
        """
        glyphs, width = layout(segments, spacing)
        offset = {"start": 0.0, "middle": width / 2, "end": width}[anchor]
        parts = []
        visible = 0
        for glyph in glyphs:
            scale = glyph.size / glyph.face.upm
            if inline:
                pen = SVGPathPen(glyph.face.glyphs, ntos=n)
                glyph.face.glyphs[glyph.name].draw(TransformPen(pen, (scale, 0, 0, -scale, glyph.x, 0)))
                d = pen.getCommands()
                if not d:
                    continue
                item = f'<path d="{d}"{glyph_attrs}/>'
            else:
                ref = self._glyph_ref(glyph)
                if ref is None:
                    continue
                item = f'<use href="#{ref}" transform="translate({n(glyph.x)} 0) scale({k(scale)} {k(-scale)})"/>'
            if glyph_class:
                delay = ""
                if glyph_delay:
                    delay = f' style="animation-delay:{n(glyph_delay[0] + glyph_delay[1] * visible)}s"'
                if inline:
                    item = f'<g class="{glyph_class}"{delay}>{item}</g>'
                else:
                    item = (
                        f'<g transform="translate({n(glyph.x)} 0)"><g class="{glyph_class}"{delay}>'
                        f'<use href="#{ref}" transform="scale({k(scale)} {k(-scale)})"/></g></g>'
                    )
            parts.append(item)
            visible += 1
        markup = f'<g transform="translate({n(x - offset)} {n(y)})"{attrs}>{"".join(parts)}</g>'
        return markup, width

    # -- output ----------------------------------------------------------
    def render(self, animated: bool = True) -> str:
        css = list(self.base_css)
        if animated:
            css += self.anim_css + [REDUCED_MOTION]
        defs = "".join(self._glyph_defs + self.defs)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" '
            f'width="{self.width}" height="{self.height}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{html.escape(self.title)}</title>'
            f'<desc id="desc">{html.escape(self.desc)}</desc>'
            f'<style>{"".join(css)}</style><defs>{defs}</defs>{"".join(self.body)}</svg>\n'
        )
