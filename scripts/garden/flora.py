"""Cupped, warm-lit flower primitives with curved petals and soft contact shade.

Every primitive draws around its own origin and returns markup. Callers place
it with a translate group, so the CSS transform used by an animation never
competes with a transform attribute: animated classes all grow, sway or
unfold about their local (0, 0).
"""

from __future__ import annotations

import hashlib
import math
import random

from .depth import soft_blur
from .svg import Doc, n

BASE_CSS = (
    ".fall{opacity:0}"
)

ANIM_CSS = (
    ".pop,.unfurl,.petal,.breathe,.fadeup,.fall,.flip"
    "{transform-origin:0 0}"
    ".grow{stroke-dasharray:1;animation:grow 1.7s cubic-bezier(.45,.05,.3,1) both}"
    "@keyframes grow{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
    ".pop{animation:pop .8s ease-out both}"
    "@keyframes pop{from{transform:scale(.97);opacity:0}to{transform:none;opacity:1}}"
    ".unfurl{animation:unfurl 1.1s ease-out both}"
    "@keyframes unfurl{from{transform:rotate(-5deg) scale(.97);opacity:0}to{transform:none;opacity:1}}"
    ".petal{animation:petal .9s ease-out both}"
    "@keyframes petal{from{transform:scale(.97);opacity:0}to{transform:none;opacity:1}}"
    ".breathe{animation:breathe 12s ease-in-out infinite}"
    "@keyframes breathe{0%,100%{transform:none}50%{transform:scale(1.008) rotate(.6deg)}}"
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
def petal_d(kind: str, length: float, width: float) -> str:
    """A petal with its base at the origin and its tip at (0, -length)."""
    l, w = length, width
    if kind == "ruffle":
        return (
            f"M0 0C{n(.7*w)} {n(-.13*l)} {n(1.12*w)} {n(-.5*l)} {n(.89*w)} {n(-.77*l)}"
            f"C{n(.84*w)} {n(-.97*l)} {n(.5*w)} {n(-1.1*l)} {n(.23*w)} {n(-.96*l)}"
            f"C{n(.06*w)} {n(-1.08*l)} {n(-.3*w)} {n(-1.1*l)} {n(-.47*w)} {n(-.96*l)}"
            f"C{n(-.89*w)} {n(-l)} {n(-1.09*w)} {n(-.71*l)} {n(-.84*w)} {n(-.51*l)}"
            f"C{n(-.8*w)} {n(-.26*l)} {n(-.25*w)} {n(-.1*l)} 0 0Z"
        )
    if kind == "notch":
        return (
            f"M0 0C{n(.6*w)} {n(-.1*l)} {n(1.08*w)} {n(-.47*l)} {n(.79*w)} {n(-.79*l)}"
            f"C{n(.65*w)} {n(-.99*l)} {n(.3*w)} {n(-1.05*l)} {n(.11*w)} {n(-.88*l)}"
            f"Q{n(.02*w)} {n(-.78*l)} {n(-.1*w)} {n(-.89*l)}"
            f"C{n(-.36*w)} {n(-1.03*l)} {n(-.73*w)} {n(-.95*l)} {n(-.85*w)} {n(-.72*l)}"
            f"C{n(-1.02*w)} {n(-.44*l)} {n(-.45*w)} {n(-.11*l)} 0 0Z"
        )
    if kind == "toothed":
        return (
            f"M0 0C{n(.72*w)} {n(-.2*l)} {n(1.02*w)} {n(-.65*l)} {n(.8*w)} {n(-.94*l)}"
            f"Q{n(.65*w)} {n(-1.03*l)} {n(.39*w)} {n(-.95*l)}"
            f"Q0 {n(-1.09*l)} {n(-.36*w)} {n(-.96*l)}"
            f"Q{n(-.64*w)} {n(-1.03*l)} {n(-.79*w)} {n(-.92*l)}"
            f"C{n(-1.05*w)} {n(-.66*l)} {n(-.7*w)} {n(-.25*l)} 0 0Z"
        )
    if kind == "kikyo":
        return (
            f"M0 0C{n(.64*w)} {n(-.11*l)} {n(1.02*w)} {n(-.43*l)} {n(.6*w)} {n(-.72*l)}"
            f"C{n(.33*w)} {n(-.84*l)} {n(.22*w)} {n(-.95*l)} {n(.02*w)} {n(-l)}"
            f"Q{n(-.05*w)} {n(-1.015*l)} {n(-.13*w)} {n(-.96*l)}"
            f"C{n(-.3*w)} {n(-.84*l)} {n(-.66*w)} {n(-.74*l)} {n(-.71*w)} {n(-.57*l)}"
            f"C{n(-.95*w)} {n(-.3*l)} {n(-.35*w)} {n(-.13*l)} 0 0Z"
        )
    if kind == "pointed":
        return (
            f"M0 0C{n(w)} {n(-.28*l)} {n(.85*w)} {n(-.76*l)} {n(.14*w)} {n(-.97*l)}"
            f"Q{n(-.02*w)} {n(-1.02*l)} {n(-.17*w)} {n(-.96*l)}"
            f"C{n(-.66*w)} {n(-.78*l)} {n(-.8*w)} {n(-.3*l)} 0 0Z"
        )
    # The rounded spoon bends a little sideways, like a petal lifting toward light.
    return (
        f"M0 0C{n(.34*w)} {n(-.14*l)} {n(.95*w)} {n(-.33*l)} {n(.84*w)} {n(-.68*l)}"
        f"C{n(.76*w)} {n(-.93*l)} {n(.18*w)} {n(-1.07*l)} {n(-.28*w)} {n(-.96*l)}"
        f"C{n(-.95*w)} {n(-.78*l)} {n(-.83*w)} {n(-.3*l)} 0 0Z"
    )


def petal_shape_ref(doc: Doc, kind: str, length: float, width: float) -> str:
    """The bare petal outline, used for silhouettes."""
    key = f"shape:{kind}:{n(length)}:{n(width)}"
    pid = "s" + hashlib.md5(key.encode()).hexdigest()[:7]
    if doc.once(key):
        doc.defs.append(f'<path id="{pid}" d="{petal_d(kind, length, width)}"/>')
    return pid


def petal_ref(doc: Doc, kind: str, length: float, width: float) -> str:
    """A cupped petal with a turning edge, tinted inner fold and soft rim light."""
    key = f"petal:{kind}:{n(length)}:{n(width)}"
    pid = "p" + hashlib.md5(key.encode()).hexdigest()[:7]
    if doc.once(key):
        l, w = length, width
        shape = petal_shape_ref(doc, kind, length, width)
        clip = doc.uid("pc")
        doc.defs.append(f'<clipPath id="{clip}"><use href="#{shape}"/></clipPath>')
        glaze = doc.linear([
            (0, "#FFF8F0", .46), (.45, "#FFF8F0", .16), (1, "#FFF8F0", 0),
        ], x1=-.55*w, y1=-l, x2=.5*w, y2=-.18*l, user=True)
        curl = (
            f"M{n(-.69*w)} {n(-.59*l)}C{n(-.77*w)} {n(-.91*l)} {n(-.2*w)} {n(-1.05*l)} {n(.36*w)} {n(-.9*l)}"
            f"C{n(.09*w)} {n(-1.005*l)} {n(-.27*w)} {n(-.91*l)} {n(-.46*w)} {n(-.72*l)}"
            f"C{n(-.54*w)} {n(-.6*l)} {n(-.56*w)} {n(-.52*l)} {n(-.58*w)} {n(-.49*l)}Z"
        )
        cup = (
            f"M{n(.12*w)} {n(-.12*l)}C{n(.5*w)} {n(-.27*l)} {n(.83*w)} {n(-.55*l)} {n(.58*w)} {n(-.85*l)}"
            f"C{n(.44*w)} {n(-.69*l)} {n(.4*w)} {n(-.47*l)} {n(.22*w)} {n(-.31*l)}Z"
        )
        parts = [
            f'<use href="#{shape}"/>',
            f'<g clip-path="url(#{clip})" stroke="none">'
            f'<path d="{cup}" fill="currentColor" fill-opacity=".11" filter="url(#{soft_blur(doc, .14)})"/>'
            f'<path d="{curl}" fill="url(#{glaze})"/>'
            f'</g>',
        ]
        if kind == "kikyo":
            veins = (
                f"M0 {n(-.12*l)}Q{n(-.16*w)} {n(-.5*l)} 0 {n(-.87*l)}"
                f"M{n(.08*w)} {n(-.15*l)}Q{n(.4*w)} {n(-.45*l)} {n(.3*w)} {n(-.7*l)}"
                f"M{n(-.08*w)} {n(-.15*l)}Q{n(-.42*w)} {n(-.48*l)} {n(-.3*w)} {n(-.73*l)}"
            )
            parts.append(f'<path d="{veins}" fill="none" stroke="currentColor" stroke-opacity=".13" stroke-width=".12" stroke-linecap="round"/>')
        else:
            parts.append(
                f'<path d="M0 {n(-l * .12)}C{n(-w * .04)} {n(-l * .27)} {n(-w * .12)} {n(-l * .6)} {n(-w * .03)} {n(-l * .81)}" '
                f'fill="none" stroke="currentColor" stroke-opacity=".12" stroke-width=".12" stroke-linecap="round"/>'
            )
        doc.defs.append(f'<g id="{pid}">{"".join(parts)}</g>')
    return pid


def leaf_d(length: float, width: float) -> str:
    l, w = length, width
    return (
        f"M0 0C{n(.84*w)} {n(-.15*l)} {n(1.05*w)} {n(-.66*l)} {n(-.2*w)} {n(-l)}"
        f"C{n(-.35*w)} {n(-.88*l)} {n(-1.03*w)} {n(-.54*l)} {n(-.66*w)} {n(-.25*l)}"
        f"Q{n(-.35*w)} {n(-.06*l)} 0 0Z"
    )


def leaf(doc: Doc, pal: dict, length: float, width: float, delay: float, shade: int = 1) -> str:
    """A slightly bowed leaf whose two sides turn differently toward the light."""
    grad = doc.memo(f"leaf:{shade}", lambda: doc.linear([
        (0, pal["leaf"][3], 1), (.43, pal["leaf"][min(2, shade + 1)], 1),
        (.6, pal["leaf"][1], 1), (1, pal["leaf"][0], 1),
    ], x1=0, y1=.18, x2=1, y2=.72))
    midrib = (
        f'M0 {n(-.04*length)}C{n(width*.07)} {n(-.27*length)} '
        f'{n(-width*.28)} {n(-.71*length)} {n(-width*.2)} {n(-.95*length)}'
    )
    body = (
        f'<path d="{leaf_d(length, width)}" transform="translate(.5 .7)" '
        f'fill="{pal["shadow"]}" fill-opacity=".12" filter="url(#{soft_blur(doc, .5)})"/>'
        f'<path d="{leaf_d(length, width)}" fill="url(#{grad})" '
        f'stroke="{pal["leaf"][0]}" stroke-width=".25" stroke-opacity=".3"/>'
        f'<path d="{midrib}" fill="none" stroke="{pal["cream"][0]}" '
        f'stroke-opacity=".43" stroke-width=".55" stroke-linecap="round"/>'
    )
    return wrap("pop", body, delay)


# -- flowers ---------------------------------------------------------------
FLOWERS = {
    # kind: layers of (count, length factor, width factor, petal shape, angle offset)
    "peony": [(7, 1.0, .56, "ruffle", 0), (6, .7, .5, "ruffle", 24), (5, .42, .4, "round", 8)],
    "rose": [(5, 1.0, .68, "round", 0), (5, .71, .6, "round", 36), (4, .4, .46, "round", 14)],
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
        return [(0, pal["cream"][0], 1), (.4, ramp[4], 1), (.76, ramp[2], 1), (1, ramp[1], 1)]
    if kind in ("sakura", "plum"):
        return [(0, ramp[5], 1), (.23, ramp[4], 1), (.53, ramp[3], 1), (.81, ramp[2], 1), (1, ramp[1], 1)]
    if kind == "kikyo":
        return [(0, ramp[5], 1), (.31, ramp[4], 1), (.67, ramp[2], 1), (1, ramp[1], 1)]
    if kind == "cosmos":
        return [(0, ramp[4], 1), (.35, ramp[3], 1), (.74, ramp[1], 1), (1, ramp[0], 1)]
    return [(0, ramp[5], 1), (.3, ramp[4], 1), (.61, ramp[2], 1), (.86, ramp[1], 1), (1, ramp[0], 1)]


def _petal_pose(index: int, j: int, count: int, offset: float) -> str:
    """Repeatable small variations keep the flower's outline naturally uneven."""
    angle = offset + j * 360 / count + math.sin(j * 2.1 + index * .6) * 3.6
    sx = 1 + math.sin(j * 1.7 + index) * .04
    sy = 1 + math.cos(j * 2.4 - index) * .055
    return f"rotate({n(angle)}) scale({n(sx, 3)} {n(sy, 3)})"


def _layers(doc: Doc, pal: dict, kind: str, hue: str, delay: float | None, stroke_width: float,
            compact: bool = False) -> str:
    """Overlapping bowls of petals, with diffuse light on each curved surface."""
    layers = []
    for index, (count, lf, wf, shape, offset) in enumerate(FLOWERS[kind]):
        if compact and index >= 2:
            break
        pid = (petal_shape_ref if compact else petal_ref)(doc, shape, UNIT * lf, UNIT * wf)
        outline = petal_shape_ref(doc, shape, UNIT * lf, UNIT * wf)
        grad = doc.memo(f"petal-color:{kind}:{hue}:{index}", lambda: doc.radial(
            _stops(pal, kind, hue), cx=.32, cy=.13, r=.96 - index * .035))
        petals = []
        for j in range(count):
            petal = (
                f'<use href="#{outline}" transform="translate(.12 .24)" fill="{pal[hue][0]}" '
                f'fill-opacity=".17" stroke="none" filter="url(#{soft_blur(doc, .18)})"/>'
                f'<use href="#{pid}"/>'
            )
            if delay is not None:
                petal = wrap("petal", petal, delay + .18 * index + .035 * j)
            petals.append(f'<g transform="{_petal_pose(index, j, count, offset)}">{petal}</g>')
        if index and not compact:
            layers.append(
                f'<use href="#{_silhouette(doc, kind, index)}" transform="translate(.1 .24)" '
                f'fill="{pal[hue][0]}" fill-opacity=".21" filter="url(#{soft_blur(doc, .26)})"/>'
            )
        layers.append(
            f'<g fill="url(#{grad})" color="{pal[hue][0]}" stroke="{pal[hue][0]}" '
            f'stroke-opacity=".2" stroke-width="{n(stroke_width, 3)}" stroke-linejoin="round">'
            f'{"".join(petals)}</g>'
        )
    return "".join(layers)


def _silhouette(doc: Doc, kind: str, index: int = 0) -> str:
    """One petal layer as bare outlines, for shadows and the light overlay."""
    def build() -> str:
        count, lf, wf, shape, offset = FLOWERS[kind][index]
        ref = petal_shape_ref(doc, shape, UNIT * lf, UNIT * wf)
        sid = doc.uid("sil")
        body = "".join(f'<use href="#{ref}" transform="{_petal_pose(index, j, count, offset)}"/>' for j in range(count))
        doc.defs.append(f'<g id="{sid}">{body}</g>')
        return sid
    return doc.memo(f"sil:{kind}:{index}", build)


def _light(doc: Doc, pal: dict) -> str:
    """A broad warm window light across the whole flower, shared by its petals."""
    return doc.memo("light", lambda: doc.linear(
        [(0, pal["cream"][0], .32), (.42, pal["cream"][0], .03),
         (.6, pal["shadow"], 0), (1, pal["shadow"], .13)],
        x1=-UNIT, y1=-UNIT, x2=UNIT, y2=UNIT, user=True))


def _head_light(doc: Doc, pal: dict, kind: str) -> str:
    def build() -> str:
        cid = doc.uid("headclip")
        doc.defs.append(f'<clipPath id="{cid}"><use href="#{_silhouette(doc, kind)}"/></clipPath>')
        return cid
    clip = doc.memo(f"headclip:{kind}", build)
    return f'<rect x="-12" y="-12" width="24" height="24" fill="url(#{_light(doc, pal)})" clip-path="url(#{clip})"/>'


def head_shadow(doc: Doc, pal: dict, r: float) -> str:
    """A soft shadow a flower head casts on whatever lies behind it."""
    grad = doc.memo("headshadow", lambda: doc.radial(
        [(0, pal["shadow"], .23 if pal["scheme"] == "light" else .36),
         (.42, pal["shadow"], .13), (.74, pal["shadow"], .035), (1, pal["shadow"], 0)]))
    return f'<ellipse cx="{n(r * .18)}" cy="{n(r * .28)}" rx="{n(r * 1.22)}" ry="{n(r * .94)}" fill="url(#{grad})"/>'


def flower_symbol(doc: Doc, pal: dict, kind: str, hue: str, compact: bool = False) -> str:
    """A finished dimensional flower at UNIT radius, reused efficiently with <use>."""
    def build() -> str:
        sid = doc.uid("fl")
        center = flower_center(pal, kind, UNIT)
        if compact:
            center_color = pal["cream"][0] if kind == "kikyo" else pal["gold"][1]
            center = (
                f'<circle cx=".12" cy=".2" r="1.4" fill="{pal[hue][0]}" fill-opacity=".4"/>'
                f'<circle r="1.25" fill="{center_color}"/>'
                f'<circle cx="-.3" cy="-.35" r=".52" fill="{pal["cream"][0]}" fill-opacity=".8"/>'
            )
        doc.defs.append(
            f'<g id="{sid}">{_layers(doc, pal, kind, hue, None, .12 if compact else .17, compact=compact)}'
            f'{_head_light(doc, pal, kind)}{center}</g>'
        )
        return sid
    return doc.memo(f"flower:{kind}:{hue}:{compact}", build)


def flower(doc: Doc, pal: dict, kind: str, r: float, delay: float, *, hue: str = "rose",
           tilt: float = 0.0, squash: float = 1.0, still: bool = False, shadow: bool = True) -> str:
    """A softly cupped flower head about the origin.

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
        head = cast + f'<use href="#{flower_symbol(doc, pal, kind, hue, compact=r < 10)}"{attr}/>'
        return f"<g>{head}</g>" if still else wrap("unfurl", head, delay)
    opened = delay + .2 * len(FLOWERS[kind])
    center = wrap("pop", flower_center(pal, kind, UNIT), opened + .25)
    head = f'<g{attr}>{_layers(doc, pal, kind, hue, delay, .27 / s)}{_head_light(doc, pal, kind)}{center}</g>'
    return wrap("unfurl", wrap("shade", cast, opened) + head, delay)


def flower_center(pal: dict, kind: str, r: float) -> str:
    gold = pal["gold"]
    if kind in ("sakura", "plum"):
        lines, dots = [], []
        dot = max(.3, r * .035)
        for k in range(8):
            a = math.radians(k * 45 + 8)
            x, y = math.cos(a) * r * .36, math.sin(a) * r * .36
            lines.append(f"M0 0Q{n(x*.52-y*.1)} {n(y*.5+x*.1)} {n(x)} {n(y)}")
            dots.append(f"M{n(x - dot)} {n(y)}a{n(dot)} {n(dot)} 0 1 0 {n(2 * dot)} 0a{n(dot)} {n(dot)} 0 1 0 {n(-2 * dot)} 0")
        return (
            f'<circle cx=".1" cy=".2" r="{n(r*.13)}" fill="{pal["rose"][0]}" fill-opacity=".2"/>'
            f'<path d="{"".join(lines)}" fill="none" stroke="{pal["rose"][1]}" stroke-width=".24" stroke-opacity=".65" stroke-linecap="round"/>'
            f'<path d="{"".join(dots)}" transform="translate(.04 .09)" fill="{gold[0]}"/>'
            f'<path d="{"".join(dots)}" fill="{gold[2]}"/>'
            f'<circle r="{n(r*.095)}" fill="{pal["rose"][2]}"/>'
            f'<circle cx="{n(-r*.025)}" cy="{n(-r*.035)}" r="{n(r*.046)}" fill="{pal["sakura"][4]}"/>'
        )
    if kind == "kikyo":
        arms = []
        for k in range(5):
            a = math.radians(k * 72 - 90)
            x, y = math.cos(a) * r * .2, math.sin(a) * r * .2
            arms.append(f"M0 0Q{n(x*.4)} {n(y*.9)} {n(x)} {n(y)}")
        return (
            f'<circle r="{n(r*.2)}" fill="{pal["kikyo"][5]}" fill-opacity=".9"/>'
            f'<path d="{"".join(arms)}" fill="none" stroke="{pal["cream"][0]}" stroke-width="{n(max(.35, r*.035))}" '
            f'stroke-linecap="round"/><circle r="{n(r*.06)}" fill="{pal["kikyo"][2]}"/>'
        )
    if kind == "rose":
        swirl = (
            f"M0 {n(-r*.05)}C{n(r*.14)} {n(-r*.12)} {n(r*.16)} {n(r*.08)} 0 {n(r*.1)}"
            f"C{n(-r*.2)} {n(r*.1)} {n(-r*.18)} {n(-r*.2)} {n(r*.04)} {n(-r*.2)}"
        )
        return (
            f'<path d="{swirl}" transform="translate(.08 .13)" fill="none" stroke="{pal["rose"][0]}" '
            f'stroke-opacity=".44" stroke-width=".6" stroke-linecap="round"/>'
            f'<path d="{swirl}" fill="none" stroke="{pal["rose"][3]}" stroke-width=".27" stroke-linecap="round"/>'
        )
    disc = {"peony": .17, "cosmos": .2, "aster": .24}[kind]
    ring = 14 if kind == "peony" else 10
    dot = max(.28, r * .025)
    dots = []
    for k in range(ring):
        a = math.radians(k * 360 / ring)
        x, y = math.cos(a) * r * disc * .72, math.sin(a) * r * disc * .72
        dots.append(f"M{n(x - dot)} {n(y)}a{n(dot)} {n(dot)} 0 1 0 {n(2 * dot)} 0a{n(dot)} {n(dot)} 0 1 0 {n(-2 * dot)} 0")
    return (
        f'<circle cx=".06" cy=".17" r="{n(r*disc*1.03)}" fill="{pal["rose"][0]}" fill-opacity=".35"/>'
        f'<circle r="{n(r*disc)}" fill="{gold[0]}"/>'
        f'<circle cx="{n(-r*disc*.1)}" cy="{n(-r*disc*.15)}" r="{n(r*disc*.87)}" fill="{gold[1]}"/>'
        f'<path d="{"".join(dots)}" fill="{gold[2]}"/>'
        f'<circle cx="{n(-r*disc*.12)}" cy="{n(-r*disc*.15)}" r="{n(r*disc*.32)}" fill="{gold[2]}"/>'
    )


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

