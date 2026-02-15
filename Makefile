PELICAN_PYTHON ?= .venv-pelican/bin/python
PAGEFIND_CMD ?= npx --yes pagefind
PAGEFIND_EXCLUDE_SELECTORS ?= .navbar,.footer,\#pronouns,.tags,script,style

all: build

build:
	$(MAKE) build-pelican-search

serve:
	$(MAKE) serve-pelican

prep-pelican-env:
	/opt/homebrew/bin/python3.12 -m venv .venv-pelican
	$(PELICAN_PYTHON) -m pip install -r requirements.txt

build-pelican:
	$(PELICAN_PYTHON) -c "from pathlib import Path; import shutil; p=Path('_build_pelican'); shutil.rmtree(p, ignore_errors=True); p.mkdir(parents=True, exist_ok=True)"
	$(PELICAN_PYTHON) -m pelican -q -s pelicanconf.py -o _build_pelican
	touch _build_pelican/.nojekyll

build-pelican-smoke:
	$(PELICAN_PYTHON) -c "from pathlib import Path; import shutil; p=Path('_build_pelican_smoke'); shutil.rmtree(p, ignore_errors=True); p.mkdir(parents=True, exist_ok=True)"
	$(PELICAN_PYTHON) -m pelican -q -s pelicanconf_smoke.py -o _build_pelican_smoke
	touch _build_pelican_smoke/.nojekyll

build-redirects:
	$(PELICAN_PYTHON) scripts/generate_redirects.py --csv migration/redirects.csv --site _build_pelican --report migration/redirect_report.txt

build-redirects-smoke:
	$(PELICAN_PYTHON) scripts/generate_redirects.py --csv migration/redirects.csv --site _build_pelican_smoke --report migration/redirect_report_smoke.txt

build-pagefind:
	$(PAGEFIND_CMD) --site _build_pelican --output-subdir pagefind --exclude-selectors "$(PAGEFIND_EXCLUDE_SELECTORS)"

build-pagefind-smoke:
	$(PAGEFIND_CMD) --site _build_pelican_smoke --output-subdir pagefind --exclude-selectors "$(PAGEFIND_EXCLUDE_SELECTORS)"

build-pelican-search:
	$(MAKE) build-pelican
	$(MAKE) build-pagefind

audit-metadata:
	$(PELICAN_PYTHON) scripts/audit_metadata.py

cutover-readiness:
	$(PELICAN_PYTHON) scripts/cutover_readiness.py

serve-pelican:
	$(PELICAN_PYTHON) -m pelican --listen --autoreload -s pelicanconf.py -o _build_pelican

publish:
	git push origin master

git:
	git push origin master
