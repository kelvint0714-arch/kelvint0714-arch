"""Render the README section headers.

Writes assets/sections/header-<id>-{light,dark}.svg from the sections in
garden.json: a pill tag, the title with its Japanese name, a cherry sprig that
draws itself under the title, and a seed-packet label on the right.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from garden import depth, flora  # noqa: E402
from garden.flora import place, wrap  # noqa: E402
from garden.palette import THEMES  # noqa: E402
from garden.svg import Doc, n  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H = 1280, 180


def build(theme: str, section: dict, index: int) -> Doc:
    pal = THEMES[theme]
    light = pal["scheme"] == "light"
    rng = random.Random(1000 + index)
    doc = Doc(
        W, H,
        title=f"Section {section['number']}. {section['title']} · {section['title_ja']}",
        desc=f"{section['subtitle'].capitalize()} · {section['subtitle_ja']}. {section['flora']}.",
    )
    flora.install(doc)
    parts = []

    # pill tag, pressed out of the page
    pill_text = f"SECTION {section['number']}"
    _, tag_w = doc.text([(pill_text, "sans-bold", 16)], 0, 0, spacing=3.5)
    pill_w = tag_w + 48
    tag, _ = doc.text([(pill_text, "sans-bold", 16)], 2 + pill_w / 2, 36, anchor="middle", spacing=3.5,
                      attrs=' fill="#FFFFFF"')
    pill = depth.button(doc, pal, 2, 10, pill_w, 36) + tag
    pill += place(pill_w + 26, 30, flora.flower(doc, pal, "kikyo", 10, .5, hue="kikyo"))
    parts.append(wrap("fadeup", pill, .1))

    # extruded title and its Japanese name
    side = [pal["kikyo"][3], pal["kikyo"][2], pal["kikyo"][1]] if light else [pal["kikyo"][1], pal["kikyo"][0], "#2A2768"]
    title, title_w = depth.text3d(doc, pal, [(section["title"], "serif-bold", 66)], 0, 106, spacing=1.5,
                                  face=pal["ink"], side=side, depth=5)
    ja_side = [pal["sakura"][2], pal["sakura"][1], pal["sakura"][0]] if light else [pal["sakura"][1], pal["sakura"][0], "#6B2E55"]
    ja, ja_w = depth.text3d(doc, pal, [(section["title_ja"], "cjk-bold", 38)], title_w + 30, 103, spacing=5,
                            face=pal["kikyo"][1] if light else pal["kikyo"][4], side=ja_side, depth=4, step=(.6, .8))
    parts.append(wrap("fadeup", title + ja, .3))

    # a cherry sprig drawn under the title, flowering at its tip
    end = max(720.0, title_w + ja_w + 120)
    vine = f"M2 126C{n(end * .25)} 118 {n(end * .5)} 134 {n(end * .75)} 124S{n(end - 30)} 120 {n(end)} 126"
    sprig = [
        f'<path class="grow" pathLength="1" d="{vine}" transform="translate(3 7)" fill="none" stroke="{pal["shadow"]}" '
        f'stroke-opacity=".12" stroke-width="3.4" stroke-linecap="round"{flora.delay_style(.6)}/>',
        f'<path class="grow" pathLength="1" d="{vine}" fill="none" stroke="{pal["bark"]}" stroke-width="2.4" '
        f'stroke-linecap="round"{flora.delay_style(.6)}/>',
        f'<path class="grow" pathLength="1" d="{vine}" transform="translate(-.4 -.8)" fill="none" stroke="#FFFFFF" '
        f'stroke-opacity=".35" stroke-width=".8" stroke-linecap="round"{flora.delay_style(.6)}/>',
    ]
    for k in range(5):
        x = end * (.16 + k * .17)
        side = -1 if k % 2 else 1
        sprig.append(place(x, 125, flora.leaf(doc, pal, 12, 4.2, 1 + k * .2), rotate=side * 60 + (0 if side < 0 else 180)))
    for k, (dx, dy, r) in enumerate([(0, 0, 11), (-16, 9, 8), (14, 10, 7)]):
        head = flora.flower(doc, pal, "sakura", r, 2.0 + k * .2, hue="sakura", tilt=rng.uniform(0, 72))
        sprig.append(place(end + dx, 126 + dy, wrap("breathe", head, -rng.uniform(0, 6))))
    sprig.append(place(end + 26, 124, flora.balloon(doc, pal, 5.5, 2.6), rotate=80))
    parts.append("".join(sprig))

    # subtitle
    sub, sub_w = doc.text([(section["subtitle"], "sans", 17)], 2, 162, spacing=2.6, attrs=f' fill="{pal["ink2"]}"')
    sub_ja, _ = doc.text([(section["subtitle_ja"], "cjk", 21)], sub_w + 24, 163, spacing=2,
                         attrs=f' fill="{pal["ink2"]}"')
    parts.append(wrap("fadeup", sub + sub_ja, .9))

    # seed-packet label on the right
    label, label_w = doc.text([(section["flora"], "sans-bold", 19)], 0, 0, spacing=2.4)
    box_w = label_w + 56
    x0 = W - 14 - box_w
    label, _ = doc.text([(section["flora"], "sans-bold", 19)], x0 + box_w / 2, 105, anchor="middle", spacing=2.4,
                        attrs=f' fill="{pal["ink"]}"')
    packet = (
        depth.raised(doc, pal, x0, 72, box_w, 52, rx=12, lift=.7)
        + f'<rect x="{n(x0 + 6)}" y="78" width="{n(box_w - 12)}" height="40" rx="8" fill="none" '
          f'stroke="{pal["kikyo"][3]}" stroke-dasharray="5 4"/>{label}'
    )
    parts.append(wrap("fadeup", packet, .5))
    for k in range(6):
        kind, hue = (("sakura", "sakura") if k % 2 else ("kikyo", "kikyo"))
        parts.append(place(W - 16 - k * 30, 38, flora.flower(doc, pal, kind, 9.5, 1.0 + (5 - k) * .15, hue=hue)))

    specs = [(rng.uniform(900, 1250), rng.uniform(-20, 20), rng.uniform(-120, -40), rng.uniform(150, 200))
             for _ in range(4)]
    parts.append(flora.falling_petals(doc, pal, rng, specs, 2.5))

    doc.add("".join(parts))
    return doc


def main() -> int:
    config = json.loads((ROOT / "garden.json").read_text(encoding="utf-8"))
    out = ROOT / "assets" / "sections"
    out.mkdir(parents=True, exist_ok=True)
    for index, section in enumerate(config["sections"]):
        for theme in ("light", "dark"):
            path = out / f"header-{section['id']}-{theme}.svg"
            path.write_text(build(theme, section, index).render(animated=True), encoding="utf-8")
            print(path.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
