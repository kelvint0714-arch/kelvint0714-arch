"""Refresh the public repository table between the GARDEN-REPOS markers in README.md.

Reads the repositories from data/snapshot.json (written by build_metrics.py,
which runs first); fetches them directly when there is no snapshot yet.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from garden import data  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
SNAPSHOT = ROOT / "data" / "snapshot.json"
START, END = "<!-- GARDEN-REPOS:START -->", "<!-- GARDEN-REPOS:END -->"
BLOSSOMS = ["✿", "❀", "✾", "❁"]


def cell(text: str | None) -> str:
    text = " ".join((text or "").split())
    return text.replace("|", "\\|") if text else "—"


def table(repos: list[dict]) -> str:
    if not repos:
        return "_The first seeds are still underground · まだ芽吹く前_"
    lines = ["| | Repository | Description | Language |", "| :-: | :--- | :--- | :--- |"]
    for i, repo in enumerate(repos):
        name = f"[{repo['name']}]({repo['html_url']})"
        if repo.get("fork"):
            name += " · fork"
        if repo.get("archived"):
            name += " · archived"
        lines.append(f"| {BLOSSOMS[i % len(BLOSSOMS)]} | {name} | {cell(repo.get('description'))} | "
                     f"{cell(repo.get('language'))} |")
    return "\n".join(lines)


def replace_block(readme: str, body: str) -> str:
    start, end = readme.index(START) + len(START), readme.index(END)
    return readme[:start] + "\n" + body + "\n" + readme[end:]


def main() -> int:
    config = json.loads((ROOT / "garden.json").read_text(encoding="utf-8"))
    if SNAPSHOT.exists():
        repos = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["repos"]
    else:
        repos = data.fetch_repos(config["user"])
    readme = README.read_text(encoding="utf-8")
    updated = replace_block(readme, table(repos))
    if updated != readme:
        README.write_text(updated, encoding="utf-8")
        print(f"README.md: {len(repos)} repositories")
    return 0


if __name__ == "__main__":
    sys.exit(main())
