"""Keep ALL custom profile visuals in the ink edition, not only the headings."""
from __future__ import annotations
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from garden import manga
from test_manga import sample

ROOT=Path(__file__).resolve().parent.parent
class InkEditionTest(unittest.TestCase):
    def test_both_themes_keep_positive_paper_and_ink(self):
        for theme,p in manga.THEMES.items():
            self.assertGreaterEqual(int(p['paper'][1:3],16),240,theme)
            self.assertLessEqual(int(p['ink'][1:3],16),32,theme)
    def test_mobile_keeps_the_drawn_bouquet(self):
        self.assertIn('data-ink-art="bouquet"',manga.bouquet_card('dark',sample(),True).render())
    def test_footer_is_also_an_ink_drawing(self):
        for theme in manga.THEMES:
            for mobile in (True,False):
                s=manga.footer(theme,mobile).render()
                self.assertIn('data-edition="ink-v2"',s)
                ET.fromstring(s)
    def test_all_custom_svg_references_use_new_namespace(self):
        readme=(ROOT/'README.md').read_text()
        refs=re.findall(r'(?:src|srcset)="(\./assets/[^\"]+)"',readme)
        self.assertTrue(refs)
        for ref in refs:
            if ref.endswith('.svg'):
                self.assertTrue(ref.startswith('./assets/ink-v2/'),ref)
    def test_all_custom_files_exist(self):
        readme=(ROOT/'README.md').read_text()
        refs=re.findall(r'(?:src|srcset)="(\./assets/[^\"]+\.svg)"',readme)
        for ref in refs:
            self.assertTrue((ROOT/ref).is_file(),ref)
    def test_all_generated_svg_use_neutral_ink_without_light_effects(self):
        files=list((ROOT/'assets'/'ink-v2').rglob('*.svg'))
        self.assertTrue(files)
        for path in files:
            s=path.read_text(encoding='utf-8');ET.fromstring(s)
            self.assertIn('data-edition="ink-v2"',s,path.name)
            for needle in ('<filter','<linearGradient','<radialGradient','<foreignObject','<script','<image','@font-face'):
                self.assertNotIn(needle,s,path.name)
            for c in re.findall(r'#[0-9a-fA-F]{6}\b',s):
                self.assertEqual(c[1:3].lower(),c[3:5].lower(),path.name)
                self.assertEqual(c[3:5].lower(),c[5:7].lower(),path.name)

if __name__=='__main__':unittest.main()
