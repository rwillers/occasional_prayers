# Urubu Behavior Inventory

This is the initial behavior inventory from the current Urubu site that Pelican must preserve.

## Template/Layout Model

- Source templates live in `_layouts/`.
- Layout values used in front matter include:
  - `home`
  - `index`
  - `page`
  - `search`
  - `tag`
- Shared base template `_layouts/_base.html` provides:
  - page `<title>` from `this.title`
  - navbar + global search input
  - static asset links (`css/`, `images/`, `manifest.json`, `js/format.js`)
  - optional `site.baseurl` URL prefix handling.

## Content Structure Expectations

- Canonical content source is Markdown in top-level content folders (for example `acna2019/`, `tec1979/`, `parish-*`, etc.).
- `index.md` files define section index pages with optional `content` lists.
- Individual prayer pages are mostly numeric filenames and currently publish as `/section/<number>.html`.
- Root pages include `index.md`, `about.md`, `search.md`, and `notfound.md`.

## Metadata/Rendering Expectations

- Front matter keys in active use include at least: `title`, `layout`, `tagline`, `content`, `attribution`, `tags`, `short_title`, and `order`.
- `tags` values drive category/attribution listings and tag pages.
- `attribution` is rendered below titles where present.
- Breadcrumbs are rendered by `page.html` when `this.breadcrumbs` exists.

## Search Behavior

- Current search implementation uses Tipue Search assets under `tipuesearch/`.
- Current `search` layout includes:
  - `tipuesearch.css`
  - `tipuesearch_content.js`/`tipuesearch_content.json`
  - `tipuesearch_set.js`
  - `tipuesearch.min.js`
- Global search form submits to `/search.html?q=...`.

## Tag Pages

- Current build emits tag pages under `/tag/<tag name>/index.html`.
- Current tag list heading text is `Categories & attributions`.
- Tag page links use raw tag text segments (including punctuation and spaces) in URL path.

## Known Migration Implications

- Pelican must be configured as a page-centric build (not article/blog-centric).
- URL patterns must preserve existing `.html` output paths.
- Search page UX can change, but query entry path (`/search.html`) should remain stable.
- Redirect support is required when URL parity is not practical; mapping lives in `migration/redirects.csv`.
