# Phase 2.5 Decision Log

Use this to lock policy decisions before finalizing canonical mappings.
Reference model: `migration/taxonomy/provenance_model.md`.
Status: approved.

Locked choices from review:

- Keep facet names as-is.
- Default ambiguous medium-confidence provenance rows to `source_text`.
- Keep default for ambiguous `After ...` rows (`source_text` when target is not clearly a person).

## Proposed Provenance Model

- `attribution`: associated with or following a specific author/person.
- `citation`: scriptural basis (book/chapter/verse references).
- `source`: non-scriptural textual source (prayer books, breviaries, sacramentaries, liturgies, church orders, etc.).

## Decision 1: Medium-confidence provenance rows

Scope: rows in `migration/taxonomy/tag_mapping_proposed.csv` where `confidence=medium` and `reviewed_action != keep`.

Recommended default:

- Accept proposed action (`move_to_attribution` or `move_to_source`) except where you want an explicit override.

## Decision 2: Source-like labels as tags vs attribution

Examples:

- `American Prayer Book`
- `Book of Common Order`
- `Prayers for the Christian Year`
- `New Every Morning`
- `Church of South India`

Recommended default:

- Treat these as `source` provenance, not `attribution` and not topical tags.

## Decision 3: Facet vocabulary for kept tags

Current proposal values:

- `topic`
- `prayer_type`
- `life_or_church_context`
- `liturgical_season`

Recommended default:

- Keep this 4-facet vocabulary for initial cleanup; refine labels later only if needed.

## Decision 4: Citation handling (scripture only)

Scope: provenance strings with explicit scripture references.

Recommended default:

- Use `move_to_citation` only for scriptural references.
- Route non-scriptural “Based on/Adapted from/From ...” rows to `move_to_source`.

## Decision 5: Provenance In Tags

Question: should one-off provenance values (especially `After ...`, `Adapted from ...`, `Based on ...`, `From ...`) remain as topical tags?

Decision:

- Do not keep provenance values as topical tags.
- Keep provenance in `attribution_author`, `citation_scripture`, and `source_text`.
- Treat `tags` as topical browsing taxonomy only.

## Decision 6: Merge candidates

Source: `migration/taxonomy/tag_merge_candidates.csv` (`4` candidates).

Recommended default:

- Approve merge for:
  - `The Epiphany` -> `Epiphany`
  - `Diocese of Southwark` <-> `Southwark Diocese` (choose one canonical)
- Hold for manual review:
  - `From a prayer of the Eastern Church` <-> `A Prayer of the Eastern Church`
  - `From the Order of Compline` <-> `Order of Compline`

Decision:

- Accept all 4 merge candidates as presented
