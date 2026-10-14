---
title: "Maintaining a Project: Templates, Releases and Semver"
course: "Git and GitHub: Zero to Pro"
module: "10. Open Source and Advanced Git"
type: Article
level: Intermediate
reading_time: 30 min
---

# Maintaining a Project: Templates, Releases and Semver: The Complete Guide

> 📚 **Before you start**
>
> - [Contributing to Open Source](contributing-to-open-source.md)
> - [Issues, Labels, Milestones and Projects](../course.md#m6) and [Branch Protection, Rulesets and CODEOWNERS](../course.md#m6)
> - [Releases, Tags and GitHub Packages](../08-github-pages-codespaces-and-packages/releases-tags-and-github-packages.md)

## Introduction

Running a small open source project is a bit like running a popular tiffin service from your home kitchen. At first it's just you and a few neighbours. Then fifty people want lunch, and you need a menu (so people stop asking what's available), an order form (so you get the address *and* the spice level), fixed delivery times, and a way to announce "from next month, Friday is thali-only" without upsetting regulars.

A project's equivalents are **issue and PR templates** (structured requests), **community health files** (the menu and rules), **releases with clear version numbers** (predictable delivery), and **changelogs and deprecation policies** (the announcements). This lesson sets all of that up and then automates releases from your commit history, so maintaining stays a pleasure rather than a second job.

> 💡 **Key Insight**
>
> A version number is a **promise to your users** about what changed. **Semantic Versioning** makes that promise machine-readable: a patch release never breaks you, a minor release adds features without breaking you, and only a major release may break you. Automate the bookkeeping so you keep the promise every time.

---

## Core Explanation

### 1. Community Health Files

GitHub recognises these files in the repository root, `docs/` or `.github/`:

| File | Purpose |
|---|---|
| `README.md` | What it is, how to install and use it |
| `LICENSE` | Permission to use it (see [Licenses in Plain English](licenses-in-plain-english.md)) |
| `CONTRIBUTING.md` | Dev setup, tests, commit style, how PRs are reviewed |
| `CODE_OF_CONDUCT.md` | Expected behaviour and how to report problems |
| `SECURITY.md` | How to report vulnerabilities privately; supported versions |
| `SUPPORT.md` | Where to ask questions (Discussions, chat, Stack Overflow tag) |
| `GOVERNANCE.md` | Who decides, how maintainers are added |
| `.github/FUNDING.yml` | Shows a **Sponsor** button (GitHub Sponsors, Open Collective and others) |
| `CODEOWNERS` | Auto-requests reviewers for paths |

**Organisation defaults:** put these files in a public repository named `.github` in your organisation, and every repository without its own copy uses them (except `LICENSE`, which must be in each repository). The **Insights → Community standards** page shows a checklist of what's missing.

### 2. Issue Forms

Issue **forms** are YAML files in `.github/ISSUE_TEMPLATE/` that render as a web form with required fields, so bug reports arrive with the version and steps to reproduce.

```yaml
# .github/ISSUE_TEMPLATE/bug_report.yml
name: Bug report
description: Something isn't working as documented
title: "[Bug]: "
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: Thanks for taking the time to report this! Please search existing issues first.
  - type: input
    id: version
    attributes:
      label: chai-bill version
      placeholder: "1.4.2"
    validations:
      required: true
  - type: dropdown
    id: python
    attributes:
      label: Python version
      options: ["3.11", "3.12", "3.13", "3.14"]
    validations:
      required: true
  - type: textarea
    id: steps
    attributes:
      label: Steps to reproduce
      description: The smallest code or bill file that shows the problem.
      render: python
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: What did you expect, and what happened instead?
    validations:
      required: true
  - type: checkboxes
    id: terms
    attributes:
      label: Code of conduct
      options:
        - label: I agree to follow this project's Code of Conduct
          required: true
```

The chooser shown when someone clicks **New issue** is configured in `config.yml`:

```yaml
# .github/ISSUE_TEMPLATE/config.yml
blank_issues_enabled: false
contact_links:
  - name: Questions and ideas
    url: https://github.com/chai-co/chai-bill/discussions
    about: Ask and discuss in GitHub Discussions, not issues.
  - name: Report a security vulnerability
    url: https://github.com/chai-co/chai-bill/security/advisories/new
    about: Please report security issues privately.
```

### 3. The Pull Request Template

`.github/pull_request_template.md` pre-fills every PR description:

~~~markdown
## What and why
<!-- What does this change, and which issue does it fix? e.g. Fixes #123 -->

## How was it tested?

## Checklist
- [ ] Tests added or updated
- [ ] Docs updated (if behaviour changed)
- [ ] Commits follow Conventional Commits and are signed off (`git commit -s`)
~~~

### 4. Triage: Labels, Discussions and Stale Issues

- **Labels** with a consistent scheme: type (`bug`, `enhancement`, `docs`), status (`triage`, `needs-repro`, `blocked`), and `good first issue` / `help wanted` for newcomers.
- **GitHub Discussions** for questions and ideas, keeping issues for actionable work. You can convert an issue to a discussion and back.
- **Saved replies** for the answers you type every week ("Please add a minimal reproduction...").
- **Stale handling**, used gently: `actions/stale` labels and eventually closes inactive issues and PRs. Exempt important labels, and use long timeouts, because closing a real bug report for inactivity annoys users.

```yaml
# .github/workflows/stale.yml
name: Close stale issues
on:
  schedule:
    - cron: "30 2 * * *"

permissions:
  issues: write
  pull-requests: write

jobs:
  stale:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/stale@v11
        with:
          days-before-stale: 60
          days-before-close: 14
          stale-issue-label: stale
          exempt-issue-labels: "pinned,security,good first issue"
          stale-issue-message: >
            This issue has had no activity for 60 days. It will close in 14 days
            unless there's new information. Thanks for reporting it!
```

### 5. Semantic Versioning

**SemVer** versions look like `MAJOR.MINOR.PATCH`:

| Bump | When | Example |
|---|---|---|
| **MAJOR** | You make an incompatible API change | `1.4.2 → 2.0.0` |
| **MINOR** | You add functionality in a backward-compatible way | `1.4.2 → 1.5.0` |
| **PATCH** | You make backward-compatible bug fixes | `1.4.2 → 1.4.3` |

Extras:

- **Pre-releases** add a hyphen: `2.0.0-beta.1`, `2.0.0-rc.1`. They sort **before** the final release.
- **Build metadata** adds a plus: `2.0.0+build.42`. It's ignored when comparing versions.
- **`0.y.z`** is initial development: anything may change at any time. Many projects treat a `0.x` minor bump as "may break".
- Your **public API** must be defined (docs, type hints, `__all__`) for SemVer to mean anything.

Pre-release identifiers compare piece by piece, numbers numerically, which surprises people sorting version strings alphabetically:

```python
import re

def parse(version):
    m = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?", version)
    if not m:
        raise ValueError(f"not semver: {version}")
    major, minor, patch, pre = m.groups()
    return int(major), int(minor), int(patch), pre

def sort_key(version):
    major, minor, patch, pre = parse(version)
    if pre is None:
        return (major, minor, patch, 1, ())
    parts = tuple((0, int(p), "") if p.isdigit() else (1, 0, p) for p in pre.split("."))
    return (major, minor, patch, 0, parts)

print(sorted(["1.10.0", "1.2.0", "1.10.0-rc.1", "1.10.0-beta.2", "1.10.0-beta.11", "1.9.3"], key=sort_key))
```

Output:

```
['1.2.0', '1.9.3', '1.10.0-beta.2', '1.10.0-beta.11', '1.10.0-rc.1', '1.10.0']
```

`1.10.0` sorts after `1.9.3`, and `beta.11` after `beta.2`; plain string sorting gets both wrong. (Python packages use **PEP 440** versions such as `2.0.0rc1`, which tools like `packaging.version` compare; the idea is the same.)

### 6. Conventional Commits Drive the Version

If commit subjects follow **Conventional Commits**, the next version can be calculated:

- `fix:` (and `perf:`) → patch
- `feat:` → minor
- `!` after the type, or a `BREAKING CHANGE:` footer → major
- `docs:`, `chore:`, `test:`, `ci:` → no release on their own

```python
def next_version(current, commit_subjects):
    major, minor, patch, _ = parse(current)
    breaking = any(re.match(r"^\w+(\(.+\))?!:", s) or "BREAKING CHANGE" in s for s in commit_subjects)
    feature = any(s.startswith("feat") for s in commit_subjects)
    fix = any(s.startswith(("fix", "perf")) for s in commit_subjects)
    if breaking:
        return f"{major + 1}.0.0" if major > 0 else f"0.{minor + 1}.0"
    if feature:
        return f"{major}.{minor + 1}.0"
    if fix:
        return f"{major}.{minor}.{patch + 1}"
    return None

print(next_version("1.4.2", ["fix(parser): handle empty GST", "docs: typo"]))
print(next_version("1.4.2", ["feat: UPI split", "fix: rounding"]))
print(next_version("1.4.2", ["feat!: drop Python 3.9 support"]))
print(next_version("0.7.1", ["refactor!: rename split_bill()"]))
print(next_version("1.4.2", ["docs: README", "chore: bump deps"]))
```

Output:

```
1.4.3
1.5.0
2.0.0
0.8.0
None
```

That's what release tools do for real, with more care (multiple packages, footers, pre-releases).

### 7. Automating Releases with release-please

**release-please** (by Google) watches `main`. As Conventional Commits land, it keeps a **release PR** open that bumps the version and updates `CHANGELOG.md`. Merging that PR creates the tag and the GitHub Release. You decide **when** to release by merging; the tool decides **what** the version and notes are.

```yaml
# .github/workflows/release-please.yml
name: release-please
on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write
  issues: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    outputs:
      release_created: ${{ steps.rp.outputs.release_created }}
      tag_name: ${{ steps.rp.outputs.tag_name }}
    steps:
      - uses: googleapis/release-please-action@v5
        id: rp
        with:
          release-type: python
          token: ${{ secrets.RELEASE_PLEASE_TOKEN }}

  publish:
    needs: release-please
    if: needs.release-please.outputs.release_created == 'true'
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v7
        with:
          ref: ${{ needs.release-please.outputs.tag_name }}
          persist-credentials: false
      - uses: astral-sh/setup-uv@v9.0.0
      - run: uv build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

Why a separate token? Pull requests and tags created with the default `GITHUB_TOKEN` don't trigger other workflows (to prevent loops), so your CI wouldn't run on the release PR. A fine-grained token or a GitHub App token fixes that. The publish job uses PyPI **trusted publishing** through OIDC, so no PyPI password is stored (see [OIDC](../07-github-actions/oidc-deploying-to-the-cloud-without-stored-keys.md)).

Alternatives: **semantic-release** (fully automatic: every qualifying merge releases), **Changesets** (contributors add small change files; popular in JavaScript monorepos), or a manual `gh release create v1.5.0 --generate-notes` with categories from `.github/release.yml`.

### 8. Changelogs and Deprecations

A good `CHANGELOG.md` (the "Keep a Changelog" style) groups changes under each version as **Added, Changed, Deprecated, Removed, Fixed, Security**, newest first, written for users rather than copied from commit messages.

**Deprecation policy**, written in CONTRIBUTING.md or your docs:

1. Mark the old API deprecated in a **minor** release, with a warning and the replacement.
2. Keep it working for at least one more minor release (or a stated period).
3. Remove it only in the next **major** release, listed under "Removed".

```python
import warnings

def split_bill(total, people):
    warnings.warn("split_bill() is deprecated; use split_evenly() instead. It will be removed in 2.0.",
                  DeprecationWarning, stacklevel=2)
    return split_evenly(total, people)

def split_evenly(total, people):
    return round(total / people, 2)

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    print(split_bill(450, 4))
print(caught[0].category.__name__, "-", caught[0].message)
```

Output:

```
112.5
DeprecationWarning - split_bill() is deprecated; use split_evenly() instead. It will be removed in 2.0.
```

### 9. Maintainer Sustainability

- **Say no**, kindly and early, to features that don't fit. A clear "Non-goals" section in the README helps.
- **Share the load**: add triagers (the **Triage** role can label and close issues without write access to code), then co-maintainers.
- **Protect `main`** with rulesets and required checks so you don't have to review everything at midnight.
- **Set expectations** in SUPPORT.md ("best effort, usually within a week").
- **Accept funding** via Sponsors if it helps, and take breaks. A pinned issue saying "away until the 20th" is fine.

---

## Try It Yourself

1. Write an issue form `feature_request.yml` with a required "Problem you're trying to solve" textarea and an optional "Proposed solution".
2. What's the next version after `2.3.9` for each set of commits? (a) `perf: cache GST rates`; (b) `feat(api): add currency field`, `fix!: return Decimal instead of float`; (c) `ci: pin actions`.
3. Sort `["2.0.0", "2.0.0-alpha", "2.0.0-alpha.1", "2.0.0-beta"]` with `sort_key` and explain the order.
4. Why might CI not run on the release PR opened by release-please, and how do you fix it?

<details>
<summary>Show answers</summary>

**1.**

```yaml
name: Feature request
description: Suggest an idea for chai-bill
labels: ["enhancement", "triage"]
body:
  - type: textarea
    id: problem
    attributes:
      label: Problem you're trying to solve
    validations:
      required: true
  - type: textarea
    id: solution
    attributes:
      label: Proposed solution
```

**2.**

```python
print(next_version("2.3.9", ["perf: cache GST rates"]))
print(next_version("2.3.9", ["feat(api): add currency field", "fix!: return Decimal instead of float"]))
print(next_version("2.3.9", ["ci: pin actions"]))
```

Output:

```
2.3.10
3.0.0
None
```

**3.**

```python
print(sorted(["2.0.0", "2.0.0-alpha", "2.0.0-alpha.1", "2.0.0-beta"], key=sort_key))
```

Output:

```
['2.0.0-alpha', '2.0.0-alpha.1', '2.0.0-beta', '2.0.0']
```

Pre-releases come before the release; a shorter identifier list sorts before a longer one with the same start; `alpha` < `beta` alphabetically.

**4.** Events created with the default `GITHUB_TOKEN` don't trigger new workflow runs. Pass a fine-grained PAT or GitHub App token through the `token` input.

</details>

---

## Real-World Examples

### Example 1: Forms Halve Triage Time

A Python library's maintainers switched from free-text issues to forms with required version and reproduction fields, and turned off blank issues. "Can you tell us your version?" comments almost disappeared, and questions moved to Discussions.

### Example 2: The "Minor" Release That Broke Everyone

A popular package removed a function in a minor release, assuming nobody used it. Thousands of builds broke overnight, since most users pinned `~=1.4`. The maintainers yanked the release, restored the function with a deprecation warning, and published their deprecation policy.

### Example 3: Release PRs as a Calm Ritual

A team using release-please merges the release PR every Thursday after checking the generated changelog. Tags, GitHub Releases, PyPI uploads and attestations all happen automatically, and nobody hand-edits version numbers any more.

---

## Common Misconceptions

### Misconception 1: "Version 1.0 means it's finished"

1.0.0 means the public API is stable and SemVer promises now apply. Projects go on to 1.1, 2.0 and beyond.

### Misconception 2: "A patch release is always safe"

It's a promise, not a guarantee. Pin versions in applications (lock files) and let Dependabot propose upgrades with CI.

### Misconception 3: "Templates are bureaucracy"

They save contributors from guessing and maintainers from asking. Keep them short.

### Misconception 4: "Stale bots tidy up projects"

Aggressive stale settings close real bugs and drive users away. Use long timeouts and exemptions, or triage by hand.

---

## Interview Relevance

Maintainer topics show up in open source, platform and senior roles:

- **SemVer rules**, pre-release ordering, `0.x`, and what counts as a breaking change.
- **Release automation**: Conventional Commits → release-please or semantic-release → tag → Release → publish with trusted publishing.
- **Templates and health files**: issue forms, PR templates, SECURITY.md, CODEOWNERS.
- **Deprecation policy** and changelogs.
- **Why `GITHUB_TOKEN` events don't trigger workflows.**

A common follow-up: *"Is adding a required parameter to a function a minor or major change?"* Major: existing callers break. Adding an **optional** parameter with a default is minor.

---

## Key Takeaways

- **Community health files** (CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, SUPPORT) and **org-wide defaults** in a `.github` repository set clear rules.
- **Issue forms, `config.yml` and a PR template** make every report and PR arrive with what you need.
- **SemVer** is a promise: patch = fixes, minor = compatible features, major = breaking; pre-releases sort before releases.
- **Conventional Commits + release-please** (or semantic-release) automate versions, changelogs, tags and publishing.
- **Deprecate in a minor, remove in a major**, and protect your own time with triage roles, rulesets and clear expectations.

---

**Up next:** [Submodules, Subtrees and Monorepos](submodules-subtrees-and-monorepos.md)
