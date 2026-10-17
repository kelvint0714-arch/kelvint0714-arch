"""Depth helpers: raised panels, pressed-candy buttons and extruded lettering.

Shadows are stacked translucent shapes rather than blur filters, so an
animated image that repaints every frame stays cheap to draw.
"""

from __future__ import annotations

from .svg import Doc, n


def raised(doc: Doc, pal: dict, x: float, y: float, w: float, h: float, rx: float = 18, lift: float = 1.0) -> str:
    """A panel standing off the page: layered drop shadow, lit top edge, shaded foot."""
    light = pal["scheme"] == "light"
    alpha = (.05, .045, .04, .035) if light else (.22, .18, .14, .1)
    shadow = "".join(
        f'<rect x="{n(x - k * .6)}" y="{n(y + k * 2.4 * lift)}" width="{n(w + k * 1.2)}" height="{n(h)}" '
        f'rx="{n(rx + k)}" fill="{pal["shadow"]}" fill-opacity="{a}"/>'
        for k, a in enumerate(alpha, start=1)
    )
    body = doc.memo("panel-body", lambda: doc.linear(
        [(0, pal["card"], 1), (1, pal["planter"][1] if light else pal["card"], 1)]))
    rim = doc.memo("panel-rim", lambda: doc.linear(
        [(0, "#FFFFFF", .95 if light else .28), (.18, "#FFFFFF", 0), (.85, pal["shadow"], 0),
         (1, pal["shadow"], .12 if light else .4)]))
    glow = doc.memo("panel-glow", lambda: doc.radial([(0, pal["glow"], .5), (1, pal["glow"], 0)], cx=.92, cy=.05, r=.6))
    return (
        shadow
        + f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{n(rx)}" fill="url(#{body})"/>'
        + f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{n(rx)}" fill="url(#{glow})"/>'
        + f'<rect x="{n(x + .75)}" y="{n(y + .75)}" width="{n(w - 1.5)}" height="{n(h - 1.5)}" rx="{n(rx - .75)}" '
          f'fill="none" stroke="url(#{rim})" stroke-width="1.5"/>'
        + f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{n(rx)}" fill="none" '
          f'stroke="{pal["border"]}" stroke-opacity=".9"/>'
    )


def button(doc: Doc, pal: dict, x: float, y: float, w: float, h: float) -> str:
    """A glossy pill pressed out of the page, kikyo to sakura."""
    r = h / 2
    face = doc.memo("btn-face", lambda: doc.linear([(0, pal["kikyo"][1], 1), (1, pal["sakura"][1], 1)], x2=1, y2=0))
    edge = doc.memo("btn-edge", lambda: doc.linear([(0, pal["kikyo"][0], 1), (1, pal["sakura"][0], 1)], x2=1, y2=0))
    gloss = doc.memo("btn-gloss", lambda: doc.linear([(0, "#FFFFFF", .55), (1, "#FFFFFF", 0)]))
    return (
        f'<rect x="{n(x + 1)}" y="{n(y + 6)}" width="{n(w)}" height="{n(h)}" rx="{n(r)}" fill="{pal["shadow"]}" fill-opacity=".14"/>'
        f'<rect x="{n(x)}" y="{n(y + 3.5)}" width="{n(w)}" height="{n(h)}" rx="{n(r)}" fill="url(#{edge})"/>'
        f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{n(r)}" fill="url(#{face})"/>'
        f'<rect x="{n(x + r * .5)}" y="{n(y + 2)}" width="{n(w - r)}" height="{n(h * .42)}" rx="{n(h * .21)}" fill="url(#{gloss})"/>'
    )


def text3d(doc: Doc, pal: dict, segments, x: float, y: float, *, face: str, side: list[str], depth: int = 5,
           step: tuple[float, float] = (.7, .9), anchor: str = "start", spacing: float = 0.0,
           shadow: bool = True) -> tuple[str, float]:
    """Lettering extruded back and to the lower right.

    `side` runs from the colour nearest the face to the deepest; it is
    stretched across `depth` layers.
    """
    markup, width = doc.text(segments, x, y, anchor=anchor, spacing=spacing)
    rid = doc.uid("run")
    doc.defs.append(f'<g id="{rid}">{markup}</g>')
    parts = []
    if shadow:
        dx, dy = step[0] * depth + 3, step[1] * depth + 5
        parts.append(f'<use href="#{rid}" transform="translate({n(dx)} {n(dy)})" fill="{pal["shadow"]}" fill-opacity=".14"/>')
    for i in range(depth, 0, -1):
        color = side[min(len(side) - 1, (i - 1) * len(side) // depth)]
        parts.append(f'<use href="#{rid}" transform="translate({n(step[0] * i)} {n(step[1] * i)})" fill="{color}"/>')
    parts.append(f'<use href="#{rid}" fill="{face}"/>')
    return "".join(parts), width

