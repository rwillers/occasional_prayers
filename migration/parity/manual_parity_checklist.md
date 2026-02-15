# Manual Parity Checklist

Use this checklist after running:

- `make build-pelican`
- `make build-pagefind`
- `make cutover-readiness`

Status: Completed for initial migration cutover readiness on `2026-02-15`.

## Core Navigation

- [x] Home page renders and section links match current production.
- [x] Section index pages render correct title, tagline, and item ordering.
- [x] Representative content pages render with expected breadcrumbs.
- [x] Tag index and tag detail pages render and navigate correctly.
- [x] About page and notfound page render correctly.

## URL and Link Behavior

- [x] URLs open at expected canonical paths.
- [x] Internal links resolve (no broken links in header/footer/content).
- [x] `.nojekyll` is present in build output.
- [x] Redirect map behavior matches expectations (if redirects are added).

## Search: Functional Parity

- [x] Query from navbar (`?q=`) pre-fills and triggers search on `/search.html`.
- [x] Representative terms return relevant results:
  - [x] `unity`
  - [x] `easter`
  - [x] `marriage`
  - [x] `healing`
  - [x] `thanksgiving`
- [x] Result snippets display readable context.
- [x] Search result links navigate correctly.
- [x] Empty/short query behavior is acceptable.

## Search: UI Parity

- [x] Search page spacing and typography are acceptable on desktop.
- [x] Search page spacing and typography are acceptable on mobile.
- [x] Search input, buttons, and results are styled consistently with site theme.
- [x] Keyboard behavior is acceptable (focus state, enter-to-search, tab order).
- [x] Dark mode readability is acceptable.

## Search Investigation Focus

Current automated query artifact (`migration/parity/pagefind_query_results.tsv`) shows several representative terms with top results pointing to `/tag/...` URLs. During manual QA, confirm whether this is acceptable or needs tuning.

If not acceptable, likely next actions:

1. Exclude tag index/detail pages from PageFind indexing.
2. Tune searchable region to prioritize prayer body content over navigation/tag lists.
3. Adjust search UI rendering defaults (result weighting/display options).
