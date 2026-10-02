# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static-site generator for a commonplace book of quotes. Quotes live in `quotes/*.yaml`; `build.py` renders them with Jinja2 into `_site/`, which GitHub Actions (`.github/workflows/deploy.yml`, Python 3.12) publishes to GitHub Pages on every push to `main`. There is no database, server, test suite or linter.

## Commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt     # Jinja2, PyYAML — the only dependencies

python build.py                      # build into _site/ (wiped and rebuilt every time)
python build.py --serve [--port N]   # build, then serve http://127.0.0.1:8000
```

The build is the only check: it exits non-zero with `error: <file>, quote #N: ...` on invalid YAML, a quote missing `text`, or any field outside `ALLOWED_FIELDS` (`text`, `author`, `source`, `tags`). After changing quotes or templates, run `python build.py` to confirm it still builds.

## Architecture

Everything happens in `build.py` in one pass: `load_quotes()` → `group()` → `render()`.

- **Categories come from file names.** `quotes/side-projects.yaml` becomes category "Side Projects" (slug `side-projects`). Nothing inside a quote declares its category. `categories:` in `config.yaml` sets their order (`order_categories()`); unlisted ones follow alphabetically, and a listed name with no file is a build error.
- **Quotes are normalized into dicts** with `id`, `text`, `author`/`author_slug`, `source`, `category`/`category_slug`, and `tags` as a list of `{name, slug}`. Templates depend on this shape, so update them together if you change it.
- **Quote `id`s** are slugs built from the author plus the first six words of the text, with `-2`, `-3`… added when two collide. They are used as HTML anchors, so editing a quote's opening words or author changes its permalink.
- **`group(quotes, keys)`** is the one grouping helper behind categories, authors and tags. Each group is `{name, slug, quotes}`, sorted by name.
- **Pages:** `home.html` → `index.html` (random quote + all categories and the top `HOME_LIMIT` (10) tags and authors by quote count; no full quote list); `terms.html` → `tag/index.html` and `author/index.html` (the full lists); `group.html` → `category|author|tag/<slug>/index.html`. `tag_cloud` and `author_list` in `_macros.html` render those lists. `quotes.json` is exported alongside them.
- **All links are relative.** `render()` works out `root` (`./`, `../../`, …) from how deep the output path is, and every template must build links as `{{ root }}...`. This is what lets the site work under a GitHub Pages project path (`/<repo>/`). Never use absolute `/` links.
- **Template globals:** `site` is the parsed `config.yaml` (`title`, `description`, `owner`, `language`, `about_url`, `repo_url`, `categories`, all optional; `about_url` and `repo_url` are the footer links), and `categories` is the ordered category list that the header nav on every page uses. `css_version` is a hash of `static/style.css`, appended to the stylesheet link in `base.html` (`style.css?v=…`) so browsers drop a cached copy whenever the CSS changes. `templates/_macros.html` has `quote_card`, which every page uses to render a quote.
- **`static/random.js`** has no data source of its own. It clones a random `.quote` from the `<template id="quote-pool">` that `home.html` fills with every `quote_card`, into `#random-slot`.
- `_site/` is build output and is gitignored. Don't edit it by hand.
