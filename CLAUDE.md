# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Academic personal website for Jake W. Liu, built on the **al-folio** Jekyll theme. Hosted on GitHub Pages at `https://jake-w-liu.github.io`.

## Common Commands

```bash
# Install dependencies
bundle install

# Local development server (port 8080)
bundle exec jekyll serve

# Production build
JEKYLL_ENV=production bundle exec jekyll build

# Docker development (alternative)
docker-compose up

# Format code (Prettier with Liquid plugin)
npx prettier . --check
npx prettier . --write

# Purge unused CSS (run after build)
purgecss -c purgecss.config.js
```

## Architecture

- **Jekyll 4.x** static site generator with Liquid templates and SCSS
- **Ruby 3.3.5** runtime; dependencies in `Gemfile`
- **Node.js** used only for Prettier formatting (see `package.json`)
- **Python 3** used only for Jupyter notebook conversion via `nbconvert`

### Key Directories

- `_config.yml` — Master site configuration (theme, plugins, CDN libraries with SRI hashes, Jekyll Scholar settings)
- `_bibliography/` — BibTeX files (`papers.bib`) processed by Jekyll Scholar for publications page
- `_pages/` — Static pages (about, publications, courses, projects, etc.)
- `_posts/` — Blog posts
- `_courses/`, `_books/`, `_news/` — Collection content types
- `_layouts/` — Page templates (Liquid); `default.liquid` is the base layout
- `_includes/` — Reusable template components
- `_sass/` — SCSS stylesheets
- `_plugins/` — Custom Jekyll plugins
- `_data/` — YAML data files for site metadata
- `assets/` — Static assets (CSS, JS, images, PDFs, Jupyter notebooks, fonts)

### Key Integrations

- **Jekyll Scholar** — Parses BibTeX in `_bibliography/` for publication listings with Altmetric/Dimensions badges
- **ImageMagick** — Auto-generates responsive WebP images at 480/800/1400px widths
- **MathJax** — LaTeX math rendering in posts/pages
- **Dark mode** — Full theme switching support

## CI/CD

GitHub Actions workflows in `.github/workflows/`:
- `deploy.yml` — Main deployment: builds with Jekyll, purges CSS, deploys to `gh-pages` branch
- `prettier.yml` — Checks formatting on PRs
- `broken-links.yml` — Lychee link checker
- `axe.yml` — Accessibility testing (manual trigger)

## Code Style

- Prettier with `@shopify/prettier-plugin-liquid` for Liquid template formatting
- Print width: 150 characters, trailing commas: ES5 (see `.prettierrc`)
- Pre-commit hooks configured (`.pre-commit-config.yaml`): trailing whitespace, end-of-file fix, YAML validation

export PATH="/opt/homebrew/opt/ruby/bin:/opt/homebrew/lib/ruby/gems/4.0.0/bin:$PATH" && bundle install
bundle exec jekyll serve  
http://127.0.0.1:4000