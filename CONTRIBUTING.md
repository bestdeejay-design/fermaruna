# Contributing to Fermaruna

Thanks for your interest in the Ferma "Runskaya" static farm website
(live at http://fermaruna.ru). This guide explains the real workflow of this repo.

## Project overview

* Static website, no npm, no framework, no bundler.
* Content lives in `content/*.json`: `site.json`, `news.json`, `faq.json`.
* Page skeletons live in `templates/`.
* `python3 scripts/build.py` (Python 3.9+, standard library only) renders the
  static HTML pages, `sitemap.xml`, `robots.txt`, and `manifest.webmanifest`.
* The repository stores the built HTML output (e.g. `index.html`, `about/`,
  `news/`, `articles/`, `privacy/`). Always commit rebuilt pages together
  with the content changes that produced them.

## How to contribute

1. Fork the repository and create a branch from `main`.
2. Edit the source of truth, not the built output:
   * Site texts and contacts: `content/site.json`
   * News entries: `content/news.json`
   * FAQ entries: `content/faq.json`
   * Layout changes: `templates/`
3. Rebuild the site:

   ```bash
   python3 scripts/build.py
   ```

   For the production domain base URL:

   ```bash
   SITE_BASE_URL=https://fermaruna.ru python3 scripts/build.py
   ```

4. Check the result locally. Any static server works, for example:

   ```bash
   python3 -m http.server 8000
   ```

   Then open http://localhost:8000 and review the pages you changed.
5. Commit both the source changes (`content/`, `templates/`) and the rebuilt
   HTML output in the same commit.
6. Open a pull request against `main` describing what changed and why.

## What not to change in a content PR

* `config.php` is excluded from git (see `config.example.php`). Never commit
  real credentials or mail settings.
* Do not commit `assets/*.svg` redesigns or `README.md` / `README.ru.md`
  rewrites in the same PR unless the PR is about them.
* Keep unrelated reformatting out of the diff so review stays easy.

## Style notes

* Content in `content/*.json` is user-facing Russian copy. Keep it plain,
  accurate, and consistent with the farm tone of the live site.
* This document, issues, and pull requests are in English.
* Validate JSON before building (a trailing comma breaks the build).
* Keep images web-friendly and place responsive variants next to the original
  under `assets/img/` following the existing `<name>-<width>.webp` pattern.

## Reporting problems

Use GitHub Issues with the provided templates. For security matters, follow
`SECURITY.md` instead of opening a public issue.
