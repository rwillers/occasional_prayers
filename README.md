# Occasional Prayers

Occasional Prayers is a static website that collects prayers from the *Book of Common Prayer*, the Anglican tradition, and the broader Church in an indexed, searchable format.

The site is built with [Pelican](https://getpelican.com/) and [PageFind](https://pagefind.app/) from Markdown content and templates in this repository.

Initial Urubu -> Pelican + PageFind migration is complete (2026-02-15). Urubu build commands remain available temporarily as a fallback path.

## Project Structure

- `_python/`: small Python helpers and custom template filters used by the build.
- `_layouts/`: site layout templates.
- `css/`, `js/`, `images/`: static assets.
- Prayer/content directories (for example `acna2019/`, `tec1979/`, `parish-year/`): Markdown source files.
- `_build/`: generated output from Urubu.
- `_workingfiles/`: working notes, import/parsing helpers, and scratch content.

## Local Development

### Prerequisites

- Python 3
- Urubu available in your environment
- Python 3.12 for Pelican migration tooling

### Common Commands

- Build the site (recommended):
  - `make build-pelican-search`
- Serve locally (Pelican):
  - `make serve-pelican`
  - or `.venv-pelican/bin/python -m pelican --listen --autoreload -s pelicanconf.py -o _build_pelican`
- Build the site (legacy Urubu fallback):
  - `make build`
  - or `python3 -m urubu build && touch _build/.nojekyll`
- Serve locally (legacy Urubu fallback):
  - `make serve`
  - or `python3 -m urubu serve`
- Capture migration baseline artifacts:
  - `make baseline`
  - or `python3 scripts/capture_baseline.py`
- Build with Pelican (without PageFind):
  - `make build-pelican`
  - or `.venv-pelican/bin/python -m pelican -s pelicanconf.py -o _build_pelican && touch _build_pelican/.nojekyll`
- Fast Pelican smoke build (migration path):
  - `make build-pelican-smoke`
  - or `.venv-pelican/bin/python -m pelican -s pelicanconf_smoke.py -o _build_pelican_smoke && touch _build_pelican_smoke/.nojekyll`
- Generate redirects from `migration/redirects.csv`:
  - `make build-redirects`
  - or `.venv-pelican/bin/python scripts/generate_redirects.py --csv migration/redirects.csv --site _build_pelican --report migration/redirect_report.txt`
- Build PageFind index (migration path):
  - `make build-pagefind`
  - or `npx --yes pagefind --site _build_pelican --output-subdir pagefind --exclude-selectors ".navbar,.footer,#pronouns,.tags,script,style"`
- Build Pelican + PageFind in sequence:
  - `make build-pelican-search`
- Run migration metadata audit:
  - `make audit-metadata`
  - or `.venv-pelican/bin/python scripts/audit_metadata.py`
- Run representative render parity checks:
  - `make check-render-parity`
  - or `.venv-pelican/bin/python scripts/check_render_parity.py`
- Run both migration audits:
  - `make migration-checks`
- Generate cutover readiness report:
  - `make cutover-readiness`
  - or `.venv-pelican/bin/python scripts/cutover_readiness.py`

## Dependencies

Python dependencies are now pinned in `requirements.txt`.

### Pelican Migration Environment

Use a dedicated virtualenv for Pelican migration work:

- `make prep-pelican-env`
- or:
  - `/opt/homebrew/bin/python3.12 -m venv .venv-pelican`
  - `.venv-pelican/bin/python -m pip install -r requirements.txt`

`requirements-urubu.txt` is kept separately for legacy Urubu-only environments because Urubu and modern Pelican have conflicting Markdown dependency ranges.

Note: `index-pelican.md` is a migration adapter used to generate Pelican's root `index.html` without changing the existing Urubu-focused `index.md` metadata shape.
Note: `make build-pagefind` uses `npx` by default and needs network access unless `pagefind` is already installed locally.

## Python Style

Use **Black** for Python code formatting/linting in this project.

- Format all Python code:
  - `.venv-pelican/bin/python -m black _python _workingfiles`
- Check formatting without writing changes:
  - `.venv-pelican/bin/python -m black --check _python _workingfiles`

If you change Python files, run Black before committing.
