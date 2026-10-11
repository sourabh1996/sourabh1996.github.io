# How lessons are written

This is the house style for every lesson on the site. The reference lessons are
`courses/agentic-ai-fundamentals/` and `courses/langgraph-fundamentals/` (modules 1 to 3). Read two of them
before writing.

## Where a lesson lives

- The catalog is defined in `build_catalog.py`. Run `python3 build_catalog.py .` after any change. It regenerates
  `catalog.json` and every `courses/<course>/course.md`. Never edit those generated files by hand.
- A lesson file is `courses/<course-slug>/<NN>-<module-slug>/<lesson-slug>.md`.
  - `NN` is the module's position, two digits. "Start Here" is always `01`, so the first real module is `02`.
  - Slugs come from `slug()` in `build_catalog.py`: lowercase, with every run of non-alphanumerics turned into `-`, ➕ removed.
  - The file name must match a lesson title in the catalog. The build fails on orphans.
- Every course starts with `01-start-here/how-this-course-works.md`.

## Front matter

```
---
title: "<Lesson title as in the catalog>"
course: <Course title>
module: "<N>. <Module title>"
type: Article | Lab
level: Beginner | Intermediate | Advanced
reading_time: <minutes> min
---
```

## Article structure

1. `# <Title>: The Complete Guide` (labs: `# Lab: ...`)
2. `> 📚 **Before you start**` with links to the exact earlier lessons this one depends on. Link written lessons by
   relative path (`../02-getting-started/what-is-langgraph.md`). Link lessons that aren't written yet through their
   module anchor on the generated course page (`../../python-fundamentals/course.md#m6`). For the very first lesson
   of a beginner course, say no prior knowledge is needed.
3. `## Introduction`: a relatable real-world hook, then what the reader will be able to do by the end.
4. `> 💡 **Key Insight**`: the one idea to remember.
5. `## Core Explanation`: numbered `###` sections. Build from the simplest case to the advanced one. Include
   diagrams (Mermaid), tables and runnable code.
6. `## Try It Yourself`: 2 to 4 exercises with answers in a `<details>` block. Answer code is also checked.
7. `## Real-World Examples`
8. `## Common Misconceptions`: `###` per misconception.
9. `## Interview Relevance`: the questions this topic gets in interviews and what a strong answer covers.
10. `## Key Takeaways`: 4 to 6 bold-led bullets.
11. `**Up next:** [Next lesson](next-lesson.md)`. Use the course.md anchor if the next lesson isn't written yet.

A lab instead has: `## What You'll Build` (with a Mermaid diagram), Key Insight, `## Step N: ...` sections,
`## Try It Yourself`, `## What You've Learned`, and Up next.

Depth: an article is typically 250 to 450 lines. Cover the topic completely, as if the reader never needs another
resource. Explain every term the first time it appears. Prefer Indian everyday examples (rupees, cricket, chai,
UPI, trains) when an example is needed.

## Code rules (checked in CI)

- `python3 tools/check_code.py <lesson.md>` runs every ```python block of a lesson in order in one namespace, the
  way a reader would paste them into one file.
- If a block is followed by a line `Output:` and a plain ``` block, the printed output must match exactly.
  **Always run the code and paste the real output.** Never type expected output by hand.
- Make output deterministic: seed randomness, sort sets and dict keys from parallel work, round floats.
- Start a block with `# not-run: <reason>` when it needs an API key, network, a GPU, a package not in
  `requirements-lessons.txt`, or a long-running server. Keep such blocks short and correct for the real library
  version. Don't follow a not-run block with `Output:`; use `Example output:` instead.
- Only import packages pinned in `requirements-lessons.txt`. Don't add packages without asking the course owner.
- For LLM calls in runnable code, use `langchain_core.language_models.fake_chat_models.FakeListChatModel` (or a
  small pretend client) so the lesson runs offline. Show the real-model version in a not-run block.
- Shell, SQL, YAML and other languages aren't executed. Show their output in a plain block after `Example output:`.
  Use SQLite (`sqlite3`, standard library) for runnable SQL in Python.

## Diagrams

- Use ```mermaid blocks. Never start a node label with a number followed by a dot, like `["1. Start"]`. Mermaid
  draws that as "Unsupported markdown: list". Write `["Step 1: Start"]` instead. The build rejects it.
- Use diagrams generously: at least one per article, and an architecture diagram whenever a lesson describes a
  system with more than two moving parts. Learners have asked for pictures they can understand at a glance.
- For the big "how it all fits together" pictures, draw a picture-style infographic with `tools/infographic.py`:
  write a spec in `diagrams/<course-slug>/<name>.py`, run `python3 tools/infographic.py <spec>`, and commit both
  the spec and the SVG it writes to `site/public/img/diagrams/<course-slug>/<name>.svg`. Embed it as
  `![Full alt text describing the picture](/img/diagrams/<course-slug>/<name>.svg)` followed on the next line by
  an `*italic caption*`. Use icons, short labels and colour groups; keep every label to a few words. Design it
  yourself; never copy someone else's infographic.
- Always pair an abstract idea with a concrete example the reader can look at: show what an ontology, a JSON
  schema, a graph or a prompt actually looks like, with real-looking values, before generalising.

## Accuracy and originality

- Write original explanations. Never copy text from courses, PDFs, books or docs.
- Facts must be current as of October 2026. When unsure about an API, version, date or product detail, check the
  official docs (WebSearch/WebFetch) or leave the detail out. Don't invent function names or flags.
- In code that shows a model name, use `claude-opus-5-5`.

## Before you push

```
python3 build_catalog.py .        # catalog, links and diagram labels
python3 tools/check_code.py       # every code example
cd site && npm run build          # the site builds
```
