PELICAN_PYTHON ?= .venv-pelican/bin/python
PYTHON_BOOTSTRAP ?= python3
PAGEFIND_CMD ?= npx --yes pagefind
PAGEFIND_EXCLUDE_SELECTORS ?= header,footer,\#pronouns,.tags,script,style

all: build

build:
	$(MAKE) build-pelican-search

serve:
	$(MAKE) serve-pelican

prep-pelican-env:
	$(PYTHON_BOOTSTRAP) -m venv .venv-pelican
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

test:
	$(PELICAN_PYTHON) -m pytest -q tests

test-all:
	$(MAKE) test
	$(MAKE) build-pelican-search
	$(MAKE) build-redirects
	$(MAKE) cutover-readiness

audit-metadata:
	$(PELICAN_PYTHON) scripts/audit_metadata.py

taxonomy-inventory:
	$(PELICAN_PYTHON) scripts/build_taxonomy_inventory.py

taxonomy-proposals:
	$(PELICAN_PYTHON) scripts/propose_taxonomy_mappings.py

taxonomy-finalize:
	$(PELICAN_PYTHON) scripts/finalize_taxonomy_mappings.py

taxonomy-extreme-proposal:
	$(PELICAN_PYTHON) scripts/propose_extreme_topical_taxonomy.py

taxonomy-extreme-option2:
	$(PELICAN_PYTHON) scripts/finalize_extreme_option2.py

taxonomy-apply-option2:
	$(PELICAN_PYTHON) scripts/apply_option2_taxonomy.py

cutover-readiness:
	$(PELICAN_PYTHON) scripts/cutover_readiness.py

serve-pelican:
	$(PELICAN_PYTHON) -m pelican --listen --autoreload -s pelicanconf.py -o _build_pelican

publish:
	git push origin master

git:
	git push origin master
