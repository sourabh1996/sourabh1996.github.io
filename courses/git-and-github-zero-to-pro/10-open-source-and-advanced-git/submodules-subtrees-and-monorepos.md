---
title: "Submodules, Subtrees and Monorepos"
course: "Git and GitHub: Zero to Pro"
module: "10. Open Source and Advanced Git"
type: Article
level: Advanced
reading_time: 30 min
---

# Submodules, Subtrees and Monorepos: The Complete Guide

> 📚 **Before you start**
>
> - [Blobs, Trees, Commits and Tags](../course.md#m3)
> - [Refs, HEAD and Detached HEAD](../course.md#m3)
> - [clone, fetch, pull and push](../course.md#m5)

## Introduction

A joint family can live in one big house with shared kitchen and shared rules, or in separate flats in the same building, each with its own key, meeting for festivals. Both work. The big house makes coordination easy and privacy hard; separate flats are the other way round.

Code faces the same choice. Your app needs a shared GST-rates library, a docs theme, and three services that change together. Do you keep everything in **one repository** (a **monorepo**), or keep separate repositories and **embed** one inside another? Git offers two embedding tools, **submodules** (a pointer to a specific commit of another repository) and **subtrees** (a copy of another repository's files merged into yours), and large monorepos need their own tricks to stay fast.

This lesson explains how each works inside Git, the commands you'll actually use, their sharp edges, and how to choose.

> 💡 **Key Insight**
>
> A **submodule** stores a **pointer** (a commit hash) to another repository: small, exact, but everyone must remember to fetch it. A **subtree** stores **a copy of the files**: everything just works for users, but syncing changes back is manual. A **monorepo** avoids the problem by putting everything in one history, then needs tooling to stay fast and to build only what changed.

---

## Core Explanation

### 1. Submodules: A Commit Pointer Inside Your Tree

```bash
git submodule add https://github.com/chai-co/gst-rates.git vendor/gst-rates
git commit -m "build: add gst-rates as a submodule"
```

That does two things:

1. Creates **`.gitmodules`**, a small config file mapping the path to the URL.
2. Records a **gitlink** in your tree: an entry with mode `160000` whose "content" is a **commit hash** in the other repository, not a blob or tree of yours.

```bash
git ls-tree HEAD vendor/
```

Example output:

```
160000 commit 4f2a9c1e8b7d6a5f4e3d2c1b0a9f8e7d6c5b4a39	vendor/gst-rates
```

So your repository says "at this commit, `vendor/gst-rates` is exactly commit `4f2a9c1`". Updating the library is a deliberate commit in **your** repository that moves the pointer.

`.gitmodules` is plain INI-style config, easy to read from a script:

```python
import configparser

gitmodules = """
[submodule "vendor/gst-rates"]
	path = vendor/gst-rates
	url = https://github.com/chai-co/gst-rates.git
	branch = main
[submodule "docs/theme"]
	path = docs/theme
	url = ../docs-theme.git
"""
cfg = configparser.ConfigParser()
cfg.read_string(gitmodules)
for section in cfg.sections():
    name = section.split('"')[1]
    sub = cfg[section]
    print(f"{name:<17} path={sub['path']:<17} url={sub['url']}  tracks={sub.get('branch', '(not set)')}")
```

Output:

```
vendor/gst-rates  path=vendor/gst-rates  url=https://github.com/chai-co/gst-rates.git  tracks=main
docs/theme        path=docs/theme        url=../docs-theme.git  tracks=(not set)
```

A **relative URL** like `../docs-theme.git` resolves against your repository's own remote, so it works whether people clone over HTTPS or SSH. `branch` is only used by `git submodule update --remote`.

### 2. Working with Submodules Day to Day

| Task | Command |
|---|---|
| Clone including submodules | `git clone --recurse-submodules <url>` |
| Already cloned without them | `git submodule update --init --recursive` |
| See which commits are checked out | `git submodule status` |
| Move submodules to the commits your branch records (after pull or switch) | `git submodule update --recursive` |
| Make pull, switch and checkout do that automatically | `git config --global submodule.recurse true` |
| Bump a submodule to the latest of its tracked branch | `git submodule update --remote vendor/gst-rates`, then commit the new pointer |
| Run a command in each submodule | `git submodule foreach 'git status --short'` |
| Show submodule changes readably in diffs | `git diff --submodule=log` |
| Remove a submodule | `git rm vendor/gst-rates`, then commit |

Sharp edges:

- **Empty folders after cloning.** Forgetting `--recurse-submodules` gives you an empty directory. This is the most common submodule complaint.
- **Detached HEAD inside the submodule.** Git checks out the exact recorded commit, not a branch (see [Refs, HEAD and Detached HEAD](../course.md#m3)). To work in it, `git switch main` inside the submodule first, commit and **push the submodule**, then commit the new pointer in the parent.
- **Pointer to an unpushed commit.** If you commit a pointer to a submodule commit you never pushed, everyone else's update fails with "not our ref". Push the submodule first; `git push --recurse-submodules=check` (or `=on-demand`) guards against it.
- **Private submodules in CI** need credentials that can read the other repository.

In GitHub Actions:

```yaml
- uses: actions/checkout@v7
  with:
    submodules: recursive          # or true for one level
    token: ${{ secrets.SUBMODULE_READ_TOKEN }}   # only needed for private submodules
```

### 3. Subtrees: A Copy You Can Sync

`git subtree` (shipped with most Git installs) merges another repository's history, or a squashed copy of it, into a subdirectory of yours:

```bash
git subtree add --prefix=vendor/gst-rates https://github.com/chai-co/gst-rates.git main --squash
```

Now `vendor/gst-rates/` contains ordinary files in your repository. Anyone who clones gets them; CI needs nothing special; there's no `.gitmodules`.

Pulling upstream updates later:

```bash
git subtree pull --prefix=vendor/gst-rates https://github.com/chai-co/gst-rates.git main --squash
```

Sending your local fixes back upstream:

```bash
git subtree push --prefix=vendor/gst-rates https://github.com/chai-co/gst-rates.git fix/rounding
```

`--squash` adds the upstream history as a single commit instead of all of it, keeping your log clean. The reverse operation, `git subtree split --prefix=packages/upi -b upi-only`, extracts a folder's history into its own branch, useful when splitting a package out of a monorepo.

| | Submodule | Subtree |
|---|---|---|
| What's stored | A commit pointer | The files themselves |
| Clone experience | Needs `--recurse-submodules` | Just works |
| Exact version pinning | Built in | Via the merge commit |
| Contributing changes back | Natural (it's a real clone) | `git subtree push`, more manual |
| Repository size | Small | Grows with the copied files |
| Best for | Large or independently versioned components; you rarely edit them | Small shared code you vendor and occasionally patch |

**Often the best answer is neither:** if the shared code is a library, publish it as a **package** (PyPI, npm, GitHub Packages) and depend on a version. Use submodules or subtrees when packaging isn't practical (docs themes, config, shared protobufs, firmware).

### 4. Monorepos

A **monorepo** keeps many projects in one repository: Google, Meta and Microsoft do this at enormous scale, and many startups do at small scale.

**Why teams choose it:**

- **Atomic changes** across projects: change an API and all its callers in one PR.
- **One version of everything**, so no "which version of core does billing use?"
- **Shared tooling**, CI, CODEOWNERS and conventions.
- **Easy code discovery and refactoring.**

**What it costs:**

- **Scale**: clones, status and CI get slow without care.
- **CI must build only what changed**, or every PR runs everything.
- **Access control** is per repository on GitHub, so you can't hide one folder from some people.
- **Ownership** needs CODEOWNERS per directory and clear rules.

A typical Python monorepo layout using **uv workspaces**:

~~~text
chai-platform/
├── pyproject.toml            # [tool.uv.workspace] members = ["packages/*", "apps/*"]
├── uv.lock                   # one lock file for everything
├── packages/
│   ├── core/
│   ├── billing/              # depends on core
│   └── upi/                  # depends on core
├── apps/
│   ├── web/                  # depends on billing and upi
│   └── admin/                # depends on billing
└── .github/
    ├── CODEOWNERS
    └── workflows/ci.yml
~~~

### 5. Building Only What Changed

The core monorepo CI idea: from the files a PR changes, find the packages touched **and everything that depends on them**, then test only those.

```python
PACKAGES = {
    "packages/core":    [],
    "packages/billing": ["packages/core"],
    "packages/upi":     ["packages/core"],
    "apps/web":         ["packages/billing", "packages/upi"],
    "apps/admin":       ["packages/billing"],
}

def affected(changed_files):
    direct = {pkg for pkg in PACKAGES for f in changed_files if f.startswith(pkg + "/")}
    result = set(direct)
    changed = True
    while changed:
        changed = False
        for pkg, deps in PACKAGES.items():
            if pkg not in result and result.intersection(deps):
                result.add(pkg)
                changed = True
    return sorted(result)

print(affected(["apps/admin/views.py"]))
print(affected(["packages/upi/qr.py", "README.md"]))
print(affected(["packages/core/money.py"]))
```

Output:

```
['apps/admin']
['apps/web', 'packages/upi']
['apps/admin', 'apps/web', 'packages/billing', 'packages/core', 'packages/upi']
```

A change to `core` rebuilds everything, which is why core packages deserve extra review. Build tools do this properly, with caching: **Bazel**, **Pants** and **Buck2** (polyglot, large scale), **Nx** and **Turborepo** (JavaScript-centred). In plain GitHub Actions, `paths:` filters on triggers handle the simple case:

```yaml
on:
  pull_request:
    paths:
      - "packages/upi/**"
      - "packages/core/**"
      - "apps/web/**"
```

A matrix can then be generated dynamically from a script like `affected()` that writes JSON to `$GITHUB_OUTPUT` (see [Matrix Builds and Caching](../07-github-actions/matrix-builds-and-caching.md)).

### 6. Keeping a Big Repository Fast

**Partial clone** downloads commits and trees but fetches file contents (blobs) only when needed:

```bash
git clone --filter=blob:none https://github.com/chai-co/chai-platform.git
```

**Sparse checkout** only puts some directories in your working tree:

```bash
git clone --filter=blob:none --sparse https://github.com/chai-co/chai-platform.git
cd chai-platform
git sparse-checkout set packages/core packages/upi apps/web
git sparse-checkout list
```

Example output:

```
packages/core
packages/upi
apps/web
```

Combined, a developer working on UPI downloads and sees only what they need. Other helpers: `git maintenance start` (background prefetch, commit-graph and repacking), the built-in file system monitor (`git config core.fsmonitor true`) for faster `git status`, and **Scalar** (`scalar clone`), which ships with Git and turns on these settings for large repositories.

For CI, `actions/checkout` supports `fetch-depth`, `filter: blob:none` and `sparse-checkout` inputs.

### 7. Choosing

| Situation | Good fit |
|---|---|
| Shared code with its own release cycle, used by many unrelated repos | **A published package** |
| A large external component pinned at exact versions, rarely edited | **Submodule** |
| A small external folder you vendor and sometimes patch, users must clone easily | **Subtree** |
| Several services and libraries owned by one organisation, changing together | **Monorepo** |
| Strict access separation between teams' code | **Separate repositories** |

---

## Try It Yourself

1. A teammate clones your repository and `vendor/gst-rates` is empty. What happened, and what one command fixes it?
2. You fixed a bug inside `vendor/gst-rates` (a submodule), committed in the parent and pushed. CI fails with "not our ref". What did you forget?
3. Using `affected()`, which packages does a change to `packages/billing/tax.py` affect?
4. Your monorepo's clone takes 20 minutes and you only work on `apps/admin`. Which two features help, and what are the commands?

<details>
<summary>Show answers</summary>

**1.** They cloned without `--recurse-submodules`. Fix: `git submodule update --init --recursive`.

**2.** You didn't push the submodule's commit to its own remote, so the parent points at a commit nobody else can fetch. Push it (`cd vendor/gst-rates && git push`), and use `git push --recurse-submodules=on-demand` in future.

**3.**

```python
print(affected(["packages/billing/tax.py"]))
```

Output:

```
['apps/admin', 'apps/web', 'packages/billing']
```

**4.** Partial clone and sparse checkout: `git clone --filter=blob:none --sparse <url>`, then `git sparse-checkout set apps/admin packages/billing packages/core` (include what it depends on).

</details>

---

## Real-World Examples

### Example 1: Firmware with Submodules

An IoT company keeps its device firmware in one repository with the vendor's SDK as a submodule pinned to a tested commit. Upgrading the SDK is a reviewed PR that changes one gitlink, and its CI runs the full hardware test suite.

### Example 2: A Docs Theme as a Subtree

A company's 30 documentation sites share a theme vendored with `git subtree`. Writers clone and build without knowing it's there. A small script runs `git subtree pull --squash` across all sites when the theme changes.

### Example 3: Moving to a Monorepo

A startup with 14 small Python repositories kept shipping mismatched versions of its shared models. Merging them into one uv workspace with a single lock file, per-directory CODEOWNERS and affected-only CI ended the version drift; cross-cutting changes became single PRs.

---

## Common Misconceptions

### Misconception 1: "A submodule tracks a branch"

It records a **specific commit**. `branch =` only tells `git submodule update --remote` where to look when you deliberately bump it.

### Misconception 2: "Subtree means I lose upstream history"

Without `--squash` the full history is merged in; with it you get one commit per sync. Either way, you can still pull and push.

### Misconception 3: "Monorepo means one giant build"

Good monorepos build and test only affected projects, with caching.

### Misconception 4: "Monorepos must be slow"

Partial clone, sparse checkout, fsmonitor and maintenance keep even very large repositories responsive.

---

## Interview Relevance

These come up in platform, DevOps and senior engineering interviews:

- **Submodule internals:** gitlinks (mode 160000), `.gitmodules`, detached HEAD, `--recurse-submodules`.
- **Submodule versus subtree versus package**, and when you'd pick each.
- **Monorepo trade-offs:** atomic changes and shared tooling versus scale and access control.
- **CI for monorepos:** affected-project detection, path filters, build caches.
- **Scaling Git:** partial clone, sparse checkout, Scalar.

A common follow-up: *"Your team keeps breaking a shared library used by five repos. What would you do?"* Discuss publishing it with SemVer and Dependabot, or merging the consumers into a monorepo so breakages show up in the same PR.

---

## Key Takeaways

- **Submodules store a commit pointer** (gitlink) plus `.gitmodules`; clone with `--recurse-submodules` and push submodule commits before the pointer.
- **Subtrees copy files into your repository**, so clones just work; sync with `git subtree pull/push`, usually with `--squash`.
- **Prefer a published package** when shared code has its own release cycle.
- **Monorepos** trade scale problems for atomic changes; build only what's affected, with per-directory CODEOWNERS.
- **Partial clone, sparse checkout and Scalar** keep big repositories fast.

---

**Up next:** [Git LFS for Large Files](git-lfs-for-large-files.md)
