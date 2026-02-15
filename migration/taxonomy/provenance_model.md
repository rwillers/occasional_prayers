# Provenance Model (Phase 2.5)

This model separates provenance from topical categorization.

## Facets

- `attribution_author`
  - Meaning: associated with or following a specific author/person.
  - Examples: `Frank Colquhoun`, `Augustine`, `After Jeremy Taylor`.
- `citation_scripture`
  - Meaning: scriptural basis or explicit biblical reference.
  - Examples: `Based on Romans 15:13`, `Ephesians 3:14–19`.
- `source_text`
  - Meaning: non-scriptural source text or institutional/liturgical source.
  - Examples: `Adapted from Book of Common Prayer`, `American Prayer Book`, `Church of South India`.

Topical browsing remains in `tags` and uses:

- `topic`
- `prayer_type`
- `life_or_church_context`
- `liturgical_season`

Policy:

- Provenance facets are stored as metadata and removed from topical `tags`.
- Topical `tags` should not include one-off provenance strings.

## Decision Rules

1. If provenance string includes scripture reference (book + chapter), classify as `citation_scripture`.
2. If provenance string refers to prayer-book/liturgical/institutional source, classify as `source_text`.
3. If provenance string refers to a specific person, classify as `attribution_author`.
4. If unclear, keep as medium-confidence and require manual review before migration.

## Important Ambiguities

Some values still need explicit review because automated classification is not definitive:

- `Daily Prayer`
- `Prayers for the Christian Year`
- `New Every Morning`
