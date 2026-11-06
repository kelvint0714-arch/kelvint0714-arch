"""Draw the chapter headings and the footer in every theme and width."""

from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from garden import manga

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    config = json.loads((ROOT / "garden.json").read_text(encoding="utf-8"))
    out = ROOT / "assets" / "sections"
    out.mkdir(parents=True, exist_ok=True)
    for index, section in enumerate(config["sections"]):
        for theme, mobile, suffix in manga.variants():
            path = out / f"header-{section['id']}-{theme}{suffix}.svg"
            path.write_text(manga.header(theme, section, index, mobile).render(), encoding="utf-8")
            print(path.name)
    for theme, mobile, suffix in manga.variants():
        (out / f"footer-{theme}{suffix}.svg").write_text(
            manga.footer(theme, mobile).render(), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
