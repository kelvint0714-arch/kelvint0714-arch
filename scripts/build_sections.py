"""Render manga chapter titles in desktop/mobile and light/dark versions."""
from __future__ import annotations
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from garden import manga
ROOT=Path(__file__).resolve().parent.parent

def build(theme: str, section: dict, index: int):
    return manga.header(theme,section,index)

def main() -> int:
    config=json.loads((ROOT/'garden.json').read_text(encoding='utf-8'))
    out=ROOT/'assets'/'sections';out.mkdir(parents=True,exist_ok=True)
    for index,section in enumerate(config['sections']):
        for mobile in (False,True):
            for theme in ('light','dark'):
                suffix='-mobile' if mobile else ''
                path=out/f"header-{section['id']}-{theme}{suffix}.svg"
                path.write_text(manga.header(theme,section,index,mobile).render(),encoding='utf-8')
                print(path.name)
    return 0
if __name__=='__main__':sys.exit(main())
