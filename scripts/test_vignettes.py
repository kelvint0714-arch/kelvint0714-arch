"""Repository scenes: valid ink drawings, sensible matches, no repeats."""
from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as ET

from garden import manga, vignettes


def repo(name, language=None, description=None):
    return {'name': name, 'html_url': f'https://github.com/someone/{name}', 'language': language,
            'description': description, 'stargazers_count': 0, 'pushed_at': '2026-10-01T00:00:00Z'}


class SceneTest(unittest.TestCase):
    def test_every_scene_draws_on_both_card_sizes(self):
        for scene in vignettes.SCENES:
            for mobile in (False, True):
                s = manga.repo_card('light', repo('x'), 0, mobile, scene).render()
                root = ET.fromstring(s)
                self.assertIn(f'data-vignette="{scene}"', s)
                ids = {e.attrib['id'] for e in root.iter() if 'id' in e.attrib}
                for ref in re.findall(r'url\(#([^)]*)\)', s):
                    self.assertIn(ref, ids, scene)
                for c in re.findall(r'#[0-9a-fA-F]{6}\b', s):
                    self.assertTrue(c[1:3].lower() == c[3:5].lower() == c[5:7].lower(), (scene, c))
                for needle in ('<filter', 'Gradient', '<image', '<script'):
                    self.assertNotIn(needle, s)

    def test_current_repositories_keep_their_scenes(self):
        chosen = vignettes.assign([repo('kelvint0714-arch.github.io', 'TypeScript', 'personal homepage'),
                                   repo('ML-practice', 'Jupyter Notebook', 'this')])
        self.assertEqual(chosen, {'kelvint0714-arch.github.io': 'valley', 'ML-practice': 'notebook'})

    def test_topics_pick_fitting_scenes(self):
        cases = {'contest-solutions': ('C++', 'ICPC solutions', 'crane'), 'dotfiles': ('Shell', None, 'terminal'),
                 'reading-notes': (None, 'notes on books', 'teacup'), 'raytracer': ('Rust', None, 'clockwork'),
                 'todo-app': ('Swift', 'an iOS app', 'fan')}
        for name, (lang, desc, scene) in cases.items():
            self.assertEqual(vignettes.ranked(repo(name, lang, desc))[0], scene, name)

    def test_no_repeats_until_every_scene_is_used(self):
        repos = [repo(f'project-{i}', 'Python') for i in range(len(vignettes.SCENES) + 3)]
        chosen = list(vignettes.assign(repos).values())
        self.assertEqual(len(set(chosen[:len(vignettes.SCENES)])), len(vignettes.SCENES))
        self.assertEqual(vignettes.assign(repos), vignettes.assign(repos))


if __name__ == '__main__':
    unittest.main()
