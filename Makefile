# Shortcuts for working on the profile locally. CI runs the same steps (.github/workflows/garden.yml).
PY ?= python3

.PHONY: test build offline lettering banner format

test:        ## run every check
	$(PY) -m unittest discover -s scripts -p 'test_*.py'

build: test  ## fetch live GitHub data, redraw every card, refresh README
	$(PY) scripts/build_sections.py
	$(PY) scripts/build_metrics.py
	$(PY) scripts/update_repositories.py

offline: test  ## redraw from data/snapshot.json without the network
	$(PY) scripts/build_sections.py
	$(PY) scripts/build_metrics.py --offline
	$(PY) scripts/update_repositories.py

lettering:   ## rebuild heading outlines after changing the font or headings (needs fonttools)
	$(PY) scripts/build_lettering.py

banner:      ## rebuild the video banner from banners/ (needs ffmpeg and Pillow)
	$(PY) scripts/build_banner.py

format:      ## reformat Python (needs black)
	$(PY) -m black scripts
