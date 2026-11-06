"""Rebuild the fixed heading lettering (garden/manga_lettering.json) from a script font.

The SVGs never embed a font: each heading becomes one outline path, in units
where 1000 = 1 em, y pointing up from the baseline (manga.title flips it).
Only needed when the heading font or the list of headings changes.

    python3 scripts/build_lettering.py [fonts/GreatVibes-Regular.ttf]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'scripts' / 'garden' / 'manga_lettering.json'
FONT = ROOT / 'fonts' / 'GreatVibes-Regular.ttf'
WORD_GAP = .16  # extra em between words


def kerning(font: TTFont) -> dict[tuple[str, str], int]:
    """Plain pair kerning from GPOS format 1 subtables (enough for headings)."""
    pairs: dict[tuple[str, str], int] = {}
    if 'GPOS' not in font:
        return pairs
    for lookup in font['GPOS'].table.LookupList.Lookup:
        for sub in lookup.SubTable:
            sub = getattr(sub, 'ExtSubTable', sub)
            if getattr(sub, 'LookupType', None) != 2 or sub.Format != 1:
                continue
            firsts = sub.Coverage.glyphs
            for first, pairset in zip(firsts, sub.PairSet):
                for rec in pairset.PairValueRecord:
                    value = getattr(rec.Value1, 'XAdvance', 0) if rec.Value1 else 0
                    if value:
                        pairs.setdefault((first, rec.SecondGlyph), value)
    return pairs


def compose(font: TTFont, label: str, kern: dict) -> dict:
    cmap, glyphs, hmtx = font.getBestCmap(), font.getGlyphSet(), font['hmtx']
    scale = 1000 / font['head'].unitsPerEm
    pen = SVGPathPen(glyphs, ntos=lambda v: f'{round(v)}')
    x, previous = 0.0, None
    for char in label:
        name = cmap.get(ord(char))
        if name is None:
            raise SystemExit(f'{char!r} is missing from the font')
        if previous:
            x += kern.get((previous, name), 0)
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, scale, x * scale, 0)))
        x += hmtx[name][0]
        if char == ' ':
            # Script capitals swash into the gap; open it up so words stay apart.
            x += WORD_GAP * font['head'].unitsPerEm
        previous = name
    return {'path': pen.getCommands(), 'advance': float(round(x * scale)), 'units': 1000}


def main(argv: list[str]) -> int:
    font = TTFont(argv[0] if argv else FONT)
    labels = list(json.loads(OUT.read_text(encoding='utf-8')))
    kern = kerning(font)
    OUT.write_text(json.dumps({label: compose(font, label, kern) for label in labels},
                              ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'{OUT.name}: {len(labels)} headings')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
