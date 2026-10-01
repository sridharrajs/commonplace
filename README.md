# Commonplace

A [commonplace book](https://en.wikipedia.org/wiki/Commonplace_book) for quotes: keep them in plain YAML files, and get a static website where you can browse them by category, author and tag.

No database and no server. Fork it, edit the YAML, push, and GitHub Pages publishes it for free.

## Make your own

1. Fork this repo (or click **Use this template**).
2. In your fork, go to **Settings → Pages** and set **Source** to **GitHub Actions**.
3. Edit `config.yaml` (title, description, your name, repo URL).
4. Replace the quotes in `quotes/` with your own and push to `main`.

The site is published at `https://<your-username>.github.io/<repo-name>/`.

## Adding quotes

Each file in `quotes/` is a category, and the file name becomes its name (`money.yaml` → **Money**, `side-projects.yaml` → **Side Projects**). Set the order categories appear in with `categories:` in `config.yaml`; any not listed come after, alphabetically. Each file is a list of quotes:

```yaml
- text: The most important quality for an investor is temperament, not intellect.
  author: Warren Buffett
  tags: [investing, temperament]

- text: |
    Sleep is the interest we have to pay on the capital which is called in at death.
    The higher the interest rate and the more regularly it is paid,
    the further the date of redemption is postponed.
  author: Arthur Schopenhauer
  tags: [sleep, longevity]
```

| Field    | Required | Notes                                                        |
| -------- | -------- | ------------------------------------------------------------ |
| `text`   | yes      | Use `text: \|` for multi-line quotes; line breaks are kept.  |
| `author` | no       | Leave it out for anonymous quotes.                           |
| `source` | no       | Book, talk, letter, tweet…                                   |
| `tags` | no       | Any tags you like. A quote can have several.                 |

The build stops with a clear error if a quote has no `text` or has a field it doesn't recognise (usually a typo).

### Why YAML?

The quotes are typed by hand, so the format is chosen for writing rather than for machines (the build still publishes `quotes.json` for those):

- **Quote marks need no escaping.** Quotes often contain `"` or `'`; in JSON each inner `"` would have to be written `\"`.
- **Multi-line text reads naturally.** `text: |` keeps line breaks exactly as typed, which matters for poems and letters.
- **Less punctuation.** No braces, quoted keys, or commas to forget.
- **Comments are allowed.** Use `# ...` to leave yourself notes.
- **Cleaner diffs.** Adding a quote adds lines without touching the one above it.

### YAML pitfalls

A few characters mean something to YAML. Look out for these when you add quotes:

| You write                     | YAML reads                  | Fix                                   |
| ----------------------------- | --------------------------- | ------------------------------------- |
| `text: Rule 1: never lose money` | build error (`: ` inside the text) | wrap in quotes, or use `text: \|`   |
| `text: We're #1 at this`      | `We're`, **silently truncated** (` #` starts a comment) | wrap in quotes, or use `text: \|` |
| `tags: [no, 1984]`          | `False`, `1984` (a boolean and a number) | `tags: ["no", "1984"]`   |

**Rule of thumb:** if a quote contains `: ` or ` #`, or starts with a quote mark, `[`, `{`, `*`, `&`, `!` or `-`, write it as a block:

```yaml
- text: |
    Rule No. 1: Never lose money. Rule No. 2: Never forget rule No. 1.
  author: Warren Buffett
```

Watch out for the `#` truncation in particular: it doesn't cause an error, so check the built page if a quote looks cut short.

## What gets built

- `/` — a random quote, then an index of every category, tag and author with quote counts
- `/category/<name>/`, `/author/<name>/`, `/tag/<name>/` — one page each
- `/quotes.json` — all quotes as JSON, for reuse elsewhere

## Run it locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python build.py --serve     # builds into _site/ and serves http://127.0.0.1:8000
```

To change the look, edit `templates/` (Jinja2) and `static/style.css`.
