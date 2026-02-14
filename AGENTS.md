# AGENTS

## Project Context

This repository contains the source for the **Occasional Prayers** website. It is a static site generated with Urubu from Markdown content, templates, and small Python helpers.

## Working Agreements

- Treat Markdown content directories (for example `acna2019/`, `tec1979/`, `parish-*`) as canonical source content.
- Treat `_build/` as generated output; do not manually edit generated HTML unless explicitly requested.
- Keep edits focused and minimal for the task at hand.
- Preserve front matter structure in Markdown files.

## Python Code Standards

- Python helper code lives primarily in `_python/` (and some scripts in `_workingfiles/`).
- Use **Black** as the Python formatting/linting standard.
- Run Black on Python changes before finishing:
  - `python3 -m black _python _workingfiles`
  - `python3 -m black --check _python _workingfiles`

## Useful Commands

- Build: `make build` or `python3 -m urubu build`
- Serve locally: `make serve` or `python3 -m urubu serve`
