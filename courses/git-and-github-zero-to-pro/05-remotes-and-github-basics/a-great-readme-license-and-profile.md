---
title: "A Great README, LICENSE and Profile"
course: "Git and GitHub: Zero to Pro"
module: "5. Remotes and GitHub Basics"
type: Article
level: Beginner
reading_time: 18 min
---

# A Great README, LICENSE and Profile: The Complete Guide

> 📚 **Before you start**
>
> - [clone, fetch, pull and push](clone-fetch-pull-and-push.md), so you can publish a repository
> - [Writing Good Commit Messages](../02-version-control-from-scratch/writing-good-commit-messages.md), the same "write for the reader" mindset

## Introduction

A recruiter opens your GitHub profile. In about thirty seconds they'll glance at your pinned repositories, open one, and read the first screen of its README. If that screen says `# project1` and nothing else, the code behind it might as well not exist. If it says what the project does, shows a screenshot, and tells them how to run it in three commands, you've made an impression before they read a line of code.

The same is true inside companies. A good README is the difference between a teammate getting a service running in ten minutes and losing an afternoon. And a missing **LICENSE** file quietly means nobody else is legally allowed to use your code, which surprises many beginners who thought "public" meant "free to use".

This article covers the files and settings that make a repository understandable and usable: the README (what goes in it, GitHub's Markdown features, and a template), choosing and adding a licence, the other community files GitHub recognises, repository settings like description and topics, and your **profile README** and pinned repositories.

By the end you'll be able to write a README that answers a visitor's first questions, add a licence and explain what "no licence" means, add contributing and security files, and turn your GitHub profile into a clear portfolio.

> 💡 **Key Insight**
>
> Write the README for a **stranger with five minutes**: what is this, why would I care, how do I run it, how do I use it, and how do I get help or contribute. Add a **LICENSE**, because without one, others have no legal right to use, copy or modify your code, even in a public repository. Then make your **profile** point at your best two to six projects.

---

## Core Explanation

### 1. How GitHub Finds and Shows Your README

GitHub renders a README automatically on the repository's front page. It looks for a file named `README` (any case; `README.md` is the norm) in this order: the `.github/` folder, the repository root, then `docs/`. Any folder that contains a README also shows it when you browse into that folder, which is useful for explaining subprojects in a monorepo.

`.md` means **Markdown**, a plain-text format where `#` makes a heading and `**bold**` makes bold text. GitHub uses **GitHub Flavored Markdown** (GFM), which adds tables, task lists, automatic links and more (section 3). Reading the raw file is still easy, which is the point: a README works in a terminal too.

### 2. What a Great README Contains

Answer the visitor's questions in the order they ask them:

| Section | Answers | Tips |
|---------|---------|------|
| **Title and one-line description** | "What is this?" | Plain words, no jargon: "Track daily chai sales and print an end-of-day report." |
| **Screenshot, GIF or example output** | "What does it look like?" | One picture beats three paragraphs; store it in the repo (`docs/`) and link it relatively |
| **Features** (optional) | "Why would I use it?" | Three to six bullets |
| **Quick start / installation** | "How do I run it?" | Copy-pasteable commands, prerequisites with versions |
| **Usage** | "How do I use it?" | Examples of the most common tasks, with output |
| **Configuration** (if any) | "What can I change?" | Environment variables in a table |
| **Running tests / development** | "How do I work on it?" | Or link to `CONTRIBUTING.md` |
| **Licence** | "Can I use it?" | One line linking to `LICENSE` |
| **Contact / support / credits** | "Who do I ask?" | Issues link, maintainers, acknowledgements |

Badges (small status images such as "CI passing" or "licence MIT") are fine at the top, but limit them to a few that tell visitors something true and current, like build status from GitHub Actions ([module 7](../course.md#m7)).

Asha commits a first version of her README alongside a licence:

```markdown
# Chai Ledger

Track daily chai sales for a small tea stall and print an end-of-day report.

## Quick start

    git clone https://github.com/asha-rao/chai-ledger.git
    cd chai-ledger
    python ledger.py

## License

MIT. See [LICENSE](LICENSE).
```

```bash
git status --short
git add README.md LICENSE docs/screenshot.png
git commit -m "Write a README and add the MIT licence"
git show --stat --format="%h %s" HEAD
```

Example output:

```
 M README.md
?? LICENSE
?? docs/

[main a6303c1] Write a README and add the MIT licence
 3 files changed, 34 insertions(+), 1 deletion(-)
 create mode 100644 LICENSE
 create mode 100644 docs/screenshot.png

a6303c1 Write a README and add the MIT licence

 LICENSE             |  21 +++++++++++++++++++++
 README.md           |  14 +++++++++++++-
 docs/screenshot.png | Bin 0 -> 146 bytes
 3 files changed, 34 insertions(+), 1 deletion(-)
```

`Bin 0 -> 146 bytes` is how Git's diff stat reports a binary file such as an image: it doesn't count lines, just sizes. A README is a living document, so expect `git log --oneline -- README.md` to grow as the project does.

A fuller template you can adapt:

````markdown
# Chai Ledger

Track daily chai sales for a small tea stall and print an end-of-day report.

![End-of-day report in the terminal](docs/screenshot.png)

## Features

- Record each sale with one command
- Daily and weekly totals by item
- Exports to CSV for your accountant

## Quick start

Requires Python 3.12 or newer.

```bash
git clone https://github.com/asha-rao/chai-ledger.git
cd chai-ledger
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python ledger.py report --today
```

## Usage

| Command | What it does |
|---------|--------------|
| `python ledger.py add "Masala chai" 2` | Record two masala chai |
| `python ledger.py report --week` | Weekly totals |

## Running tests

```bash
pytest
```

## Contributing

Issues and pull requests are welcome. Please read CONTRIBUTING.md first.

## License

[MIT](LICENSE) © 2026 Asha Rao
````

(The outer fence uses four backticks so the three-backtick blocks inside it display correctly. That's a handy GFM trick whenever you document Markdown in Markdown.)

### 3. GitHub Flavored Markdown Features Worth Using

| You type | You get |
|----------|---------|
| ```` ```python ```` … ```` ``` ```` | A code block with syntax highlighting |
| `\| a \| b \|` rows with a `\|---\|---\|` line | A table |
| `- [ ] Write tests` / `- [x] Write docs` | A task list with checkboxes |
| `> [!NOTE]` (also `TIP`, `IMPORTANT`, `WARNING`, `CAUTION`) on the first line of a quote | A coloured callout box ("alert") |
| `[the licence](LICENSE)` | A relative link that works on every branch and in forks |
| `![alt text](docs/screenshot.png)` | An image; always write alt text for screen readers |
| `<details><summary>More</summary> … </details>` | A collapsible section |
| A ```` ```mermaid ```` block | A rendered diagram (flowcharts, sequence diagrams, gitGraphs) |
| `#42`, `@ravi-kumar`, a commit hash | Links to issue 42, a user, a commit (in issues, PRs and comments; plain text in files) |
| `:tada:` | An emoji shortcode |

Prefer **relative links** to files in the repository (`docs/setup.md`) over full URLs: they keep working when someone views another branch, a fork or a local clone. GitHub also generates an outline from your headings; in long READMEs, readers use the outline button at the top of the file view to jump around, so good headings matter.

### 4. Licences: What "No Licence" Really Means

Copyright law gives the author of code exclusive rights automatically. A public repository lets people **see** your code, and GitHub's terms let others view and fork it on GitHub, but without a licence nobody may legally **use, copy, modify or distribute** it. Companies' legal teams will not touch unlicensed code. If you want people to use your project, add a licence.

The licences you'll meet most often:

| Licence | In one sentence | Typical use |
|---------|-----------------|-------------|
| **MIT** | Do anything, keep the copyright notice; no warranty | Small libraries, personal projects, most portfolios |
| **Apache-2.0** | Like MIT, plus an explicit patent grant and rules for stating changes | Company-backed open source |
| **GPL-3.0** | You may use and modify, but if you distribute the program, you must share its source under the GPL too ("copyleft") | Projects that want derivatives to stay open |
| **AGPL-3.0** | GPL, plus the share-alike duty applies when users interact with it over a network | Server software that wants to stay open even as a service |
| **MPL-2.0** | Copyleft per file: changes to these files must be shared, the rest of your program needn't be | A middle ground |
| **Unlicense / CC0** | Public-domain dedication | Snippets, examples, data |

How to add one:

- **When creating a repository** on GitHub, pick a licence from the **Add a license** menu, or with the CLI: `gh repo create chai-ledger --public --license mit --add-readme`.
- **In an existing repository**, on GitHub choose **Add file → Create new file**, type `LICENSE` as the name, and click **Choose a license template**. GitHub fills in the text with your name and the year.
- **Locally**, copy the official text from choosealicense.com (run by GitHub) into a file named `LICENSE`, fill in the year and name, and commit it.

GitHub detects the licence and shows it in the repository sidebar. In source files, many projects add a one-line **SPDX identifier** comment such as `SPDX-License-Identifier: MIT`, a standard tag that tools can read.

Two cautions. First, a licence can't be taken back for copies people already received under it; you can change the licence for future versions. Second, this is a practical summary, not legal advice; for anything with money or a company involved, ask a lawyer. [Licenses in Plain English](../course.md#m10) in module 10 goes deeper, including licence compatibility.

### 5. The Other Community Files

GitHub recognises a set of standard files and surfaces them in the interface. Put them in the root, `docs/` or `.github/`:

| File | Purpose | Where GitHub shows it |
|------|---------|----------------------|
| `CONTRIBUTING.md` | How to set up, code style, how to propose changes | Linked when someone opens an issue or pull request |
| `CODE_OF_CONDUCT.md` | Expected behaviour and how to report problems | Sidebar; the Contributor Covenant is a common template |
| `SECURITY.md` | How to report vulnerabilities privately, supported versions | The repository's **Security** tab |
| `SUPPORT.md` | Where to get help (discussions, forums) | Linked from new issues |
| `CITATION.cff` | How to cite the project in research | A **Cite this repository** button |
| `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md` | Forms and templates for new issues and pull requests | When creating them ([module 6](../course.md#m6)) |
| `.github/FUNDING.yml` | Sponsor links | A **Sponsor** button |

A repository's **Insights → Community standards** page (on public repositories) shows a checklist of which of these you have. An organisation or user can also create a public repository named **`.github`** whose community files act as **defaults** for every repository that lacks its own.

### 6. Repository Settings That Help People Find You

On the repository page, the gear icon next to **About** lets you set:

- **Description**: one line, shown in search results and on your profile.
- **Website**: a live demo or documentation site (GitHub Pages is covered in [module 8](../course.md#m8)).
- **Topics**: tags like `python`, `cli`, `point-of-sale` that make the repository discoverable in GitHub's topic pages and search.

Under **Settings → General**, you can upload a **social preview** image, shown when the link is shared on chat apps and social sites, and turn off features you don't use (wiki, projects) so visitors don't find empty tabs.

### 7. Your Profile README and Pinned Repositories

Create a **public** repository with **exactly your username** as its name (`asha-rao/asha-rao`). GitHub tells you it's a special repository, and its README appears at the top of your profile page. Keep it short:

```markdown
### Hi, I'm Asha 👋

Backend developer in Pune, learning data engineering.

- 🔭 Building [chai-ledger](https://github.com/asha-rao/chai-ledger), a sales tracker for small tea stalls
- 🌱 Learning Python, SQL and GitHub Actions
- 📫 Reach me at asha@example.com
```

Then, on your profile, use **Customize your pins** to pin up to **six** repositories (your own or ones you contributed to). Choose quality over quantity: two or three repositories with real READMEs, screenshots and tests impress more than six tutorial clones.

Other profile settings worth a minute:

- **Name, bio, location, website** in Settings → Public profile.
- **Profile picture**: a clear photo or a consistent avatar.
- **Commit email privacy**: under Settings → Emails, you can keep your email private and commit with the `ID+username@users.noreply.github.com` address GitHub gives you, so your real address isn't in public commit history. Set it with `git config --global user.email` ([Installing and Configuring Git](../02-version-control-from-scratch/installing-and-configuring-git.md)).
- **Contribution graph**: the green squares count commits whose email matches a verified address on your account, plus issues, pull requests and reviews. If your commits don't show up, check that `user.email` matches.

### 8. A README Review Checklist

Before you pin a project, read its README as a stranger would:

- Does the **first line** say what it does, in plain words?
- Is there a **picture or sample output**?
- Can someone run it by **copying commands**, with prerequisites and versions stated?
- Do all **links and images** work (relative paths, correct case; GitHub's file paths are case-sensitive)?
- Is there a **LICENSE**, and does the README mention it?
- Does it avoid **stale claims** (old screenshots, removed features, broken badges)?
- Are **secrets** absent from examples? Use placeholders like `YOUR_API_KEY`.

---

## Try It Yourself

1. **Audit.** Open three popular repositories you use (for example a Python library and a CLI tool). For each, note which sections from section 2 their README has and which it skips.
2. **Rewrite.** Take one of your own repositories (or a practice one) and rewrite its README using the template. Commit it with a good message and view it on GitHub.
3. **Licence.** Add an MIT licence through **Add file → Create new file → Choose a license template**. Pull the commit to your clone. What does `git log -1 --stat` show?
4. **Alerts and tables.** Add a `> [!WARNING]` callout and a two-column table to a README and preview it on GitHub.
5. **Profile.** Create your `<username>/<username>` repository, write a five-line profile README, and pin your two best repositories.

<details>
<summary>Show answers</summary>

1. Answers vary. Mature projects almost always have a one-line description, installation, usage and licence; many move contributing details to `CONTRIBUTING.md`.
2. A message like "Rewrite README with quick start and usage" works: imperative, specific.
3. After `git pull`, `git log -1 --stat` shows the commit GitHub made (authored by you, through the web interface) adding `LICENSE` with around 21 lines for MIT.
4. The alert syntax is a blockquote whose first line is `[!WARNING]`, followed by `>`-prefixed lines of text. The table needs a header row, a separator row of dashes, and data rows.
5. The repository must be public and named exactly like your username; GitHub confirms with a note that it's special.

</details>

---

## Real-World Examples

### Example 1: Popular Libraries

Widely used Python and JavaScript libraries open their READMEs with a one-sentence description, an installation command, and a minimal working example within the first screen. Detailed documentation lives on a separate site, linked from the README.

### Example 2: An Internal Service

A bank's platform team requires every service repository to have a README with owners, on-call channel, a "run locally" section and links to runbooks and dashboards. New engineers can find who owns a failing service in seconds.

### Example 3: A Job-Hunting Profile

A fresher pins three projects: a data pipeline with a diagram and sample output, a web app with a live demo link, and a merged pull request to an open source library. Each README states what she built and what she learned. Interviewers ask about those projects first.

---

## Common Misconceptions

### Misconception 1: "Public on GitHub means anyone can use my code"

Without a licence, copyright law reserves all rights to you. People can view and fork on GitHub, but not legally reuse it.

### Misconception 2: "The README is documentation for later"

It's the front door. Write it early and update it with each significant change; an out-of-date README is worse than a short one.

### Misconception 3: "More badges and emojis make a better README"

Clarity wins. A sentence, a screenshot and working commands beat a wall of badges.

### Misconception 4: "My contribution graph shows all my work"

It counts only commits whose email matches a verified address on your account (on the default branch or `gh-pages`, or in forks once merged), plus issues and reviews. Private work shows only if you enable private contributions in your profile settings.

---

## Interview Relevance

Your GitHub profile is often reviewed before or during interviews, and README skills come up directly:

- **"Walk me through this project."** Interviewers often start from your pinned repositories; a good README is your script.
- **"What licence would you use for X, and why?"** Show you know the difference between permissive (MIT, Apache-2.0) and copyleft (GPL) licences, and that no licence means no permission.
- **"How do you onboard someone to a codebase?"** Mention a README with a quick start, `CONTRIBUTING.md`, and keeping them current.
- **"How do you report a security issue in an open source project?"** Look for `SECURITY.md` and use the private channel it describes, not a public issue.

---

## Key Takeaways

- A great README answers, in order: **what, why, how to run, how to use, how to contribute, licence**.
- Use **GitHub Flavored Markdown** features (code blocks, tables, alerts, relative links, images with alt text) for clarity.
- **No licence means no permission** to reuse. MIT and Apache-2.0 are permissive; GPL-family licences are copyleft.
- Add **community files** (`CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`) and set a **description and topics**.
- A **profile README** (`username/username`) plus **pinned repositories** turns your account into a portfolio.

---

**Up next:** [Pull Requests End to End](../06-collaborating-on-github/pull-requests-end-to-end.md)
