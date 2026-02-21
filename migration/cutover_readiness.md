# Cutover Readiness Report

- Generated: `2026-02-20T22:05:38`
- FAIL checks: `0`
- WARN checks: `2`

## Automated Checks
| Check | Status | Detail |
|---|---|---|
| Build output | PASS | _build_pelican has 2551 HTML files |
| URL parity | WARN | non-tag parity exact; tag_delta_missing=609, tag_delta_extra=4 |
| Redirect validation | PASS | redirect generation/validation succeeded |
| Metadata audit | WARN | only known issue remains (index.md content key; handled by index-pelican.md) |
| PageFind assets | PASS | pagefind indexed pages=2493 |
| PageFind queries | PASS | representative terms return non-zero results |

## Manual Cutover Tasks
- Freeze content changes during final switch window.
- Run final `make build-pelican-search` in a network-enabled environment.
- Run post-deploy smoke checks: home, section pages, tag pages, search, and 404.

## Manual Search QA Focus
- Compare search result ordering for representative terms against current production behavior.
- Verify search UX on mobile and desktop (input behavior, result rendering, keyboard navigation).
- Check whether tag pages over-dominate results and tune indexing rules if needed.
