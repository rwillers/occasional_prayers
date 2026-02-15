# Migration Execution Log

## 2026-02-14

Started executing the "Urubu -> Pelican + PageFind Migration" plan.

Completed in this pass:

- Added migration workspace and docs:
  - `migration/README.md`
  - `migration/urubu_behavior_inventory.md`
  - `migration/redirects.csv` (header scaffold)
- Added baseline capture script:
  - `scripts/capture_baseline.py`
- Generated baseline artifacts in `migration/baseline/`:
  - URL inventory and top-level URL counts
  - Representative URL samples by section
  - Metadata key and layout usage counts
  - Tipue Search source/build asset inventories
  - Urubu layout template inventory
- Added migration dependency + build scaffolding:
  - `requirements.txt`
  - `pelicanconf.py`
  - `publishconf.py`
  - Make targets: `baseline`, `build-pelican`, `serve-pelican`
  - README updates for baseline + Pelican commands

Current blockers/notes:

- Black is not installed in the active `python3` environment, so project-specified Black commands could not run there.
- A first Pelican smoke build was attempted and exposed environment mismatch issues in current interpreter dependencies (notably Markdown API/version mismatch), causing repeated processing errors.
- The new Pelican config is currently scoped to canonical section directories; root-level pages (`index.md`, `about.md`, `search.md`, `notfound.md`) are intentionally deferred to the template migration phase.

Environment prep updates:

- Installed Python 3.12 with Homebrew (`/opt/homebrew/bin/python3.12`).
- Added `prep-pelican-env` make target and `.venv-pelican` local environment path.
- Split Urubu dependency into `requirements-urubu.txt` because `urubu==1.4.0` conflicts with modern Pelican Markdown requirements in a single resolver pass.
- Successfully prepared `.venv-pelican` with pinned dependencies from `requirements.txt` (`pelican==4.9.1`, `black==24.10.0`, `markdown==3.5.2`, `jinja2==3.1.5`).
- Verified tooling commands in the new environment:
  - `.venv-pelican/bin/python -m pelican --version`
  - `.venv-pelican/bin/python -m black --version`

Template migration updates:

- Added Pelican theme scaffold at `themes/occasional-prayers/templates/`:
  - `base.html`, `footer.html`, `page.html`, `index.html`, `home.html`, `search.html`, `tag.html`
- Added compatibility plugin `_python/pelican_compat.py`:
  - maps `layout` metadata values (`home`, `index`, `page`, `search`, `tag`) to Pelican templates
  - normalizes `tagline` and tag metadata from source front matter
  - provides section child-page lists and home/tag list context used by migrated templates
- Added root-page adapter `index-pelican.md` to generate Pelican `index.html` while keeping existing `index.md` untouched (works around Pelican metadata setter conflicts with Urubu's `content:` key).
- Added `PyYAML` to `requirements.txt` for front matter normalization in the compatibility plugin.
- Added fast smoke config and target:
  - `pelicanconf_smoke.py`
  - `make build-pelican-smoke`
- Updated build targets to clean output directories first and run Pelican in quiet mode for faster iteration.

Continued migration execution:

- Added Urubu-style breadcrumbs parity for Pelican page output:
  - `_python/pelican_compat.py` now attaches `compat_breadcrumbs` based on section/directory index ancestry.
  - `themes/occasional-prayers/templates/page.html` now renders breadcrumb trails matching legacy behavior.
- Continued PageFind migration work:
  - Replaced Tipue-driven Pelican search template logic with PageFind UI loading and `?q=` query prefill:
    - `themes/occasional-prayers/templates/search.html`
    - `search.md`
  - Added PageFind-oriented search styling to `css/style.css`.
  - Added Makefile targets:
    - `build-pagefind`
    - `build-pagefind-smoke`
    - `build-pelican-search`
  - Added template-level search-page exclusion from indexing via `data-pagefind-ignore="all"`.
- Implemented redirect generation tooling per migration spec:
  - Added `scripts/generate_redirects.py`.
  - Added Makefile targets:
    - `build-redirects`
    - `build-redirects-smoke`
  - Implemented validations:
    - duplicate `old_path`
    - missing required fields
    - unsupported status values (allowed: `301`, `302`)
    - redirect loop detection
    - unresolved `new_path` targets in generated site output
  - Added redirect report outputs:
    - `migration/redirect_report.txt`
    - `migration/redirect_report_smoke.txt`
  - Redirect HTML output includes canonical URL, meta refresh, JS fallback, and `data-pagefind-ignore="all"`.
- Ran URL parity check between baseline and Pelican output:
  - Added artifacts under `migration/parity/`:
    - `url_parity_summary.md`
    - `url_missing_in_pelican.txt`
    - `url_extra_in_pelican.txt`
    - sorted manifests used for comparison
  - Current parity result: `3126` baseline URLs vs `3126` Pelican URLs, with `0` missing and `0` extra.

Verification performed:

- Formatting:
  - `./.venv-pelican/bin/python -m black _python/pelican_compat.py scripts/generate_redirects.py pelicanconf.py pelicanconf_smoke.py publishconf.py`
  - `./.venv-pelican/bin/python -m black --check _python/pelican_compat.py scripts/generate_redirects.py pelicanconf.py pelicanconf_smoke.py publishconf.py`
- Build checks:
  - `make build-pelican-smoke` (pass)
  - `make build-pelican` (pass)
  - `make build-redirects` (pass; 0 rules evaluated, 0 redirects generated)

Environment limitation encountered:

- `make build-pagefind` currently fails in this sandbox due blocked npm registry network resolution (`ENOTFOUND registry.npmjs.org`).
- The integration is wired and ready; PageFind indexing execution must be validated in a network-enabled/local dependency environment.

## 2026-02-15

PageFind milestone validation updates:

- Confirmed PageFind indexing artifacts now exist in `_build_pelican/pagefind/` after successful `make build-pagefind` execution in a network-enabled environment.
- Captured index integrity details:
  - `pagefind-entry.json` reports `page_count: 3125`.
  - `_build_pelican` contains `3126` HTML files, indicating one intentionally excluded page in indexing scope.
- Ran representative query validation against the generated PageFind index using local HTTP serving + PageFind JS API:
  - `unity` -> 143 results
  - `easter` -> 186 results
  - `marriage` -> 47 results
  - `healing` -> 195 results
  - `thanksgiving` -> 252 results
- Wrote validation artifacts:
  - `migration/parity/pagefind_query_results.tsv`
  - `migration/parity/pagefind_validation_summary.md`

Metadata and render parity checkpoint updates:

- Added metadata audit script:
  - `scripts/audit_metadata.py`
- Added representative render parity script:
  - `scripts/check_render_parity.py`
- Added Make targets for migration checks:
  - `audit-metadata`
  - `check-render-parity`
  - `migration-checks`
- Added README command docs for the new migration checks.

Findings and fixes:

- Metadata audit (`migration/parity/metadata_audit_summary.md`) reported one edge case:
  - `index.md` contains a front matter `content:` key (known Pelican conflict risk), already handled through `index-pelican.md`.
- Representative render parity check initially surfaced title and breadcrumb mismatches.
- Implemented parity fixes in `_python/pelican_compat.py`:
  - normalized quoted title values from front matter before rendering
  - added root-page breadcrumb support for page-layout root files (for example `/about.html`, `/notfound.html`)
- Reran full Pelican build and parity checks.

Current checkpoint results:

- `migration/parity/render_parity_summary.md`:
  - URLs checked: `35`
  - strict parity failures: `0`
  - expected deviations: `1` (`/search.html` due Tipue -> PageFind UX change)
- `migration/parity/metadata_audit_summary.md`:
  - markdown files audited: `2483`
  - total issues: `1` (known `index.md` `content:` key)

Cutover-readiness automation and manual QA prep:

- Added cutover readiness script and report generation:
  - `scripts/cutover_readiness.py`
  - output: `migration/cutover_readiness.md`
- Added Make target:
  - `cutover-readiness`
- Added manual QA docs:
  - `migration/parity/manual_parity_checklist.md`
  - `migration/parity/search_investigation.md`

Cutover run notes:

- Ran `make build-pelican-search`:
  - Pelican build succeeded.
  - PageFind step initially failed in sandbox due npm DNS/network restrictions.
- Re-ran `make build-pagefind` with elevated execution:
  - Succeeded (`pagefind v1.4.0`, `3125` pages indexed).
- Ran `make cutover-readiness`:
  - `0` FAIL checks
  - `2` WARN checks:
    - known metadata edge case (`index.md` `content` key)
    - search relevance warning (`4/5` representative terms had `/tag/` top results)

Requested UI/behavior fixes from parity review prep:

- Home page source-list labels:
  - Removed short-source `<abbr>` labels from home page listing to reduce visual noise.
  - File: `themes/occasional-prayers/templates/home.html`
- Tag detail listing labels:
  - Added section/source short labels on tag detail listing rows.
  - File: `themes/occasional-prayers/templates/tag_detail.html`
- Not-found behavior:
  - Added dedicated `404.md` -> `404.html` generation for host-level not-found handling while preserving `notfound.html`.
  - Files: `404.md`, `pelicanconf.py`
  - Updated cutover parity gate to treat `/404.html` as expected extra URL.
  - File: `scripts/cutover_readiness.py`
- Search behavior and design:
  - Replaced PageFind UI widget integration with custom search rendering using PageFind JS API.
  - Added navbar `?q=` bootstrap and in-page dynamic search with load-more pagination.
  - Result rendering now explicitly includes:
    - linked title
    - source label
    - snippet
  - Files:
    - `themes/occasional-prayers/templates/search.html`
    - `css/style.css`

Build/workflow robustness improvement:

- Replaced `rm -rf` output cleanup in Pelican build targets with Python-based directory cleanup due intermittent filesystem `Directory not empty` errors on this volume.
- File: `Makefile`

Search result title/snippet hardening:

- Updated custom search renderer to better handle imperfect metadata/content extraction:
  - prefer prayer-level title and fall back away from site-level title when needed
  - strip leading breadcrumb/source labels before snippet generation
  - strip repeated leading title text so snippet starts with prayer body
- File: `themes/occasional-prayers/templates/search.html`
- Rebuilt assets:
  - `make build-pelican`
  - `make build-pagefind`

Search input UX update:

- Updated search input synchronization to preserve literal whitespace while typing (especially phrase entry with spaces) and only normalize the query internally for execution/URL state.
- File: `themes/occasional-prayers/templates/search.html`
- Rebuilt assets:
  - `make build-pelican`
  - `make build-pagefind`

Snippet content scope refinement:

- Moved `data-pagefind-body` from the page wrapper to the `<main>` element in prayer/page template so indexed snippet content excludes breadcrumb/header attribution chrome and starts from prayer text.
- File: `themes/occasional-prayers/templates/page.html`
- Rebuilt assets:
  - `make build-pelican`
  - `make build-pagefind`

Search index context refinement:

- Added hidden in-`<main>` search index context terms for page source and attribution so those fields remain searchable without showing in visible page chrome.
- Extended search snippet cleanup to strip leading source/attribution context (including PageFind meta `source`/`attribution`) before rendering excerpts.
- Files:
  - `themes/occasional-prayers/templates/page.html`
  - `themes/occasional-prayers/templates/search.html`
  - `css/style.css`
- Rebuilt assets:
  - `.venv-pelican/bin/python -m pelican -q -s pelicanconf.py -o _build_pelican`
  - `make build-pagefind`

Initial migration completion checkpoint:

- Updated parity tooling and build cleanup stability:
  - `scripts/check_render_parity.py`: relaxed `<h2>` extraction to support attributes (for example `data-pagefind-meta="title"`), resolving false render-parity failures.
  - `Makefile`: updated Pelican output cleanup to `shutil.rmtree(..., ignore_errors=True)` for `_build_pelican` and `_build_pelican_smoke` to avoid intermittent filesystem cleanup errors.
- Rebuilt and revalidated:
  - `make build-pelican`
  - `make build-pagefind`
  - `make migration-checks`
  - `make cutover-readiness`
- Final readiness state for initial migration:
  - `migration/cutover_readiness.md` reports `0` FAIL and `1` WARN.
  - Remaining WARN is the known metadata edge case on `index.md` (`content:` key), already mitigated via `index-pelican.md`.
- Updated migration status artifacts to reflect completion:
  - `TODO.md` migration item and regression gate marked complete for initial cutover.
  - `README.md` now reflects Pelican + PageFind as the active build system.
  - `migration/parity/manual_parity_checklist.md` marked complete.
