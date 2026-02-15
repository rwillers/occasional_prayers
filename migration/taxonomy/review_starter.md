# Taxonomy Review Starter

This file prioritizes the first decision batches from generated inventory artifacts so review can start with the highest-impact rows.

## Batch Order

1. Resolve provenance semantics first (`move_to_citation`, `move_to_source`, `move_to_attribution`).
2. Resolve overlap tags second (author vs source split).
3. Review remaining high-volume tags for merges/grouping.
4. Fill redirect mapping only for true tag renames/merges.

## Batch 1: Prefixed Provenance Tags

Sources:

- `migration/taxonomy/citation_like_tags.csv` (scriptural citation candidates)
- `migration/taxonomy/source_provenance_tags.csv` (non-scriptural source candidates)

High-frequency examples:

- `Adapted from Book of Common Prayer` (`12`)
- `After the Third Collect` (`7`)
- `After Jeremy Taylor` (`3`)
- `Adapted from Gelasian Sacramentary` (`2`)
- `Adapted from Irish Prayer Book` (`2`)
- `Adapted from Jeremy Taylor` (`2`)
- `Adapted from various sources` (`2`)
- `After Gelasian Sacramentary` (`2`)
- `After J. H. Newman` (`2`)
- `After Lancelot Andrewes` (`2`)

Recommended review action:

- Keep topical tags clean by moving provenance-like values out of `tags`.
- Route scriptural references to `citation`.
- Route non-scriptural textual provenance to `source`.
- Keep `attribution` for specific persons/authors.
- Default provenance rows to `remove_from_tags` in the mapping proposal.

## Batch 2: Overlap Tags (Author vs Source)

Source: `migration/taxonomy/tag_mapping_seed.csv` (`264` suggested `move_to_attribution` rows).

Highest-impact overlap examples:

- `Frank Colquhoun` (`109` overlaps)
- `American Prayer Book` (`33` overlaps of `36` tag assignments)
- `Daily Prayer` (`35` overlaps of `36` tag assignments)
- `Augustine` (`29` overlaps)
- `Church of South India` (`27` overlaps)
- `Book of Common Order` (`23` overlaps of `25` tag assignments)
- `New Every Morning` (`20` overlaps of `25` tag assignments)
- `Scottish Prayer Book` (`23` overlaps)
- `William Temple` (`22` overlaps)
- `Prayers for the Christian Year` (`19` overlaps of `21` tag assignments)

Recommended review action:

- When a value is mostly provenance/credit and appears as attribution on most pages, move it out of topical tags.
- Use `attribution` for specific persons/authors; use `source` for non-person textual or institutional sources.
- Keep an exception list where the value is intentionally navigational as a tag.

## Batch 3: Remaining Topical Tag Consolidation

Source: `migration/taxonomy/tag_inventory.csv`.

Focus first on high-volume topical categories that shape browsing:

- `The Church’s Year`
- `Intercessory Prayers`
- `Various Occasions`
- `Devotional Prayers`
- `The Trinity Season`
- `Sacraments and Ordinances`

Recommended review action:

- Define canonical group facets (season, life-context, church-context, sacramental context, source/tradition).
- Merge only truly redundant labels, then generate redirect mappings for renamed tags.

## Working Files to Edit During Review

- `migration/taxonomy/tag_mapping_seed.csv`:
  - fill `reviewed_action`, `reviewed_facet`, `review_notes`
- `migration/taxonomy/tag_mapping_proposed.csv`:
  - apply overrides to proposal rows with `confidence=medium`
- `migration/taxonomy/tag_mapping_template.csv`:
  - finalize canonical tag mappings
- `migration/taxonomy/attribution_mapping_template.csv`:
  - canonical attribution normalization
- `migration/taxonomy/tag_redirect_template.csv`:
  - add old/new tag path mappings for renamed tags
