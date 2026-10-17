"""Render the opening garden panel.

Writes assets/hero-{light,dark}.svg (animated) and
assets/hero-static-{light,dark}.svg (the finished frame, for reduced motion).
The random seed is fixed, so rebuilding without changes gives identical files.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from garden import flora  # noqa: E402
from garden.flora import place, wrap  # noqa: E402
from garden.palette import THEMES  # noqa: E402
from garden.svg import Doc, n  # noqa: E402
from garden.text import measure  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H = 1280, 400
CX = W / 2
BASE_Y = H + 8
# The text block the scenery keeps clear of: (x0, y0, x1, y1).
TEXT_BOX = (420, 96, 860, 345)


def sway(rng: random.Random, cls: str, inner: str) -> str:
    return wrap(cls, inner, -rng.uniform(0, 9))


def lavender_bed(doc, pal, rng, xs, heights, delay, scale=1.0, opacity=1.0) -> str:
    parts = []
    for i, (x, h) in enumerate(zip(xs, heights)):
        stalk = flora.lavender(doc, pal, h, rng.uniform(-16, 16), delay + i * .12 + rng.uniform(0, .15), rng, scale)
        parts.append(place(x, BASE_Y, sway(rng, rng.choice(("sway-a", "sway-b")), stalk)))
    group = "".join(parts)
    return f'<g opacity="{n(opacity)}">{group}</g>' if opacity < 1 else group


def flower_on_stem(doc, pal, rng, x, head_x, head_y, kind, r, delay, hue, leaves=(), squash=1.0, tilt=0.0) -> str:
    head = wrap("breathe", flora.flower(doc, pal, kind, r, delay + .9, hue=hue, squash=squash, tilt=tilt),
                -rng.uniform(0, 6))
    stem = flora.stemmed(doc, pal, head, BASE_Y - head_y, head_x - x, delay, leaves=leaves,
                         width=max(1.3, r * .055), sway=rng.choice(("sway-a", "sway-b")),
                         sway_delay=-rng.uniform(0, 9))
    return place(x, BASE_Y, stem)


def balloon_on_stem(doc, pal, rng, x, head_x, head_y, r, delay) -> str:
    stem = flora.stemmed(doc, pal, flora.balloon(doc, pal, r, delay + 1.4), BASE_Y - head_y, head_x - x, delay,
                         leaves=[(.55, rng.choice((-1, 1)), r * 2, r * .7)], width=1.4,
                         sway="sway-b", sway_delay=-rng.uniform(0, 9))
    return place(x, BASE_Y, stem)


def kikyo_bed(doc, pal, rng, heads, buds, delay) -> list[str]:
    """heads = (base x, head x, head y, r); buds = (base x, head x, head y, r)."""
    parts = []
    for i, (x, hx, hy, r) in enumerate(heads):
        parts.append(flower_on_stem(doc, pal, rng, x, hx, hy, "kikyo", r, delay + i * .25, "kikyo",
                                    leaves=[(.3, -1, r * 1.2, r * .42), (.55, 1, r * 1.05, r * .38)],
                                    squash=rng.uniform(.8, .92), tilt=rng.uniform(-14, 14)))
    for x, hx, hy, r in buds:
        parts.append(balloon_on_stem(doc, pal, rng, x, hx, hy, r, delay + .3))
    return parts


def bokeh(doc: Doc, pal: dict, rng: random.Random, count: int) -> str:
    tints = [pal["bokeh"], pal["sakura"][3], pal["kikyo"][4]]
    alpha = .5 if pal["scheme"] == "light" else .2
    grads = [doc.radial([(0, c, alpha), (.7, c, alpha * .3), (1, c, 0)]) for c in tints]
    parts = []
    while len(parts) < count:
        x, y = rng.uniform(40, W - 40), rng.uniform(30, H - 60)
        if TEXT_BOX[0] - 30 < x < TEXT_BOX[2] + 30 and TEXT_BOX[1] < y < TEXT_BOX[3]:
            continue
        r = rng.uniform(16, 48)
        body = f'<circle r="{n(r)}" fill="url(#{rng.choice(grads)})"/>'
        parts.append(place(x, y, f'<g class="bob" style="animation-delay:{n(-rng.uniform(0, 5))}s;'
                                 f'animation-duration:{n(rng.uniform(7, 12))}s">{body}</g>'))
    return "".join(parts)


def build(theme: str, config: dict) -> Doc:
    pal = THEMES[theme]
    hero = config["hero"]
    rng = random.Random(20251224)
    doc = Doc(
        W, H,
        title=f"{hero['title']} · {hero['verse']}",
        desc=(
            f"An opening panel in which kikyo bellflowers, lavender and cherry blossom open around the name "
            f"{hero['title']}, the line {hero['verse']} and the motto “{hero['motto']}”. "
            "Sakura petals drift down and curls of fragrance rise."
        ),
    )
    flora.install(doc)
    doc.css(
        ".nm{stroke-dasharray:1;animation:ink 2.8s cubic-bezier(.45,.05,.3,1) both}"
        "@keyframes ink{0%{stroke-dashoffset:1;fill-opacity:0}50%{fill-opacity:0}100%{stroke-dashoffset:0;fill-opacity:1}}"
        ".glow{animation:glow 9s ease-in-out infinite}"
        "@keyframes glow{0%,100%{opacity:.75}50%{opacity:1}}",
        anim=True,
    )

    bg = doc.linear([(0, pal["bg"][0], 1), (1, pal["bg"][1], 1)])
    glow = doc.radial([(0, pal["glow"], .95), (.6, pal["glow"], .35), (1, pal["glow"], 0)])
    glow2 = doc.radial([(0, pal["glow2"], .95), (1, pal["glow2"], 0)])
    ground = doc.radial([(0, pal["leaf"][2], .3), (1, pal["leaf"][2], 0)])
    clip = doc.uid("clip")
    doc.defs.append(f'<clipPath id="{clip}"><rect width="{W}" height="{H}" rx="24"/></clipPath>')

    scene = [
        f'<rect width="{W}" height="{H}" fill="url(#{bg})"/>',
        f'<ellipse class="glow" cx="{CX}" cy="236" rx="440" ry="210" fill="url(#{glow})"/>',
        f'<ellipse cx="190" cy="110" rx="330" ry="220" fill="url(#{glow2})"/>',
        f'<ellipse cx="1100" cy="150" rx="320" ry="200" fill="url(#{glow2})"/>',
        f'<ellipse cx="170" cy="410" rx="280" ry="70" fill="url(#{ground})"/>',
        f'<ellipse cx="1100" cy="410" rx="290" ry="70" fill="url(#{ground})"/>',
        bokeh(doc, pal, rng, 9),
    ]

    # -- far layer: paler lavender behind the beds
    scene.append(lavender_bed(doc, pal, rng, [12, 66, 128], [150, 176, 140], .2, .82, .45))
    scene.append(lavender_bed(doc, pal, rng, [1150, 1204, 1258], [150, 176, 140], .3, .82, .45))

    # -- cherry branches reaching in from the top
    scene.append(flora.sakura_branch(
        doc, pal, rng, (1300, 4), (1190, -6), (1070, 44), (896, 72), .2,
        twigs=[(.12, 115, 42), (.28, 72, 56), (.42, 122, 36), (.58, 84, 48), (.74, 136, 30), (.9, 100, 26)],
        width=6.5))
    scene.append(flora.sakura_branch(
        doc, pal, rng, (1300, 132), (1262, 120), (1214, 138), (1166, 160), .7,
        twigs=[(.45, 100, 20), (.85, 150, 16)], width=3.5))
    scene.append(flora.sakura_branch(
        doc, pal, rng, (292, -12), (330, 16), (380, 30), (452, 62), .45,
        twigs=[(.36, 98, 26), (.62, 62, 30), (.88, 112, 20)], width=4.5))

    # -- fragrance curling up from the beds
    for x, y, h, delay in [(70, 236, 130, 3.4), (214, 290, 110, 5.2), (150, 312, 116, 7.4),
                           (1040, 280, 120, 4.3), (1210, 240, 118, 6.3), (1118, 318, 104, 8.6)]:
        scene.append(place(x, y, flora.wisp(pal, rng, h, delay, rng.uniform(7.5, 10.5))))

    # -- left bed
    scene.append(lavender_bed(doc, pal, rng, [26, 50, 76, 102], [196, 238, 210, 172], .35))
    scene.append(flower_on_stem(doc, pal, rng, 96, 88, 332, "peony", 32, .7, "rose",
                                leaves=[(.3, -1, 28, 11), (.5, 1, 24, 10)], squash=.82, tilt=6))
    scene.extend(kikyo_bed(doc, pal, rng,
                           heads=[(150, 142, 270, 26), (206, 214, 306, 30), (264, 260, 252, 22), (326, 334, 334, 20)],
                           buds=[(182, 176, 226, 8), (292, 298, 300, 7)], delay=.6))
    scene.append(place(238, BASE_Y - 4, flora.gypsophila(pal, rng, 1.6, 6, 46)))
    scene.append(place(372, BASE_Y - 2, flora.gypsophila(pal, rng, 1.9, 5, 36)))
    scene.append(place(150, BASE_Y, flora.grass(pal, rng, .5, 7, 34)))
    scene.append(place(390, BASE_Y, flora.grass(pal, rng, 1.2, 5, 22)))

    # -- right bed
    scene.append(lavender_bed(doc, pal, rng, [1176, 1236, 1262], [182, 204, 150], .55))
    scene.extend(kikyo_bed(doc, pal, rng,
                           heads=[(998, 992, 300, 28), (1062, 1072, 262, 24), (1124, 1114, 322, 26), (934, 942, 348, 18)],
                           buds=[(1036, 1030, 236, 8), (1152, 1160, 296, 7)], delay=.9))
    scene.append(flower_on_stem(doc, pal, rng, 1204, 1212, 338, "peony", 34, 1.2, "rose",
                                leaves=[(.3, 1, 28, 11), (.5, -1, 24, 10)], squash=.84, tilt=-5))
    scene.append(place(966, BASE_Y - 2, flora.gypsophila(pal, rng, 2.0, 6, 40)))
    scene.append(place(1160, BASE_Y - 2, flora.gypsophila(pal, rng, 2.3, 5, 36)))
    scene.append(place(1060, BASE_Y, flora.grass(pal, rng, .9, 6, 30)))
    scene.append(place(900, BASE_Y, flora.grass(pal, rng, 1.5, 4, 20)))

    # -- a low border of small blossoms peeking up along the bottom
    for x, r, kind, hue, h in [(432, 7, "plum", "kikyo", 24), (455, 5.5, "sakura", "sakura", 13), (478, 8, "plum", "sakura", 30),
                               (500, 5, "plum", "peach", 11), (782, 5.5, "plum", "peach", 15), (806, 8, "sakura", "sakura", 27),
                               (830, 6.5, "plum", "kikyo", 20), (851, 5, "plum", "sakura", 10)]:
        scene.append(flower_on_stem(doc, pal, rng, x, x + rng.uniform(-4, 4), H - h, kind, r,
                                    2.3 + rng.uniform(0, .8), hue, squash=.85))
    scene.append(place(520, BASE_Y, flora.gypsophila(pal, rng, 2.6, 4, 22)))
    scene.append(place(762, BASE_Y, flora.gypsophila(pal, rng, 2.8, 4, 22)))

    # -- text
    scene.append(text_block(doc, pal, hero))

    # -- drifting sakura and pollen
    specs = [(rng.uniform(220, 1260), rng.uniform(-30, 90), rng.uniform(-240, 110), rng.uniform(330, 440))
             for _ in range(24)]
    scene.append(flora.falling_petals(doc, pal, rng, specs, 2.6))
    motes = []
    while len(motes) < 22:
        x, y = rng.uniform(30, W - 30), rng.uniform(30, H - 30)
        if TEXT_BOX[0] < x < TEXT_BOX[2] and TEXT_BOX[1] < y < TEXT_BOX[3]:
            continue
        motes.append(place(x, y, flora.mote(pal, rng, 2.5 + rng.uniform(0, 4))))
    scene.append("".join(motes))

    doc.add(f'<g clip-path="url(#{clip})">{"".join(scene)}</g>')
    doc.add(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="23.5" fill="none" stroke="{pal["border"]}"/>')
    return doc


def text_block(doc: Doc, pal: dict, hero: dict) -> str:
    light = pal["scheme"] == "light"
    parts = []
    label, _ = doc.text([(hero["corner"], "sans-bold", 20)], 40, 56, spacing=2, attrs=f' fill="{pal["ink"]}"')
    sub, _ = doc.text([(hero["corner_sub"], "sans", 13)], 40, 82, spacing=2.4, attrs=f' fill="{pal["ink2"]}"')
    parts.append(wrap("fadeup", label + sub, .3))

    eyebrow, width = doc.text([(hero["eyebrow"], "sans", 16)], CX, 124, anchor="middle", spacing=6,
                              attrs=f' fill="{pal["ink2"]}"')
    rule = []
    for side in (-1, 1):
        x0 = CX + side * (width / 2 + 16)
        rule.append(
            f'<path d="M{n(x0)} 119H{n(x0 + side * 40)}" stroke="{pal["ink3"]}" stroke-width="1"/>'
            f'<circle cx="{n(x0 + side * 45)}" cy="119" r="2.4" fill="{pal["sakura"][2]}"/>'
        )
    parts.append(wrap("fadeup", eyebrow + "".join(rule), 1.0))

    name_size = 94
    name_width = measure([(hero["title"], "serif-bold-italic", name_size)])
    grad = doc.linear(
        [(0, pal["ink"] if light else pal["kikyo"][5], 1),
         (.55, pal["kikyo"][1] if light else pal["kikyo"][3], 1),
         (1, pal["sakura"][0] if light else pal["sakura"][2], 1)],
        x1=CX - name_width / 2, y1=0, x2=CX + name_width / 2, y2=0, user=True,
    )
    name, _ = doc.text(
        [(hero["title"], "serif-bold-italic", name_size)], CX, 214, anchor="middle", inline=True,
        glyph_class="nm", glyph_delay=(1.2, .11), glyph_attrs=' pathLength="1"',
        attrs=f' fill="url(#{grad})" stroke="url(#{grad})" stroke-width=".8"',
    )
    parts.append(name)

    # ornament: a kikyo with tendrils drawn outward
    orn = []
    for side in (-1, 1):
        x0, x1 = CX + side * 18, CX + side * 150
        orn.append(
            f'<path class="grow" pathLength="1" d="M{n(x0)} 248C{n(x0 + side * 40)} 240 {n(x1 - side * 50)} 256 {n(x1)} 248" '
            f'fill="none" stroke="{pal["kikyo"][3]}" stroke-width="1" stroke-linecap="round"{flora.delay_style(2.7)}/>'
        )
        for k, t in enumerate((.35, .7)):
            lx = x0 + (x1 - x0) * t
            orn.append(place(lx, 248 + (2 if k else -2), flora.leaf(doc, pal, 9, 3.2, 3.2 + t),
                             rotate=side * 70 + (180 if k else 0)))
        orn.append(place(x1 + side * 6, 248, wrap("pop", f'<circle r="2.2" fill="{pal["sakura"][2]}"/>', 3.6)))
    orn.append(place(CX, 248, flora.flower(doc, pal, "kikyo", 10, 2.6, hue="kikyo")))
    parts.append("".join(orn))

    verse, _ = doc.text([(hero["verse"], "cjk", 27)], CX, 295, anchor="middle", spacing=9,
                        attrs=f' fill="{pal["ink"]}"')
    parts.append(wrap("fadeup", verse, 3.1))
    motto, _ = doc.text([(hero["motto"], "serif-italic", 23)], CX, 333, anchor="middle", spacing=.3,
                        attrs=f' fill="{pal["ink2"]}"')
    parts.append(wrap("fadeup", motto, 3.5))
    footer, _ = doc.text([(hero["footer"], "sans", 12)], CX, 378, anchor="middle", spacing=4.5,
                         attrs=f' fill="{pal["ink3"]}"')
    parts.append(wrap("fadeup", footer, 4.0))
    return "".join(parts)


def main() -> int:
    config = json.loads((ROOT / "garden.json").read_text(encoding="utf-8"))
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    for theme in ("light", "dark"):
        doc = build(theme, config)
        (out / f"hero-{theme}.svg").write_text(doc.render(animated=True), encoding="utf-8")
        (out / f"hero-static-{theme}.svg").write_text(doc.render(animated=False), encoding="utf-8")
        print(f"hero-{theme}.svg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
