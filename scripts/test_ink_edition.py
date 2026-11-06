"""Keep ALL custom profile visuals in the coloured ink edition, not only the headings."""

from __future__ import annotations
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from garden import manga
from test_manga import sample

ROOT = Path(__file__).resolve().parent.parent


class InkEditionTest(unittest.TestCase):
    def test_both_themes_keep_positive_paper_and_ink(self):
        for theme, p in manga.THEMES.items():
            for j in (1, 3, 5):
                self.assertGreaterEqual(int(p["paper"][j : j + 2], 16), 240, theme)
                self.assertLessEqual(int(p["ink"][j : j + 2], 16), 64, theme)

    def test_mobile_keeps_the_drawn_bouquet(self):
        self.assertIn('data-ink-art="bouquet"', manga.bouquet_card("dark", sample(), True).render())

    def test_footer_is_also_an_ink_drawing(self):
        for theme in manga.THEMES:
            for mobile in (True, False):
                s = manga.footer(theme, mobile).render()
                self.assertIn('data-edition="ink-v2"', s)
                ET.fromstring(s)

    def test_readme_only_references_generated_folders(self):
        readme = (ROOT / "README.md").read_text()
        refs = re.findall(r'(?:src|srcset)="(\./assets/[^\"]+\.svg)"', readme)
        self.assertTrue(refs)
        for ref in refs:
            self.assertRegex(ref, r"^\./assets/(sections|metrics|repos)/")

    def test_all_custom_files_exist(self):
        readme = (ROOT / "README.md").read_text()
        refs = re.findall(r'(?:src|srcset)="(\./assets/[^\"]+\.svg)"', readme)
        for ref in refs:
            self.assertTrue((ROOT / ref).is_file(), ref)

    def test_all_generated_svg_use_flat_colour_without_light_effects(self):
        files = list((ROOT / "assets").rglob("*.svg"))
        self.assertTrue(files)
        for path in files:
            s = path.read_text(encoding="utf-8")
            ET.fromstring(s)
            self.assertIn('data-edition="ink-v2"', s, path.name)
            for needle in (
                "<filter",
                "<linearGradient",
                "<radialGradient",
                "<foreignObject",
                "<script",
                "<image",
                "@font-face",
            ):
                self.assertNotIn(needle, s, path.name)
            colors = {c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b", s)}
            self.assertIn(manga.THEMES["light"]["ink"], colors, path.name)
            self.assertTrue(any(c[1:3] != c[3:5] or c[3:5] != c[5:7] for c in colors), path.name)


if __name__ == "__main__":
    unittest.main()
