# Search Parity Investigation (Manual QA Prep)

## Context

- Legacy search engine: Tipue Search (`_build/tipuesearch/tipuesearch_content.json`)
- Migrated search engine: PageFind (`_build_pelican/pagefind/`)
- Goal: identify and validate significant functionality/UI differences before cutover.
- Current search UI implementation is custom-rendered from PageFind JS API (not default PageFind UI widget) and now displays:
  - linked title
  - source label
  - snippet

## Current Automated Findings

- Representative query artifact: `migration/parity/pagefind_query_results.tsv`
- Top-result pattern:
  - `unity` -> top result is `/tag/...`
  - `easter` -> top result is `/tag/...`
  - `marriage` -> top result is `/tag/...`
  - `healing` -> top result is content page
  - `thanksgiving` -> top result is `/tag/...`
- Cutover readiness flags this as a warning:
  - `top results skew to tag pages for many terms (4/5)`

## Corpus Comparison Notes

- Tipue source corpus (`tipuesearch_content.json`):
  - total pages: `3126`
  - tag pages included: `645`
- Pelican/PageFind source corpus (`_build_pelican`):
  - total HTML pages: `3126`
  - tag pages present: `645`
  - PageFind indexed pages: `3125` (search page intentionally excluded)

Interpretation: tag pages were present in both old and new index corpora, but ranking behavior appears different and needs manual confirmation.

## Likely Causes For Observed Differences

1. Ranking model differences between Tipue and PageFind.
2. PageFind currently indexes full `<body>` content (not a constrained `data-pagefind-body` region), which may increase navigation/tag text influence.
3. Search UI component changed from Tipue templates to default PageFind UI rendering.

## Manual QA Focus

1. Compare relevance ordering vs production for representative terms.
2. Validate whether tag pages dominating top results is acceptable.
3. Validate UI differences on desktop/mobile:
   - result card hierarchy
   - snippet readability
   - spacing/typography
   - keyboard/focus behavior

## Candidate Remediations (if manual QA confirms issues)

1. Exclude `/tag/` pages from indexing.
2. Add `data-pagefind-body` to narrow indexed regions to content body only.
3. Add/adjust CSS overrides to close UI parity gaps with existing site style.
