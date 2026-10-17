"""Flower primitives.

Every primitive draws around its own origin and returns markup. Callers place
it with a translate group, so the CSS transform used by an animation never
competes with a transform attribute: animated classes all grow, sway or
unfold about their local (0, 0).
"""

from __future__ import annotations

import hashlib
import math
import random

from .svg import Doc, n

BASE_CSS = (
    ".fall,.wisp{opacity:0}.mote{opacity:.75}"
    ".wisp{stroke-dasharray:.3 1.7;stroke-dashoffset:-1}"
)

ANIM_CSS = (
    ".pop,.unfurl,.petal,.drop,.sway-a,.sway-b,.sway-h,.breathe,.twinkle,.fadeup,.fall,.flip,.bob"
    "{transform-origin:0 0}"
    ".grow{stroke-dasharray:1;animation:grow 1.7s cubic-bezier(.45,.05,.3,1) both}"
    "@keyframes grow{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
    ".pop{animation:pop .8s cubic-bezier(.34,1.56,.64,1) both}"
    "@keyframes pop{from{transform:scale(0);opacity:0}to{transform:none;opacity:1}}"
    ".unfurl{animation:unfurl 2s cubic-bezier(.22,1,.36,1) both}"
    "@keyframes unfurl{from{transform:rotate(-70deg) scale(.06);opacity:0}30%{opacity:1}to{transform:none;opacity:1}}"
    ".petal{animation:petal 1.6s cubic-bezier(.2,1.2,.4,1) both}"
    "@keyframes petal{from{transform:scale(.25,.04);opacity:0}25%{opacity:1}to{transform:none;opacity:1}}"
    ".drop{animation:drop 1.2s cubic-bezier(.22,1,.36,1) both}"
    "@keyframes drop{from{transform:scale(.4,0);opacity:0}to{transform:none;opacity:1}}"
    ".sway-a{animation:sway-a 7s ease-in-out infinite}"
    "@keyframes sway-a{0%,100%{transform:rotate(0)}25%{transform:rotate(1.5deg)}75%{transform:rotate(-1.5deg)}}"
    ".sway-b{animation:sway-b 9.5s ease-in-out infinite}"
    "@keyframes sway-b{0%,100%{transform:rotate(0)}25%{transform:rotate(-2.4deg)}75%{transform:rotate(2.4deg)}}"
    ".sway-h{animation:sway-h 6.5s ease-in-out infinite}"
    "@keyframes sway-h{0%,100%{transform:rotate(0)}25%{transform:rotate(3.2deg)}75%{transform:rotate(-3.2deg)}}"
    ".breathe{animation:breathe 6s ease-in-out infinite}"
    "@keyframes breathe{0%,100%{transform:none}50%{transform:scale(1.045) rotate(2.5deg)}}"
    ".bob{animation:bob 5s ease-in-out infinite}"
    "@keyframes bob{0%,100%{transform:none}50%{transform:translateY(-3px)}}"
    ".twinkle{animation:twinkle 3.6s ease-in-out infinite}"
    "@keyframes twinkle{0%,100%{opacity:.1;transform:scale(.45)}50%{opacity:1;transform:none}}"
    ".wisp{animation:wisp 8s cubic-bezier(.4,0,.6,1) infinite both}"
    "@keyframes wisp{0%{stroke-dashoffset:.3;opacity:0}15%{opacity:.8}75%{opacity:.5}100%{stroke-dashoffset:-1;opacity:0}}"
    ".flip{animation:flip 2.2s ease-in-out infinite}"
    "@keyframes flip{0%,100%{transform:none}50%{transform:scale(.25,1)}}"
    ".shade{animation:shade 1.2s ease both}"
    "@keyframes shade{from{opacity:0}to{opacity:1}}"
    ".fadeup{animation:fadeup 1.4s cubic-bezier(.22,1,.36,1) both}"
    "@keyframes fadeup{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}"
)


def install(doc: Doc) -> None:
    if doc.once("flora"):
        doc.css(BASE_CSS)
        doc.css(ANIM_CSS, anim=True)


def delay_style(seconds: float, extra: str = "") -> str:
    return f' style="animation-delay:{n(seconds)}s{";" + extra if extra else ""}"'


def place(x: float, y: float, inner: str, rotate: float = 0.0, scale: float = 1.0) -> str:
    parts = [f"translate({n(x)} {n(y)})"]
    if rotate:
        parts.append(f"rotate({n(rotate)})")
    if scale != 1.0:
        parts.append(f"scale({n(scale)})")
    return f'<g transform="{" ".join(parts)}">{inner}</g>'


def wrap(cls: str, inner: str, delay: float | None = None, extra: str = "") -> str:
    style = delay_style(delay, extra) if delay is not None else (f' style="{extra}"' if extra else "")
    return f'<g class="{cls}"{style}>{inner}</g>'


# -- geometry --------------------------------------------------------------
def qpoint(p0, c, p1, t):
    u = 1 - t
    return (u * u * p0[0] + 2 * u * t * c[0] + t * t * p1[0], u * u * p0[1] + 2 * u * t * c[1] + t * t * p1[1])


def qangle(p0, c, p1, t):
    """Direction of travel in degrees (SVG angles, y down)."""
    dx = 2 * (1 - t) * (c[0] - p0[0]) + 2 * t * (p1[0] - c[0])
    dy = 2 * (1 - t) * (c[1] - p0[1]) + 2 * t * (p1[1] - c[1])
    return math.degrees(math.atan2(dy, dx))


def petal_d(kind: str, length: float, width: float) -> str:
    """A petal with its base at the origin and its tip at (0, -length)."""
    l, w = length, width
    if kind == "ruffle":
        return (
            f"M0 0C{n(w)} {n(-.18*l)} {n(1.08*w)} {n(-.72*l)} {n(.56*w)} {n(-.95*l)}"
            f"Q{n(.3*w)} {n(-1.07*l)} 0 {n(-.93*l)}Q{n(-.3*w)} {n(-1.07*l)} {n(-.56*w)} {n(-.95*l)}"
            f"C{n(-1.08*w)} {n(-.72*l)} {n(-w)} {n(-.18*l)} 0 0Z"
        )
    if kind == "notch":
        return (
            f"M0 0C{n(.9*w)} {n(-.2*l)} {n(1.15*w)} {n(-.74*l)} {n(.52*w)} {n(-l)}"
            f"Q{n(.18*w)} {n(-.9*l)} 0 {n(-.84*l)}Q{n(-.18*w)} {n(-.9*l)} {n(-.52*w)} {n(-l)}"
            f"C{n(-1.15*w)} {n(-.74*l)} {n(-.9*w)} {n(-.2*l)} 0 0Z"
        )
    if kind == "toothed":
        return (
            f"M0 0C{n(.7*w)} {n(-.25*l)} {n(1.12*w)} {n(-.72*l)} {n(.92*w)} {n(-l)}"
            f"L{n(.46*w)} {n(-.9*l)}L0 {n(-1.02*l)}L{n(-.46*w)} {n(-.9*l)}L{n(-.92*w)} {n(-l)}"
            f"C{n(-1.12*w)} {n(-.72*l)} {n(-.7*w)} {n(-.25*l)} 0 0Z"
        )
    if kind == "kikyo":
        return (
            f"M0 0C{n(w)} {n(-.28*l)} {n(1.02*w)} {n(-.62*l)} {n(.34*w)} {n(-.87*l)}"
            f"L0 {n(-l)}L{n(-.34*w)} {n(-.87*l)}C{n(-1.02*w)} {n(-.62*l)} {n(-w)} {n(-.28*l)} 0 0Z"
        )
    if kind == "pointed":
        return f"M0 0C{n(w)} {n(-.3*l)} {n(.7*w)} {n(-.82*l)} 0 {n(-l)}C{n(-.7*w)} {n(-.82*l)} {n(-w)} {n(-.3*l)} 0 0Z"
    # round
    return f"M0 0C{n(w)} {n(-.15*l)} {n(1.12*w)} {n(-.7*l)} 0 {n(-l)}C{n(-1.12*w)} {n(-.7*l)} {n(-w)} {n(-.15*l)} 0 0Z"


def petal_shape_ref(doc: Doc, kind: str, length: float, width: float) -> str:
    """The bare petal outline, used for silhouettes."""
    key = f"shape:{kind}:{n(length)}:{n(width)}"
    pid = "s" + hashlib.md5(key.encode()).hexdigest()[:7]
    if doc.once(key):
        doc.defs.append(f'<path id="{pid}" d="{petal_d(kind, length, width)}"/>')
    return pid


def petal_ref(doc: Doc, kind: str, length: float, width: float) -> str:
    """A shaded petal: outline (filled by the caller), a sheen on one flank and a shade on the other."""
    key = f"petal:{kind}:{n(length)}:{n(width)}"
    pid = "p" + hashlib.md5(key.encode()).hexdigest()[:7]
    if doc.once(key):
        l, w = length, width
        shape = petal_shape_ref(doc, kind, length, width)
        parts = [f'<use href="#{shape}"/>']
        if kind == "kikyo":
            veins = (
                f"M0 {n(-.12*l)}L0 {n(-.9*l)}M{n(.08*w)} {n(-.15*l)}Q{n(.5*w)} {n(-.5*l)} {n(.3*w)} {n(-.8*l)}"
                f"M{n(-.08*w)} {n(-.15*l)}Q{n(-.5*w)} {n(-.5*l)} {n(-.3*w)} {n(-.8*l)}"
            )
            parts.append(f'<path d="{veins}" fill="none" stroke-opacity=".5" stroke-width=".28"/>')
        parts.append(
            f'<path d="{petal_d("pointed", .7 * l, .3 * w)}" transform="translate({n(.24 * w)} {n(-.14 * l)})" '
            f'fill="#FFFFFF" fill-opacity=".32" stroke="none"/>'
            f'<path d="{petal_d("pointed", .62 * l, .26 * w)}" transform="translate({n(-.34 * w)} {n(-.1 * l)})" '
            f'fill="#000000" fill-opacity=".07" stroke="none"/>'
        )
        doc.defs.append(f'<g id="{pid}">{"".join(parts)}</g>')
    return pid


def leaf_d(length: float, width: float) -> str:
    l, w = length, width
    return f"M0 0C{n(w)} {n(-.25*l)} {n(.85*w)} {n(-.78*l)} 0 {n(-l)}C{n(-.85*w)} {n(-.78*l)} {n(-w)} {n(-.25*l)} 0 0Z"


def leaf(doc: Doc, pal: dict, length: float, width: float, delay: float, shade: int = 1) -> str:
    """A broad leaf with a midrib, base at the origin, pointing up."""
    grad = doc.memo(f"leaf:{shade}", lambda: doc.linear(
        [(0, pal["leaf"][shade - 1], 1), (1, pal["leaf"][shade + 1], 1)], x1=0, y1=1, x2=0.3, y2=0))
    body = (
        f'<path d="{leaf_d(length, width)}" fill="url(#{grad})"/>'
        f'<path d="M0 {n(-.05*length)}Q{n(width*.12)} {n(-.5*length)} 0 {n(-.92*length)}" fill="none" '
        f'stroke="{pal["leaf"][3]}" stroke-opacity=".55" stroke-width=".7"/>'
    )
    return wrap("pop", body, delay)


# -- flowers ---------------------------------------------------------------
FLOWERS = {
    # kind: layers of (count, length factor, width factor, petal shape, angle offset)
    "peony": [(9, 1.0, .58, "ruffle", 0), (8, .82, .52, "ruffle", 20), (7, .63, .46, "ruffle", 8),
              (6, .44, .38, "ruffle", 33), (5, .27, .3, "round", 12)],
    "rose": [(5, 1.0, .7, "round", 0), (5, .84, .64, "round", 36), (5, .66, .56, "round", 14),
             (4, .48, .5, "round", 50), (3, .3, .42, "round", 20)],
    "sakura": [(5, 1.0, .62, "notch", 0)],
    "cosmos": [(8, 1.0, .4, "toothed", 0)],
    "aster": [(18, 1.0, .13, "pointed", 0), (14, .76, .13, "pointed", 10)],
    "plum": [(5, 1.0, .72, "round", 0)],
    "kikyo": [(5, 1.0, .62, "kikyo", 0)],
}


UNIT = 10.0  # flowers are drawn at this radius and scaled into place, so geometry and gradients are shared
PETAL_ANIMATION_MIN_R = 16.0  # smaller heads unfold as one piece


def _stops(pal: dict, kind: str, hue: str) -> list[tuple[float, str, float]]:
    ramp = pal[hue]
    if kind == "aster":
        return [(0, ramp[2], 1), (.45, ramp[4], 1), (1, pal["cream"][0], 1)]
    if kind in ("sakura", "plum"):
        return [(0, ramp[1], 1), (.4, ramp[3], 1), (1, ramp[5], 1)]
    if kind == "kikyo":
        return [(0, ramp[5], 1), (.24, ramp[4], 1), (.5, ramp[3], 1), (.82, ramp[1], 1), (1, ramp[0], 1)]
    if kind == "cosmos":
        return [(0, ramp[0], 1), (.35, ramp[1], 1), (1, ramp[3], 1)]
    return [(0, ramp[0], 1), (.3, ramp[1], 1), (.72, ramp[3], 1), (1, ramp[4], 1)]


def _layers(doc: Doc, pal: dict, kind: str, hue: str, delay: float | None, stroke_width: float) -> str:
    """Petal layers at UNIT radius; `delay` None means no per-petal animation.

    Each inner layer casts a soft shadow on the layer beneath it.
    """
    grad = doc.memo(f"fgrad:{kind}:{hue}", lambda: doc.radial(_stops(pal, kind, hue), cx=0, cy=0, r=UNIT, user=True))
    layers = []
    for index, (count, lf, wf, shape, offset) in enumerate(FLOWERS[kind]):
        pid = petal_ref(doc, shape, UNIT * lf, UNIT * wf)
        if index:
            sil = _silhouette(doc, kind, index)
            shadow = f'<use href="#{sil}" transform="translate(.5 1.1) scale(1.07)" fill="{pal["shadow"]}" fill-opacity=".2"/>'
            layers.append(shadow if delay is None else wrap("shade", shadow, delay + .2 * index + .4))
        petals = []
        for j in range(count):
            angle = offset + j * 360 / count
            anim = "" if delay is None else f' class="petal"{delay_style(delay + .2 * index + .03 * j)}'
            petals.append(f'<g transform="rotate({n(angle)})"><use href="#{pid}"{anim}/></g>')
        layers.append(
            f'<g fill="url(#{grad})" stroke="{pal[hue][0]}" stroke-opacity=".28" stroke-width="{n(stroke_width, 3)}">'
            f'{"".join(petals)}</g>'
        )
    return "".join(layers)


def _silhouette(doc: Doc, kind: str, index: int = 0) -> str:
    """One petal layer as bare outlines, for shadows and the light overlay."""
    def build() -> str:
        count, lf, wf, shape, offset = FLOWERS[kind][index]
        ref = petal_shape_ref(doc, shape, UNIT * lf, UNIT * wf)
        sid = doc.uid("sil")
        body = "".join(f'<use href="#{ref}" transform="rotate({n(offset + j * 360 / count)})"/>' for j in range(count))
        doc.defs.append(f'<g id="{sid}">{body}</g>')
        return sid
    return doc.memo(f"sil:{kind}:{index}", build)


def _light(doc: Doc, pal: dict) -> str:
    """Light from the upper left across a whole flower head."""
    dark = .16 if pal["scheme"] == "light" else .3
    return doc.memo("light", lambda: doc.linear(
        [(0, "#FFFFFF", .42), (.42, "#FFFFFF", 0), (.58, "#000000", 0), (1, "#000000", dark)],
        x1=-UNIT, y1=-UNIT, x2=UNIT, y2=UNIT, user=True))


def head_shadow(doc: Doc, pal: dict, r: float) -> str:
    """A soft shadow a flower head casts on whatever lies behind it."""
    grad = doc.memo("headshadow", lambda: doc.radial(
        [(0, pal["shadow"], .32 if pal["scheme"] == "light" else .5), (.6, pal["shadow"], .12), (1, pal["shadow"], 0)]))
    return f'<ellipse cx="{n(r * .2)}" cy="{n(r * .32)}" rx="{n(r * 1.08)}" ry="{n(r * .86)}" fill="url(#{grad})"/>'


def flower_symbol(doc: Doc, pal: dict, kind: str, hue: str) -> str:
    """A finished, lit flower at UNIT radius, defined once and reused with <use>."""
    def build() -> str:
        sid = doc.uid("fl")
        overlay = f'<use href="#{_silhouette(doc, kind)}" fill="url(#{_light(doc, pal)})"/>'
        doc.defs.append(
            f'<g id="{sid}">{_layers(doc, pal, kind, hue, None, .6)}{overlay}{flower_center(pal, kind, UNIT)}</g>'
        )
        return sid
    return doc.memo(f"flower:{kind}:{hue}", build)


def flower(doc: Doc, pal: dict, kind: str, r: float, delay: float, *, hue: str = "rose",
           tilt: float = 0.0, squash: float = 1.0, still: bool = False, shadow: bool = True) -> str:
    """A lit flower head about the origin, lifted off the page by its own shadow.

    Large heads open petal by petal; small ones are a single reused symbol that
    unfolds as a whole, which keeps busy scenes cheap to repaint. `still`
    leaves out the animation entirely.
    """
    s = r / UNIT
    transform = []
    if tilt:
        transform.append(f"rotate({n(tilt)})")
    if squash != 1.0:
        transform.append(f"scale(1 {n(squash)})")
    transform.append(f"scale({n(s, 3)})")
    attr = f' transform="{" ".join(transform)}"'
    cast = head_shadow(doc, pal, r) if shadow and r >= 5 else ""
    if still or r < PETAL_ANIMATION_MIN_R:
        head = cast + f'<use href="#{flower_symbol(doc, pal, kind, hue)}"{attr}/>'
        return f"<g>{head}</g>" if still else wrap("unfurl", head, delay)
    opened = delay + .2 * len(FLOWERS[kind])
    overlay = wrap("shade", f'<use href="#{_silhouette(doc, kind)}" fill="url(#{_light(doc, pal)})"/>', opened)
    center = wrap("pop", flower_center(pal, kind, UNIT), opened + .25)
    head = f'<g{attr}>{_layers(doc, pal, kind, hue, delay, .6 / s)}{overlay}{center}</g>'
    return wrap("unfurl", wrap("shade", cast, opened) + head, delay)


def flower_center(pal: dict, kind: str, r: float) -> str:
    gold = pal["gold"]
    if kind in ("sakura", "plum"):
        lines, dots = [], []
        dot = max(.7, r * .05)
        for k in range(8):
            a = math.radians(k * 45 + 8)
            x, y = math.cos(a) * r * .36, math.sin(a) * r * .36
            lines.append(f"M0 0L{n(x)} {n(y)}")
            dots.append(f"M{n(x - dot)} {n(y)}a{n(dot)} {n(dot)} 0 1 0 {n(2 * dot)} 0a{n(dot)} {n(dot)} 0 1 0 {n(-2 * dot)} 0")
        return (
            f'<path d="{"".join(lines)}" stroke="{pal["rose"][1]}" stroke-width=".6" stroke-opacity=".7"/>'
            f'<path d="{"".join(dots)}" fill="{gold[1]}"/><circle r="{n(r*.1)}" fill="{pal["rose"][2]}"/>'
        )
    if kind == "kikyo":
        arms = []
        for k in range(5):
            a = math.radians(k * 72 - 90)
            x, y = math.cos(a) * r * .2, math.sin(a) * r * .2
            arms.append(f"M0 0Q{n(x*.4)} {n(y*.9)} {n(x)} {n(y)}")
        return (
            f'<circle r="{n(r*.2)}" fill="{pal["kikyo"][5]}" fill-opacity=".9"/>'
            f'<path d="{"".join(arms)}" fill="none" stroke="{pal["cream"][0]}" stroke-width="{n(max(.8, r*.05))}" '
            f'stroke-linecap="round"/><circle r="{n(r*.06)}" fill="{pal["kikyo"][2]}"/>'
        )
    if kind == "rose":
        swirl = (
            f"M0 {n(-r*.05)}C{n(r*.14)} {n(-r*.12)} {n(r*.16)} {n(r*.08)} 0 {n(r*.1)}"
            f"C{n(-r*.2)} {n(r*.1)} {n(-r*.18)} {n(-r*.2)} {n(r*.04)} {n(-r*.2)}"
        )
        return f'<path d="{swirl}" fill="none" stroke="{pal["rose"][0]}" stroke-width="{n(max(.8, r*.04))}" stroke-linecap="round"/>'
    disc = {"peony": .17, "cosmos": .2, "aster": .24}[kind]
    ring = 14 if kind == "peony" else 10
    dot = max(.6, r * .03)
    dots = []
    for k in range(ring):
        a = math.radians(k * 360 / ring)
        x, y = math.cos(a) * r * disc * .72, math.sin(a) * r * disc * .72
        dots.append(f"M{n(x - dot)} {n(y)}a{n(dot)} {n(dot)} 0 1 0 {n(2 * dot)} 0a{n(dot)} {n(dot)} 0 1 0 {n(-2 * dot)} 0")
    return (
        f'<circle r="{n(r*disc)}" fill="{gold[1]}"/><path d="{"".join(dots)}" fill="{gold[0]}"/>'
        f'<circle r="{n(r*disc*.35)}" fill="{gold[2]}"/>'
    )


def bud(pal: dict, r: float, hue: str, delay: float) -> str:
    ramp = pal[hue]
    body = (
        f'<path d="M0 0C{n(r*.9)} {n(-r*.4)} {n(r*.7)} {n(-r*1.5)} 0 {n(-r*1.9)}C{n(-r*.7)} {n(-r*1.5)} {n(-r*.9)} {n(-r*.4)} 0 0Z" fill="{ramp[2]}"/>'
        f'<path d="M0 0C{n(r*.5)} {n(-r*.4)} {n(r*.45)} {n(-r*1.2)} 0 {n(-r*1.75)}" fill="none" stroke="{ramp[0]}" stroke-opacity=".35" stroke-width=".7"/>'
        f'<path d="M0 0C{n(r*.7)} {n(-r*.1)} {n(r*.8)} {n(-r*.6)} {n(r*.3)} {n(-r*.9)}M0 0C{n(-r*.7)} {n(-r*.1)} {n(-r*.8)} {n(-r*.6)} {n(-r*.3)} {n(-r*.9)}" '
        f'fill="none" stroke="{pal["leaf"][1]}" stroke-width="1.1" stroke-linecap="round"/>'
    )
    return wrap("pop", body, delay)


def balloon(doc: Doc, pal: dict, r: float, delay: float) -> str:
    """A kikyo bud: a puffed five-seamed balloon on green sepals, base at the origin."""
    ramp = pal["kikyo"]
    grad = doc.memo("balloon", lambda: doc.linear([(0, ramp[2], 1), (.6, ramp[3], 1), (1, ramp[4], 1)],
                                                  x1=0, y1=1, x2=.2, y2=0))
    body = (
        f'<path d="M0 {n(-r*.15)}C{n(r*1.05)} {n(-r*.25)} {n(r*1.08)} {n(-r*1.25)} 0 {n(-r*1.7)}'
        f'C{n(-r*1.08)} {n(-r*1.25)} {n(-r*1.05)} {n(-r*.25)} 0 {n(-r*.15)}Z" fill="url(#{grad})" '
        f'stroke="{ramp[1]}" stroke-opacity=".3" stroke-width=".6"/>'
        f'<path d="M0 {n(-r*.2)}C{n(r*.45)} {n(-r*.6)} {n(r*.4)} {n(-r*1.3)} 0 {n(-r*1.66)}'
        f'M0 {n(-r*.2)}C{n(-r*.45)} {n(-r*.6)} {n(-r*.4)} {n(-r*1.3)} 0 {n(-r*1.66)}" fill="none" '
        f'stroke="{ramp[1]}" stroke-opacity=".35" stroke-width=".6"/>'
        f'<path d="M0 0C{n(r*.5)} {n(-r*.05)} {n(r*.7)} {n(-r*.25)} {n(r*.6)} {n(-r*.42)}'
        f'M0 0C{n(-r*.5)} {n(-r*.05)} {n(-r*.7)} {n(-r*.25)} {n(-r*.6)} {n(-r*.42)}" fill="none" '
        f'stroke="{pal["leaf"][1]}" stroke-width="1.2" stroke-linecap="round"/>'
    )
    return wrap("pop", body, delay)


def cubic(p0, p1, p2, p3, t):
    u = 1 - t
    return (
        u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
        u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
    )


def sakura_branch(doc: Doc, pal: dict, rng: random.Random, p0, p1, p2, p3, delay: float,
                  twigs: list[tuple[float, float, float]], width: float = 5.0) -> str:
    """A cherry branch along a cubic curve with blossoming twigs.

    twigs = (t along the branch, angle in degrees, length). Blossoms open in
    clusters at each twig tip and in small knots along the branch.
    """
    bark = pal["bark"]
    d = f"M{n(p0[0])} {n(p0[1])}C{n(p1[0])} {n(p1[1])} {n(p2[0])} {n(p2[1])} {n(p3[0])} {n(p3[1])}"
    parts = [
        f'<path class="grow" pathLength="1" d="{d}" fill="none" stroke="{bark}" stroke-width="{n(width)}" '
        f'stroke-linecap="round"{delay_style(delay)}/>',
    ]
    blossoms = []
    for t, angle, length in twigs:
        x, y = cubic(p0, p1, p2, p3, t)
        a = math.radians(angle)
        tx, ty = x + math.cos(a) * length, y + math.sin(a) * length
        bend = rng.uniform(-.25, .25) * length
        parts.append(
            f'<path class="grow" pathLength="1" d="M{n(x)} {n(y)}Q{n((x+tx)/2 - math.sin(a)*bend)} {n((y+ty)/2 + math.cos(a)*bend)} {n(tx)} {n(ty)}" '
            f'fill="none" stroke="{bark}" stroke-width="{n(max(1.2, width*(1-t)*.6))}" stroke-linecap="round"{delay_style(delay + .4 + t*.8)}/>'
        )
        start = delay + .9 + t * .9
        for k in range(rng.randint(3, 5)):
            r = rng.uniform(7.5, 12.5)
            bx, by = tx + rng.uniform(-13, 13), ty + rng.uniform(-10, 10)
            head = flower(doc, pal, "sakura", r, start + k * .18, hue="sakura", tilt=rng.uniform(0, 72),
                          squash=rng.uniform(.75, 1))
            blossoms.append(place(bx, by, wrap("breathe", head, -rng.uniform(0, 6))))
        for _ in range(rng.randint(1, 2)):
            bx, by = tx + rng.uniform(-14, 14), ty + rng.uniform(4, 14)
            bud_body = (
                f'<path d="M0 0L0 6" stroke="{bark}" stroke-width=".7"/>'
                f'<ellipse cy="8.5" rx="2.6" ry="3.4" fill="{pal["sakura"][2]}"/>'
            )
            blossoms.append(place(bx, by - 6, wrap("pop", bud_body, start + .6), rotate=rng.uniform(-30, 30)))
        if rng.random() < .6:
            blossoms.append(place(tx + rng.uniform(-6, 6), ty, leaf(doc, pal, rng.uniform(10, 14), 4.4, start + .3),
                                  rotate=angle + 90 + rng.uniform(-40, 40)))
    # knots of blossom right on the branch
    for _ in range(int(len(twigs) * 2.2)):
        t = rng.uniform(.2, .97)
        x, y = cubic(p0, p1, p2, p3, t)
        r = rng.uniform(6.5, 10.5)
        head = flower(doc, pal, "sakura", r, delay + 1.2 + t * .9, hue="sakura", tilt=rng.uniform(0, 72),
                      squash=rng.uniform(.8, 1))
        blossoms.append(place(x + rng.uniform(-4, 4), y + rng.uniform(-4, 6), head))
    return "".join(parts + blossoms)


def stemmed(doc: Doc, pal: dict, head: str, height: float, lean: float, delay: float,
            leaves: list[tuple[float, int, float, float]] = (), width: float = 2.0, sway: str = "sway-a",
            sway_delay: float = 0.0) -> str:
    """A head on a curved stem. Origin is the stem base; leaves = (t, side, length, width)."""
    p0, p1 = (0.0, 0.0), (lean, -height)
    c = (lean * .1, -height * .55)
    stem = (
        f'<path class="grow" pathLength="1" d="M0 0Q{n(c[0])} {n(c[1])} {n(p1[0])} {n(p1[1])}" fill="none" '
        f'stroke="{pal["stem"]}" stroke-width="{n(width)}" stroke-linecap="round"{delay_style(delay)}/>'
    )
    parts = [stem]
    for t, side, length, lw in leaves:
        x, y = qpoint(p0, c, p1, t)
        angle = qangle(p0, c, p1, t) + 90 + side * 48
        parts.append(place(x, y, leaf(doc, pal, length, lw, delay + .5 + t * .6), rotate=angle))
    parts.append(place(p1[0], p1[1], head))
    return wrap(sway, "".join(parts), sway_delay)


def _whorl(doc: Doc, pal: dict, k: int) -> str:
    """Unit lavender whorl: two side buds and a paler front bud."""
    def build() -> str:
        lav = pal["lav"]
        side, front = lav[max(0, k - 1)], lav[k]
        wid = doc.uid("lw")
        doc.defs.append(
            f'<g id="{wid}">'
            f'<ellipse cx="-2.7" cy="-.6" rx="2" ry="3.5" transform="rotate(-36 -2.7 -.6)" fill="{side}"/>'
            f'<ellipse cx="2.7" cy="-.6" rx="2" ry="3.5" transform="rotate(36 2.7 -.6)" fill="{side}"/>'
            f'<ellipse cy="-2.3" rx="2.1" ry="3.3" fill="{front}"/></g>'
        )
        return wid
    return doc.memo(f"whorl:{k}", build)


def lavender(doc: Doc, pal: dict, height: float, lean: float, delay: float, rng: random.Random,
             scale: float = 1.0) -> str:
    """A lavender stalk rooted at the origin, whorls of buds popping upward."""
    lav = pal["lav"]
    p0, p1 = (0.0, 0.0), (lean, -height)
    c = (lean * .15, -height * .55)
    parts = [
        f'<path class="grow" pathLength="1" d="M0 0Q{n(c[0])} {n(c[1])} {n(p1[0])} {n(p1[1])}" fill="none" '
        f'stroke="{pal["stem"]}" stroke-width="{n(1.7*scale)}" stroke-linecap="round"{delay_style(delay)}/>'
    ]
    for side in (-1, 1):
        t = rng.uniform(.04, .16)
        x, y = qpoint(p0, c, p1, t)
        angle = qangle(p0, c, p1, t) + 90 + side * rng.uniform(20, 34)
        body = f'<path d="{leaf_d(height*rng.uniform(.18, .26), 2.4*scale)}" fill="{pal["leaf"][2]}"/>'
        parts.append(place(x, y, wrap("pop", body, delay + .3), rotate=angle))
    whorls = max(8, int(height / 14) + 4)
    for i in range(whorls):
        u = i / (whorls - 1)
        t = .48 + .52 * (u ** .85)
        x, y = qpoint(p0, c, p1, t)
        angle = qangle(p0, c, p1, t) + 90
        s = (1.05 - .5 * u) * scale
        k = min(4, 1 + int(u * 3.2 + rng.uniform(-.3, .3)))
        ref = _whorl(doc, pal, max(1, k))
        parts.append(
            f'<g transform="translate({n(x)} {n(y)}) rotate({n(angle)}) scale({n(s)})">'
            f'<use href="#{ref}" class="pop"{delay_style(delay + 1.0 + u * 1.0)}/></g>'
        )
    tip = f'<ellipse cy="{n(-3*scale*.5)}" rx="{n(1.6*scale*.6)}" ry="{n(3*scale*.6)}" fill="{lav[3]}"/>'
    parts.append(place(p1[0], p1[1], wrap("pop", tip, delay + 2.1), rotate=qangle(p0, c, p1, 1) + 90))
    return "".join(parts)


def gypsophila(pal: dict, rng: random.Random, delay: float, sprigs: int = 6, height: float = 40) -> str:
    """Baby's breath: a spray of tiny white flowers on hair-thin stems."""
    parts = []
    for i in range(sprigs):
        a = math.radians(-90 + rng.uniform(-50, 50))
        h = height * rng.uniform(.6, 1.0)
        x, y = math.cos(a) * h, math.sin(a) * h
        parts.append(
            f'<path class="grow" pathLength="1" d="M0 0Q{n(x*.2)} {n(y*.6)} {n(x)} {n(y)}" fill="none" '
            f'stroke="{pal["leaf"][2]}" stroke-width=".7"{delay_style(delay)}/>'
        )
        for _ in range(rng.randint(3, 5)):
            dx, dy = rng.uniform(-5, 5), rng.uniform(-5, 3)
            r = rng.uniform(1.3, 2.2)
            dot = f'<circle r="{n(r)}" fill="{pal["cream"][0]}" stroke="{pal["lav"][4]}" stroke-width=".5"/><circle r="{n(r*.35)}" fill="{pal["gold"][2]}"/>'
            parts.append(place(x + dx, y + dy, wrap("pop", dot, delay + 1 + rng.uniform(0, .6))))
    return "".join(parts)


def grass(pal: dict, rng: random.Random, delay: float, blades: int = 5, height: float = 30) -> str:
    parts = []
    for _ in range(blades):
        h = height * rng.uniform(.6, 1.1)
        lean = rng.uniform(-14, 14)
        parts.append(
            f'<path class="grow" pathLength="1" d="M0 0Q{n(lean*.3)} {n(-h*.6)} {n(lean)} {n(-h)}" fill="none" '
            f'stroke="{pal["leaf"][rng.randint(1, 2)]}" stroke-width="{n(rng.uniform(1, 1.8))}" stroke-linecap="round"{delay_style(delay + rng.uniform(0, .4))}/>'
        )
    return "".join(parts)


# -- atmosphere ------------------------------------------------------------
def falling_petals(doc: Doc, pal: dict, rng: random.Random, specs: list[tuple[float, float, float, float]],
                   start: float) -> str:
    """Petals drifting down and across; specs = (x, y, dx, dy) in px."""
    colors = [pal["sakura"][2], pal["sakura"][3], pal["sakura"][3], pal["sakura"][4], pal["rose"][3], pal["kikyo"][4]]
    parts = []
    for k, (x, y, dx, dy) in enumerate(specs):
        name = f"fall{k}"
        mid = dx * .45 + rng.uniform(-40, 40)
        spin = rng.choice((-1, 1)) * rng.uniform(220, 520)
        doc.css(
            f"@keyframes {name}{{0%{{transform:translate({n(x)}px,{n(y)}px) rotate(0);opacity:0}}"
            f"12%{{opacity:.95}}50%{{transform:translate({n(x+mid)}px,{n(y+dy*.5)}px) rotate({n(spin*.5)}deg)}}"
            f"88%{{opacity:.85}}100%{{transform:translate({n(x+dx)}px,{n(y+dy)}px) rotate({n(spin)}deg);opacity:0}}}}",
            anim=True,
        )
        size = rng.uniform(5.5, 9)
        duration = rng.uniform(11, 18)
        d = petal_d("notch", size, size * .62)
        parts.append(
            f'<g class="fall" style="animation:{name} {n(duration)}s linear {n(start + k * rng.uniform(.6, 1.4))}s infinite both">'
            f'<g class="flip" style="animation-duration:{n(rng.uniform(1.6, 3))}s">'
            f'<path d="{d}" transform="translate(0 {n(size/2)})" fill="{rng.choice(colors)}"/></g></g>'
        )
    return "".join(parts)


def wisp(pal: dict, rng: random.Random, height: float, delay: float, duration: float) -> str:
    """A curl of fragrance rising from the origin."""
    a, b = rng.uniform(9, 17), -rng.uniform(9, 17)
    d = (
        f"M0 0C{n(a)} {n(-height*.22)} {n(b)} {n(-height*.42)} {n(a*.35)} {n(-height*.6)}"
        f"S{n(a)} {n(-height*.88)} {n(b*.4)} {n(-height)}"
    )
    style = f' style="animation-delay:{n(delay)}s;animation-duration:{n(duration)}s"'
    return (
        f'<path class="wisp" pathLength="1" d="{d}" fill="none" stroke="{pal["wisp"]}" stroke-opacity=".22" stroke-width="5" stroke-linecap="round"{style}/>'
        f'<path class="wisp" pathLength="1" d="{d}" fill="none" stroke="{pal["wisp"]}" stroke-width="1.3" stroke-linecap="round"{style}/>'
    )


def mote(pal: dict, rng: random.Random, delay: float) -> str:
    r = rng.uniform(1, 2.1)
    color = rng.choice((pal["gold"][2], pal["gold"][1], pal["lav"][4], pal["rose"][4]))
    body = f'<circle r="{n(r*2.6)}" fill="{color}" fill-opacity=".18"/><circle r="{n(r)}" fill="{color}"/>'
    return f'<g class="twinkle mote" style="animation-delay:{n(delay)}s;animation-duration:{n(rng.uniform(2.6, 4.8))}s">{body}</g>'
