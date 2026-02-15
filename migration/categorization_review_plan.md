# Categorization Review and Cleanup Plan

## Goal

Complete one comprehensive taxonomy cleanup so tags, attribution, citation, and source metadata are consistent, maintainable, and search-friendly without introducing URL regressions.

## Why This Is Needed (Current Baseline)

Current in-repo metadata and migration artifacts indicate the taxonomy has grown organically and now mixes multiple concepts:

- `2484` markdown files in active scope.
- `2462` files with `tags`.
- `1318` files with `attribution`.
- `644` distinct tags.
- `487` distinct attribution values.
- `1159` files where `attribution` is duplicated as a tag.
- `111` files with citation-like tags (`After ...`, `Adapted from ...`, `Based on ...`).
- `272` tags are singletons.
- `645` generated tag pages currently exist in output.

This confirms the TODO concern: categorization, grouping, and provenance handling are currently conflated.

## Non-Goals

- Do not manually edit generated HTML in `_build_pelican/`.
- Do not redesign the whole front-end information architecture in the same pass.
- Do not rewrite prayer text/content except metadata normalization.

## Success Criteria

- Every content page has normalized metadata according to a documented schema.
- No attribution value is duplicated in topical tags unless explicitly intentional.
- Citation/source semantics are not represented as free-form topical tags.
- Tags are reserved for topical browsing facets only.
- Tag URLs remain backward-compatible via redirects or alias handling.
- Build, metadata audit, and parity checks pass.
- Taxonomy policy is documented so future imports remain clean.

## Proposed Canonical Metadata Model

Use explicit metadata fields with clear semantic boundaries:

- `tags`: topical categories used for tag navigation pages.
- `attribution`: associated with or following a specific author/person.
- `citation`: scriptural basis (for example explicit biblical references).
- `source`: non-scriptural textual source (for example prayer books, breviaries, sacramentaries, liturgies).

If adding `source` or `citation` is too large for this pass, keep them in mapping/report artifacts first and stage schema extension in the same branch before final cleanup commit.

## Execution Plan

### Phase 1: Taxonomy Inventory and Decision Framework

1. Generate a taxonomy inventory report from front matter:
   - distinct tags with counts
   - distinct attribution values with counts
   - overlap matrix (`tag == attribution`)
   - citation-like tag list
   - near-duplicates and formatting variants
2. Define facet policy:
   - topical category
   - liturgical season/time
   - life context
   - sacramental/office context
   - source/tradition
   - attribution/citation/source provenance
3. Decide nesting strategy:
   - represent nesting as grouped display only (preferred low-risk), or
   - encode hierarchy in metadata fields and grouped templates.

### Phase 2: Canonical Vocabulary and Mapping Table

1. Create a controlled vocabulary file (CSV or YAML) with:
   - `raw_value`
   - `canonical_value`
   - `facet`
   - `action` (`keep`, `merge`, `move_to_attribution`, `move_to_citation`, `move_to_source`, `drop`)
2. Add a second table for URL continuity:
   - `old_tag`
   - `new_tag`
   - expected redirect path pair
3. Review and freeze mapping before mass edits.

### Phase 3: Automated Migration

1. Implement/extend a script to apply mapping to front matter in canonical content directories.
2. Script behavior:
   - idempotent updates
   - preserve front matter ordering/shape
   - keep deterministic tag ordering
   - emit CSV reports of each transformed file and each dropped/rewired value
3. For changed tag names, generate redirect entries for old `/tag/<old>/` paths to new canonical paths.

### Phase 4: Template and Search Alignment

1. Update tag index/detail templates to support grouped display (if nesting/grouping chosen).
2. Ensure search context still indexes meaningful source/attribution signals without over-weighting tag listings.
3. Re-run representative search checks to verify reduced tag-page dominance regressions.

### Phase 5: Validation and QA

1. Run automated checks:
   - `make audit-metadata`
   - `make test`
   - `make build-pelican`
   - `make build-pagefind` (in network-enabled environment)
   - `make cutover-readiness`
2. Add a taxonomy-specific audit output:
   - orphan/unknown tags
   - disallowed citation patterns remaining in `tags`
   - attribution/tag overlap count target
3. Manual QA:
   - tag index usability
   - tag detail relevance
   - representative search queries
   - redirect verification for renamed tags

### Phase 6: Governance and Lock-In

1. Document taxonomy policy in `README.md` (or dedicated metadata guide).
2. Add import/update guardrails:
   - lint check against controlled vocabulary
   - pre-commit or CI check to reject new uncategorized/free-form provenance tags
3. Close TODO only when metrics and QA gates pass.

## One-Pass Delivery Checklist

- [ ] Controlled vocabulary and mapping files committed.
- [ ] Front matter migration script committed.
- [ ] Canonical metadata migration applied to source markdown.
- [ ] Tag URL redirects generated for renamed tags.
- [ ] Template/search adjustments completed if needed.
- [ ] Automated checks and manual QA completed with results recorded.
- [ ] Taxonomy governance docs updated.
