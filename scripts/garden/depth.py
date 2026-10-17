"""Softly raised surfaces and shallow, warm-lit lettering for the garden."""

from __future__ import annotations

from .svg import Doc, n


def blend(a: str, b: str, amount: float) -> str:
    """Blend two palette colors without introducing another color dependency."""
    ca, cb = a.lstrip("#"), b.lstrip("#")
    channels = [round(int(ca[i:i + 2], 16) * (1 - amount) + int(cb[i:i + 2], 16) * amount)
                for i in (0, 2, 4)]
    return "#" + "".join(f"{value:02X}" for value in channels)


def soft_blur(doc: Doc, amount: float) -> str:
    """Share small diffusion filters between shadows, petals and lettering."""
    def build() -> str:
        fid = doc.uid("soft")
        doc.defs.append(
            f'<filter id="{fid}" x="-40%" y="-100%" width="180%" height="300%" '
            f'color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="{n(amount)}"/></filter>'
        )
        return fid
    return doc.memo(f"soft-blur:{n(amount)}", build)


def raised(doc: Doc, pal: dict, x: float, y: float, w: float, h: float,
           rx: float = 24, lift: float = 1.0) -> str:
    """A rounded surface with a thin curved edge and a diffuse contact shadow."""
    light = pal["scheme"] == "light"
    rounding = max(rx, 21)
    edge = max(1.6, 2.8 * lift)
    face = doc.memo("card-face", lambda: doc.linear([
        (0, "#FFFCF8" if light else "#39303B", 1),
        (.48, pal["card"], 1),
        (1, "#F3E9EB" if light else "#2E2631", 1),
    ], x1=.08, y1=0, x2=.87, y2=1))
    rim = doc.memo("card-edge", lambda: doc.linear([
        (0, pal["border"], 1),
        (1, "#D6C6CE" if light else "#1F1B24", 1),
    ]))
    glow = doc.memo("card-window-light", lambda: doc.radial([
        (0, pal["cream"][0], .68 if light else .035),
        (.52, pal["cream"][0], .16 if light else .01),
        (1, pal["cream"][0], 0),
    ], cx=.15, cy=.03, r=.86))
    blur = soft_blur(doc, 2.6)
    return (
        f'<rect x="{n(x + .9)}" y="{n(y + edge + 1.2)}" width="{n(w - 1.8)}" height="{n(h)}" '
        f'rx="{n(rounding)}" fill="{pal["shadow"]}" fill-opacity="{.16 if light else .33}" '
        f'filter="url(#{blur})"/>'
        f'<rect x="{n(x)}" y="{n(y + edge)}" width="{n(w)}" height="{n(h)}" '
        f'rx="{n(rounding)}" fill="url(#{rim})"/>'
        f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{n(rounding)}" '
        f'fill="url(#{face})" stroke="{pal["border"]}" stroke-opacity=".5" stroke-width=".6"/>'
        f'<rect x="{n(x + .5)}" y="{n(y + .5)}" width="{n(w - 1)}" height="{n(h - 1)}" '
        f'rx="{n(rounding)}" fill="url(#{glow})"/>'
        f'<path d="M{n(x + 1)} {n(y + h * .45)}V{n(y + rounding)}'
        f'Q{n(x + 1)} {n(y + 1)} {n(x + rounding)} {n(y + 1)}H{n(x + w - rounding)}" '
        f'fill="none" stroke="{pal["cream"][0]}" stroke-opacity="{.85 if light else .1}" '
        f'stroke-width="1.15" stroke-linecap="round"/>'
    )


def button(doc: Doc, pal: dict, x: float, y: float, w: float, h: float) -> str:
    """A gently domed pill for compact labels."""
    light = pal["scheme"] == "light"
    face = doc.memo("button-face", lambda: doc.linear([
        (0, pal["cream"][0] if light else pal["planter"][0], 1),
        (1, pal["sakura"][4] if light else pal["planter"][1], 1),
    ], x1=.2, y1=0, x2=.8, y2=1))
    radius = h / 2
    return (
        f'<rect x="{n(x)}" y="{n(y + 1.5)}" width="{n(w)}" height="{n(h)}" rx="{n(radius)}" '
        f'fill="{pal["shadow"]}" fill-opacity="{.13 if light else .27}"/>'
        f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{n(radius)}" '
        f'fill="url(#{face})" stroke="{pal["border"]}" stroke-opacity=".45" stroke-width=".6"/>'
    )


def text3d(doc: Doc, pal: dict, segments, x: float, y: float, *, face: str,
           side: list[str], depth: int = 5, step: tuple[float, float] = (.7, .9),
           anchor: str = "start", spacing: float = 0.0,
           shadow: bool = True) -> tuple[str, float]:
    """Shallow relief: diffuse cast shade, curved-color edge, then a lit face."""
    light = pal["scheme"] == "light"
    dx, dy = step
    parts = []
    if shadow:
        shade, _ = doc.text(
            segments, x + dx * depth + .4, y + dy * depth + 1.1,
            anchor=anchor, spacing=spacing,
            attrs=f' fill="{pal["shadow"]}" opacity="{.2 if light else .42}" '
                  f'filter="url(#{soft_blur(doc, .75)})"',
        )
        parts.append(shade)
    for level in range(max(0, depth), 0, -1):
        color = side[min(len(side) - 1, round((1 - level / max(depth, 1)) * (len(side) - 1)))]
        relief, _ = doc.text(segments, x + dx * level, y + dy * level,
                             anchor=anchor, spacing=spacing, attrs=f' fill="{color}"')
        parts.append(relief)
    edge, _ = doc.text(
        segments, x - .2, y - .3, anchor=anchor, spacing=spacing,
        attrs=f' fill="{pal["cream"][0]}" opacity="{.74 if light else .3}"',
    )
    parts.append(edge)
    face_gradient = doc.memo(f"letter-face:{face}", lambda: doc.linear([
        (0, blend(face, pal["cream"][0], .1), 1),
        (.47, face, 1),
        (1, blend(face, pal["kikyo"][0], .08), 1),
    ], x1=0, y1=0, x2=.55, y2=1))
    front, width = doc.text(segments, x, y, anchor=anchor, spacing=spacing,
                            attrs=f' fill="url(#{face_gradient})"')
    parts.append(front)
    return "".join(parts), width

