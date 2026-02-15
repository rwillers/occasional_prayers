# Cutover Readiness Report

- Generated: `2026-02-15T14:36:53`
- FAIL checks: `0`
- WARN checks: `1`

## Automated Checks
| Check | Status | Detail |
|---|---|---|
| Build output | PASS | _build_pelican has 3127 HTML files |
| URL parity | PASS | missing=0, extra=1 (expected: /404.html) |
| Redirect validation | PASS | redirect generation/validation succeeded |
| Metadata audit | WARN | only known issue remains (index.md content key; handled by index-pelican.md) |
| Render parity | PASS | strict failures=0, expected deviations=1 |
| PageFind assets | PASS | pagefind indexed pages=2465 |
| PageFind queries | PASS | representative terms return non-zero results |

## Manual Cutover Tasks
- Freeze content changes during final switch window.
- Run final `make build-pelican-search` in a network-enabled environment.
- Run post-deploy smoke checks: home, section pages, tag pages, search, and 404.
- Keep Urubu build path available until post-deploy verification is complete.

## Manual Search QA Focus
- Compare search result ordering for representative terms against current production behavior.
- Verify search UX on mobile and desktop (input behavior, result rendering, keyboard navigation).
- Check whether tag pages over-dominate results and tune indexing rules if needed.
