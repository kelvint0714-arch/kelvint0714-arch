"""Render softly raised chapter lettering with a loose, layered flower sprig.

Writes assets/sections/header-<id>-{light,dark}.svg from garden.json. The
transparent composition uses a little pastel light instead of a card frame;
curving stems and tilted blooms carry the eye out from beneath the title.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from garden import depth, flora  # noqa: E402
from garden.flora import place, wrap  # noqa: E402
from garden.palette import THEMES  # noqa: E402
from garden.svg import Doc  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H = 960, 186


def build(theme: str, section: dict, index: int) -> Doc:
    pal = THEMES[theme]
    doc = Doc(
        W, H,
        title=f"Section {section['number']}. {section['title']} · {section['title_ja']}",
        desc=f"{section['subtitle'].capitalize()} · {section['subtitle_ja']}.",
    )
    flora.install(doc)
    light = pal["scheme"] == "light"

    # These feathered pools of light disappear into the page rather than
    # enclosing the heading in another rectangular panel.
    petal_glow = doc.radial([
        (0, pal["glow"], .4 if light else .27),
        (.46, pal["glow"], .18 if light else .12),
        (1, pal["glow"], 0),
    ])
    seal_glow = doc.radial([
        (0, pal["kikyo"][3], .24 if light else .15),
        (.55, pal["kikyo"][3], .08),
        (1, pal["kikyo"][3], 0),
    ])
    parts = [
        f'<ellipse cx="829" cy="102" rx="129" ry="82" fill="url(#{petal_glow})"/>',
        f'<ellipse cx="54" cy="81" rx="49" ry="51" fill="url(#{seal_glow})"/>',
    ]

    # An irregular, shallow medallion has a soft lower edge and a little
    # upper-left light. It reads as a petal pressed around the folio number.
    seal_fill = doc.linear([
        (0, pal["cream"][0] if light else pal["planter"][0], 1),
        (.52, pal["card"], 1),
        (1, pal["sakura"][4] if light else pal["planter"][1], 1),
    ], x1=.08, y1=.02, x2=.9, y2=1)
    seal_shape = "M-25 1C-30-16-13-30 5-28C24-28 34-10 29 8C26 28 7 35-11 28C-25 23-31 12-25 1Z"
    seal = (
        f'<path d="{seal_shape}" transform="translate(.8 2)" fill="{pal["shadow"]}" '
        f'fill-opacity="{.12 if light else .28}"/>'
        f'<path d="{seal_shape}" fill="url(#{seal_fill})" stroke="{pal["border"]}" '
        f'stroke-opacity=".45" stroke-width=".65"/>'
        f'<path d="M-22-3C-24-18-10-27 5-25C13-25 19-21 22-17" fill="none" '
        f'stroke="{pal["cream"][0]}" stroke-opacity="{.68 if light else .13}" '
        f'stroke-width="1.2" stroke-linecap="round"/>'
    )
    number, _ = depth.text3d(
        doc, pal, [(str(section["number"]), "serif-bold", 26)], 0, 8,
        anchor="middle", spacing=1.1, face=pal["ink2"],
        side=[pal["rose"][2], pal["rose"][4]], depth=2, step=(.18, .26), shadow=False,
    )
    parts.append(place(54, 77, wrap("fadeup", seal + number, .04), rotate=-5))

    # The shared text renderer supplies a fine bevel and contact shadow,
    # keeping the depth shallow enough for the serif strokes to stay clear.
    title, title_w = depth.text3d(
        doc, pal, [(section["title"].title(), "serif-bold", 50)], 104, 84,
        spacing=.3, face=pal["ink"],
        side=[pal["kikyo"][2], pal["kikyo"][3], pal["kikyo"][4]],
        depth=3, step=(.28, .43),
    )
    ja, _ = depth.text3d(
        doc, pal, [(section["title_ja"], "cjk", 24)], 132 + title_w, 80,
        spacing=3.2, face=pal["ink2"],
        side=[pal["rose"][2], pal["rose"][3]], depth=2, step=(.2, .3), shadow=False,
    )
    sub, sub_w = doc.text(
        [(section["subtitle"].capitalize(), "sans", 13)], 107, 121,
        spacing=.55, attrs=f' fill="{pal["ink2"]}"',
    )
    sub_ja, _ = doc.text(
        [(section["subtitle_ja"], "cjk", 14.5)], 129 + sub_w, 122,
        spacing=1.1, attrs=f' fill="{pal["ink2"]}"',
    )
    parts.append(wrap("fadeup", title + ja + sub + sub_ja, .08))

    # The long, loose stem curves below both text rows. Shorter branches
    # arc behind the flowers rather than arranging them into a straight row.
    stems = (
        "M146 151C246 173 377 134 479 151C572 169 657 173 730 140"
        "C777 119 811 117 829 90"
        "M756 129C780 142 800 143 799 124"
        "M800 116C827 139 857 137 862 119"
        "M816 108C845 111 843 75 850 60"
        "M855 135C887 146 909 116 887 91"
    )
    sprig = [
        f'<path d="{stems}" transform="translate(.8 1.6)" fill="none" '
        f'stroke="{pal["shadow"]}" stroke-opacity="{.1 if light else .2}" '
        f'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>',
        f'<path d="{stems}" fill="none" stroke="{pal["stem"]}" stroke-opacity=".72" '
        f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>',
        f'<path d="{stems}" transform="translate(-.25 -.5)" fill="none" '
        f'stroke="{pal["cream"][0]}" stroke-opacity="{.45 if light else .13}" '
        f'stroke-width=".5" stroke-linecap="round" stroke-linejoin="round"/>',
    ]

    for x, y, length, width, angle in (
        (290, 155, 15, 4.5, -55),
        (446, 146, 14, 4, 73),
        (649, 158, 22, 6.5, -51),
        (735, 138, 24, 7, 49),
        (794, 120, 27, 7.5, -40),
        (836, 77, 22, 6, -61),
        (845, 137, 25, 7.5, 105),
        (886, 143, 24, 6.5, 69),
        (902, 110, 19, 5.5, 38),
    ):
        sprig.append(place(x, y, flora.leaf(doc, pal, length, width, .2), rotate=angle))

    main_kind = "peony" if index % 2 == 0 else "sakura"
    companion_kind = "sakura" if index % 2 == 0 else "peony"
    # Warm pink blooms form one overlapping cluster. Smaller, paler rear
    # flowers suggest distance; violet appears only in a small companion.
    # The large rounded foreground flower has one slow breathing motion.
    flowers = (
        (850, 60, "sakura", "sakura", 22, 19, .7, .86),
        (887, 91, "kikyo", "kikyo", 17, -24, .78, .78),
        (799, 124, "sakura", "sakura", 20, -18, .82, .95),
        (862, 119, companion_kind, "rose", 29, 24, .88, 1),
    )
    for x, y, kind, hue, radius, tilt, squash, opacity in flowers:
        bloom = flora.flower(
            doc, pal, kind, radius, 0, hue=hue, tilt=tilt,
            squash=squash, still=True, shadow=True,
        )
        sprig.append(place(x, y, f'<g opacity="{opacity}">{bloom}</g>'))
    front = flora.flower(
        doc, pal, main_kind, 36 if index % 2 == 0 else 35, .35, hue="sakura",
        tilt=-12 + index * 5, squash=.9, still=False, shadow=True,
    )
    sprig.append(place(829, 90, wrap("breathe", front, -1.7 - index)))
    parts.append(wrap("fadeup", "".join(sprig), .2))

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
