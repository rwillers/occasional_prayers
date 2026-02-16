# AGENTS

## Project Context

This repository contains the source for the **Occasional Prayers** website. It is a static site generated with Pelican + PageFind from Markdown content, templates, and small Python helpers.

## Working Agreements

- Treat Markdown content directories (for example `acna2019/`, `tec1979/`, `parish-*`) as canonical source content.
- Treat `_build_pelican/` as generated output; do not manually edit generated HTML unless explicitly requested.
- Keep edits focused and minimal for the task at hand.
- Preserve front matter structure in Markdown files.

## Python Code Standards

- Python helper code lives primarily in `_python/` and `scripts/`.
- Use **Black** as the Python formatting/linting standard.
- Run Black on Python changes before finishing:
  - `.venv-pelican/bin/python -m black _python scripts tests`
  - `.venv-pelican/bin/python -m black --check _python scripts tests`

## Useful Commands

- Build: `make build` or `make build-pelican-search`
- Serve locally: `make serve` or `make serve-pelican`
- Test: `make test`
