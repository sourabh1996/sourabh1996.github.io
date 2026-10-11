# Site Plan: Your Own DataVidhya-Style Learning Site on GitHub Pages

## The short version

- **Built with Astro**, a static-site generator made for content sites. Lessons are written as Markdown (MDX) files. Interactive pieces such as the playgrounds are small React components dropped into a lesson.
- **Hosted free on GitHub Pages.** Every time a change is merged, a GitHub Action rebuilds the site and publishes it. The address is `https://<your-username>.github.io` (or `/<repo-name>` if you use a different repo name), and you can point your own domain at it later.
- **No server and no database.** Everything is plain HTML, CSS and a little JavaScript, so it is fast, free and hard to break.

## What the site will look like

Modelled on the DataVidhya screenshots, in a dark theme with a light-mode toggle.

| Page | What's on it |
|---|---|
| **Catalog** | Grid of course cards: icon, level badge (Beginner / Intermediate / Advanced), title, two-line description, hours, "N modules · N lessons". Filter by track and level. Search box. |
| **Course page** | Course header with "Finish first" and "Unlocks" links, then **Course content**: numbered, collapsible modules with a progress counter (3/15), each lesson tagged Video, Article or Lab with a tick when done. Each module shows its **Before you start** links. |
| **Article page** | Breadcrumbs (Catalog / Course / Module), theme toggle, **Before you start** box, the article itself, and a right sidebar with **Reading Progress** and **On This Page**. Previous / Next lesson buttons at the bottom. |
| **Video lesson** | Embedded YouTube video, a short summary and a link to the matching Deep Dive. |
| **Lab page** | Step-by-step instructions, starter code, a "show solution" toggle, and an "Open in Colab" button for Python labs. |

Article building blocks, each a reusable component: **Key Insight** callout, **Before you start** box, diagram frame with caption, code block with copy button, **Try It Yourself** playground frame, misconception cards, interview Q&A, key-takeaways box, and quiz.

## How the content gets generated

1. **One source of truth.** The catalog (`catalog.json`) is generated from `build_catalog.py`. It holds every course, module, lesson and prerequisite link. The site reads it to build the catalog and course pages, so the structure never drifts from the plan.
2. **One file per lesson.** For example, `src/content/lessons/23-agentic-ai-fundamentals/02-understanding-agents/what-is-an-ai-agent-deep-dive.mdx`, with frontmatter for title, type, level and prerequisites.
3. **I write lessons in batches, one module at a time,** following the article template. Every code example is run before it ships, and every diagram is drawn as an SVG so it stays sharp and works in both themes.
4. **Automatic checks on every build.** The build fails on a broken link, a missing prerequisite, or a lesson listed in the catalog that points to a missing file. It also re-checks that every syllabus topic is still covered.
5. **You review through pull requests.** Each batch arrives as a pull request you can preview, comment on and merge. Merging publishes it.

Until a lesson is written, its page shows a "Coming soon" card, so the full catalog can go live on day one and fill in over time.

## Things a static site can't do on its own

- **Ask AI button:** this needs a server to keep an API key secret. Leave it out at launch and add it later with a small serverless function (for example Cloudflare Workers).
- **Student counts and accounts:** there are no logins. Reading progress and completed lessons are saved in the reader's own browser.
- **Videos:** these come from you (recorded and uploaded to YouTube). Until then, video lessons show a written summary.

## What I need from you to start

1. **Your GitHub username,** and whether you want the site at `<username>.github.io` (recommended) or under a different repo name.
2. **Connect GitHub to Claude** and create (or let me create) the repo, so I can open pull requests on it.
3. **Your go-ahead** on Astro (see the decision card in the thread).

## Suggested order of work

1. Site skeleton: catalog, course page and article page in the DataVidhya style, with all 30 courses listed and the sample article live.
2. Agentic AI track first (courses 23 to 29), since it's the platform's focus, then Generative AI (18 to 22), then the foundations tracks.
3. Playgrounds, diagrams and labs added alongside each module's articles.
