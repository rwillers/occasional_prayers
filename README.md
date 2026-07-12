# Occasional Prayers

Occasional Prayers is a static website that collects prayers from the *Book of Common Prayer*, the Anglican tradition, and the broader Church in an indexed, searchable format.

The site is built with [Pelican](https://getpelican.com/) and [PageFind](https://pagefind.app/) from Markdown content and templates in this repository.

The Urubu -> Pelican + PageFind migration was completed on 2026-02-15.

## Project Structure

- `_python/`: small Python helpers and custom template filters used by the build.
- `css/`, `js/`, `images/`: static assets.
- Prayer/content directories (for example `acna2019/`, `tec1979/`, `parish-year/`): Markdown source files.
- `_build_pelican/`: generated output from Pelican.
- `migration/`: migration artifacts, reports, and taxonomy decision records.

## Local Development

### Prerequisites

- Python 3.12
- Node.js (for PageFind indexing)

### Common Commands

- Build the site (recommended):
  - `make build-pelican-search`
- Serve locally (Pelican):
  - `make serve-pelican`
  - or `.venv-pelican/bin/python -m pelican --listen --autoreload -s pelicanconf.py -o _build_pelican`
- Build with Pelican (without PageFind):
  - `make build-pelican`
  - or `.venv-pelican/bin/python -m pelican -s pelicanconf.py -o _build_pelican && touch _build_pelican/.nojekyll`
- Fast Pelican smoke build:
  - `make build-pelican-smoke`
  - or `.venv-pelican/bin/python -m pelican -s pelicanconf_smoke.py -o _build_pelican_smoke && touch _build_pelican_smoke/.nojekyll`
- Generate redirects from `migration/redirects.csv`:
  - `make build-redirects`
  - or `.venv-pelican/bin/python scripts/generate_redirects.py --csv migration/redirects.csv --site _build_pelican --report migration/redirect_report.txt`
- Build PageFind index:
  - `make build-pagefind`
  - or `npx --yes pagefind --site _build_pelican --output-subdir pagefind --exclude-selectors "header,footer,#pronouns,.tags,script,style"`
- Build Pelican + PageFind in sequence:
  - `make build-pelican-search`
- Run automated test suite (pytest):
  - `make test`
- Run full verification suite (tests + build + redirects + readiness):
  - `make test-all`
- Run metadata audit:
  - `make audit-metadata`
  - or `.venv-pelican/bin/python scripts/audit_metadata.py`
- Build taxonomy inventory and mapping templates:
  - `make taxonomy-inventory`
  - or `.venv-pelican/bin/python scripts/build_taxonomy_inventory.py`
- Build proposed taxonomy mapping decisions (Phase 2.5 draft):
  - `make taxonomy-proposals`
  - or `.venv-pelican/bin/python scripts/propose_taxonomy_mappings.py`
- Finalize approved taxonomy mappings (apply merge decisions):
  - `make taxonomy-finalize`
  - or `.venv-pelican/bin/python scripts/finalize_taxonomy_mappings.py`
- Build "extreme" topical taxonomy proposal (ACNA topical + seasons + Other Feasts):
  - `make taxonomy-extreme-proposal`
  - or `.venv-pelican/bin/python scripts/propose_extreme_topical_taxonomy.py`
- Finalize "extreme option 2" (core + 4 structural fallback tags):
  - `make taxonomy-extreme-option2`
  - or `.venv-pelican/bin/python scripts/finalize_extreme_option2.py`
- Apply "extreme option 2" tags to markdown source:
  - `make taxonomy-apply-option2`
  - or `.venv-pelican/bin/python scripts/apply_option2_taxonomy.py`
- Generate deployment readiness report:
  - `make cutover-readiness`
  - or `.venv-pelican/bin/python scripts/cutover_readiness.py`

## Publishing Automation

GitHub Actions workflow: `.github/workflows/publish.yml`

Behavior:

- Runs build + migration checks on pull requests and pushes.
- Deploys on pushes to `master`.
- Supports manual deploy via workflow dispatch (`deploy: true`).

Create a GitHub Actions environment named `production`. Add these environment secrets:

- `CLOUDFLARE_ACCOUNT_ID`: account containing the Pages project.
- `CLOUDFLARE_API_TOKEN`: custom API token with `Account > Cloudflare Pages > Edit` permission.

Required GitHub repository variable:

- `CLOUDFLARE_PAGES_PROJECT_NAME`: name of the existing Cloudflare Pages project.

The deploy job is bound to the `production` environment, so its protection rules apply before Cloudflare credentials become available. Restrict deployment branches to `master` and add required reviewers if production deploys should require approval.

The Pages project's production branch must also be `master`. The workflow uploads the generated `_build_pelican/` directory with Wrangler, records a GitHub deployment, and runs smoke checks against the deployment-specific `pages.dev` URL. Configure `occasionalprayers.com` and `www.occasionalprayers.com` as custom domains on the Pages project before DNS cutover.

## Dependencies

Python dependencies are now pinned in `requirements.txt`.

### Python Environment

Use a dedicated virtualenv for local builds/tests:

- `make prep-pelican-env`
- or:
  - `python3 -m venv .venv-pelican`
  - `.venv-pelican/bin/python -m pip install -r requirements.txt`

Note: `index-pelican.md` is a migration adapter used to generate Pelican's root `index.html` without changing the existing `index.md` metadata shape.
Note: `make build-pagefind` uses `npx` by default and needs network access unless `pagefind` is already installed locally.
Note: historical migration artifacts are retained in `migration/`.

## Python Style

Use **Black** for Python code formatting/linting in this project.

- Format all Python code:
  - `.venv-pelican/bin/python -m black _python scripts tests`
- Check formatting without writing changes:
  - `.venv-pelican/bin/python -m black --check _python scripts tests`

If you change Python files, run Black before committing.
