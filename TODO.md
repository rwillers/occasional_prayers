# TODO

- [ ] Migrate site from Urubu to Pelican + PageFind.
- [ ] Revisit categorization approach (consolidate similar and related terms, consider ability to nest categories, put tags into logical groupings, rethink attribution/citation inclusion given large number, etc.).
- [ ] Standardize visual design and supporting CSS with Ordinarium.com project.
- [ ] Add (beta) prayer language modernization feature ("thou" -> "you", etc.)
- [ ] Add 1559 occasional prayers (http://justus.anglican.org/resources/bcp/1559/Godly_Prayers.htm) [1552 and 1549 don't have separate sections]
- [ ] Add 1979 collects
- [ ] Add 1979 additional prayers
- [ ] Add 1928 collects

## Plan: Urubu -> Pelican + PageFind Migration

### Objective

Replace Urubu with Pelican as the static site generator and add PageFind for full-text search, while preserving current URLs, content fidelity, templates, metadata behavior, and deploy workflow.

### Confirmed Decisions (2026-02-14)

- Deployment target remains the current custom host flow (as used by existing publish process), with room to improve the deployment mechanism later (for example GitHub Actions).
- URL continuity is required; redirects are acceptable where exact parity is not practical.
- Search UX can be improved as part of this migration.
- Use a new output directory before cutover (for example `_build_pelican`), then switch to final output path at release.
- Use `requirements.txt` for dependency management.
- Perform a single cutover release, not phased section-by-section migration.
- Use Python `3.12` for Pelican/PageFind tooling unless a compatibility issue is discovered.
- Implement redirects as repo-managed generated HTML redirect pages (source-controlled mapping), not as server-only rules.

### Scope

In scope:
- Build-system migration from `python3 -m urubu` to Pelican commands and config.
- Template migration from current layouts to Pelican Jinja templates.
- Content parsing and metadata compatibility for all existing Markdown content.
- PageFind indexing and search UI integration.
- Local build, serve, and production/deploy parity.
- Regression checks for URLs, tags, and rendering fidelity.

Out of scope for this migration:
- Taxonomy redesign (covered by a separate TODO item).
- Visual redesign (covered by a separate TODO item).
- Net-new content additions (covered by separate TODO items).

### Success Criteria

- All current content sections build without manual file-by-file edits.
- Existing canonical URLs remain stable where feasible; any URL changes are explicitly mapped with redirects.
- Tag/category/archive pages are generated with equivalent behavior.
- Search is powered by PageFind, works for representative queries across major sections, and improves current search UX.
- Build process is reproducible locally with documented commands.
- Deployment output remains static and host-compatible (including `.nojekyll` behavior if still required).

### Implementation Plan

1. Discovery and baseline capture
- Inventory current build behavior from `Makefile`, `_site.yml`, `_layouts/`, `_python/`, and generated `_build/`.
- Capture baseline artifacts:
  - URL inventory from current built site.
  - Representative pages from each major content section.
  - Current search behavior and search index assets.
- Identify Urubu-specific features currently relied on (custom filters, metadata conventions, collections, pagination, tag pages).

2. Pelican foundation setup
- Add Pelican dependencies and define pinned versions.
- Add/maintain `requirements.txt` as the source of Python dependencies for migration and runtime tooling.
- Create Pelican config for:
  - Content paths and static paths.
  - URL and save-as patterns matching current structure.
  - Timezone/default metadata handling.
  - Tag/category behavior and slug rules.
- Add separate dev/prod config overlays if needed.
- Add minimal smoke build command and verify output into a new build directory (for example `_build_pelican`).

3. Template and asset migration
- Port `_layouts/` templates into Pelican theme/templates while preserving existing markup and CSS hooks.
- Migrate shared partials/macros and metadata rendering behavior.
- Wire current static assets (`css/`, `js/`, `images/`) into Pelican static handling.
- Keep general visual output unchanged except where needed to improve search UX.

4. Content and metadata compatibility
- Validate front matter parsing across all sections.
- Implement metadata adapters or preprocessors for edge cases:
  - Missing/variant metadata keys.
  - Existing tag field conventions.
  - Any Urubu-specific parsing assumptions.
- Integrate existing Python filters/helpers into Pelican plugin/filter hooks where required.

5. PageFind integration
- Add PageFind build step to index Pelican output.
- Create or migrate search page UI to use PageFind JS assets and query API.
- Ensure indexing excludes non-content pages where appropriate.
- Validate search relevance, snippet rendering, and performance on large content sets.

6. Build, serve, and deploy workflow updates
- Update `Makefile` and README build commands for Pelican + PageFind.
- Preserve developer ergonomics for local build/serve.
- Confirm deploy compatibility with current custom hosting target, including static output root and `.nojekyll` expectations.
- Keep current deploy path functional for cutover; optionally design a follow-up GitHub Actions deploy path after cutover.

7. Regression verification and rollout
- Run URL parity checks between Urubu output and Pelican output.
- Run content parity checks on a representative sample (including long, tagged, and edge-case pages).
- Run link integrity checks and manual QA on navigation and search.
- Prepare single-release cutover checklist:
  - Freeze content changes during final switch window.
  - Final rebuild with Pelican + PageFind.
  - Deploy and post-deploy verification.
- Keep rollback option:
  - Retain Urubu build path temporarily until Pelican release is verified.

### Redirect Implementation Specification (Repo-Managed)

Redirect source of truth:
- Add a versioned mapping file at `migration/redirects.csv`.
- CSV columns:
  - `old_path`: legacy request path beginning with `/` (for example `/acna2019/4 2.html`).
  - `new_path`: target canonical path beginning with `/`.
  - `status`: redirect type (`301` default for permanent).
  - `note`: optional migration note/context.

Generation step:
- Add a build-time script (for example `scripts/generate_redirects.py`) that reads `migration/redirects.csv`.
- For each mapping, generate an HTML file at the legacy path in build output containing:
  - `<meta http-equiv="refresh" content="0; url=...">`
  - `<link rel="canonical" href="...">`
  - Small JS fallback `window.location.replace(...)`.
- Ensure generated redirect pages are excluded from PageFind indexing.

Validation step:
- Fail build on duplicate `old_path` entries.
- Fail build when `new_path` does not exist in generated output.
- Fail build when redirect loops are detected.
- Emit a redirect summary report (count generated, count invalid, unresolved paths).

Operational rules:
- Prefer exact URL parity first; use redirects only where parity is not practical.
- New redirect entries must be added in the same pull request as any URL-changing migration change.
- Keep redirect mappings indefinitely unless explicit cleanup decision is made after traffic analysis.

### Deliverables

- Pelican config files and dependency updates.
- Migrated templates and static asset wiring.
- PageFind-enabled search implementation.
- Updated `Makefile` and `/Users/rwillers/Library/Mobile Documents/com~apple~CloudDocs/Sites/occasional_prayers/README.md`.
- Migration notes with parity-check results and known deviations.

### Risks and Mitigations

- URL drift risk:
  - Mitigation: enforce explicit URL/save-as patterns and compare URL manifests before cutover.
- Metadata inconsistency across large corpus:
  - Mitigation: run metadata audit script and introduce normalization rules.
- Search quality regression:
  - Mitigation: define test queries across sections and compare result quality before cutover.
- Template behavior differences:
  - Mitigation: snapshot and diff representative rendered pages.

### Estimated Execution Order

1. Discovery and baseline capture.
2. Pelican foundation setup.
3. Template migration.
4. Metadata compatibility.
5. PageFind integration.
6. Workflow updates.
7. Regression verification and cutover.

### Clarifications Needed Before Execution

- None currently blocking execution planning.
