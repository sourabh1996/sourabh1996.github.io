# Learn Agentic AI

A free, in-depth learning platform that takes readers from their first line of Python to multi-agent systems in production. It is laid out like DataVidhya's Learn section and published as a static site on GitHub Pages.

## What's where

| Path | What it is |
|---|---|
| `build_catalog.py` | The single source of truth for courses, modules, lessons and prerequisite links. Run it to regenerate everything below. |
| `syllabus_coverage.py` | Every topic from the bootcamp syllabus, mapped to its lesson. The build fails if one goes missing. |
| `catalog.json` | Generated catalog, read by the site. |
| `curriculum-outline.md`, `syllabus-coverage.md`, `courses/*/course.md` | Generated, human-readable views of the catalog. |
| `courses/<course>/<module>/<lesson>.md` | Written lessons. These become pages on the site. |
| `site/` | The Astro website. |
| `.github/workflows/deploy.yml` | Rebuilds and publishes the site on every push to `main`. |

## Run it locally

```bash
python3 build_catalog.py .     # regenerate the catalog and check coverage + prerequisites
cd site && npm install && npm run dev
```

## Publish

In the GitHub repo settings, set **Pages → Source** to **GitHub Actions**. Every push to `main` then rebuilds and publishes the site.
