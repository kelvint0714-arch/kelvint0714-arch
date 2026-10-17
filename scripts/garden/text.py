"""Text set as glyph outlines.

An SVG shown through <img> cannot load web fonts, and letter-spacing on SVG
text is not rendered the same everywhere, so every label is drawn from the
fonts in fonts/ as <use> references to glyph paths. Pair kerning is read from
the GPOS 'kern' feature.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

FONTS = Path(__file__).resolve().parents[2] / "fonts"

FILES = {
    "serif": "CormorantGaramond-Medium.ttf",
    "serif-bold": "CormorantGaramond-SemiBold.ttf",
    "serif-italic": "CormorantGaramond-MediumItalic.ttf",
    "serif-bold-italic": "CormorantGaramond-SemiBoldItalic.ttf",
    "sans": "Montserrat-Medium.ttf",
    "sans-bold": "Montserrat-SemiBold.ttf",
    "cjk": "NotoSerifJP-Medium-subset.ttf",
    "cjk-bold": "NotoSerifJP-SemiBold-subset.ttf",
}
# Characters missing from a face are taken from its partner.
FALLBACK = {
    "serif": "cjk",
    "serif-bold": "cjk-bold",
    "serif-italic": "cjk",
    "serif-bold-italic": "cjk-bold",
    "sans": "cjk",
    "sans-bold": "cjk-bold",
    "cjk": "sans",
    "cjk-bold": "sans-bold",
}


class Face:
    def __init__(self, key: str) -> None:
        self.key = key
        self.font = TTFont(FONTS / FILES[key])
        self.upm = self.font["head"].unitsPerEm
        self.cmap = self.font.getBestCmap()
        self.glyphs = self.font.getGlyphSet()
        self.hmtx = self.font["hmtx"]
        self._kern_tables = _kern_subtables(self.font)
        self._kern_cache: dict[tuple[str, str], int] = {}

    def glyph(self, char: str) -> str | None:
        return self.cmap.get(ord(char))

    def advance(self, glyph: str) -> int:
        return self.hmtx[glyph][0]

    def kern(self, left: str, right: str) -> int:
        key = (left, right)
        if key not in self._kern_cache:
            self._kern_cache[key] = _lookup_kern(self._kern_tables, left, right)
        return self._kern_cache[key]

    @lru_cache(maxsize=None)
    def outline(self, glyph: str) -> str:
        pen = SVGPathPen(self.glyphs, ntos=lambda v: str(round(v)))
        self.glyphs[glyph].draw(pen)
        return pen.getCommands()


def _kern_subtables(font: TTFont) -> list:
    if "GPOS" not in font:
        return []
    gpos = font["GPOS"].table
    indices: set[int] = set()
    for record in gpos.FeatureList.FeatureRecord:
        if record.FeatureTag == "kern":
            indices.update(record.Feature.LookupListIndex)
    tables = []
    for index in sorted(indices):
        lookup = gpos.LookupList.Lookup[index]
        for sub in lookup.SubTable:
            if lookup.LookupType == 9:
                if sub.ExtensionLookupType != 2:
                    continue
                sub = sub.ExtSubTable
            elif lookup.LookupType != 2:
                continue
            coverage = {g: i for i, g in enumerate(sub.Coverage.glyphs)}
            if sub.Format == 1:
                pairs = {}
                for glyph, i in coverage.items():
                    for record in sub.PairSet[i].PairValueRecord:
                        value = getattr(record.Value1, "XAdvance", 0) if record.Value1 else 0
                        pairs[(glyph, record.SecondGlyph)] = value or 0
                tables.append((1, coverage, pairs))
            elif sub.Format == 2:
                tables.append((2, coverage, sub))
    return tables


def _lookup_kern(tables: list, left: str, right: str) -> int:
    for fmt, coverage, data in tables:
        if left not in coverage:
            continue
        if fmt == 1:
            if (left, right) in data:
                return data[(left, right)]
            continue
        class1 = data.ClassDef1.classDefs.get(left, 0)
        class2 = data.ClassDef2.classDefs.get(right, 0)
        record = data.Class1Record[class1].Class2Record[class2]
        value = getattr(record.Value1, "XAdvance", 0) if record.Value1 else 0
        return value or 0
    return 0


@lru_cache(maxsize=None)
def face(key: str) -> Face:
    return Face(key)


@dataclass
class Glyph:
    face: Face
    name: str
    x: float  # pen position in px from the run's origin
    size: float
    char: str


def layout(segments: list[tuple[str, str, float]], spacing: float = 0.0) -> tuple[list[Glyph], float]:
    """Place (text, face, size) segments on one baseline.

    `spacing` is extra tracking in px after every character except the last.
    Returns the glyphs and the run width in px.
    """
    placed: list[Glyph] = []
    pen = 0.0
    previous: tuple[Face, str] | None = None
    for text, key, size in segments:
        for char in text:
            primary = face(key)
            chosen = primary if primary.glyph(char) else face(FALLBACK[key])
            name = chosen.glyph(char)
            if name is None:
                raise SystemExit(
                    f"'{char}' (U+{ord(char):04X}) is not in the {key} fonts; run scripts/fetch_fonts.py"
                )
            scale = size / chosen.upm
            if previous and previous[0] is chosen:
                pen += chosen.kern(previous[1], name) * scale
            placed.append(Glyph(chosen, name, pen, size, char))
            pen += chosen.advance(name) * scale + spacing
            previous = (chosen, name)
    width = pen - spacing if placed else 0.0
    return placed, width


def measure(segments: list[tuple[str, str, float]], spacing: float = 0.0) -> float:
    return layout(segments, spacing)[1]
