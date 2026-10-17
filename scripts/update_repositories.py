"""Refresh linked manga repository panels using the existing public snapshot.

The plain-text index remains available in a details block. The BANNER block,
README surroundings and other repositories are never changed.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
sys.path.insert(0,str(Path(__file__).resolve().parent))
from garden import data, manga
ROOT=Path(__file__).resolve().parent.parent
README=ROOT/'README.md'
SNAPSHOT=ROOT/'data'/'snapshot.json'
START,END='<!-- GARDEN-REPOS:START -->','<!-- GARDEN-REPOS:END -->'
BLOSSOMS=['✿','❀','✾','❁']

def cell(text: str | None) -> str:
    text=' '.join((text or '').split())
    return text.replace('|','\\|') if text else '—'

def table(repos: list[dict]) -> str:
    # Retained for older callers and the original repository tests.
    if not repos:return '_The first seeds are still underground · まだ芽吹く前_'
    lines=['| | Repository | Description | Language |','| :-: | :--- | :--- | :--- |']
    for i,repo in enumerate(repos):
        name=f"[{repo['name']}]({repo['html_url']})"
        if repo.get('fork'):name+=' · fork'
        if repo.get('archived'):name+=' · archived'
        lines.append(f"| {BLOSSOMS[i%len(BLOSSOMS)]} | {name} | {cell(repo.get('description'))} | {cell(repo.get('language'))} |")
    return '\n'.join(lines)

def replace_block(readme: str,body: str) -> str:
    if readme.count(START)!=1 or readme.count(END)!=1:
        raise ValueError('Expected exactly one GARDEN-REPOS block; README left untouched.')
    start,end=readme.index(START)+len(START),readme.index(END)
    if end<start:raise ValueError('GARDEN-REPOS markers are out of order.')
    return readme[:start]+'\n'+body+'\n'+readme[end:]

def safe_link(value):
    value=str(value or '')
    if urlparse(value).scheme not in ('https','http'):
        raise ValueError('Repository links must be HTTP(S).')
    return value

def cards(repos: list[dict],out: Path) -> str:
    out.mkdir(parents=True,exist_ok=True)
    public=[r for r in repos if not r.get('private')]
    parts=[];plain=[];generated=set()
    for index,repo in enumerate(public):
        name=str(repo['name']);link=safe_link(repo['html_url']);slug=manga.repo_slug(repo)
        for mobile in (False,True):
            for theme in ('light','dark'):
                suffix='-mobile' if mobile else ''
                target=out/f'{slug}-{theme}{suffix}.svg'
                target.write_text(manga.repo_card(theme,repo,index,mobile).render(),encoding='utf-8')
                generated.add(target.name)
        tags=' / '.join(x for x in [repo.get('language') or 'Language not specified','fork' if repo.get('fork') else '', 'archived' if repo.get('archived') else ''] if x)
        alt=f"{name}. {repo.get('description') or 'No description provided.'} {tags}. {repo.get('stargazers_count') or 0} stars. Updated {(repo.get('pushed_at') or '—')[:10]}. Open repository."
        parts.append(manga.picture(f'./assets/repos/{slug}',alt,href=link))
        plain.append(f'<p><a href="{manga.esc(link)}"><strong>{manga.esc(name)}</strong></a><br />{manga.esc(repo.get("description") or "No description provided.")}<br /><sub>{manga.esc(tags)}</sub></p>')
    # Remove only obsolete panels with this generator's own filename format.
    for previous in out.glob('*.svg'):
        if re.fullmatch(r'.+-[0-9a-f]{7}-(light|dark)(-mobile)?\.svg',previous.name) and previous.name not in generated:
            previous.unlink()
    if not parts:parts=['<p>No public repositories yet.</p>']
    parts.append('<details>\n<summary>Repository text index / 仓库文字索引</summary>\n\n'+'\n\n'.join(plain)+'\n\n</details>')
    return '\n\n'.join(parts)

def main() -> int:
    config=json.loads((ROOT/'garden.json').read_text(encoding='utf-8'))
    repos=json.loads(SNAPSHOT.read_text(encoding='utf-8'))['repos'] if SNAPSHOT.exists() else data.fetch_repos(config['user'])
    repos=[r for r in repos if not r.get('private') and r.get('name','').lower()!=config['user'].lower()]
    readme=README.read_text(encoding='utf-8')
    updated=replace_block(readme,cards(repos,ROOT/'assets'/'repos'))
    if updated!=readme:README.write_text(updated,encoding='utf-8')
    print(f'README.md: {len(repos)} linked manga repository panels')
    return 0
if __name__=='__main__':sys.exit(main())
