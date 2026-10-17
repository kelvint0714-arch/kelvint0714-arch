"""Checks for the data parsing, README blocks and image builders."""

from __future__ import annotations

import json
import sys
import unittest
import xml.dom.minidom
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_hero  # noqa: E402
import build_metrics  # noqa: E402
import build_sections  # noqa: E402
import update_repositories  # noqa: E402
from garden import data  # noqa: E402

CALENDAR_PAGE = """
<h2 id="js-contribution-activity-description">
  12
  contributions
    in the last year
</h2>
<td tabindex="0" data-ix="0" data-date="2026-10-11" id="contribution-day-component-0-0" data-level="0" class="ContributionCalendar-day"></td>
<td tabindex="0" data-ix="0" data-date="2026-10-12" id="contribution-day-component-1-0" data-level="2" class="ContributionCalendar-day"></td>
<td tabindex="0" data-ix="0" data-date="2026-10-13" id="contribution-day-component-2-0" data-level="4" class="ContributionCalendar-day"></td>
<td tabindex="0" data-ix="0" data-date="2026-10-14" id="contribution-day-component-3-0" data-level="1" class="ContributionCalendar-day"></td>
<tool-tip for="contribution-day-component-0-0" class="sr-only">No contributions on October 11th.</tool-tip>
<tool-tip for="contribution-day-component-1-0" class="sr-only">3 contributions on October 12th.</tool-tip>
<tool-tip for="contribution-day-component-2-0" class="sr-only">8 contributions on October 13th.</tool-tip>
<tool-tip for="contribution-day-component-3-0" class="sr-only">1 contribution on October 14th.</tool-tip>
"""


def snapshot() -> dict:
    return {
        "user": "someone",
        "fetched_at": "2026-10-15T00:00:00Z",
        "calendar": {"total": 12, "days": [["2026-10-11", 0, 0], ["2026-10-12", 2, 3], ["2026-10-13", 4, 8]]},
        "profile": {"followers": 1, "public_repos": 1},
        "repos": [{"name": "a|b", "html_url": "https://example.com", "description": "pipes | here", "language": None,
                   "fork": True, "stargazers_count": 0, "pushed_at": None, "archived": False}],
        "languages": {"Python": 300, "CSS": 100},
        "events": [
            {"type": "PushEvent", "repo": "someone/site", "created_at": "2026-10-14T10:00:00Z",
             "payload": {"ref": "refs/heads/main"}},
            {"type": "PushEvent", "repo": "someone/site", "created_at": "2026-10-14T08:00:00Z",
             "payload": {"ref": "refs/heads/main"}},
            {"type": "WatchEvent", "repo": "other/tool", "created_at": "2026-10-13T08:00:00Z", "payload": {}},
            {"type": "PushEvent", "repo": "someone/site", "created_at": "2026-08-01T08:00:00Z",
             "payload": {"ref": "refs/heads/main"}},
        ],
    }


class CalendarTest(unittest.TestCase):
    def test_parse(self):
        days, total = data.parse_calendar(CALENDAR_PAGE)
        self.assertEqual(total, 12)
        self.assertEqual([(d.date.day, d.level, d.count) for d in days], [(11, 0, 0), (12, 2, 3), (13, 4, 8), (14, 1, 1)])

    def test_streaks_allow_today_to_be_empty(self):
        days = [data.Day(date(2026, 10, d), 1, c) for d, c in [(1, 1), (2, 1), (3, 1), (4, 0), (5, 2), (6, 1), (7, 0)]]
        self.assertEqual(data.streaks(days), (3, 2))

    def test_weeks_start_on_sunday(self):
        days = [data.Day(date(2026, 10, 14), 0, 0)]  # a Wednesday
        columns = data.week_columns(days)
        self.assertEqual(len(columns), 1)
        self.assertEqual(columns[0][3], days[0])


class NotesTest(unittest.TestCase):
    def test_same_day_pushes_merge_and_old_events_drop(self):
        now = datetime(2026, 10, 15, tzinfo=timezone.utc)
        notes = build_metrics.recent_notes(snapshot(), ZoneInfo("Asia/Shanghai"), now)
        self.assertEqual([n["text"] for n in notes], ["Pushed 2 times to main", "Starred"])


class RepositoriesTest(unittest.TestCase):
    def test_table_escapes_pipes_and_marks_forks(self):
        table = update_repositories.table(snapshot()["repos"])
        self.assertIn("[a|b](https://example.com) · fork", table)
        self.assertIn("pipes \\| here", table)
        self.assertIn("| — |", table)

    def test_replace_block_keeps_surroundings(self):
        readme = f"top\n{update_repositories.START}\nold\n{update_repositories.END}\nbottom"
        result = update_repositories.replace_block(readme, "new")
        self.assertEqual(result, f"top\n{update_repositories.START}\nnew\n{update_repositories.END}\nbottom")


class ImagesTest(unittest.TestCase):
    def assert_svg(self, markup: str):
        xml.dom.minidom.parseString(markup)
        self.assertIn("prefers-reduced-motion", markup)

    def test_builders_write_well_formed_svg(self):
        config = json.loads((build_hero.ROOT / "garden.json").read_text(encoding="utf-8"))
        hero = build_hero.build("dark", config)
        self.assert_svg(hero.render(animated=True))
        self.assertNotIn("@keyframes", hero.render(animated=False))
        self.assert_svg(build_sections.build("light", config["sections"][0], 0).render())
        snap = snapshot()
        now = datetime(2026, 10, 15, tzinfo=timezone.utc)
        for doc in (build_metrics.calendar_card("light", snap), build_metrics.bouquet_card("dark", snap),
                    build_metrics.notes_card("light", snap, ZoneInfo("UTC"), now)):
            self.assert_svg(doc.render())


if __name__ == "__main__":
    unittest.main()
