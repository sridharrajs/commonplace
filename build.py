#!/usr/bin/env python3
"""Build the commonplace book from quotes/*.yaml into a static site in _site/."""

import argparse
import functools
import http.server
import json
import re
import shutil
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
QUOTES_DIR = ROOT / "quotes"
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
OUT_DIR = ROOT / "_site"

ALLOWED_FIELDS = {"text", "author", "source", "tags"}


class BuildError(Exception):
    pass


def slugify(value):
    slug = re.sub(r"[^\w]+", "-", value.lower()).strip("-")
    return slug or "untitled"


def load_config():
    path = ROOT / "config.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_quotes():
    """Read every quotes/<category>.yaml file. The file name is the category."""
    quotes = []
    seen_ids = set()
    for path in sorted(QUOTES_DIR.glob("*.yaml")):
        entries = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        if not isinstance(entries, list):
            raise BuildError(f"{path.name}: expected a list of quotes")

        category = path.stem
        for i, entry in enumerate(entries, 1):
            where = f"{path.name}, quote #{i}"
            if not isinstance(entry, dict) or not str(entry.get("text") or "").strip():
                raise BuildError(f"{where}: every quote needs a 'text' field")
            unknown = set(entry) - ALLOWED_FIELDS
            if unknown:
                raise BuildError(f"{where}: unknown field(s) {', '.join(sorted(unknown))}; allowed: {', '.join(sorted(ALLOWED_FIELDS))}")

            text = str(entry["text"]).strip()
            author = str(entry.get("author") or "").strip() or None
            tags = entry.get("tags") or []
            if isinstance(tags, str):
                tags = [tags]

            # Stable id from author + opening words, used as the quote's anchor.
            base_id = slugify(f"{author or 'anonymous'} {' '.join(text.split()[:6])}")
            quote_id, n = base_id, 2
            while quote_id in seen_ids:
                quote_id, n = f"{base_id}-{n}", n + 1
            seen_ids.add(quote_id)

            quotes.append(
                {
                    "id": quote_id,
                    "text": text,
                    "author": author,
                    "author_slug": slugify(author) if author else None,
                    "source": str(entry.get("source") or "").strip() or None,
                    "category": category.replace("-", " ").title(),
                    "category_slug": slugify(category),
                    "tags": [{"name": str(t).strip(), "slug": slugify(str(t))} for t in tags if str(t).strip()],
                }
            )
    return quotes


def group(quotes, keys):
    """Group quotes by the (name, slug) pairs returned by keys(quote)."""
    groups = {}
    for quote in quotes:
        for name, slug in keys(quote):
            groups.setdefault(slug, {"name": name, "slug": slug, "quotes": []})["quotes"].append(quote)
    return sorted(groups.values(), key=lambda g: g["name"].lower())


def order_categories(categories, order):
    """Put categories in the order given in config.yaml; unlisted ones follow alphabetically."""
    slugs = [slugify(str(name)) for name in order or []]
    unknown = [s for s in slugs if s not in {c["slug"] for c in categories}]
    if unknown:
        raise BuildError(f"config.yaml: categories lists {', '.join(unknown)}, but there is no matching file in quotes/")
    rank = {slug: i for i, slug in enumerate(slugs)}
    return sorted(categories, key=lambda c: rank.get(c["slug"], len(rank)))


def render(env, template, out_path, **context):
    # Relative links ("../../") let the site work at any URL, including a GitHub Pages project path.
    depth = out_path.count("/")
    root = "../" * depth or "./"
    out = OUT_DIR / out_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(env.get_template(template).render(root=root, **context), encoding="utf-8")


def build():
    config = load_config()
    quotes = load_quotes()

    categories = order_categories(group(quotes, lambda q: [(q["category"], q["category_slug"])]), config.get("categories"))
    authors = group(quotes, lambda q: [(q["author"], q["author_slug"])] if q["author"] else [])
    tags = group(quotes, lambda q: [(t["name"], t["slug"]) for t in q["tags"]])

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir()

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)
    env.globals["site"] = config
    env.globals["categories"] = categories  # for the header nav on every page

    render(env, "home.html", "index.html", quotes=quotes, categories=categories, authors=authors, tags=tags)
    for kind, label, groups in (("category", "Category", categories), ("author", "Author", authors), ("tag", "Tag", tags)):
        for g in groups:
            render(env, "group.html", f"{kind}/{g['slug']}/index.html", label=label, group=g)

    shutil.copytree(STATIC_DIR, OUT_DIR / "static")
    (OUT_DIR / ".nojekyll").touch()
    export = [{k: q[k] for k in ("id", "text", "author", "source", "category")} | {"tags": [t["name"] for t in q["tags"]]} for q in quotes]
    (OUT_DIR / "quotes.json").write_text(json.dumps(export, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Built {len(quotes)} quotes · {len(categories)} categories · {len(authors)} authors · {len(tags)} tags → {OUT_DIR.relative_to(ROOT)}/")


def serve(port):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=OUT_DIR)
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Serving at http://127.0.0.1:{port}  (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true", help="serve the built site locally after building")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    try:
        build()
    except (BuildError, yaml.YAMLError) as e:
        sys.exit(f"error: {e}")

    if args.serve:
        serve(args.port)


if __name__ == "__main__":
    main()
