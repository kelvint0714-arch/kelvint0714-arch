"""Download the open-licensed fonts the profile images embed.

Latin faces are stored whole. Noto Serif JP is requested from the Google Fonts
API as a subset holding only the Japanese characters that appear in garden.json and
the build scripts, so it stays small; run this again after changing any
Japanese label.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"
CSS_API = "https://fonts.googleapis.com/css2"
LICENSE_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/{slug}/OFL.txt"

# file name -> (family, axis spec, license slug)
LATIN = {
    "CormorantGaramond-Medium.ttf": ("Cormorant Garamond", "wght@500", "cormorantgaramond"),
    "CormorantGaramond-SemiBold.ttf": ("Cormorant Garamond", "wght@600", "cormorantgaramond"),
    "CormorantGaramond-MediumItalic.ttf": ("Cormorant Garamond", "ital,wght@1,500", "cormorantgaramond"),
    "Montserrat-Medium.ttf": ("Montserrat", "wght@500", "montserrat"),
    "Montserrat-SemiBold.ttf": ("Montserrat", "wght@600", "montserrat"),
}
CJK = {
    "NotoSerifJP-Medium-subset.ttf": ("Noto Serif JP", "wght@500", "notoserifjp"),
    "NotoSerifJP-SemiBold-subset.ttf": ("Noto Serif JP", "wght@600", "notoserifjp"),
}
CJK_RE = re.compile(r"[　-ヿ㐀-鿿＀-￯·、，。：；！？]")


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "profile-fonts/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def font_url(family: str, spec: str, text: str | None = None) -> str:
    query = {"family": f"{family}:{spec}"}
    if text:
        query["text"] = text
    css = fetch(f"{CSS_API}?{urllib.parse.urlencode(query)}").decode()
    match = re.search(r"url\((https://[^)]+)\)", css)
    if not match:
        raise SystemExit(f"No font URL for {family} {spec}")
    return match.group(1)


def cjk_characters() -> str:
    scripts = sorted(p for p in (ROOT / "scripts").rglob("*.py") if p.name != Path(__file__).name)
    sources = [ROOT / "garden.json", *scripts]
    found: set[str] = set()
    for path in sources:
        found.update(CJK_RE.findall(path.read_text(encoding="utf-8")))
    return "".join(sorted(found))


def main() -> int:
    FONTS.mkdir(exist_ok=True)
    licenses: set[str] = set()
    for name, (family, spec, slug) in LATIN.items():
        target = FONTS / name
        if not target.exists():
            target.write_bytes(fetch(font_url(family, spec)))
            print(f"saved {name}")
        licenses.add(slug)

    characters = cjk_characters()
    for name, (family, spec, slug) in CJK.items():
        (FONTS / name).write_bytes(fetch(font_url(family, spec, characters)))
        print(f"saved {name} ({len(characters)} characters)")
        licenses.add(slug)

    for slug in sorted(licenses):
        target = FONTS / f"OFL-{slug}.txt"
        if not target.exists():
            target.write_bytes(fetch(LICENSE_URL.format(slug=slug)))
    (FONTS / "cjk-characters.json").write_text(
        json.dumps({"characters": characters}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
