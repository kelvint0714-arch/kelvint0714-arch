"""Manga redraw regression tests. Offline fixtures are never saved as user data."""
from __future__ import annotations
import copy
import json
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_metrics
import update_repositories as repos
from garden import manga

NS={'s':'http://www.w3.org/2000/svg'}
def sample():
    return dict(user='fixture',fetched_at='2026-10-15T00:00:00Z',
                calendar=dict(total=9,days=[['2026-10-12',1,1],['2026-10-13',4,8],['2026-10-14',0,0]]),
                repos=[],languages={'Python':300,'CSS':100},events=[])

def repository(**kwargs):
    r={'name':'sample','html_url':'https://github.com/fixture/sample','description':'A plain test description','language':'Python','stargazers_count':3,'pushed_at':'2026-10-15T00:00:00Z','fork':False,'archived':False}
    r.update(kwargs);return r

class MangaTest(unittest.TestCase):
    def test_calendar_preserves_dates_counts_and_levels(self):
        snap=sample()
        for theme in manga.THEMES:
            for mobile in (False,True):
                root=ET.fromstring(manga.calendar_card(theme,snap,mobile).render())
                actual=sorted((e.attrib['data-date'],int(e.attrib['data-level']),int(e.attrib['data-count'])) for e in root.iter() if 'data-date' in e.attrib)
                self.assertEqual(actual,[tuple(d) for d in snap['calendar']['days']])
    def test_language_exact_byte_shares(self):
        for mobile in (False,True):
            root=ET.fromstring(manga.bouquet_card('light',sample(),mobile).render())
            bars=[e for e in root.iter() if 'data-language' in e.attrib]
            self.assertEqual([(e.attrib['data-language'],int(e.attrib['data-bytes']),float(e.attrib['data-share'])) for e in bars],[('Python',300,.75),('CSS',100,.25)])
    def test_other_keeps_total(self):
        snap=sample();snap['languages']={f'Language{i}':i+1 for i in range(9)}
        root=ET.fromstring(manga.bouquet_card('light',snap).render())
        bars=[e for e in root.iter() if 'data-bytes' in e.attrib]
        self.assertEqual(len(bars),6);self.assertEqual(sum(int(e.attrib['data-bytes']) for e in bars),45)
    def test_every_color_is_monochrome(self):
        for theme in manga.THEMES:
            docs=[manga.calendar_card(theme,sample()),manga.bouquet_card(theme,sample()),manga.repo_card(theme,repository(),0),manga.header(theme,{'number':'01','title':'PROJECT GARDEN'},0)]
            for doc in docs:
                colors=re.findall(r'#[0-9a-fA-F]{6}\b',doc.render())
                self.assertTrue(colors)
                for c in colors:self.assertEqual(c[1:3].lower(),c[3:5].lower());self.assertEqual(c[3:5].lower(),c[5:7].lower())
    def test_no_blur_gradients_external_fonts_or_scripts(self):
        rendered=manga.header('light',{'number':'01','title':'PROJECT GARDEN'},0).render()
        for needle in ('<filter','<script','<foreignObject','<linearGradient','<radialGradient','@font-face','data:font'):
            self.assertNotIn(needle,rendered)
    def test_all_local_paint_references_resolve(self):
        doc=manga.bouquet_card('dark',sample());root=ET.fromstring(doc.render())
        ids={e.attrib['id'] for e in root.iter() if 'id' in e.attrib}
        for ref in re.findall(r'url\(#([^)]*)\)',doc.render()):self.assertIn(ref,ids)
    def test_drawings_are_deterministic(self):
        a=manga.header('light',{'number':'01','title':'PROJECT GARDEN'},0).render()
        b=manga.header('light',{'number':'01','title':'PROJECT GARDEN'},0).render()
        self.assertEqual(a,b)
    def test_empty_states_are_valid(self):
        snap=sample();snap['calendar']={'total':0,'days':[]};snap['languages']={}
        for doc in (manga.calendar_card('light',snap,True),manga.bouquet_card('dark',snap),manga.notes_card('light',snap,[],'UTC')):ET.fromstring(doc.render())
    def test_strings_are_xml_escaped(self):
        r=repository(name='A&B<>',description='Text <script> & "quotes"')
        root=ET.fromstring(manga.repo_card('light',r,0).render())
        self.assertEqual(root.find('s:title',NS).text,'A&B<>')
    def test_html_is_escaped_and_card_links_are_real(self):
        with tempfile.TemporaryDirectory() as td:
            body=repos.cards([repository(name='A&B',description='<script>alert(1)</script>')],Path(td))
            self.assertIn('<a href="https://github.com/fixture/sample">',body)
            self.assertIn('&lt;script&gt;',body);self.assertNotIn('<script>',body)
            self.assertIn('<details>',body)
            self.assertEqual(len(list(Path(td).glob('*.svg'))),4)
    def test_unsafe_links_rejected(self):
        with self.assertRaises(ValueError):repos.safe_link('javascript:alert(1)')
    def test_private_repositories_excluded(self):
        with tempfile.TemporaryDirectory() as td:
            body=repos.cards([repository(name='secret-repo',private=True)],Path(td))
            self.assertNotIn('secret-repo',body);self.assertFalse(list(Path(td).glob('*.svg')))
    def test_old_generated_panels_cleaned_but_other_files_kept(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);(out/'custom.svg').write_text('keep')
            repos.cards([repository(name='old')],out);repos.cards([repository(name='new')],out)
            self.assertFalse(list(out.glob('old-*.svg')));self.assertTrue((out/'custom.svg').exists())
    def test_slug_names_are_safe_and_collision_resistant(self):
        for name in ('A/B','../secret','a|b','<script>'):
            slug=manga.repo_slug(repository(name=name));self.assertRegex(slug,r'^[a-z0-9-]+$')
        self.assertNotEqual(manga.repo_slug(repository(name='A/B')),manga.repo_slug(repository(name='A|B')))
    def test_invalid_markers_do_not_overwrite(self):
        for doc in ('missing',repos.START+repos.START+repos.END,repos.END+repos.START):
            with self.assertRaises(ValueError):repos.replace_block(doc,'new')
    def test_snapshot_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'snapshot.json';s=sample();p.write_text(json.dumps(s))
            with patch.object(build_metrics,'SNAPSHOT',p),patch.object(build_metrics,'ROOT',Path(td)),patch.object(build_metrics.data,'collect',side_effect=OSError('test network failure')):
                self.assertEqual(build_metrics.load_snapshot('fixture',False),s)
    def test_no_input_mutation(self):
        s=sample();before=copy.deepcopy(s)
        manga.calendar_card('light',s);manga.bouquet_card('dark',s)
        self.assertEqual(s,before)
    def test_responsive_picture_has_four_variants(self):
        html=manga.picture('./assets/example','a test')
        for ending in ('-light.svg','-dark.svg','-light-mobile.svg','-dark-mobile.svg'):self.assertIn(ending,html)
        self.assertIn('max-width: 600px',html)
    def test_long_descriptions_fit_without_losing_accessible_source(self):
        description='很长的说明文字 and a_long_identifier_'*15
        r=repository(description=description)
        doc=manga.repo_card('light',r,0,True)
        root=ET.fromstring(doc.render());self.assertIn(description,root.find('s:desc',NS).text)
        for line in manga.wrap(description,17,420,3):self.assertLessEqual(manga.text_width(line,17),421)
    def test_future_repository_keeps_its_name(self):
        doc=manga.repo_card('dark',repository(name='brand-new-work'),5)
        self.assertIn('brand-new-work',doc.render());self.assertIn('Repository',doc.render())

if __name__=='__main__':unittest.main()
