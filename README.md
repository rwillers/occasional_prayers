# Occasional Prayers

Occasional Prayers is a static website that collects prayers from the *Book of Common Prayer*, the Anglican tradition, and the broader Church in an indexed, searchable format.

The site is built with [Urubu](https://urubu.jandecaluwe.com/) from Markdown content and templates in this repository.

## Project Structure

- `_python/`: small Python helpers and custom template filters used by the build.
- `_layouts/`: site layout templates.
- `css/`, `js/`, `images/`: static assets.
- Prayer/content directories (for example `acna2019/`, `tec1979/`, `parish-year/`): Markdown source files.
- `_build/`: generated output from Urubu.
- `_workingfiles/`: working notes, import/parsing helpers, and scratch content.

## Local Development

### Prerequisites

- Python 3
- Urubu available in your environment

### Common Commands

- Build the site:
  - `make build`
  - or `python3 -m urubu build && touch _build/.nojekyll`
- Serve locally:
  - `make serve`
  - or `python3 -m urubu serve`

## Python Style

Use **Black** for Python code formatting/linting in this project.

- Format all Python code:
  - `python3 -m black _python _workingfiles`
- Check formatting without writing changes:
  - `python3 -m black --check _python _workingfiles`

If you change Python files, run Black before committing.
