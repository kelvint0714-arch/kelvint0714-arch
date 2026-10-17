"""Offline regression checks for the calendar-only dimensional ink patch."""
from __future__ import annotations
import copy
from datetime import date, timedelta
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from garden import calendar3d, manga
import build_metrics


def sample(length=371, dense=False):
    start = date(2025, 10, 12)
    days = []
    for k in range(length):
        level = 4 if dense else k % 5
        days.append([(start+timedelta(days=k)).isoformat(), level, level*2])
    return {'user':'fixture','calendar':{'total':sum(d[2] for d in days),'days':days},
            'fetched_at':'2026-10-17T09:47:03Z','languages':{'Python':100,'CSS':20},
            'events':[],'repos':[]}


def nodes(markup):
    return [e for e in ET.fromstring(markup).iter() if 'data-date' in e.attrib]


class Calendar3DTest(unittest.TestCase):
    def test_every_date_count_level_preserved_in_all_variants(self):
        snap = sample()
        for theme in ('light','dark'):
            for mobile in (False,True):
                s = calendar3d.calendar_card(theme,snap,mobile).render()
                actual = sorted((e.attrib['data-date'],int(e.attrib['data-level']),int(e.attrib['data-count'])) for e in nodes(s))
                self.assertEqual(actual,[tuple(d) for d in snap['calendar']['days']])
    def test_no_input_mutation(self):
        snap=sample();old=copy.deepcopy(snap)
        calendar3d.calendar_card('light',snap,True).render()
        self.assertEqual(snap,old)
    def test_weekdays_are_still_sunday_first(self):
        for e in nodes(calendar3d.calendar_card('light',sample(),True).render()):
            expected=(date.fromisoformat(e.attrib['data-date']).weekday()+1)%7
            self.assertEqual(int(e.attrib['data-weekday']),expected)
    def test_mobile_371_days_in_two_bands_without_overlap(self):
        ns=nodes(calendar3d.calendar_card('light',sample(),True).render())
        self.assertEqual(len(ns),371)
        groups={band:sorted(e.attrib['data-date'] for e in ns if int(e.attrib['data-band'])==band) for band in (0,1)}
        self.assertLess(groups[0][-1],groups[1][0])
        self.assertEqual(len(groups[0]),189)
        self.assertEqual(len(groups[1]),182)
    def test_very_long_ranges_are_not_truncated(self):
        snap=sample(550)
        for mobile in (True,False):
            self.assertEqual(len(nodes(calendar3d.calendar_card('light',snap,mobile).render())),550)
    def test_366_days_kept_including_leap_day(self):
        s=sample(366)
        s['calendar']['days']=[[(date(2028,1,1)+timedelta(days=k)).isoformat(),a[1],a[2]] for k,a in enumerate(s['calendar']['days'])]
        actual=[e.attrib['data-date'] for e in nodes(calendar3d.calendar_card('light',s).render())]
        self.assertIn('2028-02-29',actual);self.assertEqual(len(actual),366)
    def test_empty_calendar_is_valid(self):
        snap=sample(0)
        for mobile in (True,False):
            rendered=calendar3d.calendar_card('dark',snap,mobile).render()
            self.assertEqual(nodes(rendered),[])
            self.assertIn('The first seeds are still waiting.',rendered)
    def test_dense_calendar_is_valid(self):
        s=calendar3d.calendar_card('dark',sample(dense=True),True).render()
        self.assertEqual(len(nodes(s)),371)
    def test_black_white_without_gradients_blur_or_external_dependencies(self):
        s=calendar3d.calendar_card('dark',sample(8)).render()
        for needle in ('<filter','<linearGradient','<radialGradient','<image','<script','<foreignObject','@font-face','data:font','<animate'):
            self.assertNotIn(needle,s)
        for c in re.findall(r'#[\da-fA-F]{6}\b',s):
            self.assertEqual(c[1:3],c[3:5]);self.assertEqual(c[3:5],c[5:7])
    def test_both_themes_are_the_same_positive_ink_drawing(self):
        self.assertEqual(calendar3d.calendar_card('light',sample(5)).render(),calendar3d.calendar_card('dark',sample(5)).render())
    def test_all_svg_ids_are_unique_and_paint_refs_resolve(self):
        s=calendar3d.calendar_card('light',sample()).render()
        ids=[e.attrib['id'] for e in ET.fromstring(s).iter() if 'id' in e.attrib]
        self.assertEqual(len(ids),len(set(ids)))
        for ref in re.findall(r'url\(#([^)]*)\)',s):self.assertIn(ref,ids)
    def test_front_right_top_faces_are_present(self):
        s=calendar3d.calendar_card('light',sample(12)).render()
        faces={e.attrib['data-face'] for e in ET.fromstring(s).iter() if 'data-face' in e.attrib}
        self.assertEqual(faces,{'top','front','right'})
    def test_deterministic(self):
        snap=sample(32)
        self.assertEqual(calendar3d.calendar_card('light',snap).render(),calendar3d.calendar_card('light',snap).render())
    def test_duplicate_dates_rejected(self):
        s=sample(1);s['calendar']['days']*=2
        with self.assertRaises(ValueError):calendar3d.calendar_card('light',s)
    def test_snapshot_total_not_replaced_by_other_statistic(self):
        s=sample(5);s['calendar']['total']=123456
        markup=calendar3d.calendar_card('light',s).render()
        self.assertIn('123,456',markup)
    def test_build_metrics_entrypoint_uses_new_renderer(self):
        self.assertIn('data-calendar-style="ink-3d-v1"',build_metrics.calendar_card('light',sample(3)).render())
    def test_old_bouquet_renderer_is_unchanged(self):
        s=sample(2)
        self.assertEqual(build_metrics.bouquet_card('light',s).render(),manga.bouquet_card('light',s).render())
    def test_daily_offline_generation_maintains_both_calendar_paths_and_readme(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);snap=root/'data/snapshot.json';snap.parent.mkdir()
            snap.write_text(json.dumps(sample(4)))
            (root/'garden.json').write_text(json.dumps({'user':'fixture','timezone':'UTC'}))
            original='keep the banner and the non-calendar layout exactly as-is'
            (root/'README.md').write_text(original)
            with patch.object(build_metrics,'ROOT',root),patch.object(build_metrics,'SNAPSHOT',snap),patch.object(build_metrics,'OUT',root/'assets/ink-v2/metrics'):
                self.assertEqual(build_metrics.main(['--offline']),0)
            for theme in ('light','dark'):
                for suffix in ('','-mobile'):
                    name=f'calendar-{theme}{suffix}.svg'
                    a=root/'assets/metrics'/name;b=root/'assets/ink-v2/metrics'/name
                    self.assertEqual(a.read_bytes(),b.read_bytes())
                    self.assertIn('ink-3d-v1',a.read_text())
            self.assertEqual((root/'README.md').read_text(),original)

if __name__=='__main__':unittest.main()
